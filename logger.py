import logging

logger = logging.getLogger("Sbscut Auto Rater")

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("sbscut.log")

formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
