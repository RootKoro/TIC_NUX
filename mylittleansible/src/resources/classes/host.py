from dataclasses import dataclass
from os import getlogin


@dataclass
class Host:
    """ Describes a precise host. """
    name: str
    ssh_address: str
    ssh_port: int
    auth: bool
    ssh_user: str = getlogin()
    ssh_password: str = ""
    ssh_key_file: str = ""
