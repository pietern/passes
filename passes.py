#!/usr/bin/env python

import ephem
import os
import signal
import sys
import math
import re
import subprocess
import time
import parsedatetime

from datetime import datetime
from time import mktime
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

  def date(self):
    cal = parsedatetime.Calendar()
    time_struct, _ = cal.parse(self.options.time)
    return datetime.utcfromtimestamp(mktime(time_struct))

  def observer(self):
    observer = ephem.Observer()
    observer.lat = math.pi * self.options.lat / 180.0
    observer.lon = math.pi * self.options.lon / 180.0
    observer.date = self.date()
    return observer

  def run(self, args):
    obs = self.observer()

    passes = []
    for sat in self.tle.sats:
      if self.pattern.match(sat.name):
        passes.extend(sat.next_passes())

    # Sort passes by AOS time
    passes = sorted(passes, key=lambda p: p.aos_time)

    if self.options.execute:
      if self.options.time != "now":
        raise Exception("cannot execute in non-realtime mode")
      self.execute(passes, args)
    else:
      self.display(passes)

  # Take sorted list of passes, convert it into a list of
  # lists of passes that overlap.
  def passes_to_chunks(self, passes):
    passes = passes[:]
    chunks = []
    while len(passes) > 0:
      # Group overlapping passes together
      chunk = [passes.pop(0)]
      while len(passes) > 0:
        if passes[0].aos_time <= chunk[-1].los_time:
          chunk.append(passes.pop(0))
        else:
          break

      chunks.append(chunk)
    return chunks

  def execute(self, passes, args):
    chunks = self.passes_to_chunks(passes)
    for chunk in range(chunks):
      self.display(chunk)

      # Wait until AOS
      now = datetime.now()
      aos = ephem.localtime(chunk[0].aos_time)
      until_aos = (aos - now).total_seconds()
      print("Sleeping %d seconds until AOS" % (until_aos))
      time.sleep(until_aos)

      # Run command for pass(es)
      process = subprocess.Popen(args, preexec_fn=os.setsid)

      # Wait until LOS
      now = datetime.now()
      los = ephem.localtime(chunk[-1].los_time)
      until_los = (los - now).total_seconds()
      print("Sleeping %d seconds until LOS" % (until_los))
      time.sleep(until_los)

      # Send the signal to all the process groups
      os.killpg(os.getpgid(process.pid), signal.SIGTERM)

  def display(self, passes):
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
  parser.add_option("-t", "--time", type='string', default="now",
      help='Time of observation')
  parser.add_option("-x", action='store_true', dest='execute',
      help='Execute command for the duration of one or more passes')

  (options, args) = parser.parse_args()

  if options.lat is None or options.lon is None:
    debug("Please specify both latitude and longitude")
    sys.exit(1)

  m = Main(options)
  m.run(args)

if __name__ == "__main__":
  main()
