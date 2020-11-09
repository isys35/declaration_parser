import logging

logger = logging.getLogger("parser_loger")
logger.setLevel(logging.INFO)
console_headler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(lineno)d : %(message)s')
console_headler.setFormatter(formatter)
logger.addHandler(console_headler)
