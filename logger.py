import logging
import multiprocessing
import os
import sys
from logging.handlers import RotatingFileHandler

_logdir = "logs"
_logfile = f"{_logdir}/app.log"
_debug_logfile = f"{_logdir}/debug.log"
if not os.path.exists(_logdir):
	os.makedirs(_logdir, exist_ok=True)


def _listener_configurer():
	date_fmt = "%Y-%m-%d %H:%M:%S"
	fmt = logging.Formatter('[%(asctime)s][%(levelname)s][%(processName)s] %(message)s',
							datefmt=date_fmt)

	file_handler = RotatingFileHandler(_logfile, 'a', 65536, 10)
	file_handler.setFormatter(fmt)

	debug_handler = RotatingFileHandler(_debug_logfile, 'a', 65536, 10)
	debug_handler.setFormatter(fmt)
	debug_handler.setLevel(logging.DEBUG)

	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(fmt)

	root = logging.getLogger()
	root.addHandler(file_handler)
	root.addHandler(debug_handler)
	root.addHandler(console_handler)


def _listener_process(queue):
	_listener_configurer()
	while True:
		try:
			record = queue.get()
			if record is None:
				break
			logger = logging.getLogger(record.name)
			logger.handle(record)
		except Exception:
			import sys, traceback
			print('Whoops! Problem:', file=sys.stderr)
			traceback.print_exc(file=sys.stderr)


class Listener:
	def __init__(self):
		self.queue = multiprocessing.Queue(-1)
		self.__process = multiprocessing.Process(target=_listener_process, args=(self.queue,))

	def start(self):
		self.__process.start()

	def shutdown(self):
		self.queue.put_nowait(None)
		self.__process.join()
