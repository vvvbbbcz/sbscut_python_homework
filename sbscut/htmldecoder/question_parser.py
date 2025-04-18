import html.parser
import logging
from enum import Enum

logger = logging.getLogger("sbscut.question_parser")


class State(Enum):
	FREE = 0
	START = 1
	TYPE = 2
	QUESTION_START = 3
	QUESTION = 4
	CODE = 5
	ANSWER = 6
	END = 7


_starttag2state: dict[str, State] = {
	"td": State.START,
	"font": State.TYPE,
	"input": State.QUESTION,
	"textarea": State.ANSWER,
	"pre": State.CODE
}

_endtag2state: dict[str, State] = {
	"td": State.END,
	"font": State.QUESTION_START,
	"textarea": State.QUESTION,
	"pre": State.QUESTION
}

_state2key: dict[State, str] = {
	State.TYPE: "type",
	State.QUESTION: "question",
	State.CODE: "question",
}


class QuestionParser(html.parser.HTMLParser):
	def __init__(self):
		super().__init__()
		self.__state: State = State.FREE
		self.__question_cache: dict = {
			"number": 0,
			"type": "",
			"question": "",
			"answer": []
		}
		self.__answer_cache: list[str] = []
		self.result: list[dict] = []

	def handle_starttag(self, tag, attrs):
		tag_attrs = {}
		for attr in attrs:
			tag_attrs[attr[0]] = attr[1]

		state_before = self.__state
		self.__state = _starttag2state.get(tag, state_before)
		if self.__state == State.START:
			self.clean_cache()

		if tag == "font" and state_before != State.START:
			self.__state = state_before

		if tag == "input":
			if tag_attrs.get("type") == "text":
				self.__answer_cache.append(tag_attrs["name"])
				self.__question_cache["question"] += "<?>"
			elif tag_attrs.get("type") == "radio":
				self.__answer_cache.append(tag_attrs["name"])
				self.__question_cache["question"] += "\n"

		if tag == "textarea":
			self.__answer_cache.append(tag_attrs["name"])

	def handle_data(self, data):
		data = (data
				.replace("\u202a", "")
				.replace("\u202b", "")
				.replace("\u202c", "")
				.replace("\u202d", "")
				.replace("\u202e", "")
				.replace("\xa0", "")
				.replace("\r", ""))

		if self.__state == State.TYPE:
			self.__question_cache["type"] = data
		elif self.__state == State.QUESTION_START:
			self.__question_cache["question"] += data[1:]
		elif self.__state == State.QUESTION:
			self.__question_cache["question"] += data
		elif self.__state == State.CODE:
			self.__question_cache["question"] += "\n"
			self.__question_cache["question"] += data

	def handle_endtag(self, tag):
		self.__state = _endtag2state.get(tag, self.__state)
		if self.__state == State.END:
			self.__question_cache["number"] += 1
			self.__question_cache["answer"] = self.__answer_cache

			self.result.append(self.__question_cache.copy())
			logger.debug("Get question: " + str(self.__question_cache))

			self.clean_cache()
			self.__state = State.FREE

	def clean_cache(self):
		self.__question_cache["type"] = ""
		self.__question_cache["question"] = ""
		self.__question_cache["answer"] = []
		self.__answer_cache = []
