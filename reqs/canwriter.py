"""
This module provides the class for periodically writing user CAN messages on
the bus.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from openxc.interface import BluetoothVehicleInterface
import weakref
import json
from utils import Scheduler

import time
import pdb

class CANWriter():
	"""
	CANWriter loads and parses the wcan.json file in order to schedule the
	writing of the user's CAN messages. Here is an example of the file:
	{
		"write_messages": {
    		"0x138": {
      			"data": "0xa000000000000000",  
      			"frequency": 1
    		},
    		"0x082": {
      			"data": "0x000000000000000b",  
      			"frequency": 2
    		}
  		}
	}
	For every CAN id the user wants to write for, it has to specify both
	the 8 byte data and the frequency, as shown in the example.
	"""
	def __init__(self,event_manager,conf_file="wcan.json"):
		self._w_vi = None
		self._write_ids = []
		self._event_manager = event_manager
		self._conf_loaded = self._load_configuration_from_file(conf_file)

		# The schedule for the messages to write is maintained by the
		# Scheduler class. See scheduler.py
		self._scheduler = Scheduler()
		if self._conf_loaded and len(self._write_ids) > 0:
			self._scheduler.load_periodic_tasks_schedule(self._write_ids)

	"""
	CANWriter will listen for the connection event in order to start writing
	on the can bus. As soon as VI is connected the scheduler is requested to
	execute. For any other VI event (disconnection o error) the scheduler will
	stop executing.
	"""
	# TODO: Check the events differents from "connection"
	def consume(self, event):
		if self._conf_loaded \
			and event['type'] == 'VI' \
			and event['name'] == 'connection':
			if event['value'] == 'connected':
				self._w_vi = weakref.ref(event['vi'])
				self._scheduler.execute()
			else:
				self._scheduler.stop()
				self._w_vi = None

	"""
	Opens the configuration file and tries to load it. Parsing and data 
	enrichment is made using self._conf_parse() method.
	"""
	def _load_configuration_from_file(self, configuration_file):
		ret = False
		if configuration_file is None:
			return ret
		try:
			with open(configuration_file) as json_data:
				conf_dict = json.load(json_data)
				if self._conf_parse(conf_dict):
					for can_id in conf_dict['write_messages'].keys():
						self._write_ids.append( \
							conf_dict['write_messages'][can_id])
					ret = True
				else:
					print "TODO: Add a log! Configuration error wcan.conf!"
				json_data.close()

		except ValueError as ve: 
			print "TODO: Add a log! Configuration format error wcan.conf! " \
				+str(ve)

		except Exception as e:
			print "TODO: Add a log! Configuration error wcan.conf! "+str(e)
		
		finally:
			return ret

	"""
	Checks if the configuration is ok and enrich the data by adding
	all the informations needed by the scheduler.
	RULES:
	- data and frequency are mandatory for each ID
	- Frequency has to be a number != 0
	- Data must be an hex representation of an 8 byte vector like
	  "0x01234567890abcde"
	"""
	def _conf_parse(self,configuration):
		# TODO: Check for data to be exactly 8 byte
		for can_id in configuration['write_messages']:
			message = configuration['write_messages'][can_id]
			if not all (k in message for k in \
				('data','frequency')):
				return False

			# All this informations are required by the scheduler. 
			# See Scheduler class
			message['id'] = can_id
			message['period'] = 1.0/message['frequency']
			message['func'] = self._write_func
			message['args'] = [can_id, message['data']]

			# This information is not necessary to the scheduler, so it
			# can be removed to keep the dictionary clean
			message.pop('frequency', None)
			message.pop('data', None)

		return True

	"""
	This is the definition of the function that the scheduler has to call
	every time it has a task ready for execution. The args of this function
	are simply the can_id to write on and the data to write.
	See Scheduler class
	"""
	def _write_func(self,args):
		try:
			can_id = args[0]
			data = args[1]
			vi = self._w_vi()
 			if vi is not None:
 				vi.write_raw(can_id, data, bus=1)
 		except Exception as e:
 			self._scheduler.stop()
			self._w_vi = None
  			self._event_manager.new_vi_error_event(e,fired_by="CANWriter")

  	"""
  	Let's clean the scheduler in order to avoid problems after destruction
  	"""
	def __del__(self):
		self._scheduler.kill()
