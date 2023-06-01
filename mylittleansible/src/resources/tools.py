""" Shared Tools. """

import logging
from sys import stdout

import colorlog


class Logs():
    """ Implements logging's features and provides logging's needed functionalities for this project. """

    def __init__(self):
        # logging.basicConfig()
        self.logger = logging.getLogger('MLA')
        self.logger.setLevel(logging.DEBUG)

    def setFormatter(self, fmt: str) -> colorlog.ColoredFormatter:
        """ Creates and sets a custom formatter with colors for logging. """
        return colorlog.ColoredFormatter(
            fmt,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        )

    def setHandler(self) -> None:
        """ Sets the handler an dadd it to the logging."""
        fmt = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler = logging.StreamHandler(stdout)

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(self.setFormatter(fmt))

        self.logger.addHandler(handler)


def stdCloser(stdin: any, stdout_channel: any, stderr: any):
    stdin.close()
    stdout_channel.close()
    stderr.close()


def execute_command(logger, sudo: bool, client: any, command: str, host_pwd: str = "") -> any:
    """ Command executor. """
    if sudo:
        stdin, stdout_channel, stderr = client.exec_command(
            f'echo "{host_pwd}" | {command}'
        )
        logger.debug(f'Execute command "{command}" WITH sudo.\n')
    else:
        stdin, stdout_channel, stderr = client.exec_command(f'{command}')
        logger.debug(f'Execute command "{command}" WITHOUT sudo.\n')

    stdout_str = stdout_channel.read().decode()
    stderr_str = stderr.read().decode()

    stdCloser(stdin, stdout_channel, stderr)

    return stdout_str, stderr_str
