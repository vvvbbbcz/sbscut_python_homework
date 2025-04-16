import html.parser
from logger import logger
from config_decoder import config


class LinkParser(html.parser.HTMLParser):
	def __init__(self):
		super().__init__()
		self.link_cache = ""
		self.link = ""

	def handle_starttag(self, tag, attrs):
		if tag == "a":
			tag_attrs = {}
			for attr in attrs:
				tag_attrs[attr[0]] = attr[1]

			if tag_attrs.get("href") is not None:
				self.link_cache = tag_attrs["href"]
				logger.debug("Get link cache: " + self.link_cache)

	def handle_data(self, data):
		if data == config.homework:
			self.link = self.link_cache
			logger.debug("Get link: " + self.link)
