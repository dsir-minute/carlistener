"""
This module exports an abstract threaded implementation of a parser
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

import Queue
import threading

import pdb

class ThreadedParser(threading.Thread):
	"""
	A threaded parser is an abstract class that should be extended in order
	to performe cpu-intensive parsing asynchronously

	Using a threaded parser, a message to be parsed will be enqueued in a
	local FIFO and then processed asynchronously by a separate thread which 
	will call a callback once the processing is completed.

	This way, who calls the enqueue() method will not be blocked during
	the parsing.
	"""
	
	def __init__(self, callback=None):
		threading.Thread.__init__(self)
		self.daemon = True
		self._can_run = True
		self._callback = callback
		self._q = Queue.Queue() 
		self.start()

	"""
	This method allows to enqueue the element that has to be parsed. The
	parser thread is going to get this element from the FIFO and then parse
	it asynchronously.
	"""
	def enqueue(self,element):
		self._q.put(element)

	"""
	The main thread will simply block on the queue waiting for an element to
	be obtained. As soon as a new element arrives it will be passed to the
	_parse() method, that must be overridden by subclasses.
	"""
	def run(self):
		while self._can_run:
			try:
  				element = self._q.get(True,5)
				if element is not None:
					self._parse(element)

			except Queue.Empty:
				pass

			except Exception as e:
				# TODO: Good log please
				print "Exception in ThreadedParser or subclass: "+str(e)

			finally:
				pass

	"""
	Gracefully stops the parser thread
	"""
	def stop(self):
		self._can_run = False

	"""
	This method has to be overridden by subclasses in order to really parse
	the element. Subclasses are then responsible to call the _callback 
	function once the element was parsed.
	"""
	def _parse(self,element):
		raise NotImplemented("This method is intended to be implemented by subclasses")
