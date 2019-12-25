#!/usr/bin/env python3
import configparser
import sys
import signal
import argparse
from os import path

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow

from dibi.db import DbThread
from dibi.ui import UI
from dibi.configuration import ConfigurationParser, ConnectionInfo

myloginpath_supported = False
try:
    import myloginpath
    myloginpath_supported = True
except Exception:
    pass


def load_from_login_path():
    p = argparse.ArgumentParser()
    p.add_argument('--login-path', required=False)
    args, rest = p.parse_known_args()
    if not args.login_path:
        return True, {}, rest

    try:
        return False, myloginpath.parse(args.login_path), rest
    except configparser.NoSectionError as err:
        print(err)
    except FileNotFoundError as err:
        print(err)

    return True, {}, rest


def dibi():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    conf = {}
    rest = None
    connection_required = True
    if myloginpath_supported:
        connection_required, conf, rest = load_from_login_path()

    config = ConfigurationParser()
    connections = config.connections

    connection_required = connection_required and not bool(connections)

    p = argparse.ArgumentParser()
    p.add_argument('--host', required=connection_required)
    p.add_argument('--user', '-u', required=connection_required)
    p.add_argument('--password', '-p', required=connection_required)
    p.add_argument('--port', '-P', type=int, default=3306)
    p.set_defaults(**conf)
    args = p.parse_args(rest)

    if args.host is not None:
        connections = [ConnectionInfo(label='default', **vars(args))] + connections

    def expand(filename: str) -> str:
        return path.join(path.dirname(__file__), filename)

    app = QApplication(sys.argv)
    for font in [
            expand('fonts/Cabin-Bold.ttf'),
            expand('fonts/Cabin-Medium.ttf'),
            expand('fonts/Cabin-Regular.ttf'),
    ]:
        QtGui.QFontDatabase.addApplicationFont(font)

    t = DbThread()
    widget = UI(t, connections)

    window = QMainWindow()
    window.layout().setSpacing(0)
    window.setCentralWidget(widget)
    window.show()
    app.setStyleSheet(open(expand('styles.qss')).read())
    return_code = app.exec_()
    t.job.emit('disconnect', '', '', {})
    sys.exit(return_code)


if __name__ == "__main__":
    dibi()
