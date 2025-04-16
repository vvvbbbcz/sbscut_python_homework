import html.parser
from enum import Enum
from termios import OFDEL

from logger import logger


class State(Enum):
	FREE = 0
	START = 1
	TYPE = 2
	QUESTION_START = 3
	QUESTION = 4
	CODE = 5
	END = 6


_starttag2state: dict[str, State] = {
	"td": State.START,
	"font": State.TYPE,
	"input": State.QUESTION,
	"textarea": State.QUESTION,
	"pre": State.CODE
}

_endtag2state: dict[str, State] = {
	"td": State.END,
	"font": State.QUESTION_START,
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
		self.state: State = State.FREE
		self.question_cache: dict = {
			"type": "",
			"question": "",
			"answer": []
		}
		self.answer_cache: list[str] = []
		self.result: list[dict] = []

	def handle_starttag(self, tag, attrs):
		tag_attrs = {}
		for attr in attrs:
			tag_attrs[attr[0]] = attr[1]

		state_before = self.state
		self.state = _starttag2state.get(tag, state_before)
		if self.state == State.START:
			self.clean_cache()

		if tag == "font" and state_before != State.START:
			self.state = state_before

		if tag == "input":
			if tag_attrs.get("type") == "text":
				self.answer_cache.append(tag_attrs["name"])
				self.question_cache["question"] += "<?>"

		if tag == "textarea":
			self.answer_cache.append(tag_attrs["name"])

	def handle_data(self, data):
		if self.state == State.TYPE:
			self.question_cache["type"] = data
		elif self.state == State.QUESTION_START:
			self.question_cache["question"] += data[1:]
		elif self.state == State.QUESTION:
			self.question_cache["question"] += data
		elif self.state == State.CODE:
			self.question_cache["question"] += data

	def handle_endtag(self, tag):
		self.state = _endtag2state.get(tag, self.state)
		if self.state == State.END:
			self.question_cache["answer"] = self.answer_cache
			self.result.append(self.question_cache)
			print(self.question_cache)
			self.clean_cache()
			self.state = State.FREE

	def clean_cache(self):
		self.question_cache["type"] = ""
		self.question_cache["question"] = ""
		self.question_cache["answer"] = []
		self.answer_cache = []
