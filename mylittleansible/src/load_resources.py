""" Module that permit to load resources (todos and inventory files). """

from os import path

from yaml import FullLoader, YAMLError, load

import resources.classes.modules as mod
from resources.classes.host import Host
from resources.classes.todo import Todo


def load_todos(todos_file_path: str, logger) -> list[Todo]:
    """ Loads todos from the given `todo_file_path` in a list and returns it """
    todos: Todo = Todo([])
    try:
        if path.isfile(todos_file_path):
            with open(todos_file_path, 'r', encoding="utf-8") as todos_file:
                converted_todos = load(todos_file.read(), FullLoader)
            for todo in converted_todos:
                todos.todo.append(mod.Base(todo["module"], todo["params"]))
            logger.info("Todo loaded successfully.")
        else:
            logger.error("No such file")
            raise FileNotFoundError(todos_file_path)
    except YAMLError:
        logger.error("An error occurred when loading the todos file.")
    except Exception as e:
        logger.error(e.__str__())
    return todos.todo


def load_host(inventory_file_path, logger):
    """ Loads the specified hosts from the given `inventory_file_path` in a list and returns it. """
    hosts: list[Host] = []
    try:
        if path.isfile(inventory_file_path):
            with open(inventory_file_path, "r", encoding="utf-8") as inventories:
                converted_inventories = load(inventories.read(), FullLoader)
                for hostname in converted_inventories["hosts"]:
                    params = converted_inventories["hosts"][hostname]

                    logger.info(f"Target host: {hostname}")

                    target = Host(
                        hostname,
                        params["ssh_address"],
                        params["ssh_port"],
                        False if "ssh_key_file" in params else True,
                        params["ssh_user"] if "ssh_user" in params and "ssh_key_file" not in params else None,
                        params["ssh_password"] if "ssh_password" in params and "ssh_key_file" not in params else None,
                        params["ssh_key_file"] if "ssh_key_file" in params and "ssh_key_file" not in params else None
                    )
                    hosts.append(target)
        else:
            logger.error("No such file")
            raise FileNotFoundError(inventory_file_path)
    except YAMLError:
        logger.error("An error occurred when loading the inventory file.")
    except Exception as e:
        logger.error(e.__str__())
    return hosts
