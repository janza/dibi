#!/usr/bin/env python3
import configparser
import sys
import signal
import argparse
from os import path

from typing import List
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget

from dibi.ui import Ui_main
from dibi.configuration import ConfigurationParser, ConnectionInfo

myloginpath_supported = False
try:
    import myloginpath
    myloginpath_supported = True
except Exception:
    pass


def load_from_login_path():
    p = argparse.ArgumentParser()
    p.add_argument('--login-path')
    args, rest = p.parse_known_args()

    if args.login_path:
        try:
            return myloginpath.parse(args.login_path), rest
        except configparser.NoSectionError as err:
            print(err)
        except FileNotFoundError as err:
            print(err)

    return {}, rest


class AppWindow(QWidget):
    def __init__(self, config: ConfigurationParser):
        super().__init__()
        self.config = config
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.ui.set_connections(config.connections)
        self.ui.change_connections.connect(self.save_config)
        self.show()
        self.setWindowTitle('DiBi')

    def save_config(self, connections: List[ConnectionInfo]):
        self.config.save(connections)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    conf = {}
    rest = None
    if myloginpath_supported:
        conf, rest = load_from_login_path()

    config = ConfigurationParser()
    connections = config.connections

    p = argparse.ArgumentParser()
    p.add_argument('--host')
    p.add_argument('--user', '-u')
    p.add_argument('--password', '-p')
    p.add_argument('--port', '-P', type=int, default=3306)
    p.set_defaults(**conf)
    args = p.parse_args(rest)

    if args.host is not None:
        connections = [ConnectionInfo(label='default', **vars(args))] + connections

    def expand(filename: str) -> str:
        return path.join(path.dirname(__file__), filename)

    app = QApplication(sys.argv)
    window = AppWindow(config)
    window.show()
    app.setWindowIcon(QtGui.QIcon(expand('dibi.png')))
    return_code = app.exec_()
    sys.exit(return_code)


if __name__ == "__main__":
    main()
