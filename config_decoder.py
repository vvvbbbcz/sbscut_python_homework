import json


class Config:
	def __init__(self):
		config_file = open("config.json", "r")
		config_dict: dict = json.load(config_file)
		config_file.close()

		self.homework: str = config_dict.get("homework", "")
		self.cookies: dict = config_dict.get("cookies", {})
		self.user_agent: str = config_dict.get("user_agent", "")
		self.ds_api_key: str = config_dict.get("deepseek_api_key", "")
		self.threads: int = config_dict.get("threads", 1)
		self.start_question: int = config_dict.get("start_question", 0)
		self.log_level: str = config_dict.get("log_level", "INFO")


config: Config = Config()
