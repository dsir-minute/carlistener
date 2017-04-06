"""
This modue contains all the classes that push events towards REST server.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

from .threadedconsumer import ThreadedConsumer
from utils import PeriodicTimer
import json
import time
import requests
import json

import pdb

class RESTConsumer(ThreadedConsumer):

	"""
	RESTConsumer sends events to a REST server.
	"""

	__name__ = "RESTConsumer"
	
	URL = "https://api.myjson.com/bins/t4ppn"
	REQUEST_INTERVAL_S = 5

	def __init__(self, event_manager, url=URL,req_intvl_s=REQUEST_INTERVAL_S):
		ThreadedConsumer.__init__(self)
		self._event_manager = event_manager
		self._url = url
		self._req_intvl_s = req_intvl_s
		self._last_data = {}
		self._last_event_ts = 0
		self._last_req_ts = 0
		self._pt = PeriodicTimer(req_intvl_s,self._rest_req)
		self._pt.run() 
 	"""
 	"""
 	def _consume(self, event):
		if event['type'] == 'CAN' or event['type'] == 'OBD':
			self._last_data[event['name']] = str(event['value'])
			self._last_data['time'] = event['time']
			self._last_data['lastUpd'] = str(int(time.time()))
			self._last_event_ts = time.time()

	def _rest_req(self,args):
		if self._last_event_ts > self._last_req_ts:
			self._last_req_ts = time.time()
			r = None
			try:
				r = requests.put(self._url, data=json.dumps(self._last_data),headers={'Content-Type':'application/json'})
				self._event_manager.new_log_event("status_code", r.status_code, fired_by=self.__name__)
			except Exception as e:
				self._event_manager.new_log_event("error", e, fired_by=self.__name__)

	"""
	This method is required in order to avoid exception when the json.dumps()
	method tries to write down an event containing a python object, e.g. the 
	vi object reference you get on VI connected event or any Exception you
	get on VI error events.
	See https://docs.python.org/2/library/json.html
	"""
	def _skip_unserializable(self,obj):
		return str(obj)
