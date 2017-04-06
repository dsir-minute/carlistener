import json
import pdb

"""
This is a parser to be used for publishing data on the Collabox cloud.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

class CollaboxOutletParser():
	"""
	Collabox Outlet parser will simply accept events and add metadata to them
	in order to comply with the required Collabox data format.
	To parse the data it will always requre the car VIN because it is a
	mandatory part of the data to be sent.
	"""

	def __init__(self):
		pass
		
	def parse(self,message,vin='Unknown_VIN'):
		outlet_message = {};
		if message is not None and {'type','time'}.issubset(message):
			outlet_message['metadata'] = { 'vin' : vin \
				, 'type' : message['type'] }
			outlet_message['timestamp'] = message['time']
			if message['type'] == 'GPS':
				outlet_message['data'] = {
					'latitude' : message['latitude'],
					'longitude' : message['longitude'],
					'geohash' : message['geohash'],
					'n_sats' : message['n_sats']
				}
				if 'speed' in message:
					outlet_message['data']['speed'] = message['speed']
				if 'heading' in message:
					outlet_message['data']['heading'] = message['heading']
				if 'altitude' in message:
					outlet_message['data']['altitude'] = message['altitude']

			elif message['type'] == 'VI':
				outlet_message['data'] = {
					message['name'] : message['value']
				}
			elif message['type'] == 'CAN':
				if {'name','value'}.issubset(message):
					outlet_message['data'] = {
						message['name'] : message['value']
					}
				elif {'id','data'}.issubset(message):
					outlet_message['data'] = {
						message['id'] : message['data']
					}
			elif message['type'] == 'OBD':
				if message['name'] != 'VIN':
					outlet_message['data'] = {
						message['name'] : message['value']
					}
	
			try:
				return json.dumps(outlet_message)
			except:
				return None
				
		else:
			# TODO: Define error
			pass
