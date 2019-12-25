from typing import Dict, List
from dataclasses import dataclass, field, asdict
from configparser import ConfigParser
import subprocess
from os import path


@dataclass
class ConnectionInfo:
    label: str
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

    def toDict(self) -> Dict[str, str]:
        return asdict(self)

    def __str__(self):
        return f'{self.host}:{self.port} {self.user} through {self.ssh_user}@{self.ssh_host}:{self.ssh_port}'


class ConfigurationParser():
    filepath: str

    def __init__(self, filepath: str = ''):
        if not filepath:
            filepath = path.expanduser('~/.dibi.conf')
        self.filepath = filepath

    @property
    def connections(self) -> List[ConnectionInfo]:
        iniconfig = ConfigParser()
        iniconfig.read(self.filepath)
        return [
            ConnectionInfo(
                section,
                iniconfig[section]['host'],
                iniconfig[section].getint('port'),
                iniconfig[section]['user'],
                iniconfig[section].get('password', ''),
                iniconfig[section].get('password_cmd', ''),
                iniconfig[section].get('ssh_host', ''),
                iniconfig[section].getint('ssh_port', fallback=22),
                iniconfig[section].get('ssh_user', ''),
            )
            for section in iniconfig.sections()
        ]

    def save(self, connections: List[ConnectionInfo]):
        iniconfig = ConfigParser()
        for connection in connections:
            iniconfig[connection.label] = {
                'host': connection.host,
                'port': str(connection.port),
                'user': connection.user,
                'password': connection.password if not connection.password_cmd else '',
                'password_cmd': connection.password_cmd,
                'ssh_host': connection.ssh_host,
                'ssh_user': connection.ssh_user,
            }

        with open(self.filepath, 'w') as configfile:
            iniconfig.write(configfile)
