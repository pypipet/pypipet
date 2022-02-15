import logging, sys
from logging.handlers import TimedRotatingFileHandler

def get_console_handler(formatter):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    return console_handler

def get_file_handler(formatter, log_file):
    file_handler = TimedRotatingFileHandler(log_file)
    file_handler.setFormatter(formatter)
    return file_handler