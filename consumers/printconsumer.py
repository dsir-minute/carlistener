"""
This module contains all the classes that prints the events on screen
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .threadedconsumer import ThreadedConsumer

class PrintConsumer(ThreadedConsumer):
	"""
	This is a simple ThreadConsumer that just print the str() representation
	of the event.
	"""
	def __init__(self):
		ThreadedConsumer.__init__(self)
	
	"""
	The overridden _consume() method from the ThreadedConsumer() class
	"""
	def _consume(self, event):
		print str(event)
