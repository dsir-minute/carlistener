"""
This module provides a class for filtering CAN IDs on the VI dongle.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from openxc.interface import BluetoothVehicleInterface
import threading
from eventmanager import *

class FilterConfiguratorException(Exception):
	"""
	This is just to have a meaningful named exception
	"""
	pass

class FilterConfigurator(threading.Thread):
	"""
	This class is responsible for sending the VI all the CAN ID that the user
	wants to read.

	By default the VI firmware is compiled to filter everything except 
	OBD IDs. In order to read all the CAN ID the user requires, CarListener
	has to send	the filter_message() command for each ID. Actually the 
	maximum number of user IDs is 16, you can always check and modify this 
	number in the vi firmware by editing src/can/canutil.h
	"""

	"""
	Constructor requires a reference to the event manager and a dictionary
	containing all the CAN IDs and the required dynamics for every one of it.
	This is an example of messages dictionary:
	{
		0x100 : {
			'max_frequency': 0,
			'force_send_changed': True
			},
		0x101 : {
			'max_frequency' : 2.0,
			'force_send_changed': False
		}
	}
	"max_frequency" is the maximum frequency the message can be sent by the 
	dongle to the CarListener. If 0 then the maximum configured frequency for
	the vi firmware will be used.
	If "force_send_changed" is True and the message changes faster than the
	max_frequency, the dongle will send it immediatly. If False, the message
	will be sent exactly at the max_frequency, even if it changes faster.
	See:
	  http://vi-firmware.openxcplatform.com/en/latest/config/raw-examples.html
	  CANParser class
	"""
	def __init__(self,event_manager,messages):
		threading.Thread.__init__(self)
		self.daemon = True
		self._can_run = True
		self._event_manager = event_manager
		self._connect_event = threading.Event()
		self._connect_event.clear()
		self._vi = None
		self._messages = messages
		self.start()
	
	"""
	The filter configurator will run for ever, waiting for a VI to connect.
	As soon as VI is connected it will set all the required filters.
	"""
	def run(self):
		while self._can_run:
			try:
  				connected = self._connect_event.wait(2)
  				if connected is True:
  					for can_id in self._messages:
  						if not self._vi.filter_message(1 \
  							, can_id \
  							, max_frequency=\
  								self._messages[can_id]['max_frequency'] \
  							, force_send_changed=\
  								self._messages[can_id]['force_send_changed']):
  							self._event_manager.new_vi_error_event( \
  								FilterConfiguratorException( \
  									"Cannot set filter for id "+str(can_id)) \
  								,fired_by="FilterConfigurator")
  							break
  			
  			except Exception as e: 
  				self._event_manager.new_vi_error_event( \
  					e,fired_by="FilterConfigurator")

  			finally:
  				self._connect_event.clear()

  	"""
  	Gracefully stop the filter configurator
  	"""
	def stop(self):
		self._can_run = False

	"""
	The filter configurator will listen for the connected and disconnected
	events in order to start the filter configuration by setting/clearing
	the	self._connect_event lock.
	"""
	def consume(self, event):
		if event['type'] == 'VI' \
			and event['name'] == 'connection':
			if event['value'] == 'connected':
				self._vi = event['vi']
				self._connect_event.set()
			elif event['value'] == 'disconnected':
				self._connect_event.clear()
