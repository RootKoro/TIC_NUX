from os import listdir, path

from resources.tools import execute_command, Logs


class Base:
    """ Base of all modules. """
    module: str
    params: dict
    logs: Logs
    logger: any

    def __init__(self, module: str, params: dict):
        self.module = module
        self.params = params
        self.logs = Logs()
        self.logs.setHandler()
        self.logger = self.logs.logger

    def process(self, ssh_client, ssh_password="", ssh_host=""):
        """ Apply the action to `ssh_client` using `params`. """
        ...


class Copy(Base):
    """ extends `Base` and contains as parameters:
        - src: path of the file / directory to copy (str);
        - dest: destination path (str);
        - backup: backup or not (bool).
    """

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)

    def mkdir_p(self, sftp: any, remote_directory: str) -> None:
        """ Recursively generates directory if doesn't exist on remote host. """
        if remote_directory != '':
            try:
                sftp.chdir(remote_directory)
            except IOError:
                dirname, basename = path.split(remote_directory.rsplit('/'))
                self.mkdir_p(sftp, dirname)
                sftp.mkdir(basename)
                sftp.chdir(dirname)

    def put_dir(self, sftp: any, src: str, dest: str) -> None:
        """ Send the whole directory to remote host. """
        _, dir_name = path.split(src)
        src_dir = listdir(src)

        for item in src_dir:
            item_path = path.join(src, item)

            if path.isfile(item_path):
                self.logger.debug(f"put file {item_path} on {dest}/{item}\n")
                sftp.put(item_path, f"{dest}/{item}", confirm=False)

            elif path.isdir(item_path):
                self.mkdir_p(sftp, f"{dest}/{dir_name}")
                self.put_dir(sftp, item_path, f"{dest}/{dir_name}")

    def process(self, ssh_client: any) -> None:
        src = path.abspath(self.params["src"]).rstrip('/')
        dest = self.params["dest"].rstrip('/')
        _, item = path.split(src)

        sftp = ssh_client.open_sftp()

        if path.isdir(src):
            self.mkdir_p(sftp, f"{dest}/{item}")
            self.put_dir(sftp, src, f"{dest}/{item}")
        elif path.isfile(src):
            self.mkdir_p(sftp, dest)
            self.logger.debug(f"put single file {src} on {dest}/{item}")
            sftp.put(src, f"{dest}/{item}", confirm=False)

        # return "successfully copied."


class Template(Base):
    """ extends `Base` and contains as parameters:
        - src: path of the template (str);
        - dest: path of the file to template using the template (str);
        - vars: variables to change in the templated file (dict).
    """

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)


class Service(Base):
    """ extends `Base` and contains as parameters:
        - name: name of the service (str);
        - state: describing the state of the service (str).
    """
    launch_tuple = ('started', 'restarted', 'stopped')
    activation_tuple = ('enabled', 'disabled')

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)

    def service_state(self, ssh_client: any, ssh_password: str) -> str:
        """ Determines service's state. """
        command = ""
        if self.params["state"] in self.launch_tuple:
            command = f"sudo -S systemctl is-active {self.params['name']}"
        elif self.params["state"] in self.activation_tuple:
            command = f"sudo -S systemctl is-enabled {self.params['name']}"

        if command == "":
            return "failed"

        stdout, _ = execute_command(
            self.logger, True, ssh_client, command, ssh_password)
        return stdout[:-1]

    def executor(self, ssh_client: any, ssh_password: str, ssh_host: str, action: str) -> str:
        """ Execute the actions and return the state. """
        command = f"sudo -S systemctl {action} {self.params['name']}"
        _, stderr = execute_command(
            self.logger, True, ssh_client, command, ssh_password)

        if "incorrect" in stderr:
            self.logger.info(
                f"Incorrect password provided in inventory file for {ssh_host}. ")
            self.logger.info(
                f"Service module can't be executed without sudo password.")
            self.logger.error(
                f"No password were provided in inventory file for {ssh_host}. ")
            self.logger.error(
                f"Service module can't be executed without sudo password.")
            return "incorrect"

        return self.service_state(ssh_client, ssh_password)

    def process(self, ssh_client, ssh_password, ssh_host):
        action = self.params["state"][:-
                                      2] if self.params["state"] != "stopped" else self.params["state"][:-3]

        if "failed" in self.service_state(ssh_client, ssh_password):
            self.logger.debug(
                f"{self.params['name']} initial state on {ssh_host} is FAILED.")

        exec = self.executor(ssh_client, ssh_password, ssh_host, action)
        if "failed" in exec:
            self.logger.info(
                f"A problem occured when executing {action} for {self.params['name']} on {ssh_host}. ")
            self.logger.info(f"Current state is {exec}")
            self.logger.error(
                f"A problem occured when executing {action} for {self.params['name']} on {ssh_host}. ")
            self.logger.error(f"Current state is {exec}")
            return "ko"

        return "changed"


class Command(Base):
    """ extends `Base` and contains as parameters:
        - command: name of the service (str);
        - shell: describing the state of the service (str).
    """

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)

    def process(self, ssh_client, ssh_host):
        commands = self.params["command"]

        self.logger.info(f"{ssh_host}: command list:\n{commands}\n")
        self.logger.info(
            "Make sure to be in debug mode to see stdout and stderr for each command.\n")

        for command in commands.split('\n'):
            stdout, stderr = execute_command(
                self.logger, False, ssh_client, command)
            self.logger.info(f"On {ssh_host}, executed command: {command}\n")

            self.logger.debug(
                f"While executing {command} on {ssh_host}, STDOUT:")
            self.logger.debug(f"{stdout}\n")

            self.logger.debug(
                f"While executing {command} on {ssh_host}, STDERR:")
            self.logger.debug(f"{stderr}\n")

        return "ok"


