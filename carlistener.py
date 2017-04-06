#!/usr/bin/python

""" Main program to be run as a script from terminal: ./carlistener.py

The main program purposes are: 
- Instantiate everything is needed for running the CarListener 
- Define a callback to be called by the OpenXC dongle at frame reception
- Keep connecting / reconnecting to the dongle 

It is meant to be run forever but it can be interrupted by CTRL+C from
terminal
"""

__author__ 	= "Dario Fiumicello"
__email__ 	= "dario.fiumicello@gmail.com"

import time
from gpspoll.gpspoll import GPSPoll
from parsers import *
from consumers import *
from eventmanager import *
from reqs import *
from openxc.interface import BluetoothVehicleInterface
from openxc.interface import SerialVehicleInterface
from Queue import *
from utils import *

# This is for debug purposes only, can be removed once system is in production
import pdb

""" All global objects used for the program
"""
can_parser = None
can_writer = None
obd_parser = None
gps_poll = None
vi_wdg = None
event_manager = None
bt_cache = None
requested_ids = []

""" This callback is used by the OpenXC dongle when a new frame arrives
"""
def can_frame_received(frame, **kwargs):
  if 'id' in frame:
    if frame['id'] in requested_ids:
      can_parser.enqueue(frame)
    elif frame['id'] in OBDParser.obd_ids:
      obd_parser.enqueue(frame)

"""
MAIN
"""
if __name__ == '__main__':

  event_manager = EventManager()
  gps_poll = GPSPoll(location_update_callback=event_manager.new_gps_event)
  obd_parser = OBDParser(callback=event_manager.new_obd_event)
  can_parser = CANParser(callback=event_manager.new_can_event)

  requested_ids = can_parser.get_requested_ids()

  filter_configurator = FilterConfigurator(event_manager,can_parser.get_configured_messages())
  can_writer = CANWriter(event_manager)
  vi_wdg = VIWatchdog()

  bt_cache = BTCache()

  event_manager.set_timesource(SYSTimesource())

  # All event consumers
  event_manager.register_consumer(filter_configurator)
  event_manager.register_consumer(vi_wdg)
  
  event_manager.register_consumer(PrintConsumer())
  event_manager.register_consumer(RESTConsumer(event_manager))
  #event_manager.register_consumer(MQTTConsumer(event_manager \
  #  ,CollaboxOutletParser()))
  #event_manager.register_consumer(can_writer)
  #event_manager.register_consumer(JSONFileConsumer())
  event_manager.register_consumer(OBDVINRequest(event_manager))
  #event_manager.register_consumer(OBDSpeedRequest(event_manager))
  #event_manager.register_consumer(OBDFuelTankLevelRequest(event_manager))

  #event_manager.register_consumer(WSConsumer(event_manager \
  #  ,NullParser(),"localhost",8001))

  while True:
    event_manager.new_log_event("info", "Connecting to VI..." \
          , fired_by="Main")

    vi = None;

    try:
      vi = BluetoothVehicleInterface(address=bt_cache.get_address() \
        ,callback=can_frame_received \
        ,payload_format='json')
      vi.start() # This will block until VI is connected
      event_manager.new_vi_connect_event(vi)
      if not bt_cache.set_address(vi.address):
        event_manager.new_log_event("warning" \
          ,"Cannot cache bluetooth address. Please check cache file path!" \
          , fired_by="BTCache");

      # This inner cycle is meant to periodically check the status of the VI
      # independently from the OpenXC library.
      # It happened sometimes that even if the connection was interrupted the 
      # vi.join() didn't return; using vi.join(5) we block the VI thread for 
      # 5 seconds and then check if everything was ok.
      while True:
        vi.join(5)
        #event_manager.new_gps_event({ "longitude":2.073287, "latitude":48.800045, "altitude":8.2})
        #time.sleep(2)
        #event_manager.new_gps_event({ "longitude":2.094528, "latitude":48.809006, "altitude":138.0})
        if not vi_wdg.vi_ok() or not vi.is_alive():
          break
    except Exception as e:
      #pdb.set_trace() # TODO: let this became an event
      event_manager.new_vi_error_event(e,fired_by="Main")

    try:
      vi.stop()
    except Exception as e:
      event_manager.new_vi_error_event(e,fired_by="Main")

    try:
      # The vi.disconnect() method was not present in the original OpenXC
      # library. It was added because sometimes, after an error, the BT
      # connection remained on, so this software wasn't able to connect
      # anymore. vi.disconnect() closes the BT socket causing an
      # effective disconnection
      vi.disconnect()
    except Exception as e:
      event_manager.new_vi_error_event(e,fired_by="Main")
      
    event_manager.new_vi_disconnect_event()
    del vi
    time.sleep(1)

  # Cleanup stuff at the end of the program
  filter_configurator.stop()
  gps_poll.stop()
  obd_parser.stop()
  can_parser.stop()
  can_writer.stop()
  event_manager.stop()

      
      
  
