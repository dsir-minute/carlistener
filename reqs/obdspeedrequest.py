"""
This module provides a class for requesting the car Speed via OBD
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .obdrequest import *

class OBDSpeedRequest(OBDRecurringRequest):
	"""
	This class is just an extension of OBDRecurringRequest. It declares the
	mode and pid for Speed request and a period for the execution
	"""
	OBD_MODE = 0x01
	OBD_PID = 0x0d
	PERIOD_S = 1.0
	EVENT_NAME = "Speed"

	"""
	The constructor will simply initialize the superclass with the correct
	mode, pid and event name.
	"""
	def __init__(self,event_manager):
		OBDRecurringRequest.__init__(self \
			,event_manager \
			,OBDSpeedRequest.OBD_MODE \
			,OBDSpeedRequest.OBD_PID \
			,OBDSpeedRequest.EVENT_NAME \
			,OBDSpeedRequest.PERIOD_S)
