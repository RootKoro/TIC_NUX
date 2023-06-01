import logging
import colorlog

from sys import stdout

# Create a custom formatter with colors
formatter = colorlog.ColoredFormatter(
    # "%(log_color)s%(levelname)s:%(message)s",
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    },
)

# Create a logger and set its level
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Create a handler and set the formatter
handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Example usage
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
