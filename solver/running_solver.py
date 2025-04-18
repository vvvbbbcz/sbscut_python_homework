import hashlib
import logging
from multiprocessing import Queue

from cache_manager import add_cache
from logger import init_logger
from solver.solver import Solver


def launcher(threads: int, cache: dict, ques: list[dict]) -> Solver:
	queue: Queue = Queue(len(ques) + threads)
	answers: Queue = Queue(len(ques))
	worker = Solver("RunningWorker", threads, queue, answers, solver)
	worker.start()

	for question in ques:
		index: str = str(question["number"])

		if index not in cache:
			queue.put(question)
			continue

		ques_hash = hashlib.sha1(question["question"].encode("utf-8")).hexdigest()
		cache_hash = cache.get(index)["hash"]
		if cache_hash == ques_hash:
			question["answer"] = cache[index]["answer"]
			answers.put(question)
			add_cache(question)
		else:
			queue.put(question)
	for i in range(threads):
		queue.put(None)

	return worker



def solver(questions: Queue, answers: Queue):
	init_logger()
	logger = logging.getLogger("sbscut.running_solver")
	logger.info("Running worker started")

	while True:
		question = questions.get()
		if question is None:
			break

		exec(question["question"])
