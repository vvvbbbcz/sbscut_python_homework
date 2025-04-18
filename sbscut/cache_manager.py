import hashlib
import json
import logging
import os
from multiprocessing import Queue, Process, Pipe
from multiprocessing.connection import Connection

from sbscut.config_decoder import config

_queue = Queue(-1)

_cache_dir = "caches"


def add_cache(c: dict):
	_queue.put(c.copy())


def loader(conn: Connection, homework: str):
	cache: dict = {}
	try:
		file = open(f"{_cache_dir}/{homework}.json", "r", encoding="utf-8")
		cache = json.load(file)
	except Exception as e:
		logger = logging.getLogger("sbscut.cache_manager")
		logger.warning(f"Cannot load cache: {e}")
	conn.send(cache)


def handler(q: Queue, homework: str):
	logger = logging.getLogger("sbscut.cache_manager")
	cache: dict = {}

	while True:
		c: dict = q.get()
		if c is None:
			break
		c["hash"] = hashlib.sha1(c["question"].encode("utf-8")).hexdigest()
		c.pop("type")
		c.pop("question")
		num = c.pop("number")
		cache[str(num)] = c
		logger.debug(f"Get cache: {c}")

	with open(f"{_cache_dir}/{homework}.json", "w", encoding="utf-8") as file:
		json.dump(cache, file, ensure_ascii=False, indent=2)
		logger.info(f"Saved {len(cache)} caches")


class Cache:
	__logger = logging.getLogger("sbscut.cache_manager")
	__pipe: tuple[Connection, Connection] = Pipe(duplex=False)

	def __init__(self):
		self.__worker = Process(name="CacheWorker", target=handler, args=(_queue, config.homework))
		self.__loader = Process(name="CacheLoader", target=loader, args=(self.__pipe[1], config.homework))

	def start(self):
		if not os.path.exists(_cache_dir):
			os.makedirs(_cache_dir, exist_ok=True)

		self.__worker.start()
		self.__loader.start()
		self.__logger.info("Cache Manager started")

	def load(self) -> dict:
		self.__loader.join()
		cache: dict = self.__pipe[0].recv()
		self.__logger.info(f"Loaded {len(cache)} caches")
		return cache

	def shutdown(self):
		self.__logger.info("Gracefully shutting down Cache Manager...")
		_queue.put_nowait(None)
		self.__worker.join()
