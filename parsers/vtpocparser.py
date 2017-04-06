import json

class VTPocParser():
	def parse(self,event):
		if event['type'] == 'GPS':
			return json.dumps({
				"vin":"vin00",
				"lon": str(event['longitude']),
				"lat": str(event['latitude']),
				"groupId":"222"})
		elif event['type'] == 'SYS':
			return json.dumps({
				"vin":"vin00",
				"cpu_load": str(event['cpu_load']),
				"cpu_temp": "{:.2f}".format(event['cpu_temp']),
				"hostname": event['hostname'],
				"groupId":"222"})
		return None
