"""
This module defines a consumer that sends all the messages over a
WebSocket.
"""

from .threadedconsumer import ThreadedConsumer
from autobahn.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory
from twisted.internet.protocol import ReconnectingClientFactory

import os,threading,time
import string
import socket

import pdb

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

__registry = {}

def register_protocol(protocol,hostname,port):
	try:
		ip = socket.gethostbyname(hostname)
		__registry[socket.gethostbyname(ip)+':'+port] = protocol    
		return True
	except socket.error:
		return False

def unregister_protocol(protocol):
	for k,v in __registry.items():
		if v == protocol:
			del __registry[k]
			break

def get_protocol(hostname,port):
	try:
		ip = socket.gethostbyname(hostname)
		if ip+':'+str(port) in __registry:
			return __registry[ip+':'+str(port)]
	except socket.error:
		return None

class MyClientFactory(WebSocketClientFactory, ReconnectingClientFactory):
	maxDelay=10

	def clientConnectionFailed(self, connector, reason):
		self.retry(connector)

	def clientConnectionLost(self, connector, reason):
		self.retry(connector)

class NullProtocol(WebSocketClientProtocol):
	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))
		conn_data = response.peer.split(':')
		register_protocol(self,conn_data[1],conn_data[2])
		# TODO: Check if response is wrong

	def onOpen(self):
		print("WebSocket connection open.")

	def onMessage(self, payload, isBinary):
		if isBinary:
			print("Binary message received: {0} bytes".format(len(payload)))
		else:
			print("Text message received: {0}".format(payload.decode('utf8')))

	def onClose(self, wasClean, code, reason):
		print("WebSocket connection closed: {0}".format(reason))
		unregister_protocol(self)

class WSConsumer(ThreadedConsumer):

	__name__ = "WSConsumer"

	def __init__(self,event_manager,parser,addr,port,protocol_class=NullProtocol):
		ThreadedConsumer.__init__(self)
		self._event_manager = event_manager
		self._parser = parser
		self._addr = addr
		self._port = port
		self._protocol_class = protocol_class
		
		self._connected = False
		self._backlog = []

		self._connect_thread = \
			threading.Thread(target=self._keep_connecting)
		self._connect_thread.daemon = True
		self._connect_thread.start()

	def _keep_connecting(self):
		from twisted.internet import reactor

		while True:
			try:
				factory = MyClientFactory(u"ws://"+self._addr+":"+str(self._port))
				factory.protocol = self._protocol_class
				reactor.connectTCP(self._addr, self._port, factory)
				reactor.run(installSignalHandlers=0)

			except Exception as e:
				self._event_manager.new_log_event("error", e \
					, fired_by="WSConsumer")
				time.sleep(10)

 	def _consume(self, event):
		self._backlog.append(event)

		proto = get_protocol(self._addr, self._port)

		if proto is not None:

 			for bl_event in self._backlog:
 				
 				outlet_message = self._parser.parse(bl_event)
 				if outlet_message is not None:
					proto.sendMessage(str(outlet_message).encode('utf8'))
					
			self._backlog = []

