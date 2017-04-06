import threading
import time
import subprocess

__author__ = "Dario Fiumicello"
__email__ = "dario.fiumicello@gmail.com"

class SystemMonitor(threading.Thread):
	CMD_CPU_LOAD = "cat /proc/loadavg | awk '{print $1}'"
	CMD_CPU_TEMP = "cat /sys/class/thermal/thermal_zone0/temp"
	CMD_HOSTNAME = "cat /etc/hostname | tr -d '\n'"
	POLLING_PERIOD = 5

	def __init__(self, callback=None):
		threading.Thread.__init__(self)
		self.daemon = True
		self._can_run = True
		self._callback = callback
		self.start()

	def run(self):
		while self._can_run:
			try:
				cpu_temp = subprocess.check_output(SystemMonitor.CMD_CPU_TEMP, shell=True)
				cpu_load = subprocess.check_output(SystemMonitor.CMD_CPU_LOAD, shell=True)
				hostname = subprocess.check_output(SystemMonitor.CMD_HOSTNAME, shell=True)
				self._callback({"cpu_temp": float(cpu_temp)/1000 \
					, "cpu_load": float(cpu_load)
					, "hostname": hostname } \
					,"SYS")

			except Exception as e:
				# TODO: Good log please
				print "Exception in SystemMonitor: "+str(e)

			time.sleep(SystemMonitor.POLLING_PERIOD);


	def stop(self):
		self._can_run = False
