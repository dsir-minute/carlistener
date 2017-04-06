#!/usr/bin/python

""" Main program to be run as a script from terminal: ./gpslistener.py

This is a stripped version of the CarListener that only listens for GPS
events

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
from Queue import *
from utils import *

from sysmon.systemmonitor import SystemMonitor

# This is for debug purposes only, can be removed once system is in production
import pdb

""" All global objects used for the program
"""
gps_poll = None


"""
MAIN
"""
if __name__ == '__main__':

  event_manager = EventManager()
  gps_poll = GPSPoll(location_update_callback=event_manager.new_gps_event)
  system_monitor = SystemMonitor(callback=event_manager._new_event)

  event_manager.set_timesource(SYSTimesource())
  event_manager.register_consumer(PrintConsumer())
  event_manager.register_consumer(WSConsumer(event_manager \
    ,VTPocParser(),"vtpoc.ddns.net",8085))
  #  ,VTPocParser(),"192.168.1.3",8085))

  event_manager.new_log_event("info", "Listening for GPS events..." \
          , fired_by="Main")
  while True:
    #event_manager.new_gps_event({ "longitude":2.073287, "latitude":48.800045})
    time.sleep(2)
    #event_manager.new_gps_event({ "longitude":2.094528, "latitude":48.809006})
    time.sleep(2)

  gps_poll.stop()
  system_monitor.stop()
  event_manager.stop()

      
      
  
