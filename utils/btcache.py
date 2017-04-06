"""
The class contained in this module provides the persistent storage of 
the last Bluetooth device the application connected to
"""

__author__ 	= "Dario Fiumicello"
__email__ 	= "dario.fiumicello@gmail.com"

class BTCache():
	def __init__(self \
		,filename="/tmp/carlistener_bt.cache"):
		self._filename = filename;

	"""
	Gets the saved address. Returns None if no address was saved or an error
	occurred
	"""
	def get_address(self):
		address = None
		file = None
		try:
			file = open(self._filename, "r")
			address = file.read()
			if address == '':
				address = None
			file.close()
		except IOError:
			if file != None and file.is_open():
				file.close()
		return address

	"""
	Tries to write the address on file. Returns True if the write had success,
	False otherwise
	"""
	def set_address(self,address):
		file = None
		try:
			file = open(self._filename, "w")
			if address != None:
				file.write(address)
			file.close()
		except IOError:
			if file != None and file.is_open():
				file.close()
			return False
		return True
