import logging
from .utility import *

LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
DEFAULT_LEVEL = "info"

FORMAT = (
    "%(asctime)s [%(filename)s|%(funcName)s] [%(levelname)s] [%(lineno)s] %(message)s"
)

LOG_FILE_DEFAULT = "pipet_default.log"

def parse_log_level(log_level):
    return LEVELS.get(log_level, LEVELS[DEFAULT_LEVEL])

def setup_logging(log_level, log_path='./'):
    logger = logging.getLogger('__default__')
    logger.setLevel(parse_log_level(log_level))
    
    formatter = logging.Formatter(FORMAT)
    logger.addHandler(get_console_handler(formatter))
    logger.addHandler(get_file_handler(formatter, 
                                       log_path+LOG_FILE_DEFAULT))
    #  propagate the error up to parent
    logger.propagate = False

