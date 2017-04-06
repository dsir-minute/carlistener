"""
This modue contains all the classes that store events on file.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .threadedconsumer import ThreadedConsumer
import json
import re

import pdb

class JSONFileConsumer(ThreadedConsumer):
	"""
	JSONFileConsumer stores every event into a JSON file.

	The result of a session (from VI connection to VI disconnection/error)
	will be a file containing a JSON array with the
	representation of all events. The file will be stored in 
	DEFAULT_OUTPUT_DIR and will be named:
	DEFAULT_FILE_PREFIX YYYYMMDD_HHMMSS DEFAULT_FILE_EXT
	(e.g.: car_data_20160813_174000.json)
	"""

	# TODO: Allow configuration of the OUTPUT_DIR and the file name
	DEFAULT_OUTPUT_DIR = "/mnt/datalog/"
	DEFAULT_FILE_PREFIX = "car_data_"
	DEFAULT_FILE_EXT = ".json"

	def __init__(self, output_dir=DEFAULT_OUTPUT_DIR):
		ThreadedConsumer.__init__(self)
		self._file = None
		self._output_dir = output_dir
 
 	"""
 	The _consume() method will handle all the stuff required to 
 	open/close/write the JSON file.

 	The file will be openes as soon as a new "VI connected" event appears and
 	will be closed when any "VI" event that is not "connected" (either 
 	"disconnected" or "error") occurs.

 	Once the file is open every subsequent event will be written as an element
 	of a JSON array.

 	Notice that every time an event is written, the JSON array will be closed
 	and the file will be flushed. This will mitigate the risk of data loss
 	and corruption since the system can be brutally powered off at every
 	moment. If more events occur then the file descriptor is simply moved
 	backward in order to remove the array closure and to continue writing.
 	"""
 	def _consume(self, event):
 		try:
 			# The file is opened only at connection. All event before 
 			# VI connection will not be logged
			if event['type'] == 'VI' and event['name'] == 'connection':
				if event['value'] == 'connected':
					self._file = open(self._output_dir \
						+"/" \
						+JSONFileConsumer.DEFAULT_FILE_PREFIX \
						+re.sub("\.[0-9]+" \
							,"" \
							,event['time'] \
								.replace("-","") \
								.replace("T","_") \
								.replace(":",""))
						+JSONFileConsumer.DEFAULT_FILE_EXT, "w")
					self._file.write("[\n\t"+json.dumps(event \
						,default=self._skip_unserializable)+"\n]")
					self._file.flush()
				else:
					# A VI event of disconnection or error occured, just
					# close the file.
					if self._file != None:
						self._file.seek(-2,2)
						self._file.write(",\n\t"+json.dumps(event \
							,default=self._skip_unserializable)+"\n]\n")
						self._file.close()
						self._file = None
			else:
				if self._file != None and not self._file.closed:
					self._file.seek(-2,2)
					self._file.write(",\n\t"+json.dumps(event, \
						default=self._skip_unserializable)+"\n]")
					self._file.flush()

		except IOError:
			#TODO: Add log
			if self._file != None and not self._file.closed:
				self._file.close()
				self._file = None
		
	"""
	This method is required in order to avoid exception when the json.dumps()
	method tries to write down an event containing a python object, e.g. the 
	vi object reference you get on VI connected event or any Exception you
	get on VI error events.
	See https://docs.python.org/2/library/json.html
	"""
	def _skip_unserializable(self,obj):
		return str(obj)
