import logging
from multiprocessing import Queue

import requests
from requests import Response

from sbscut.htmldecoder.view_state_parser import ViewStateParser


url: str = "http://1024.se.scut.edu.cn/%E8%AF%BE%E5%89%8D%E9%A2%84%E4%B9%A0.aspx"
_logger = logging.getLogger("sbscut.submitter")


def submit(answers: Queue, parser: ViewStateParser, cookies: dict, headers: dict):
	data: dict[str, str] = {
		"ctl00$MainContent$btnSave": "保存",
		"__EVENTTARGET": "",
		"__EVENTARGUMENT": "",
		"__VIEWSTATE": parser.view_state,
		"__VIEWSTATEGENERATOR": parser.view_state_generator,
		"__EVENTVALIDATION": parser.event_validation
	}

	while not answers.empty():
		answer = answers.get()["answer"]
		for key in answer:
			data[key] = answer[key]

	try:
		_logger.info("Submitting answer...")
		response: Response = requests.post(url=url, data=data, cookies=cookies, headers=headers)
		if response.status_code == 200:
			_logger.info("Submitted successfully!")
		else:
			_logger.error(f"Failed to submit: {response.status_code}")
	except Exception as e:
		_logger.error(f"Failed to submit: {e}")
