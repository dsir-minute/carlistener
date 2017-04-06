"""
This module contains the OBDParser and all the classes required to handle
OBD messages
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .threadedparser import ThreadedParser
import binascii
import pdb

class OBDParser(ThreadedParser):
	"""
	OBDParser is just a threaded parser that will read a raw OBD frame and
	will convert it into an OBD event.

	The element to be parsed must be a dictionary containing "id" and "data"
	fields, where "id" is the OBD id and "data" is a string representation of
	the 8 byte raw OBD message

	TODO: Actually only the VIN is supported and there is no check on the ID
	that is going to be parsed and on the element structure. Shame on me!
	"""

	obd_ids = [i for i in range(0x7e8,0x7ef)]
	OBD_SINGLE_FRAME = 0x00
	OBD_FIRST_FRAME = 0x10
	OBD_SUBSEQUENT_FRAME = 0x20

	INVALID_VIN="INVALID_VIN"

	def __init__(self, callback):
		ThreadedParser.__init__(self, callback)
		self._multiframe_handler = None
		
	"""
	The parse method recognizes OBD frames, tries to reassemble them if they
	are fragmented and, if valid, fires a new OBD event through the callback.

	Multiframe reassembly is done through the OBDMultiframeHandle class, since
	vi firmware doesn't directly support ISOTP frame reassembly ATM.

	TODO: Actually the only OBD frame it supports are the VIN, the Speed and the Fuel Tank Level
	"""
	def _parse(self, element):
		if 'data' not in element:
			return
		raw_response_string = element['data']
		if raw_response_string.startswith("0x"):
			raw_data = bytearray.fromhex(raw_response_string[2:])
			raw_message = None
			
			if raw_data[0] & 0xF0 == OBDParser.OBD_SINGLE_FRAME:
				n_bytes = raw_data[0] & 0x0F
				mode = raw_data[1] - 0x40
				pid = raw_data[2]

				if mode == 0x01:
					if pid == 0x0d: # Speed
						speed = raw_data[3]
						self._callback( \
							{'name' : 'Speed', 'value' : speed })
					elif pid == 0x2f: # Fuel Tank Level
						speed = raw_data[3]*100/255
						self._callback( \
							{'name' : 'FuelTankLevel', 'value' : speed })

			# TODO: vi firmware doesn't fully support multiframes directly.
			# Actually it just recognizes if a frame is the start of a
			# multiframe one and sends back the control flow frame "0x30..."
			# immediatly, but frame reconstruction has to be made outside the
			# vi firmware, that's why we need to distinguish here between
			# single or multiframes.
			# See src/libs/isotp-c on vi-firmware for further details
			elif raw_data[0] & 0xF0 == OBDParser.OBD_FIRST_FRAME:
				mode = raw_data[2] - 0x40
				pid = raw_data[3]

				# TODO I should get also the last nibble of the first byte, 
				# but I'll ignore it now since I'm fat and lazy.
				# (... no, really, just having the first nibble is enough ATM)
				length = raw_data[1]
			
				# TODO: Actually this manages just the VIN response
				if mode == 0x09 and pid == 0x02:
					self._multiframe_handler = OBDMultiframeHandle(mode,pid,length)
					self._multiframe_handler.append_data(0,raw_data[4:])
			
			elif raw_data[0] & 0xF0 == OBDParser.OBD_SUBSEQUENT_FRAME:
				if self._multiframe_handler != None:
					index = raw_data[0] & 0x0F
					raw_message = self._multiframe_handler.append_data(index,raw_data)
					if raw_message is not None:
						# The VIN has been reassembled, let's fire the event
						self._multiframe_handler = None
						reply = {'name' : 'VIN' }
						try:
							reply['value'] = raw_message.decode()
						except UnicodeDecodeError:
							reply['value'] = OBDParser.INVALID_VIN
							reply['hex_value'] = binascii.hexlify(raw_message)
						self._callback(reply)
			else:
				print "ERROR: OBDParser can only handle the VIN ATM, sorry! :("


class OBDMultiframeHandle():
	"""
	OBDMultiframeHandle is an helper class that stores ISO-TP multiframes
	fragments and reassemble them as soon as all of them are received.
	"""
	def __init__(self,mode,pid,total_bytes):
		self.mode = mode
		self.pid = pid
		self.total_bytes = total_bytes
		self.received_bytes = 0
		self._fragments = {}

	"""
	Every time a new fragment is received it is reordered and stored
	internally. If all fragments were received the append_data will return the
	raw OBD message, otherwise it will return None
	"""
	def append_data(self,index,data):
		self._fragments[index] = data
		self.received_bytes += len(data)
		if self.received_bytes == self.total_bytes:
			message = bytearray()
			for v in sorted(self._fragments):
				message.extend(self._fragments[v][1:])
			return message			
		return None

		
