import logging

from .constant import VERSION


formatter: logging.Formatter = logging.Formatter(
    f"%(levelname)s: %(asctime)s v{VERSION} %(filename)s:%(lineno)d %(message)s")

logger: logging.Logger = logging.getLogger('drtpa-scraper')
logger.setLevel(logging.INFO)

stream_handler: logging.StreamHandler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def get_logger() -> logging.Logger:
    return logger
