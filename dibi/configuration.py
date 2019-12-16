from dataclasses import dataclass, field
from configparser import ConfigParser
import subprocess


@dataclass
class ConnectionInfo:
    host: str
    port: int
    user: str
    password: str = field(default='')
    password_cmd: str = field(default='')
    ssh_host: str = ''
    ssh_port: int = 22
    ssh_user: str = ''

    def __post_init__(self):
        self.port = int(self.port)
        if self.password_cmd:
            self.password = subprocess.check_output(self.password_cmd, shell=True).decode().strip()

    def __str__(self):
        return f'{self.host}:{self.port} {self.user} through {self.ssh_user}@{self.ssh_host}:{self.ssh_port}'


class ConfigurationParser():
    def __init__(self, filepath: str):
        iniconfig = ConfigParser()
        iniconfig.read(filepath)
        self.config = iniconfig

    @property
    def connections(self):
        return [
            ConnectionInfo(
                self.config[section]['host'],
                self.config[section].getint('port'),
                self.config[section]['user'],
                self.config[section].get('password', ''),
                self.config[section].get('password_cmd', ''),
                self.config[section].get('ssh_host', ''),
                self.config[section].getint('ssh_port', fallback=22),
                self.config[section].get('ssh_user', ''),
            )
            for section in self.config.sections()
        ]
