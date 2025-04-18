import hashlib
import logging
from multiprocessing import Queue

from openai import OpenAI

from sbscut.cache_manager import add_cache
from sbscut.config_decoder import config
from sbscut.logger import init_logger
from sbscut.solver.solver import Solver


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

	system_prompts: dict[str, str] = {
		"单选": "你是一个正在写Python课程作业的学生，作业均为单选题。"
				"只需要输出选项前的序号（如“A”），不需要作出任何解释。",
		"填空": "你是一个正在写Python课程作业的学生，作业均为填空题。"
				"题目的空位用“<?>”表示，一道题有一个或多个空位，答案按顺序输出，并以换行分割，每个空的答案均只有一行。"
				"只需要输出答案，不需要任何解释。",
		"写运行结果": "你是一个正在写Python课程作业的学生，作业均为写运行结果的题目。"
					  "如果有提供了多个输入，则不同的输出之间以换行分割。"
					  "只需要输出运行结果，不需要任何解释。",
		"程序填空": "你是一个正在写Python课程作业的学生，作业均为程序填空题。"
					"题目的空位以“__(1)__”、“__(2)__”的形式出现，一道题有一个或多个空位。"
					"每个答案前面要添加题号，格式为“(1) ”、“(2) ”"
					"只需要输出答案，不需要任何解释。",
		"程序设计": "你是一个正在写Python课程作业的学生，作业均为程序设计题。"
					"需要输出完整的Python代码，不需要任何注释，也不要使用markdown，代码片段不要用“```”包裹。"
	}

	system_message = {
		"role": "system",
		"content": ""
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

		system_message["content"] = system_prompts[question["type"]]
		user_message["content"] = f"{question["type"]}题：\n{question["question"]}"
		response = client.chat.completions.create(
			model="deepseek-chat",
			messages=messages,
			temperature=0.0
		)

		answer: str = response.choices[0].message.content

		if question["type"] == "单选":
			logger.info(f"Get answer of question {question['number']}: {answer}")
			values: dict[str, str] = {"A": "1000", "B": "0100", "C": "0010", "D": "0001"}

			value: str = values[answer[0]]
			fill: dict[str, str] = {question["answer"][0]: value}
			question["answer"] = fill
		elif question["type"] == "填空":
			answers: list[str] = answer.splitlines(keepends=False)
			logger.info(f"Get answer of question {question['number']}: {answers}")

			if len(answers) != len(question["answer"]):
				logger.warning(f"Answer of question {question['number']} length mismatch")
				logger.warning(f"Answer is {answers}")
				continue

			fill: dict[str, str] = {}
			for blank in question["answer"]:
				fill[blank] = answers.pop(0)
			question["answer"] = fill
		else:
			logger.info(f"Get answer of question {question['number']}: {repr(answer)}")

			fill: dict[str, str] = {question["answer"][0]: answer}
			question["answer"] = fill

		ans.put(question)
		add_cache(question)

	logger.info("AI worker shut down")
