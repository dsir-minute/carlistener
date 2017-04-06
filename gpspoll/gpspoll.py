""" Wrapper over the gpsd daemon

The purposes of this class are:
- Wrapping and hiding the usage of gpsd
- Providing a method to synchronously obtain the last available position
- Calling a callback function as soon as a new GPS position is available
- Acting as a time source by providing the timestamp of the GPS module
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from gps import *
from time import *
import time
import threading
import geohash
import math

class GPSPoll(threading.Thread):
  """ The GPSPoll class is designed as an independent thread in order to 
  call the callback function asynchronously.
  """

  # If True, the location_update_callback() will be called only when a
  # significant variation occurs, if False the callback will be called
  # every time gpsd updates the fix.
  NOTIFY_ON_CHANGE_ONLY = False

  def __init__(self, location_update_callback=None):
    threading.Thread.__init__(self)
    self.daemon = True
    self._location_update_callback = location_update_callback
    self._gpsd = gps(mode=WATCH_ENABLE)  
    self._last_GPS_fix_lock = threading.Lock()
    self._last_GPS_fix = gpsfix() 
    self._last_geohash = ''
    self._last_n_sats = 0
    self._last_time = self._gpsd.utc
    self._can_run = True
    self.start()
 
  """ This is the default Thread method called on start()
  """
  def run(self):
    while self._can_run:
      # This method will block on the gpsd daemon. It will return as soon as
      # new gps information is available 
      self._gpsd.next()

      currentGeohash = ''
      if self._gpsd.fix.mode != MODE_NO_FIX:
        self._last_time = self._gpsd.utc;
        self._last_n_sats = self._gpsd.satellites_used if \
          self._gpsd.satellites_used != NaN else 0
        try:
          if self._gpsd.fix.latitude != NaN \
            and self._gpsd.fix.longitude != NaN \
            and self._gpsd.fix.epx != NaN \
            and self._gpsd.fix.epy != NaN:
            currentGeohash = geohash.encode(self._gpsd.fix.latitude \
              , self._gpsd.fix.longitude \
              ,precision=self.get_geohash_precision(self._gpsd.fix.epx \
              ,self._gpsd.fix.epy) \
            )  
        except Exception as e:
          # TODO: Fire an error event
          print e
          pass

        # We will call the location_update_callback only if the current 
        # geohash is different from the last one OR if the
        # NOTIFY_ON_CHANGE_ONLY is False.
        # Since the geohash is computed according to the precision 
        # informations provided by gpsd, it will only change when 
        # the new latitude / longitude data have changed significantly.
        # NOTE: You can still have situations where you don't move the GPS
        # module and you will have a location update. That is dued to the fact
        # that gpsd precision data may also fluctuate and the function to
        # calculate geohash precision has some approximation. You can reduce
        # the number of this fluctuation by subtracting 1 to the result
        # of get_geohash_precision() function
        if GPSPoll.NOTIFY_ON_CHANGE_ONLY is False \
          or currentGeohash != self._last_geohash:
          with self._last_GPS_fix_lock:
            self._last_geohash = currentGeohash
            self._last_GPS_fix = self._gpsd.fix
          if self._location_update_callback is not None:
            self._location_update_callback(self.position())
   
  """ This class can act also as a time source, thus providing a timestamp
  through the get_time() method. See EventManager.set_timesource()
  """
  def get_time(self):
    if self._last_time == None or self._last_time == NaN:
      return None
    else:
      return self._last_time

  """ This function provides an approximated geohash precision by knowing the
  epx and epy values provided by gpsd.
  See:
  - https://en.wikipedia.org/wiki/Geohash
  - http://geohash.org/
  - http://stackoverflow.com/questions/13448595/geohash-string-length-and-accuracy
  """
  def get_geohash_precision(self,epx,epy):
    if epx == NaN or epy == NaN:
      return 1
    maxVal = max(epx,epy)
    return int(max(min(math.floor(math.log(5000000/maxVal, 2)/2.5+1),12),1))

  """ This is a synchronous function to get the last GPS position data when
  known.
  """
  def position(self):
    lastPosition = { }
    with self._last_GPS_fix_lock:
      if self._last_GPS_fix.mode != MODE_NO_FIX:
        lastPosition = { 
                'latitude' : self._last_GPS_fix.latitude,
                'longitude' : self._last_GPS_fix.longitude,
                'gpsd_time' : self._gpsd.utc,
                'geohash' : self._last_geohash,
                'n_sats' : self._last_n_sats
               }
        if self._last_GPS_fix.speed != NaN:
          lastPosition['speed'] = self._last_GPS_fix.speed
        if self._last_GPS_fix.altitude != NaN:
          lastPosition['altitude'] = self._last_GPS_fix.altitude
        if self._last_GPS_fix.track != NaN:
          lastPosition['heading'] = self._last_GPS_fix.track

    return lastPosition

    """ The stop() function can be used to securely stop the thread that calls
    the location update callback function.
    """
    def stop(self):
      self._can_run = False
