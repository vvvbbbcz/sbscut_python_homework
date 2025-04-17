import logging
import multiprocessing
import os
import sys
from logging import LogRecord, StreamHandler
from logging.handlers import RotatingFileHandler, QueueHandler
from multiprocessing import Queue

_logdir = "logs"
_logfile = f"{_logdir}/app.log"
_debug_logfile = f"{_logdir}/debug.log"

_queue: Queue = multiprocessing.Queue(-1)


def init_logger():
	root = logging.getLogger()
	root.handlers.clear()
	root.addHandler(QueueHandler(_queue))
	root.setLevel(logging.NOTSET)


def _listener_configurer(level: str):
	date_fmt = "%Y-%m-%d %H:%M:%S"
	fmt = logging.Formatter('[%(asctime)s][%(levelname)s][%(processName)s][%(name)s][%(filename)s:%(lineno)d] %(message)s',
							datefmt=date_fmt)

	file_handler = RotatingFileHandler(_logfile, 'a', 65536, 10)
	file_handler.setFormatter(fmt)
	file_handler.setLevel(logging.INFO)

	debug_handler = RotatingFileHandler(_debug_logfile, 'a', 65536, 10)
	debug_handler.setFormatter(fmt)
	debug_handler.setLevel(logging.DEBUG)

	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(fmt)
	console_handler.setLevel(level)

	root = logging.getLogger()
	root.handlers.clear()
	root.addHandler(file_handler)
	root.addHandler(debug_handler)
	root.addHandler(console_handler)


def _listener_process(queue: Queue, level: str):
	_listener_configurer(level)
	while True:
		record: LogRecord = queue.get()
		if record is None:
			break
		logger = logging.getLogger(record.name)
		logger.handle(record)


class LogListener:
	logger = logging.getLogger("sbscut.log_listener")

	def __init__(self, level: str):
		self.__process = multiprocessing.Process(name="LogListener", target=_listener_process, args=(_queue, level))

	def start(self):
		if not os.path.exists(_logdir):
			os.makedirs(_logdir, exist_ok=True)

		self.__process.start()
		init_logger()
		self.logger.info("Log Listener started")

	def shutdown(self):
		self.logger.info("Gracefully shutting down Log Listener...")
		_queue.put_nowait(None)
		self.__process.join()
