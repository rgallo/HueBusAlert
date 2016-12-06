import json
import requests
import time
import datetime
import dateutil.parser
from phue import Bridge

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

def set_light(huebridge, lightname, hue, sat, bri):
    huebridge.set_light(lightname, {'hue': hue, 'sat': sat, 'bri': bri, 'on': True})

def loop(url, huebridge, lightname, ranges, defaultrange):
    resp = requests.get(url).json()
    #print resp
    mvjs = resp["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0]["MonitoredStopVisit"]
    arrivaltimes = map(dateutil.parser.parse, filter(None, [mvj.get("MonitoredVehicleJourney", {}).get("MonitoredCall", {}).get("ExpectedDepartureTime", None) for mvj in mvjs]))
    now = datetime.datetime.now(utc)
    print "Now: {}".format(now)
    print arrivaltimes
    print [(t-now).seconds for t in arrivaltimes]
    for range in ranges:
      if [t for t in arrivaltimes if range["min"] < (t-now).seconds < range["max"]]:
        set_light(huebridge, lightname, range.get("hue", 254), range.get("sat", 254), range.get("bri", 254))
        break
    else:
      set_light(huebridge, lightname, defaultrange.get("hue", 254), defaultrange.get("sat", 254), defaultrange.get("bri", 254))

def main():
    with open("config.json", "r") as cfgfile:
        config = json.load(cfgfile)
    huebridge = Bridge(config.get("bridge"))
    url = "{}?{}".format(BUSTIME_URL, "&".join("{}={}".format(k, v) for k, v in config.get("apiparams").iteritems()))
    print url
    lightname = config.get("lightname")

    while True:
        loop(url, huebridge, lightname, config.get("ranges"), config.get("defaultrange"))
        time.sleep(30)


if __name__ == "__main__":
    main()
