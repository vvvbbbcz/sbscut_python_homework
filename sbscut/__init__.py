import requests
from requests import Response

from sbscut.answer_submitter import submit
from sbscut.cache_manager import Cache
from sbscut.config_decoder import config
from sbscut.htmldecoder.link_parser import LinkParser
from sbscut.htmldecoder.question_parser import QuestionParser
from sbscut.htmldecoder.view_state_parser import ViewStateParser
from sbscut.logger import LogListener
from sbscut.solver import ai_solver

url: str = "http://1024.se.scut.edu.cn/"
homework: str = config.homework
cookies: dict = config.cookies
headers = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
			  "application/signed-exchange;v=b3;q=0.7",
	"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
	"User-Agent": config.user_agent
}


def main():
	log_listener = LogListener(config.log_level)
	log_listener.start()

	cache = Cache()
	cache.start()

	link_parser = LinkParser()
	response: Response = requests.get(url=url, cookies=cookies, headers=headers)
	link_parser.feed(response.text)
	response.close()

	question_parser = QuestionParser()
	view_state_parser = ViewStateParser()
	response: Response = requests.get(url=(url + link_parser.link), cookies=cookies, headers=headers)
	question_parser.feed(response.text)
	view_state_parser.feed(response.text)
	response.close()

	ques_cache: dict = cache.load()

	ai_ques: list[dict] = question_parser.result
	ai_worker = ai_solver.launcher(config.ai_threads, ques_cache, ai_ques)

	# running_ques: list[dict] = question_parser.result_running
	# running_worker = running_solver.launcher(config.running_threads, ques_cache, running_ques)

	answers = ai_worker.join()
	# running_worker.join()
	cache.shutdown()

	submit(answers, view_state_parser, cookies, headers)

	log_listener.shutdown()


if __name__ == '__main__':
	main()
