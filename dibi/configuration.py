from typing import Dict, List
from dataclasses import dataclass, field, asdict
from configparser import ConfigParser, NoSectionError
import argparse
import subprocess
from os import path
from time import time


myloginpath_supported = False
try:
    import myloginpath
    myloginpath_supported = True
except Exception:
    pass


start = time()


def t(label: str):
    print(label, time() - start)


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

    def get_password(self):
        if self.password_cmd and not self.password:
            return subprocess.check_output(self.password_cmd, shell=True).decode().strip()
        return self.password

    def __post_init__(self):
        self.port = int(self.port)
        self.ssh_port = int(self.ssh_port)

    def toDict(self) -> Dict[str, str]:
        return asdict(self)

    def __str__(self):
        return f'{self.host}:{self.port} {self.user} through {self.ssh_user}@{self.ssh_host}:{self.ssh_port}'


def load_from_login_path():
    p = argparse.ArgumentParser()
    p.add_argument('--login-path')
    args, rest = p.parse_known_args()

    if args.login_path:
        try:
            return myloginpath.parse(args.login_path), rest
        except NoSectionError as err:
            print(err)
        except FileNotFoundError as err:
            print(err)

    return {}, rest


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

        conf = {}
        rest = None
        if myloginpath_supported:
            conf, rest = load_from_login_path()

        p = argparse.ArgumentParser()
        p.add_argument('--host')
        p.add_argument('--user', '-u')
        p.add_argument('--password', '-p')
        p.add_argument('--port', '-P', type=int, default=3306)
        p.set_defaults(**conf)
        args = p.parse_args(rest)

        args_connection = None
        if args.host is not None:
            args_connection = ConnectionInfo(label='default', **vars(args))

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
        ] + ([args_connection] if args_connection else [])

    def save(self, connections: List[ConnectionInfo]):
        iniconfig = ConfigParser()
        for connection in connections:
            if connection.label == 'default':
                continue

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