class SysCTL(Base):
    """ extends `Base` and contains as parameters:
        - attribute: kernel attribute to update (str);
        - value: value to link to the kernel attribute (any);
        - permanent: permanemt or not (bool).
    """

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)

    def none_perm_module_state(self, ssh_client: any, ssh_password: str) -> str:
        """ Determines the module's NON PERMANENT state. """
        command = f"sudo -S sysctl -n {self.params['attribute']}"
        stdout, _ = execute_command(
            self.logger, True, ssh_client, command, ssh_password)

        return stdout[:-1]

    def permanent_module_state(self, ssh_client: any, ssh_password: str) -> any:
        """ Determines the module's PERMANENT state. """
        command = f'cat /etc/sysctl.conf | grep {self.params["attribute"]} | cut -d "=" -f2'
        stdout, _ = execute_command(self.logger, False, ssh_client, command)
        value = stdout[:-1]
        none_perm_value = self.none_perm_module_state(ssh_client, ssh_password)

        return none_perm_value, value

    def executor(self, ssh_client: any, ssh_password: str) -> str:
        """ Applies changes to the given ssh_host's kernel. """
        if not self.params["permanent"]:
            command = f'sudo -S sysctl -w {self.params["attribute"]}={str(self.params["value"])}'
            execute_command(self.logger, True, ssh_client,
                            command, ssh_password)
            return self.none_perm_module_state(ssh_client, ssh_password)

        none_perm_value, _ = self.permanent_module_state(
            ssh_client, ssh_password
        )

        if none_perm_value != self.params['value']:
            command = f'sudo -S echo {self.params["attribute"]}={self.params["value"]} >> /etc/sysctl.conf'
            execute_command(self.logger, True, ssh_client,
                            command, ssh_password)

        command = "sudo -S sysctl -p"
        execute_command(self.logger, True, ssh_client, command, ssh_password)
        return self.none_perm_module_state(ssh_client, ssh_password)

    def process(self, ssh_client, ssh_password, ssh_host):
        if not self.params['permanent']:
            none_perm_value = self.none_perm_module_state(
                ssh_client, ssh_password)
            if self.params['value'] != none_perm_value:
                self.logger.debug(
                    f"{self.params['attribute']} < > {self.params['value']} on {ssh_host}, current: {none_perm_value}"
                )
        else:
            none_perm_value, perm_value = self.permanent_module_state(
                ssh_client, ssh_password)
            if none_perm_value != self.params['value']:
                self.logger.debug(
                    f"{self.params['attribute']}={self.params['value']} not applied permanently yet on {ssh_host}. ")
                self.logger.debug(f"Currently value: {none_perm_value}. ")
                self.logger.debug(
                    f"Currently defined in /etc/sysctl.conf file: {perm_value}")

        if none_perm_value == self.params['value']:
            return "ok"

        module_value = self.executor(ssh_client, ssh_password)

        if module_value == self.params['value']:
            return "changed"

        self.logger.debug(
            f"{self.params['attribute']} <--- {self.params['value']} FAILED on {ssh_host}, current: {module_value}"
        )

        return "ko"


class Apt(Base):
    """ extends `Base` and contains as parameters:
        - name: name of the package;
        - state: install (present) or uninstall (absent) the package (str).
    """
    action: str

    def __init__(self, module: str, params: dict):
        super.__init__(module, params)
        self.action = "install" if self.params["state"] == "present" else "uninstall"

    def executor(self, ssh_client: any, ssh_host: str) -> str:
        """ Execute the actions and return the state. """
        command = f'dpkg -s {self.params["name"]} | grep "Status"'
        stdout, _ = execute_command(self.logger, False, ssh_client, command)

        if self.params["state"] == "present":
            if "ok installed" in stdout:
                self.logger.info(
                    f"{self.params['name']} already installed on {ssh_host}. Todos DONE with status OK.")
                return "ok"
        elif self.params["state"] == "absent":
            if "ok installed" not in stdout:
                self.logger.info(
                    f"{self.params['name']} already uninstalled on {ssh_host}. Todos DONE with status OK.")
                return "ok"

        return "to change"

    def process(self, ssh_client, ssh_password, ssh_host):
        command = f'echo "{ssh_password}" | sudo -S apt-get update'
        _, stderr = execute_command(
            self.logger,
            True,
            ssh_client,
            command,
            ssh_password
        )

        if "incorrect" in stderr:
            self.logger.warning(
                f"Incorrect password provided in inventory file for {ssh_host}. ")
            self.logger.warning(
                f"apt module can't be executed without sudo password.")
            self.logger.error(
                f"No password were provided in inventory file for {ssh_host}. ")
            self.logger.error(
                f"apt module can't be executed without sudo password.")
            return "ko"
        state = self.executor(ssh_client, ssh_host)

        if state == "ok":
            return state

        install_cmd = f'echo "{ssh_password}" | sudo -S apt-get install -y {self.params["name"]}'
        uninstall_cmd = f'echo "{ssh_password}" | sudo -S apt-get auto-remove -y {self.params["name"]}'
        command = install_cmd if self.action == "install" else uninstall_cmd

        stdout, stderr = execute_command(
            self.logger,
            True,
            ssh_client,
            command,
            ssh_password
        )

        self.logger.debug(
            f"While trying to {self.action} {self.params['name']}, STDOUT:\n{stdout}")

        if stderr != "" and "dpkg-preconfigure: unable to re-open stdin:" not in stderr:
            self.logger.error(
                f"While trying to {self.action} {self.params['name']}, STDERR:\n{stderr}")
            return "ko"

        return "changed"
