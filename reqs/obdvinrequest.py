"""
This module provides a class for requesting the car VIN via OBD
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .obdrequest import *

class OBDVINRequest(OBDSingleRequest):
	"""
	This class is just an extension of OBDRequest. It declares the mode and
	pid for VIN request and a timeout function to be called by superclass
	when no VIN can be retrieved
	"""
	OBD_MODE = 0x09
	OBD_PID = 0x02
	EVENT_NAME = "VIN"
	UNKNOWN_VIN = "UNKNOWN_VIN"

	"""
	The constructor will simply initialize the superclass with the correct
	mode, pid and event name.
	"""
	def __init__(self,event_manager):
		OBDSingleRequest.__init__(self \
			,event_manager \
			,OBDVINRequest.OBD_MODE \
			,OBDVINRequest.OBD_PID \
			,OBDVINRequest.EVENT_NAME)

	"""
	If the VIN cannot be retreived then it will be assumed as UNKNOWN. VIN is
	not mandatory on OBD, so some cars may lack this feature.
	"""
	def _timeout(self):
		self._event_manager.new_obd_event({'name' : OBDVINRequest.EVENT_NAME \
		, 'value' : OBDVINRequest.UNKNOWN_VIN })
