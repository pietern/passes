#!/usr/bin/env python

import ephem
import os
import sys
import math
import re

from optparse import OptionParser

class TLEs:
  def __init__(self, main, path):
    self.main = main
    self.path = path
    self.sats = []
    self.read()

  def read(self):
    f = open(self.path, 'r')
    sats = []

    try:
      while True:
        line1 = f.readline()
        line2 = f.readline()
        line3 = f.readline()
        if line1 == '':
          break

        sat = ephem.readtle(line1, line2, line3)

        try:
          self.main.observer().next_pass(sat)
          sats.append(Sat(self.main, sat))
        except ValueError:
          # Skip if this satellite doesn't pass over observer (probably geostationary)
          pass
    finally:
      f.close()

    self.sats = sats

class Sat:
  def __init__(self, main, sat):
    self.main = main
    self.sat = sat
    self.name = sat.name

  def next_passes(self):
    obs = self.main.observer()
    passes = []

    while len(passes) < self.main.count:
      p = Pass(self.sat, list(obs.next_pass(self.sat)))

      if self.main.options.elevation < p.max_elevation:
        passes.append(p)

      # Skip over pass so the next iteration picks up the next pass
      obs.date = p.los_time + 1 * ephem.second

    return passes

class Pass:
  def __init__(self, sat, info):
    self.sat = sat
    self.aos_time = ephem.Date(info[0])
    self.aos_azimuth = info[1]
    self.max_elevation_time = ephem.Date(info[2])
    self.max_elevation = 180 * info[3] / math.pi
    self.los_time = ephem.Date(info[4])
    self.los_azimuth = info[5]

class Main:
  def __init__(self, options):
    self.options = options
    self.tle = TLEs(self, options.tle)
    self.pattern = re.compile(options.pattern)
    self.count = options.count

  def observer(self):
    observer = ephem.Observer()
    observer.lat = math.pi * self.options.lat / 180.0
    observer.lon = math.pi * self.options.lon / 180.0
    return observer

  def run(self):
    obs = self.observer()

    passes = []
    for sat in self.tle.sats:
      if self.pattern.match(sat.name):
        passes.extend(sat.next_passes())

    # Sort passes by AOS time
    passes = sorted(passes, key=lambda p: p.aos_time)

    for p in passes:
      aos = ephem.localtime(p.aos_time)
      los = ephem.localtime(p.los_time)

      print("%02d-%02d %02d:%02d:%02d -- %02d-%02d %02d:%02d:%02d (max el. %5.2f): %s" %
          (aos.month, aos.day, aos.hour, aos.minute, aos.second,
           los.month, los.day, los.hour, los.minute, los.second,
           p.max_elevation, p.sat.name))

def debug(msg):
  sys.stderr.write(msg + "\n")

def main():
  parser = OptionParser()
  parser.add_option("--lat", type='float', metavar='LATITUDE',
      default=os.getenv('LATITUDE'),
      help='QTH latitude (environment variable LATITUDE)')
  parser.add_option("--lon", type='float', metavar='LONGITUDE',
      default=os.getenv('LONGITUDE'),
      help='QTH longitude (environment variable LONGITUDE)')
  parser.add_option("--tle", type='string', metavar='FILE',
      help='File containing TLEs')
  parser.add_option("--pattern", type='string', default='.*',
      help='Regexp for satellite to filter')
  parser.add_option("-c", "--count", type='int', default=1,
      help='Number of passes per satellite')
  parser.add_option("-e", "--elevation", type='int', default=10,
      help='Minimal maximum elevation of pass')

  (options, args) = parser.parse_args()

  if options.lat is None or options.lon is None:
    debug("Please specify both latitude and longitude")
    sys.exit(1)

  m = Main(options)
  m.run()

if __name__ == "__main__":
  main()
