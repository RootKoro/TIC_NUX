from dataclasses import dataclass

from . import modules


@dataclass
class Todo:
    """ Representing a Todo object, it describes the it's name and parameters. """
    todo: list
