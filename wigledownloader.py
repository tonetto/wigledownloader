#!/usr/bin/env python
# -*- coding: utf-8 -*-

## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## version 2 as published by the Free Software Foundation.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
##
## author: Leonardo Tonetto

__author__ = "Leonardo Tonetto"
__copyright__ = "Copyright 2016, Leonardo Tonetto"
__license__ = "GPLv2"
__version__ = "0.1"

import sys

try:
    import wigle
except ImportError:
    print >> sys.stderr, 'Please install wigle (eg. pip install wigle)'
    sys.exit(1)

import argparse, pickle, time

def drange(start, stop, step):
    """
    Float point implementation of range()

    Based on (but not exactly):
    http://stackoverflow.com/questions/477486/python-decimal-range-step-value
    """
    ## few sanity checks first
    if start < stop and step < 0:
        raise RuntimeError('Wrong input variables, step should be > 0.')
    if start > stop and step > 0:
        raise RuntimeError('Wrong input variables, step should be < 0.')
    r = start
    while start < stop and r < stop:
     	yield r
     	r += step
    while start > stop and r > stop:
        yield r
        r += step


class WigleDownloader:
    """
    Downloads AP info from wigle.net

    [HARDCODED] YEEEAH!
    lat/lon_min/max : interval of the desired area.
    lat_lon_div : number of divisions along each axis (used to double check).
    div_map: initial num. of subdivisions inside each original division
             this has to have the same number of columns/rows as the *_div arg.
             Ref.: [0][0] is the upper left box
             In case none is given, 1 is applied to all boxes
    """
    ## Some constants
    wigle_downloads_per_page = wigle.WIGLE_PAGESIZE
    wigle_max_ap_per_query = 10000
    ## These add up to 24h, time we would expect to have the quota renewed
    wigle_timeout_backoff = [0.25*3600, ## 15 minutes
                             0.25*3600,
                             0.5*3600,
                             1*3600,
                             2*3600,
                             4*3600,
                             8*3600,
                             8*3600]    ##  8 hours
    file_default_remain = './coord.remain'
    
    def __init__( self, user, password, coordfile, outpath ):
        try:
            ## Wigle, wigle, wigle :-)
            self.wigle = wigle.Wigle( user, password )
        except wigle.WigleAuthenticationError as wae:
            print >> sys.stderr, 'Authentication error for {1}.'.format(user)
            print >> sys.stderr, wae.message
            sys.exit(-1)
        except wigle.WigleError as werr:
            print >> sys.stderr, werr.message
            sys.exit(-2)

        self.outpath = outpath
        self.coordfile = coordfile
        ## This is for the city of Munich-DE
        ## TODO: replace this with geocoding
        self.latmin = 47.95
        self.latmax = 48.43
        self.lonmin = 11.00
        self.lonmax = 12.15
        self.latdiv = 6
        self.londiv = 10
        ## For the lazy: use this one
        ## Do not modify this lazy map after this point since rows will be the same object...
        #self.div_map = [[1]*self.londiv]*self.latdiv
        ## Or you can do it like that
        self.div_map = [[ 2, 2, 2, 2, 2, 2, 8, 2, 2, 2],
                        [ 2, 2, 2, 2, 4, 3, 2, 5, 2, 2],
                        [ 2, 4, 5, 4, 4, 5, 2, 4, 2, 2],
                        [ 2, 4, 4, 8,18, 8, 8, 6, 2, 2],
                        [ 2, 2, 3, 4,16, 8, 4, 2, 2, 2],
                        [ 2, 2, 4, 4, 4, 4, 2, 2, 2, 2]]
        self.INTERVALS = []
        self.REMAINING_INTERVALS = []


    def run(self):
        """
        Just so that it does not look so ugly
        """
        ## We either call compute_intervals() or parse_coordfile()
        if self.coordfile:
            self.parse_coordfile()
        else:
            self.compute_intervals()

        self.REMAINING_INTERVALS = self.INTERVALS[:]
        self.REMAINING_INTERVALS.reverse()

        ## Now we (continue) download(ing)
        self.download()


    def download(self):
        """
        Download whatever is inside self.INTERVALS using
        wigle pythong API (not official apparently)
        """
        def callback_newpage(since):
            pass
        def _download( lat1, lat2, lon1, lon2, backoff_idx=0 ):
            """
            This one will be called recursively until the subdivision
            is fully downloaded. In case it reaches 10k it breaks down
            this subdivision into two parts by dividing the longitude
            interval into two. Something like this:

                         lat2
                  -----------------
                 |                 |              ^
                 |                 |              | N
            lon1 |                 | lon2
                 |                 |
                 |                 |
                  -----------------
                         lat1

            Becomes:

                         lat2
                  -----------------
                 |        |        |              ^
                 |        |        |              | N
            lon1 |        |        | lon2
                 |        |lon1_5  |
                 |        |        |
                  -----------------
                         lat1

            """
            print >> sys.stdout, 'Downloading ({0},{1},{2},{3})'.format( lat1, lat2, lon1, lon2 )
            try:
                RESULTS = self.wigle.search( lat_range   = ( lat1, lat2 ),
                                             long_range  = ( lon1, lon2 ),
                                             on_new_page = callback_newpage,
                                             max_results = WigleDownloader.wigle_max_ap_per_query )
                # Need to double check this
                if len(RESULTS) >= 9998:
                    print >> sys.stderr, 'Subdividing {0} {1} {2} {3}'.format(lat1,lat2,lon1,lon2)
                    ## Will break down longitude interval into two parts
                    lon1_5 = (lon2-lon1)/2.0
                    R1 = _download( lat1, lat2, lon1, lon1_5 )
                    R2 = _download( lat1, lat2, lon1_5, lon2 )
                    RESULTS = R1.copy()
                    RESULTS.update(R2)

            except wigle.WigleRatelimitExceeded as wrle:
                wait_s = WigleDownloader.wigle_timeout_backoff[backoff_idx]
                print >> sys.stderr, 'Already got WigleRatelimitExceeded.'
                print >> sys.stderr, 'Sleeping for {0} seconds before trying again.'.format(wait_s)
                time.sleep(wait_s)
                ## We may enter an infinite loop here...
                ## TODO: solve it (for now check the stdout for problems)
                return _download(lat1, lat2, lon1, lon2,
                                 backoff_idx=(backoff_idx+1)%len(WigleDownloader.wigle_timeout_backoff))
            except wigle.WigleError as we:
                print >> sys.stderr, we
                print >> sys.stderr, 'Something wrong with Wigle, stopping..'
                raise
            except KeyboardInterrupt:
                print >> sys.stderr, 'Stopping the script.'
                sys.exit(0)
            except:
                print >> sys.stderr, 'This looks like a bug.', sys.exc_info()[0]
                return []
            else:
                sucess_string = 'Sucess downloading ({0},{1},{2},{3}) with {4} APs'
                print >> sys.stdout, sucess_string.format( lat1, lat2, lon1, lon2, len(RESULTS) )
                return RESULTS
                
        try:
            ##
            for interval in self.INTERVALS:
                assert len(interval) == 4, 'Something wrong generating self.INTERVALS.'

                lat1,lat2,lon1,lon2 = interval
                AP_SUBDIVISION = _download( lat1, lat2, lon1, lon2 )

                ## Write this out using pickle
                ## TODO: write out as sqlite file
                pickle_file = '{0}/{1}_{2}_{3}_{4}.p'.format( self.outpath, lat1, lat2, lon1, lon2 )
                pickle.dump(AP_SUBDIVISION, open( pickle_file, "wb" ))
                
                ## Note: this was .reverse()'ed before
                ## Pop'ing from the end of the list is much quicker
                self.REMAINING_INTERVALS.pop()
                
                ## Write out coord.remain
                with open( WigleDownloader.file_default_remain, 'wb' ) as coord_remain_file:
                    for interval in self.REMAINING_INTERVALS:
                        print >> coord_remain_file, ','.join(map(str,interval))

        except KeyboardInterrupt:
            print >> sys.stderr, 'Stopping the script.'
            sys.exit(0)
        except:
            print >> sys.stderr, 'This looks like a bug.', sys.exc_info()[0]
            sys.exit(-3)
            

    def compute_intervals(self):
        """
        Returns a list with tuples containing:
            [(box_lat_min,box_lat_max,box_lon_min,box_lon_max),...]
        Since [0][0] is the upper left corner, lon grows positively
        but lat grows negatively.
        """
        if len(self.div_map) != self.latdiv or len(self.div_map[0]) != self.londiv:
            raise RuntimeError('Map dimensions not correct!')

        ## Compute the size of each initial box (in degrees).
        lat_step = -(self.latmax - self.latmin) / self.latdiv
        lon_step =  (self.lonmax - self.lonmin) / self.londiv

        ## Compute the intervals.
        initial_lat = self.latmax
        initial_lon = self.lonmin
        for row in self.div_map:
            initial_lon = self.lonmin
            for subdivisions in row:
                lat_sub_step = lat_step / float(subdivisions)
                lon_sub_step = lon_step / float(subdivisions)

                ## min for each subdivision, for max we just add sub_step to it.
                lats = list(drange(initial_lat,initial_lat+lat_step,lat_sub_step))
                lons = list(drange(initial_lon,initial_lon+lon_step,lon_sub_step))

                self.INTERVALS.extend([( lat, lat+lat_sub_step,
                                         lon, lon+lon_sub_step ) for lat,lon in zip( lats, lons )])
                initial_lon += lon_step
            initial_lat += lat_step


    def parse_coordfile( self, coordfile ):
        """
        Parses the coord.remain file with the following format:

        lat1,lat2,lon1,lon2

        """
        with open(coordfile) as f:
            line = f.readline()
            while line:
                COORDS = line.strip().split(',')
                assert len(COORDS) == 4, 'Something is wrong with coord.remain file.'
                self.INTERVALS.append(tuple(COORDS))
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wigle Downloader arguments')
    parser.add_argument(
        '-u', '--user', help='Wigle username', required=True )
    parser.add_argument(
        '-p', '--password', help='Wigle password', required=True )
    parser.add_argument(
        '--coordfile', help='coord.remain file path', required=False, default=None )
    parser.add_argument(
        '-o', '--outpath', help='Path to store pickle files.')

    args = parser.parse_args()
    wigledownloader = WigleDownloader( args.user, args.password, args.coordfile, args.outpath )
    ## Not recommended to put this in a subprocess.
    wigledownloader.run()
