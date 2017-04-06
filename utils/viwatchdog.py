"""
This module contains a watchdog class to check that VI is really connected
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

class VIWatchdog():
	"""
	The VIWatchdog will listen for every VI related error and will report
	the vi as "NOK" if it is not connected.

	The reason for this class to exist is because sometimes,
	even if vi.is_alive() returns True it doesn't mean that VI is really
	connected and working, especially when Bluetooth related error occurs.
	"""
	def __init__(self):
		self._vi_ok = False

	"""
	Just listen for VI related events and set the internal _vi_ok flag only
	if the last VI event was a successfull connection
	"""
	def consume(self,event):
		if event['type'] == 'VI':
			if event['name'] == 'connection':
				if event['value'] == 'connected':
					self._vi_ok = True
				else:
					self._vi_ok = False
			elif event['name'] == 'error':
				self._vi_ok = False

	"""
	Synchronous method to be called in order to check for VI Ok. It should
	be used in conjunction with vi.is_alive() method when checking if VI is
	really working
	"""
	def vi_ok(self):
		return self._vi_ok
		