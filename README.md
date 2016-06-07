# wigledownloader

Downloads all APs from wigle.net from a given area

## In a nutshell

```bash
pip install wigle
git clone https://github.com/tonetto/wigledownloader.git
mkdir ./files
python2 wigledownloader/wigledownloader.py -u <user> -p <password> -o ./files/
```

Please read the rest of this document to understand how to specify which area you want to download APs from.

## About it

This is a (very) simple python code that downloads all available APs listed at wigle.net for a given area.

## How to specify your desired area

I was super lazy while coding this, so the only way for this (at the moment) is editing the source code.

Inside the `wigledownloader.py` you'll find the following lines:

```python
        ...
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
        ...
```
Please edit:
* `latmin, latmax, lonmin, lonmax` which should be self-explanatory,
* `latdiv` and `londiv` are the number of divisions you want along the latitude axis (y-axis) and along the longitude axis (x-axis), and finally
* `div_map` with the number of subdivisions you would like inside each division.

The following image represents the example that is hardcoded into this script:

![Wigle Munich](https://github.com/tonetto/wigledownloader/blob/master/misc/wigle_munich.jpg "Wigle map of Munich")

There are 6 divisions on the y-axis (latitude) and 10 divisions on the x-axis (longitude). The numbers inside each division represent the number of subdivisions within each division (it's not so complicated).

If you do not want to bother picking these numbers manually, uncomment the lines (show in the code snippet above as `#self.div_map = [[1]*self.londiv]*self.latdiv`) and comment the long list with the same name below it.

In either way, if the code finds more APs it can actually download from wigle (with a single query), the download of that subdivision is restarted. This time, the box is subdivided (again) into two smaller parts. This operation will repeat as long as needed. Therefore, even if you take the lazy approach it will eventually work.

The problem of the lazy approach is that each time the number of downloaded APs reaches a limit, all the already downloaded are discarded before subdivided the area again.

## Running it

This should be very simple, but there are two ways of doing it:
* From zero (you never ran it before for the same query):
```bash
python2 wigledownloader/wigledownloader.py -u <user> -p <password> -o ./files/
```

As soon as you run this code (and periodically) it writes in a file called `coord.remain` the remaining subdivisions it still has to download. You are going to use this file to restart your download if you ever have to stop it.

* After running it for a while (restarting):
```bash
python2 wigledownloader/wigledownloader.py -u <user> -p <password> -o ./files/ --coordfile coord.remain
```
This way it should continue from where it left the last time it was running.

## Output files

For now it is simplying saving everything as a [pickle](https://docs.python.org/2/library/pickle.html "Python object serialization") file.
