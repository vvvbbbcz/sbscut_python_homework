import html.parser
import logging

logger = logging.getLogger("sbscut.view_state_parser")


class ViewStateParser(html.parser.HTMLParser):
	def __init__(self):
		super().__init__()
		self.view_state = ""
		self.view_state_generator = ""
		self.event_validation = ""

	def handle_starttag(self, tag, attrs):
		if tag == "input":
			tag_attrs = {}
			for attr in attrs:
				tag_attrs[attr[0]] = attr[1]

			if tag_attrs["id"] == "__VIEWSTATE":
				self.view_state = tag_attrs["value"]
				logger.debug("Get __VIEWSTATE: " + self.view_state)
				return

			if tag_attrs["id"] == "__VIEWSTATEGENERATOR":
				self.view_state_generator = tag_attrs["value"]
				logger.debug("Get __VIEWSTATEGENERATOR: " + self.view_state_generator)
				return

			if tag_attrs["id"] == "__EVENTVALIDATION":
				self.event_validation = tag_attrs["value"]
				logger.debug("Get __EVENTVALIDATION: " + self.event_validation)
				return

	def reset(self):
		super().reset()
		self.view_state = ""
		self.view_state_generator = ""
		self.event_validation = ""

	def set_data(self, data: dict):
		data["__VIEWSTATE"] = self.view_state
		data["__VIEWSTATEGENERATOR"] = self.view_state_generator
		data["__EVENTVALIDATION"] = self.event_validation
		self.reset()
