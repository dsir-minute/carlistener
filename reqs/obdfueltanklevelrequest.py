"""
This module provides a class for requesting the fuel tank level via OBD
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .obdrequest import *

class OBDFuelTankLevelRequest(OBDRecurringRequest):
	"""
	This class is just an extension of OBDRecurringRequest. It declares the
	mode and pid for fuel tank level request and a period for the execution
	"""
	OBD_MODE = 0x01
	OBD_PID = 0x2f
	PERIOD_S = 1.0
	EVENT_NAME = "FuelTankLevel"

	"""
	The constructor will simply initialize the superclass with the correct
	mode, pid and event name.
	"""
	def __init__(self,event_manager):
		OBDRecurringRequest.__init__(self \
			,event_manager \
			,OBDFuelTankLevelRequest.OBD_MODE \
			,OBDFuelTankLevelRequest.OBD_PID \
			,OBDFuelTankLevelRequest.EVENT_NAME \
			,OBDFuelTankLevelRequest.PERIOD_S)
