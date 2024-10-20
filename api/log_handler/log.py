import logging
from colorlog import ColoredFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = ColoredFormatter(
    '%(log_color)s%(asctime)-15s %(levelname)-8s [%(filename)s:%(lineno)-4d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('log_handler/app.log')
file_handler.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)-8s [%(filename)s:%(lineno)-4d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

if __name__ == '__main__':
    logger.debug('This is a debugging message')
    logger.info('This is an information')
    logger.warning('This is a warning message')
    logger.error('This is an error')
    logger.critical('This is a critical message')
