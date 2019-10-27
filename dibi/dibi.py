#!/usr/bin/env python3

import pymysql
import sys
import signal
import re
import argparse

from PyQt5.QtWidgets import QApplication
from dibi.ui import UI


class Controller():
    def __init__(self, c):
        self.c = c
        self.table_cache = {}
        self.current_db = None
        self.current_table = None

    @staticmethod
    def get_table_from_query(query):
        m = re.search(
            r'from\s+`?([a-z0-9_]+)`?\.?`?([a-z0-9_]+)?`?', query, re.IGNORECASE)

        if m:
            db, table = m.groups()
            if table is None:
                return None, db
            return db, table
        return None, None

    @staticmethod
    def get_db_from_use(query):
        m = re.search(r'use\s+`?([a-z0-9_]+)', query, re.IGNORECASE)
        if not m:
            return None
        return m.groups()[0]

    def text_update(self, text, params=None):
        with self.c.cursor() as cursor:
            if text[:3].lower() == 'use':
                self.current_db = self.get_db_from_use(text)
            elif text[:6].lower() == 'select':
                text += ' LIMIT 100'
                db, table = self.get_table_from_query(text)
                if db:
                    self.current_db = db
                if table:
                    self.current_table = table

            cursor.execute(text, params)
            return cursor

    def get_db_list(self):
        with self.c.cursor(pymysql.cursors.Cursor) as cursor:
            cursor.execute('show databases')
            return [db[0] for db in cursor]

    def get_reference(self, column, value):
        with self.c.cursor() as cursor:
            cursor.execute('''
SELECT table_name, column_name, referenced_table_name, referenced_column_name
FROM information_schema.KEY_COLUMN_USAGE
WHERE constraint_schema = %s
AND referenced_column_name is not null
AND table_name = %s
AND column_name = %s
            ''', (self.current_db, self.current_table, column))
            for row in cursor:
                return self.text_update('select * from `'+row['referenced_table_name']+'` where `'+row['referenced_column_name']+'` = %s', (
                    value
                ))
            return None

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
    p = argparse.ArgumentParser()
    p.add_argument('--host')
    p.add_argument('--user', '-u')
    p.add_argument('--password', '-p')
    p.add_argument('--port', '-P', type=int, default=3306)
    args = p.parse_args()
    c = pymysql.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        port=args.port,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        app = QApplication(sys.argv)
        try:
            app.setStyle('crap')
        except Exception as err:
            print(err)
            pass
        # qtmodern.styles.dark(app)
        widget = UI(Controller(c))
        widget.show()
        sys.exit(app.exec_())
    finally:
        c.close()


if __name__ == "__main__":
    dibi()
