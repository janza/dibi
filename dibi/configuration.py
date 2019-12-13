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

    def __post_init__(self):
        self.port = int(self.port)
        if self.password_cmd:
            self.password = subprocess.check_output(self.password_cmd, shell=True).decode().strip()


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
            )
            for section in self.config.sections()
        ]
