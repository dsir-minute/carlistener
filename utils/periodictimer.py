import time
import threading
import pdb

"""
This modue contains a class to schedule async periodic jobs.
"""

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

class PeriodicTimer():

	def __init__(self,period,f,*args):
		self._can_run = True
		self._period = period
		self._f = f;
		self._args = args
	
	def _do_every(self):
		def g_tick():
			t = time.time()
			count = 0
			while True:
				count += 1
				yield max(t + count*self._period - time.time(),0)
		g = g_tick()
		while self._can_run:
			time.sleep(next(g))
			if self._can_run:
				self._f(self._args)

	def run(self):
		t = threading.Thread(target=self._do_every)
		t.daemon = True
		t.start()

	def stop(self):
		self._can_run = False
