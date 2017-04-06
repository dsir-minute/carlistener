"""
This module contains everything related CAN messages parsing, including
reading the user configuration for messages and signals
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .threadedparser import ThreadedParser
import json
import math
import time

import pdb

class CANParser(ThreadedParser):
	"""
	CANParser reads the file can.json and parse the required CAN signals from
	received can messages.
	"""

	"""
	The constructor will accept a callback that will be called by the parser
	when it correctly parsed a CAN message. This callback will receive a CAN
	event dictionary, containing the signal name and the converted value.
	Constructor will also load the configuration from the file and will fire
	an exception if there is an error in it.
	"""
	def __init__(self,callback,conf_file="can.json"):
		ThreadedParser.__init__(self, callback)
		self._configuration = { 'messages' : {} }
		self.load_configuration_from_file(conf_file)
		
	"""
	Returns a list of the user defined CAN IDs
	"""
	def get_requested_ids(self):
		return self._configuration['messages'].keys()

	"""
	Returns a dictionary containing the configured can messages and their
	dynamics. example:
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
	See FilterConfigurator class
	"""
	def get_configured_messages(self):
		return self._configuration['messages']

	"""
	The main parsing method will use the informations configured by the user
	into the can.json file, which is similar to the OpenXC firmware
	configuration file.
	See:
		_conf_check() method
		can.json.example
		http://vi-firmware.openxcplatform.com/en/latest/config/config.html
	"""
	def _parse(self, element):
		can_id = element['id']
		if can_id in self._configuration['messages'].keys():
			#pdb.set_trace()
			can_value_as_string = element['data']
			for signal in self._configuration['messages'][can_id]['signals']:
				now = time.time()
				sig_conf = self._configuration['messages'][can_id]['signals'][signal]
				if sig_conf['raw'] == False:
					sig_value = self._get_signal_value_from_can_message( \
						can_value_as_string \
						,sig_conf['bit_start'] \
						,sig_conf['bit_size'])
					
					clear_to_notify = False

					if sig_conf['max_frequency'] == 0:
						if sig_conf['send_same'] is True:
							clear_to_notify = True
						else:
							if sig_value != sig_conf['last_value']:
								clear_to_notify = True
					
					else: # max_frequency != 0
						if sig_conf['force_send_changed'] == True \
						and sig_value != sig_conf['last_value']:
							clear_to_notify = True
						else:
							if now > \
							sig_conf['last_change_ts'] + \
							1.0/sig_conf['max_frequency']:
								if sig_conf['send_same'] == True:
									clear_to_notify = True
								else:
									if sig_value != sig_conf['last_value']:
										clear_to_notify = True

					if clear_to_notify is True:
						final_value = None

						if 'states' in sig_conf:
							for k, v in sig_conf['states'].iteritems():
								if sig_value in v:
									final_value = k
									break;
						else:
							final_value = sig_value \
								* sig_conf['factor'] \
								+ sig_conf['offset']
						
						self._callback(	\
							{'name' : sig_conf['generic_name'] \
							, 'value' : final_value})

						sig_conf['last_value'] = sig_value
						sig_conf['last_change_ts'] = now

				else: # This is a RAW message, just send it back as is
					self._callback({
						'name' : hex(element['id']),
						'id' : hex(element['id']),
						'data' : element['data']
						})	

	"""
	Used to obtain the value of a signal inside a can message.
	Example: You have the message 0x0010000000000000 and you want to get
	the second byte multiplied by 0.5 and with an offset of 4:
	You will have bit_pos=8, bit_size=8, offset=4 and factor=0.5, so you will
	obtain:
		0x0010000000000000 -->
		--bit_pos=8--> 0x10000000000000 -->
		--bit_size=8--> 0x10 -->
		--factor=0.5--> 0x08 -->
		--offset=4--> 0x0c --> 12
	"""
	def _get_signal_value_from_can_message( \
			self,value_as_string,bit_pos,bit_size,offset=0,factor=1):
		value_bit_length = (len(value_as_string)-2)*4
		rshift = value_bit_length - bit_pos - bit_size
		mask = long((1<<bit_size)-1)
		value = long(value_as_string,16)
		return long((((value >> rshift) & mask) * factor) + offset)

	"""
	This method load the configuration file and pass it to the _conf_check()
	method in order to verify its correctness
	"""
	def load_configuration_from_file(self, configuration_file):
		if configuration_file is None:
			return False
		
		with open(configuration_file) as json_data:
			conf_dict = json.load(json_data)
			if self._conf_check(conf_dict):
				self._configuration = conf_dict
			else:
				print "Configuration error! TODO: Add log"
			json_data.close()

		return True

	"""
	This method will take the configuration json obtained from the 
	configuration file, will parse it looking for errors and will enrich it
	with all the informations required for the _parse() method to run.

	The configuration json must have this structure:
	"messages": {
    	"0xA_CAN_ID": {
      		"signals": {
        		"A_SIGNAL_NAME": {
          			"generic_name": "A_GENERIC_NAME_FOR_THE_SIGNAL",
          			"bit_start": START_BIT (MSB),
          			"bit_size": N,
        		},
        		"ANOTHER_SIGNAL_NAME": {
          			"generic_name": "ANOTHER_GENERIC_NAME_FOR_THE_SIGNAL",
          			"bit_start": START_BIT (MSB),
          			"bit_size": M,
          			"max_frequency": F,
          			"send_same": True|False,
          			"force_send_changed": True|False
        		}
        		"A_STATE_SIGNAL": {
          			"generic_name": "A_GENERIC_NAME_FOR_THE_STATE_SIGNAL",
          			"bit_start": START_BIT (MSB),
          			"bit_size": P,
          			"states": {
            			"Short"   : [1],
            			"Medium"  : [2],
            			"Long"  :   [3]
          			}
        		}
        	}
      	},
      	"0xANOTHER_CAN_ID_TAKEN_AS_RAW": {
      	}
      	...
    }

	RULES:
	- generic_name, bit_start and bit_size are mandatory
	- max_frequency can be present. if not present it is assumed 0
	- force_send_changed can be present. if not present it is assumed true
	- send_same can be present. if not it is assumed true
	- offset and factor can be present. if not they are assumed as 0 and 1
	- if state is present then offset and factor are not considered

	The keywords are the same defined for the OpenXC firmware. You can find
	detailed informations on what the keywords do here:
		http://vi-firmware.openxcplatform.com/en/latest/config/config.html
	Please see also the file can.json.example
	"""
	def _conf_check(self,configuration):
		try:
			g_max_frequency = 0
			g_force_send_changed = True
			if 'max_frequency' in configuration:
				g_max_frequency = configuration['max_frequency']
			if 'force_send_changed' in configuration:
				g_force_send_changed = configuration['force_send_changed']

			for can_id in configuration['messages'].keys():
				if not 'signals' in configuration['messages'][can_id] \
					or \
					len(configuration['messages'][can_id]['signals'].values()) \
					== 0:
					# No signals configured for the message means that the
					# message is a raw one. let's a placeholder signal stating
					# this fact
					configuration['messages'][can_id]['signals'] = {
						can_id : { 'raw' : True }
					}
					if 'max_frequency' not in configuration['messages'][can_id]:
						configuration['messages'][can_id]['max_frequency'] = g_max_frequency
					if 'force_send_changed' not in configuration['messages'][can_id]:
						configuration['messages'][can_id]['force_send_changed'] = g_force_send_changed
					
				else:
					# We have signals! Let's configure them
					msg_max_frequency = 1.0
					msg_force_send_changed = False
					for signal in \
						configuration['messages'][can_id]['signals'].values():
						if not all (k in signal for k in \
							('bit_start','bit_size','generic_name')):
							return False
						if not 'max_frequency' in signal:
							signal['max_frequency'] = g_max_frequency
						if not 'force_send_changed' in signal:
							signal['force_send_changed'] = g_force_send_changed
						if not 'send_same' in signal:
							signal['send_same'] = True
						if not 'offset' in signal:
							signal['offset'] = 0
						if not 'factor' in signal:
							signal['factor'] = 1
						signal['last_value'] = None
						signal['last_change_ts'] = 0
						signal['raw'] = False

						msg_force_send_changed = msg_force_send_changed or signal['force_send_changed']
						if msg_max_frequency != 0 and \
							signal['send_same'] == True and \
							(signal['max_frequency'] == 0 or signal['max_frequency'] > msg_max_frequency):
							msg_max_frequency = signal['max_frequency']

					if 'max_frequency' not in configuration['messages'][can_id]:
						configuration['messages'][can_id]['max_frequency'] = msg_max_frequency
					if 'force_send_changed' not in configuration['messages'][can_id]:
						configuration['messages'][can_id]['force_send_changed'] = msg_force_send_changed

			configuration['messages'] = {long(k,16):v for k,v in configuration['messages'].items()}
			return True

		except Exception as e:
			return False
			






