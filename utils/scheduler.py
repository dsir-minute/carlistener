"""
This module contains a class that allows to schedule a set of periodic tasks
"""

__author__ 	= "Dario Fiumicello"
__email__ 	= "dario.fiumicello@gmail.com"

import time
import threading

import pdb

class Scheduler(threading.Thread):
	"""
	The Scheduler class provides a simple and efficent way to schedule a set 
	of periodic	tasks asynchronously.
	
	The list of task is basicly a list of dictionaries where every dictionary
	contains the following fields:
	
	{
		"id": "aTaskId",
		"period": periodInSecs,
		"func": theCallbackFunctionToBeExecutedPeriodically,
		"args": aListOfArgumentsToPassToTheFunction
	}
	
	- The id can be everything that identifies univocally the task, like a
	string or a number.
	- The period represent the number of seconds between two consecutive
	executions of the task.
	- func is the reference to a callback function to be called for executing
	the task.
	- args is a list of arguments to be passed to the callback function. The
	list is passed "as is", so the function has to access to these arguments
	using args[0], args[1] and so on.
	"""
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self._schedule = None
		self._execute_event = threading.Event()
		self._execute_event.clear()
		self._can_run = True
		self._can_execute = False
		self.start()

	"""
	The run method is responsible for the real execution of the tasks. It just
	calls the private self._execute() function when the user enables the
	execution.
	"""
	def run(self):
		while self._can_run:
			self._can_execute = self._execute_event.wait(2)
	   		if self._can_execute is True:
	   			self._execute()

	"""
	Accept a list of tasks and prepare the schedule to be executed.

	See __init__() method for the task format
	"""
	def load_periodic_tasks_schedule(self,tasks):
		self._schedule = self._get_periodic_schedule(tasks)

	"""
	Starts the execution of a loaded schedule if any.
	"""
	def execute(self):
		if self._schedule != None:
			self._execute_event.set()

	"""
	Stops the execution of the current schedule
	"""
	def stop(self):
		self._can_execute = False
		self._execute_event.clear()

	"""
	Stop everything and kills the underlying thread. It is called by the
	class destructor
	"""
	def kill(self):
		self.stop()
		self._can_run = False

	"""
	Create the periodic task schedule by adding to the tasks dictionaries
	some additional fields to be used during schedule execution.

	Since we are scheduling periodic tasks, the same schedule will be repeated
	after at most the least common multiple among all periods, so we "simply"
	need to find a schedule that covers the lcm of the tasks' periods and we
	are done.

	The schedule will basically be a list of lists of tasks to be executed at
	a certain time. let's do an example:
	Supposing you have task a with period 1s, task b with period 0.5s and
	task c with period 0.33 s. The schedule will be something like this:
	
	+------+-------+-----------------------------+
	| t    | tasks | t_to_wait_before_next_tasks |
	+------+-------+-----------------------------+
	| 0    | a,b,c | 0.33                        |
	| 0.33 | c     | 0.16                        |
	| 0.5  | b     | 0.16                        |
	| 0.66 | c     | 0.33                        |
	| 1    | a,b   | 0.33                        |
	| 1.33 | c     | 0.16                        |
	| 1.5  | b     | 0.16                        |
	| 1.66 | c     | 0.33                        |
   	|              GOTO t=0                      |
	+------+-------+-----------------------------+
	
	Having this schedule we can use a single thread that goes like this:
	- Execute tasks a,b,c
	- Sleep 0.33s
	- Execute task c
	- Sleep 0.16
	- ...
	"""
	def _get_periodic_schedule(self,all_tasks):
		for task in all_tasks:
			task['last_exec_time'] = 0
			task['next_exec_time'] = task['period']

		# All tasks will be executed at the beginning, so let's add all
		# of them to the next_tasks list.
		next_tasks = all_tasks

		schedule = []
		idx = 0
		wait = 0
		while True:
			# Find what will be the next task to be executed
			min_next_exec_time = min([i['next_exec_time'] for i in all_tasks])
			max_last_exec_time = max([i['last_exec_time'] for i in all_tasks])
			wait = min_next_exec_time - max_last_exec_time

			# Append the next_tasks to be executed to the schedule. At the
			# very first iteration this will be equal to all the defined tasks.
			schedule.append( \
				{'idx': idx, 'next_exec_delay':wait, 'tasks' : next_tasks})

			# Now let's find the next tasks to be executed. They will be all
			# the tasks equals to the minimum next execution time.
			next_tasks = \
				filter(lambda x: \
					abs(x['next_exec_time'] - min_next_exec_time) < 0.001 \
					, all_tasks)

			# If next_tasks will be all tasks then we have completed the 
			# periodic schedule, so we can leave.
			if len(next_tasks) == len(all_tasks):
				break
		
			for task in next_tasks:
				task['last_exec_time'] = min_next_exec_time
				task['next_exec_time'] = \
					task['last_exec_time'] + task['period']

			idx += 1

		return sorted(schedule, key=lambda k: k['idx']) 

	"""
	The real execution of the tasks will be made by the _execute() method.
	
	The thread will run as explained int the _get_periodic_schedule() method.
	
	In order to correctly respect the period and to avoid time shift it will
	use a "generator" trick for deciding how long to sleep.
	See: http://stackoverflow.com/a/28034554/2493668
	"""
	def _execute(self):
		i = 0
		def g_delay():
			j = 0
			next_exec_delay = 0
			t = time.time()
			while True:
				t+=next_exec_delay
				next_exec_delay = self._schedule[j]['next_exec_delay']
				j = (j + 1) % len(self._schedule)
				yield max(t + next_exec_delay - time.time(),0)
				
		
		g = g_delay()
		while self._can_execute:
			schedule_info = self._schedule[i]
			for task in schedule_info['tasks']:
				task['func'](task['args'])
			i = (i + 1) % len(self._schedule)
			time.sleep(next(g))

	"""
	The destructor will ensure that the schedule is not running anymore
	"""
	def __del__(self):
		self.kill()
