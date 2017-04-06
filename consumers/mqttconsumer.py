"""
This module defines the consumers for MQTT
"""

from .threadedconsumer import ThreadedConsumer
import paho.mqtt.client as mqtt
import os,threading,time

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

class MQTTConsumer(ThreadedConsumer):
	""" 
	MQTT Consumer will push the events over an MQTT broker, using the
	format specified by an external parser that can be passed as argument.

	This consumer encapsulates "Paho" as the MQTT client.
	See https://pypi.python.org/pypi/paho-mqtt/1.1

	The topic on which the data are pushed will be like
	NRCSV/<CAR_VIN>/<EVENT_NAME>
	The format of the data is decided using a parser class that will accept
	the event and return a formatted message to be pushed by the MQTT client.

	This consumer will also store all events that arrives before the OBD VIN
	and will publish them only after the VIN is received. This is necessary
	because the VIN is part of the topic and you cannot publish anything
	if you don't have it.

	Actually the configured broker is Litmus Collabox, but any broker can be
	used by changing self.address variable and eventually passing a different
	parser if the data format has to be changed.
	"""

	def __init__(self,event_manager,parser):
		ThreadedConsumer.__init__(self)
		self._event_manager = event_manager
		self._parser = parser
		self.address = "loopdocker1.cloudapp.net"
		self.topic_prefix = "NRCSV"
		self.topic_suffix = None
		self._mqtt_client_id = 'CarListener'+str(os.getpid())
		self._client = mqtt.Client(client_id=self._mqtt_client_id \
			,clean_session=False)
		self._backlog = []
		self._mqtt_connected = False
		self._client.on_connect = self.on_connect
		self._client.on_disconnect = self.on_disconnect
		
		self._connect_thread = threading.Thread(target=self._keep_connecting)
		self._connect_thread.daemon = True
		self._connect_thread.start()

	"""
	This method will always try to connect to the MQTT broker, even if a
	socket error occurs. I should have used the connect_async() + loop_start()
	solution, but if there is an error like "Name or service not known", PAHO
	won't allow me to reconnect automatically.
	"""
	def _keep_connecting(self):
		while True:
			try:
				self._client.connect(self.address,keepalive=10)
				self._client.loop_forever()
			except Exception as e:
				self._event_manager.new_log_event("error", e \
					, fired_by="MQTTConsumer")
				time.sleep(10)

	"""
	Called by PAHO when it establish a connection to the MQTT broker
	"""
	def on_connect(self, client, userdata, flags, rc):
		if rc == 0:
			self._mqtt_connected = True
		else:
			self._mqtt_connected = False

	"""
	Called by PAHO when it disconnects from the MQTT broker
	"""
	def on_disconnect(self, client, userdata, rc):
		self._mqtt_connected = False
		
	"""
	The _consume() method is responsible for:
	- Saving all messages that arrived before the VIN
	- Publishing all saved messages on the topic as soon as the VIN is received
	- Keep publishing all other session events
	"""
 	def _consume(self, event):
 		if event['type'] == "OBD" and event['name'] == 'VIN':
 			# When VIN is received we have the complete MQTT topic
 			self.topic_suffix = event['value']
 		else:
 			# Just append the event on the backlog, it will be really
 			# really published afterwards only if the topic is complete and
 			# the client is connected to the MQTT broker
 			self._backlog.append(event)

 		if self.topic_suffix is not None and self._mqtt_connected:
 			# Everything looks ok to publish the data. Just go through the
 			# backlog and publish everything in it.
 			for bl_event in self._backlog:
 				# TODO: Parser should not have to accept a specific argument
 				# (i.e. VIN), I have to make this more generic and isolated
 				try:
 					outlet_message = self._parser.parse(bl_event,vin=self.topic_suffix)
 				
	 				# Yes, outlet_message can also be "None" because the parser
	 				# may want, for example, to aggregate some data before 
	 				# publishing them. All of this stuff and any eventual 
	 				# state machine has to be done in the parser.
					if outlet_message is not None:
						ret = self._client.publish(self.topic_prefix+"/" \
							+self.topic_suffix+"/" \
							+bl_event['name'], outlet_message, qos=2)
				except Exception as e:
					self._event_manager.new_log_event("error", e \
						, fired_by="MQTTConsumer")
					
			# TODO: I should clear the backlog only if the messages where really
			# published by the broker. Actually the publish() method of PAHO
			# returns True even if the data weren't really published (because
			# of a network failure or dropped connection). PAHO will keep
			# this unpublished messages into a queue and will publish them
			# as soon as the connection is restored, but in the meanwhile bad
			# things can happen, so I really need to change this behaviour,
			# almost certainly inside PAHO itself.
			self._backlog = []


