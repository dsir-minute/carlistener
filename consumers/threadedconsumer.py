"""
This module exports an abstract threaded implementation of an event consumer
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

import Queue
import threading

import pdb

class ThreadedConsumer(threading.Thread):
	"""
	A threaded consumer is an abstract class that should be extended by
	event consumers that may perform time consuming jobs when a new event
	arrives.

	Using a threaded consumer, the event forwarded by the EventManager is
	placed into an internal queue and then processed asynchronously, so that
	the EventManager can continue forwarding the event to all the other
	consumers, avoiding starvation.

	See EventManager.
	"""

	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self._can_run = True
		self._q = Queue.Queue() 
		self.start()

	"""
	This is the consume() method called by the event manager. Its only
	purpose is to put the event into a local FIFO queue, so it is really
	fast. The event is then processed asynchronously.
	"""
	def consume(self,event):
		self._q.put(event)

	"""
	The main thread will simply block over the queue waiting for a new event
	to arrive. As soon as the queue is not empty anymore the event will be
	passed to the _consume() method, which has to be extended by subclasses
	and can be used to perform time-consuming jobs.
	"""
	def run(self):
		while self._can_run:
			try:
  				event = self._q.get(True,5)
				if event is not None:
					self._consume(event)

			except Queue.Empty:
				pass

			except Exception as e:
				print "ThreadedConsumer: Exception in ThreadedConsumer or subclasses: "+str(e)

			finally:
				pass

	"""
	This will simply cause the main thread to quit.
	"""
	def stop(self):
		self._can_run = False

	"""
	This method has to be implemented by inheriting consumers. Inside this
	method they can safely do time-consuming jobs.
	"""
	def _consume(self,event):
		raise NotImplemented("This method is intended to be implemented by subclasses")
