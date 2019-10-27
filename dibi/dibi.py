#!/usr/bin/env python3

import pymysql
import sys
import signal

from PyQt5.QtWidgets import QApplication
from dibi.ui import UI


class Controller():
    def __init__(self, c):
        self.c = c
        self.table_cache = {}

    def text_update(self, text):
        with self.c.cursor() as cursor:
            if text[:len('select')].lower() == 'select':
                text += ' LIMIT 100'
            cursor.execute(text)
            return cursor

    def get_db_list(self):
        with self.c.cursor(pymysql.cursors.Cursor) as cursor:
            cursor.execute('show databases')
            return [db[0] for db in cursor]

    def get_table_list(self, db):
        try:
            return self.table_cache[db]
        except Exception:
            pass

        with self.c.cursor(pymysql.cursors.Cursor) as cursor:
            if db is None:
                cursor.execute('show tables')
            else:
                cursor.execute('show tables in {}'.format(db))
            tables = [table[0] for table in cursor]
            if db is not None:
                self.table_cache[db] = tables
            return tables


def dibi():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    c = pymysql.connect(
        host='127.0.0.1',
        user='',
        password='',
        # database='',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        app = QApplication(sys.argv)
        data = [
            {"ok": 1, "nok": 2},
            {"ok": 1, "nok": 2},
            {"ok": 1, "nok": 2},
            {"ok": 1, "nok": 2},
            {"ok": 1, "nok": 2},
            {"ok": 1, "nok": 2},
        ]
        widget = UI(Controller(c))
        widget.set_data(data)
        widget.show()
        sys.exit(app.exec_())
    finally:
        c.close()


if __name__ == "__main__":
    dibi()
