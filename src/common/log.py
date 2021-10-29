import logging
from logging import handlers

DEFINE_LOG_FORMAT = "%(asctime)s   %(levelname)s   [%(filename)s:%(lineno)d]    %(message)s"


class Logger(object):

    def __init__(self):
        self.__logger = logging.getLogger()
        self.__logger.setLevel(logging.INFO)
        self.__log_format = logging.Formatter(DEFINE_LOG_FORMAT)

    def get_logger(self):
        file_handler = handlers.TimedRotatingFileHandler(filename='../../logs/tnn.log', when='MIDNIGHT', backupCount=30, encoding='utf-8')
        file_handler.setFormatter(self.__log_format)
        self.__logger.addHandler(file_handler)
        return self.__logger


logger = Logger().get_logger()