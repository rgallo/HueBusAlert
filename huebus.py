import json
import requests
import time
import datetime
import dateutil.parser
from phue import Bridge
import argparse

BUSTIME_URL="http://bustime.mta.info/api/siri/stop-monitoring.json"

# https://stackoverflow.com/questions/796008/cant-subtract-offset-naive-and-offset-aware-datetimes
ZERO = datetime.timedelta(0)
class UTC(datetime.tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO
utc = UTC()
###

def get_light_state(huebridge, lightname):
    lightstate = huebridge.get_light(lightname).get("state")
    return {'hue': lightstate["hue"], 'sat': lightstate["sat"], 'bri': lightstate["bri"], 'on': lightstate["on"]}

def set_light(huebridge, lightname, hue, sat, bri):
    huebridge.set_light(lightname, {'hue': hue, 'sat': sat, 'bri': bri, 'on': True})

def loop(url, huebridge, lightname, ranges, defaultrange):
    resp = requests.get(url).json()
    mvjs = resp["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0]["MonitoredStopVisit"]
    arrivaltimes = map(dateutil.parser.parse, filter(None, [mvj.get("MonitoredVehicleJourney", {}).get("MonitoredCall", {}).get("ExpectedDepartureTime", None) for mvj in mvjs]))
    now = datetime.datetime.now(utc)
    print [(t-now).seconds for t in arrivaltimes]
    for range in ranges:
      if [t for t in arrivaltimes if range["min"] < (t-now).seconds < range["max"]]:
        set_light(huebridge, lightname, range.get("hue", 254), range.get("sat", 254), range.get("bri", 254))
        break
    else:
      set_light(huebridge, lightname, defaultrange.get("hue", 254), defaultrange.get("sat", 254), defaultrange.get("bri", 254))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", help="runtime in minutes")
    args = parser.parse_args()
    runtime = int(args.runtime)
    endtime = datetime.datetime.now() + datetime.timedelta(minutes=runtime)
    with open("config.json", "r") as cfgfile:
        config = json.load(cfgfile)
    huebridge = Bridge(config.get("bridge"))
    lightname = config.get("lightname")
    initial_lightstate = get_light_state(huebridge, lightname)
    url = "{}?{}".format(BUSTIME_URL, "&".join("{}={}".format(k, v) for k, v in config.get("apiparams").iteritems()))

    while datetime.datetime.now() < endtime:
        print datetime.datetime.now(), endtime
        loop(url, huebridge, lightname, config.get("ranges"), config.get("defaultrange"))
        time.sleep(30)
    huebridge.set_light(lightname, initial_lightstate)


if __name__ == "__main__":
    main()
