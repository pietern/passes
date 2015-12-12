# passes.py

Compute satellite passes over some location.

## Requirements

* (PyEphem)[http://rhodesmill.org/pyephem/]

## Usage

Download some TLEs (from Celestrak for example):

```
curl -o tle/iridium.txt http://celestrak.com/NORAD/elements/iridium.txt
```

Find passes of Iridium dummy masses:

```
$ ./passes.py --lat 37 --lon -122 --tle tle/iridium.txt --pattern='DUMMY' -c 1
12-12 01:57:23 -- 12-12 02:10:36 (max el. 47.25): DUMMY MASS 1 [-]
12-12 02:25:50 -- 12-12 02:39:13 (max el. 85.67): DUMMY MASS 2 [-]
```

All options:

```
$ ./passes.py --help
Usage: passes.py [options]

Options:
  -h, --help            show this help message and exit
  --lat=LATITUDE        QTH latitude (environment variable LATITUDE)
  --lon=LONGITUDE       QTH longitude (environment variable LONGITUDE)
  --tle=FILE            File containing TLEs
  --pattern=PATTERN     Regexp for satellite to filter
  -c COUNT, --count=COUNT
                        Number of passes per satellite
  -e ELEVATION, --elevation=ELEVATION
                        Minimal maximum elevation of pass
```

You can export `LATITUDE` and `LONGITUDE` environment variables and they will be picked up automatically.

If you downloaded your TLEs from Celestrak, you can update them with the `update.sh` script:

```
$ ./update.sh ./tle
Updating amateur.txt...
Updating goes.txt...
Updating iridium.txt...
Updating weather.txt...
```

## Links

* TLEs: http://celestrak.com/NORAD/elements/

## License

MIT
