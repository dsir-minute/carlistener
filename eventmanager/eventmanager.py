"""
This module provides the EventManager class
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

import Queue
import threading
import weakref
from datetime import datetime

import pdb

class EventManager(threading.Thread):
	"""
	EventManager purpose is to collect every kind of event that happens
	and to forward them to every registered "event consumer".

	It runs in an independent thread and has an inlet fifo queue where all 
	events can be placed asynchronously when fired. When the queue is not 
	empty the main thread will keep popping events and forward them to the 
	registered consumers by calling their consume() method. The consume()
	method itself should not be extremely time consuming, otherwise other
	consumers may suffer starvation. See the ThreadConsumer class.

	An event will always have a type, a name and a timestamp.
	- "type" can be one of:
		- VI: Events related to the vi, like (dis)connection or errors
		- OBD: Events related to OBD, like the reception of an OBD message
		- CAN: Events related to the reception of CAN signals from the VI
		- GPS: Used for position updates coming from the GPS shield
	- "name" is strictly related to the event type and it is usually set by
	  the event producer.
	- "time" is an ISO 8601 date that is added by the event manager as
	  soon as someone produces an event. The timestamp is taken by a
	  class called "TimeSource" that is registered after the EventManager and
	  provides a "get_time()" method

	"""

	"""
	Constructor simply initialize the thread and al the needed stuff.
	Consumers are put int a set in order to avoid duplicates in case of
	double registration
	"""
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self._can_run = True
		self._q = Queue.Queue()
		self._consumers = set()
		self._timesource = None
		self._consumers_lock = threading.RLock()
		self.start()

	"""
	This method is used for registering a class that can provides the
	ISO 8601 date through the get_time() method
	"""
	def set_timesource(self,timesource):
		self._timesource = timesource

	"""
	All the new_XXX_event() are just decorators over the private _new_event() 
	method.
	"""
	def new_can_event(self,event):
		self._new_event(event,'CAN')		

	def new_obd_event(self,event):
		self._new_event(event,'OBD')		

	def new_gps_event(self,event):
		event.update({ 'name' : 'Position' })
		self._new_event(event,'GPS')		

	"""
	When VI gets connected a reference to the new vi object is passed using
	the connection event. This way every consumer that needs to call method
	over vi can immediatly obtain its reference.
	"""
	def new_vi_connect_event(self,vi):
		self._new_event({ \
			'name':'connection', \
			'value':'connected', \
			'vi':vi },'VI')

	def new_vi_disconnect_event(self):
		self._new_event({ \
			'name':'connection', \
			'value':'disconnected' },'VI')

	def new_log_event(self,name,value,fired_by=None):
		self._new_event({ \
			'name':name, \
			'value':value, \
			'fired_by':fired_by },'LOG')

	"""
	When an error occurs over vi it is forwarded through the VI error event.
	Producer can also specify who it is for debug purposes
	"""
	def new_vi_error_event(self,exception,fired_by=None):
		self._new_event({ \
			'name':'error', \
			'value':exception, \
			'fired_by':fired_by },'VI')

	"""
	This is the main thread method. Every time there is an event on the queue
	it will be popped and forwarded to all consumers.
	"""
	def run(self):
		while self._can_run:
			try:
				# get(True,5) blocks for 5 secs if the queue is empty.
				# If an event is inserted during the block it will be
				# immediatly unblocked and the event will be processed.
  				event = self._q.get(True,5)
				if event is not None:
					with self._consumers_lock:
						for consumer in self._consumers:
							consumer.consume(event)

			except Queue.Empty:
				pass

			except Exception as e:
				pdb.set_trace()
				# TODO: Good log please
				print "Exception in "+self.__name__+": "+e

			finally:
				pass

		self._timesource = None


	"""
	If the event manager is stopped then every consumer will be stopped and 
	all of them will be removed from the consumer set. This is one of the last
	operations before closing the program
	"""
	def stop(self):
		with self._consumers_lock:
			for consumer in self._consumers:
				consumer.stop()
			consumer.clear()
		self._can_run = False

	"""
	For register a new consumer. 
	Consumers classes has to provide the consume(event) method. Note that a
	lock is used to prevent changing the consumers' set while it is being
	iterated over on the "run()" method.
	"""
	def register_consumer(self,consumer):
		with self._consumers_lock:
			self._consumers.add(consumer)

	"""
	For unregister a consumer.
	A lock is used to prevent the same situation of "register_consumer()"
	method
	"""
	def unregister_consumer(self,consumer):
		with self._consumers_lock:
			self._consumers.discard(consumer)

	"""
	Private method to add an already tagged new event. See the methods
	new_XXX_event() above.
	Every time it is called it adds the "time" tag and put the event in the
	queue
	"""
	def _new_event(self,event,event_type):
		event['type'] = event_type
		if self._timesource is not None:
			event['time'] = self._timesource.get_time()
		self._q.put(event)

