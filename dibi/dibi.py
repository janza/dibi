#!/usr/bin/env python3
import sys
import signal
from os import path

from typing import List
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget

from dibi.ui import Ui_main
from dibi.configuration import ConfigurationParser, ConnectionInfo


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
    config = ConfigurationParser()

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
