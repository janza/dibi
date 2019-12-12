from typing import Dict
from dataclasses import dataclass, field, asdict
from configparser import ConfigParser
import subprocess


@dataclass
class ConnectionInfo:
    host: str
    port: str
    user: str
    password: str = field(default='')
    password_cmd: str = field(default='')

    def __post_init__(self):
        self.port = int(self.port)
        if self.password_cmd:
            self.password = subprocess.check_output(self.password_cmd, shell=True).decode().strip()


class ConfigurationParser():
    config: Dict['str', 'str']

    def __init__(self, filepath: str):
        iniconfig = ConfigParser()
        iniconfig.read(filepath)
        sections = iniconfig.sections()
        self.config = {}
        if not sections:
            return

        first_section = sections[0]
        self.config = asdict(ConnectionInfo(**dict(iniconfig[first_section])))
