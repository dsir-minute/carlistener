"""
This module contains a class for getting the time from the system clock
"""

__author__ 	= "Dario Fiumicello"
__email__ 	= "dario.fiumicello@gmail.com"

from datetime import datetime
import dateutil.parser
import os

class SYSTimesource():
	"""
	The purpose of this class is to act as a Timesource for the event manager.
	providing the system time.
	See EventManager
	"""
	def __init__(self):
		pass
	
	"""
	The standard method used by the event manager to get the current time
	"""
  	def get_time(self):
		return datetime.utcnow().isoformat()+"Z"
