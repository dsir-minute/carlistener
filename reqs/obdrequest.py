""" 
This module defines generic classes for performing OBD requests.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from openxc.interface import BluetoothVehicleInterface
import threading
import weakref
import time
from eventmanager import *

class OBDRequest(threading.Thread):
	"""
	This is a generic class that can be used to make asynchronous OBD
	requests. It encapsulates all the details about VI OBD request and call
	a generic method to be extended by subclasses in order to perform sigle or
	recurrent OBD requests.
	"""

	OBD_BROADCAST_PID = 0x7df

	"""
	Subclasses has to initialize OBDRequest with the 
	OBD mode and pids and an event_name to be used as the "name" value for the
	"OBD" event that will be fired upon response.
	"""
	def __init__(self,event_manager,mode,pid,event_name):
		threading.Thread.__init__(self)
		self.daemon = True
		self._w_vi = None
		self._mode = mode
		self._pid = pid
		self._can_run = True
		self._can_execute = False
		self._event_manager = event_manager
		self._event_name = event_name
		self._response_event = threading.Event()
		self._execute_event = threading.Event()
		self._execute_event.clear()
		self._response_event.clear()
		self.start()

	"""
	Once initialized, OBDRequest will start listening for the VI dongle to 
	connect. The requests are performed as soon as the dongle is connected and
	interrupted once it is disconnected or the subclasses will clear the 
	self._execute_event().
	When the VI reconnects the requests are made again.
	If the _execute() methods returns True it will be rescheduled after it
	quits, otherwise it will not be rescheduled unless a new VI connection
	occurs
	"""
	def run(self):
		while self._can_run:
			self._can_execute = self._execute_event.wait(2)
	   		if self._can_execute is True:
	   			if not self._execute():
	   				self._execute_event.clear()

  	"""
  	When called it will gracefully stop the OBDRequest thread
  	"""
	def stop(self):
		self._can_run = False

	"""
	This method is called by the event manager when a new event occur.
	OBDRequest will check if the event is related to its request and, if so,
	will set the lock on the request thread, notifying the received response
	"""
	def consume(self, event):
		if event['type'] == 'VI' \
			and event['name'] == "connection":
			if event['value'] == 'connected':
				self._w_vi = weakref.ref(event['vi'])
				self._execute_event.set()
			else:
				self._execute_event.clear()
				self._w_vi = None

		elif event['type'] == 'OBD' and event['name'] == self._event_name:
			self._response_event.set()

	"""
	This method can be used to perform the very OBD request.
	It just encapsulates the details of the low level code.
	"""
	def _do_request(self):
		vi = self._w_vi()
		if vi != None:
			vi.create_diagnostic_request( \
				OBDRequest.OBD_BROADCAST_PID \
				, self._mode \
				, pid=self._pid \
				, bus=1)

	"""
	The _execute() event is meant to be implemented by subclasses in order 
	to perform their own one-shot / recurring requests. The _execute() method
	MUST return a boolean value telling that it wants to be rescheduled again.
	If it returns True it will be rescheduled immediatly, otherwise it will
	not be rescheduled unless a new VI connection occurs. see run(self) method
	"""
	def _execute(self):
		raise NotImplemented("This method is intended to be implemented by subclasses")


class OBDSingleRequest(OBDRequest):
	"""
	This class can be extended in order to perform one-shot OBD requests, like
	VIN. Itis not meant to be called directly but to be extended by subclasses
	"""
	N_RETRY = 3
	TIMEO_REP_S = 2

	def __init__(self,event_manager,mode,pid,event_name,n_retry=N_RETRY \
		, timeo_rep=TIMEO_REP_S):
		self._n_retry = n_retry
		self._timeo_rep = timeo_rep
		OBDRequest.__init__(self,event_manager,mode,pid,event_name)
	
	"""
	This method encapsulates the real one-shot request. It will make the 
	request _n_retry times and will wait for _timeo_rep seconds for a reply
	"""
	def _execute(self):
		try:
			i=0;
			response_received = False
			while i < self._n_retry and response_received is False:
				self._do_request()
				response_received = self._response_event.wait(self._timeo_rep)
  				i = i+1
				
			if response_received is False:
				self._timeout()

  		except Exception as e: 
  			self._event_manager.new_vi_error_event(e,fired_by="OBDSingleRequest")

  		return False # Do not schedule any further execution


	"""
	This function is called when OBDRequest didn't receive any response. It is
	meant to be overridden by subclasses in order to react to the timeout
	"""
	def _timeout(self):
		pass

class OBDRecurringRequest(OBDRequest):
	"""
	Keep executing an OBD request until conenction to the VI is closed.
	"""
	def __init__(self,event_manager,mode,pid,event_name,period):
		OBDRequest.__init__(self,event_manager,mode,pid,event_name)
		self._period = period
		
	def _execute(self):
		try:
			t = time.time()
			self._do_request()
			time.sleep(max(t + self._period - time.time(),0))
		
  		except Exception as e: 
  			self._event_manager.new_vi_error_event(e,fired_by="OBDRequest")

  		return True
	
	"""
	Override the OBDRequest consume() method in order to start sending OBD
	requests only when the VIN is received. This way there won't be 
	overlapping requests that may cause problems on the OBD bus
	The recurring request will be stopped as soon as the VI is disconnected or
	gets an error.

	TODO: I should move the whole OBD requests schedulation in something 
	different and configurable.
	"""
	def consume(self, event):
		if event['type'] == 'VI' \
			and event['name'] == "connection":
			if event['value'] == 'connected':
				self._w_vi = weakref.ref(event['vi'])
			else:
				self._execute_event.clear()
				self._w_vi = None
		elif event['type'] == 'OBD':
			if event['name'] == self._event_name:
				self._response_event.set()
			elif event['name'] == 'VIN':
				self._execute_event.set()
		

