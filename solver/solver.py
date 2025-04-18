from multiprocessing import Process
from multiprocessing import Queue


class Solver:
	def __init__(self, name, threads: int, ques: Queue, ans: Queue, solver):
		self.workers: list[Process] = []
		self.ans: Queue = ans

		for i in range(threads):
			self.workers.append(Process(name=f"{name}-{i}", target=solver, args=(ques, ans)))

	def start(self):
		for worker in self.workers:
			worker.start()

	def join(self) -> Queue:
		for worker in self.workers:
			worker.join()

		return self.ans
