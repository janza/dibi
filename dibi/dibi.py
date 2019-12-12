#!/usr/bin/env python3
import configparser
import sys
import signal
import re
import argparse
from os import path

import MySQLdb
import MySQLdb.cursors
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

from dibi.ui import UI
from dibi.configuration import ConfigurationParser

myloginpath_supported = False
try:
    import myloginpath
    myloginpath_supported = True
except:
    pass


from collections import deque


class SQLParser():
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


class DbThread(QtCore.QObject):
    db_list_updated = pyqtSignal(list)
    table_list_updated = pyqtSignal(list)
    error = pyqtSignal(str)
    query_result = pyqtSignal(list)
    execute = pyqtSignal(str, tuple)
    use_db = pyqtSignal(str)
    running_query = pyqtSignal(bool)

    job = pyqtSignal(
        [str, str, str, dict],
        [str, str, int, dict],
    )

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.queue = deque([])
        self.table_cache = {}
        self.c = None

    @pyqtSlot(str, str, int, dict)
    @pyqtSlot(str, str, str, dict)
    def enqueue(self, request_type, param_a, param_b=None, more=None):
        while self.c is None:
            self.sleep(1)
        try:
            self.process(request_type, param_a, param_b, more)
        except Exception as err:
            self.error.emit(str(err))

    def longRunning(self):
        self.running_query.emit(True)
        self.c = MySQLdb.connect(
            host=self.args.host,
            user=self.args.user,
            password=self.args.password,
            port=self.args.port,
            cursorclass=MySQLdb.cursors.DictCursor
        )
        self.running_query.emit(False)
        self.job.connect(self.enqueue)
        self.job.emit('db_list', '', '', {})

    def process(self, request_type, params, extra, more):
        if request_type == 'query':
            self.send_results(params)

        elif request_type == 'table_contents':
            self.send_results('show columns in `{}`'.format(params))

        elif request_type == 'table_list':
            self._get_table_list(params)

        elif request_type == 'table_data':
            self.send_results('select * from `{}`'.format(params))

        elif request_type == 'db_list':
            self.db_list_updated.emit(self.get_db_list())

        elif request_type == 'get_reference':
            self.get_reference(column=params, value=extra)

        elif request_type == 'commit':
            self.c.commit()

        elif request_type == 'rollback':
            self.c.rollback()

        elif request_type == 'update':
            self.update_record(record=more, column_name=params, value=extra)

        else:
            print('unknown request_type', request_type)

    def update_record(self, record, column_name, value):
        if not self.current_table:
            raise RuntimeError('No table selected to update {}'.format(column_name))

        rows = self.run_query('show index from `{}` where non_unique = false or key_name="primary"'.format(self.current_table))

        index = []
        for row in rows:
            if row['Key_name'].lower() == 'primary':
                index.append(row['Column_name'])

        if not index:
            name = None
            for row in rows:
                if name is None:
                    name = row['Key_name']
                if row['Key_name'].lower() == name:
                    index.append(row['Column_name'])

        if not index:
            raise RuntimeError('Could not find unique index to update {}'.format(column_name))

        query = 'update `{}` set `{}` = %s where {}'.format(
            self.current_table, column_name, ' AND '.join([
                '`{}` = %s'.format(i) for i in index
            ]))
        params = (value,) + tuple([record[i] for i in index])
        self.run_query(query, params)

    def _get_table_list(self, db):
        self.run_query('use `{}`'.format(db))
        self.current_db = db
        self.use_db.emit(db)
        try:
            self.table_list_updated.emit(self.table_cache[db])
            return
        except KeyError:
            pass

        tables = [list(row.values())[0]
                  for row in self.run_query('show tables')]
        self.table_cache[db] = tables
        self.table_list_updated.emit(tables)

    def _prepare_query(self, query):
        if query[:3].lower() == 'use':
            self.current_db = SQLParser.get_db_from_use(query)
            self.use_db.emit(self.current_db)

        elif query[:6].lower() == 'select':
            query += ' LIMIT 100'
            db, table = SQLParser.get_table_from_query(query)
            if db:
                self.current_db = db
            if table:
                self.current_table = table

        return query

    def _split_queries(self, queries):
        for query in queries.split(';'):
            if query.strip():
                yield self._prepare_query(query)

    def send_results(self, text, params=None):
        c = iter(self.run_query(text, params))
        try:
            first_row = next(c)
        except StopIteration:
            self.query_result.emit([])
            return
        columns = tuple(first_row.keys())
        self.query_result.emit(
            [columns, tuple(first_row.values())] +
            [tuple(r.values()) for r in c])

    def get_db_list(self):
        return [db['Database'] for db in self.run_query('show databases')]

    def get_reference(self, column, value):
        c = self.run_query(
            '''
SELECT table_name, column_name, referenced_table_name, referenced_column_name
FROM information_schema.KEY_COLUMN_USAGE
WHERE constraint_schema = %s
AND referenced_column_name is not null
AND table_name = %s
AND column_name = %s''',
            (self.current_db, self.current_table, column))
        try:
            row = next(iter(c))
        except StopIteration:
            raise RuntimeError('Error finding reference')

        if row is None:
            raise RuntimeError('Error finding reference')

        self.send_results(
            'select * from `{}` where `{}` = %s'
            .format(
                row['referenced_table_name'], row['referenced_column_name']
            ), (value, ))

    def run_query(self, text, params=None):
        with self.c.cursor() as cursor:
            for query in self._split_queries(text):
                if not query.strip():
                    continue

                self.running_query.emit(True)
                self.execute.emit(query, params or ())
                cursor.execute(query, params)
                self.running_query.emit(False)

            return cursor


def load_from_login_path():
    p = argparse.ArgumentParser()
    p.add_argument('--login-path')
    args = p.parse_args()
    if not args.login_path:
        return True, {}

    try:
        return False, myloginpath.parse(args.login_path)
    except configparser.NoSectionError:
        print('Invalid --login-path')
        return False, {}


def dibi():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    conf = {}
    connection_required = True
    if myloginpath_supported:
        connection_required, conf = load_from_login_path()

    if not conf:
        config = ConfigurationParser(path.expanduser('~/.dibi.ini'))
        if config.config:
            conf = config.config
            connection_required = False

    p = argparse.ArgumentParser()
    p.add_argument('--host', required=connection_required)
    p.add_argument('--user', '-u', required=connection_required)
    p.add_argument('--password', '-p', required=connection_required)
    p.add_argument('--port', '-P', type=int, default=3306)
    p.set_defaults(**conf)
    args = p.parse_args()

    def expand(filename):
        return path.join(path.dirname(__file__), filename)

    app = QApplication(sys.argv)
    for font in [
            expand('fonts/Cabin-Bold.ttf'),
            expand('fonts/Cabin-Medium.ttf'),
            expand('fonts/Cabin-Regular.ttf'),
    ]:
        QtGui.QFontDatabase.addApplicationFont(font)

    t = DbThread(args)
    widget = UI(t)

    window = QMainWindow()
    window.layout().setSpacing(0)
    window.setCentralWidget(widget)
    window.show()
    app.setStyleSheet(open(expand('styles.qss')).read())
    return_code = app.exec_()
    sys.exit(return_code)


if __name__ == "__main__":
    dibi()
