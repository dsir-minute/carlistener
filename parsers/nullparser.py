import json

class NullParser():
	def parse(self,event):
		try:
			return json.dumps(event)
		except:
			return None