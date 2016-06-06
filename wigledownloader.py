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

import argparse, os, subprocess, shutil, glob, time

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
    def __init__( self, user, password, coordfile ):
        self.wigle_user = user
        self.wigle_password = password
        self.latmin = 47.95
        self.latmax = 48.43
        self.lonmin = 11.00
        self.lonmax = 12.15
        self.latdiv = 6
        self.londiv = 10
        self.div_map = [[ 2, 2, 2, 2, 2, 2, 8, 2, 2, 2],
                        [ 2, 2, 2, 2, 4, 3, 2, 5, 2, 2],
                        [ 2, 4, 5, 4, 4, 4, 2, 4, 2, 2],
                        [ 2, 4, 4, 8,18, 8, 8, 6, 2, 2],
                        [ 2, 2, 2, 4,16, 8, 4, 2, 2, 2],
                        [ 2, 2, 4, 4, 4, 4, 2, 2, 2, 2]]
        self.intervals = self._compute_intervals()


    def _compute_intervals(self):
        """
        Returns a list with tuples containing:
            [(box_lat_min,box_lat_max,box_lon_min,box_lon_max),...]
        """
        if len(self.div_map) != self.latdiv or len(self.div_map[0]) != self.londiv:
            raise RuntimeError('Map dimensions not correct!')

        lat_setp = (self.latmax - self.latmin)

    def parse_coordfile( self, coordfile ):
        with open(coordfile) as f:
            line = f.readline()
            while line:
                line = line.strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Wigle Downloader arguments')
    parser.add_argument(
        '-u', '--user', help='Wigle username', required=True )
    parser.add_argument(
        '-p', '--password', help='Wigle password', required=True )
    parser.add_argument(
        '--coordfile', help='coord.remain file path', required=False, default=None )

    args = parser.parse_args()
    wigledownloader = WigleDownloader(args.user, args.password, args.coordfile)
