import hashlib
import logging
from multiprocessing import Queue

from openai import OpenAI

from cache_manager import add_cache
from config_decoder import config
from logger import init_logger
from solver.solver import Solver


def launcher(threads: int, cache: dict, ques: list[dict]) -> Solver:
	queue: Queue = Queue(len(ques) + threads)
	answers: Queue = Queue(len(ques))
	worker = Solver("AiWorker", threads, queue, answers, solver)
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



def solver(ques: Queue, ans: Queue):
	init_logger()
	logger = logging.getLogger("sbscut.ai_solver")
	logger.info("AI worker started")

	client = OpenAI(api_key=config.ds_api_key, base_url="https://api.deepseek.com")

	system_message = {
		"role": "system",
		"content": "你是一个正在写Python课程作业的学生，作业有填空题、写运行结果和程序设计题三种。"
				   "填空题的空位用“<?>”表示，一道题有一个或多个空位，答案按顺序输出，并以换行分割，每个空的答案均只有一行。"
				   "写运行结果的题目，如果有提供了多个输入，则不同的输出之间以换行分割。"
				   "程序设计题需要输出完整的Python代码，不需要任何注释，也不要使用markdown。"
				   "所有题目只需要输出答案，不需要任何解释。"
	}

	user_message = {
		"role": "user",
		"content": ""
	}

	messages = [system_message, user_message]

	while True:
		question = ques.get()
		if question is None:
			break

		user_message["content"] = f"{question["type"]}题：\n{question["question"]}"
		response = client.chat.completions.create(
			model="deepseek-chat",
			messages=messages,
			temperature=0.0
		)

		answer: str = response.choices[0].message.content

		if question["type"] == "填空":
			answers: list[str] = answer.splitlines(keepends=False)
			# answers: list[str] = ['int', 'float', 'complex']
			logger.info(f"Get answer of question {question['number']}: {answers}")

			if len(answers) != len(question["answer"]):
				logger.warning(f"Answer of question {question['number']} length mismatch")
				logger.warning(f"Answer is {answers}")
				continue

			fill: dict[str, str] = {}
			for blank in question["answer"]:
				fill[blank] = answers.pop(0)
			question["answer"] = fill
		# elif question["type"] == "程序设计":
		else:
			logger.info(f"Get answer of question {question['number']}: {repr(answer)}")

			fill: dict[str, str] = {question["answer"][0]: answer}
			question["answer"] = fill

		ans.put(question)
		add_cache(question)

	logger.info("AI worker shut down")
