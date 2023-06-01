from os import getlogin, path
from socket import error as SocketError
from sys import argv

from paramiko import (AuthenticationException,
                      BadHostKeyException, SSHClient, SSHException)

from resources.classes.host import Host
from resources.classes.modules import (Apt, Command, Copy, Service, SysCTL)
from resources.classes.todo import Todo
from resources.tools import Logs
from load_resources import load_host, load_todos

TODO_FILE_PATH = ""
INVENTORY_FILE_PATH = ""
LOGS = Logs()
LOGS.setHandler()
logger = LOGS.logger


def _valid_args() -> bool:
    global TODO_FILE_PATH, INVENTORY_FILE_PATH
    try:
        if len(argv) != 5 or "-i" not in argv or "-f" not in argv:
            logger.error("Invalid arguments")
            logger.info("the program should be run like this:")
            logger.info("mla -f todos.yml -i inventory.yml")
            return False

        TODO_FILE_PATH = argv[argv.index("-f") + 1]
        INVENTORY_FILE_PATH = argv[argv.index("-i") + 1]

        return True
    except Exception as e:
        logger.error("Invalid arguments")
        logger.info("the program should be run like this:")
        logger.info("mla -f todos.yml -i inventory.yml")
        return False


def ssh_conn(host: Host) -> any:
    """ Initiate SSH connexion with specified host. """
    logger.debug("Attempting to establish an SSH connection")
    ssh_client = SSHClient()
    state = False
    try:
        if host.auth:
            logger.debug("Connecting via username & password method")
            ssh_client.connect(host.ssh_address, host.ssh_port,
                               host.ssh_user, host.ssh_password)
            state = True
        else:
            logger.debug("Connecting via public key method")
            ssh_client.connect(
                host.ssh_address, host.ssh_port, pkey=host.ssh_key_file)
            state = True
    except BadHostKeyException:
        logger.error("The host key could not be verified.")
    except AuthenticationException:
        logger.error("The authentication failed.")
    except SSHException:
        logger.error("The SSH connection could not be established.")
    except SocketError:
        logger.error("The socket could not be established.")
    except Exception as e:
        logger.error(f"{e.__str__()}")

    return state, ssh_client


def executor(host: Host, todos: Todo):
    """ For a precise host, executes the todos. """
    for _ in range(3):
        state, ssh_client = ssh_conn(host)
        if state:
            break

    if not state:
        logger.info(
            f"Could not connect to host {host.ssh_address}, process stopping."
        )
        logger.error(
            f"Failed to connect to {host.ssh_address}, process stopping."
        )
        logger.error(
            f"Used `username` + `password` authentication: {host.auth}.")
        return

    for index, todo in enumerate(todos):
        match todo.module:
            case "apt":
                module = Apt(todo.module, todo.params)
                status = module.process(
                    ssh_client,
                    host.ssh_password,
                    host.ssh_address
                )
            case "command":
                module = Command(todo.module, todo.params)
                status = module.process(ssh_client, host.ssh_address)
            case "copy":
                module = Copy(todo.module, todo.params)
                status = module.process(ssh_client)
            case "service":
                module = Service(todo.module, todo.params)
                status = module.process(
                    ssh_client,
                    host.ssh_password,
                    host.ssh_address
                )
            case "sysctl":
                module = SysCTL(todo.module, todo.params)
                status = module.process(
                    ssh_client,
                    host.ssh_password,
                    host.ssh_address
                )
            case "template":
                logger.warn(
                    f"The module `{todo.module}` has yet to be implemented.")
                continue
            case __:
                logger.error(f"Unrecognized module `{todo.module}`, skipping.")
                continue

        status = status if status is not None else "ok"
        logger.info(
            f"Todo no {index} done ; module: `{todo.module}` on {host.ssh_address} ====> {status.upper()}\n"
        )

    ssh_client.close()


def main():
    global TODO_FILE_PATH, INVENTORY_FILE_PATH

    if not _valid_args():
        return

    try:
        hosts = load_host(INVENTORY_FILE_PATH, logger)
        todos = load_todos(TODO_FILE_PATH, logger)

        for host in hosts:
            executor(host, todos)
            logger.info("Closing ssh connection.")

        logger.info("Closing MLA session.")
    except Exception as e:
        logger.error(f""" Error: {e.__str__()} """)


if __name__ == "__main__":
    main()
