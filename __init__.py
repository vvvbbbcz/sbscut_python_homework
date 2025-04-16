import requests
from requests import Response

from config_decoder import config
from htmldecoder.link_parser import LinkParser
from htmldecoder.question_parser import QuestionParser
from htmldecoder.view_state_parser import ViewStateParser
from logger import logger

view_state_parser = ViewStateParser()
url: str = "http://1024.se.scut.edu.cn/"
homework: str = config.homework
cookies: dict = config.cookies
logger.setLevel(config.log_level)
headers = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
			  "application/signed-exchange;v=b3;q=0.7",
	"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
	"User-Agent": config.user_agent
}


def main():
	link_parser = LinkParser()
	response: Response = requests.get(url=url, cookies=cookies, headers=headers)
	link_parser.feed(response.text)
	response.close()

	question_parser = QuestionParser()
	response: Response = requests.get(url=(url + link_parser.link), cookies=cookies, headers=headers)
	question_parser.feed(response.text)


if __name__ == '__main__':
	main()
