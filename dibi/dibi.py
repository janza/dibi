#!/usr/bin/env python3
import configparser
import sys
import signal
import re
import argparse
import subprocess
from os import path
from typing import List, Dict, Iterator, Optional, Tuple, Union
from collections import deque

from sshtunnel import SSHTunnelForwarder
import MySQLdb
import MySQLdb.cursors
import MySQLdb.connections
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from dibi.ui import UI
from dibi.configuration import ConfigurationParser, ConnectionInfo

myloginpath_supported = False
try:
    import myloginpath
    myloginpath_supported = True
except Exception:
    pass


class SQLParser():
    @staticmethod
    def get_table_from_query(query: str) -> Union[Tuple[str, str], Tuple[None, None]]:
        m = re.search(
            r'from\s+`?([a-z0-9_]+)`?\.?`?([a-z0-9_]+)?`?', query, re.IGNORECASE)

        if m:
            db, table = m.groups()
            if table is None:
                return None, db
            return db, table
        return None, None

    @staticmethod
    def get_db_from_use(query: str) -> Optional[str]:
        m = re.search(r'use\s+`?([a-z0-9_]+)', query, re.IGNORECASE)
        if not m:
            return None
        return m.groups()[0]

    @staticmethod
    def get_shell_cmd_for_pipe(query: str) -> str:
        return '-- !'.join(query.split('-- !')[1:])


class DbThread(QtCore.QObject):
    db_list_updated = pyqtSignal(list, str)
    table_list_updated = pyqtSignal(list)
    error = pyqtSignal(str)
    info = pyqtSignal(str)
    query_result = pyqtSignal(list)
    execute = pyqtSignal(str, tuple)
    use_db = pyqtSignal(str)
    running_query = pyqtSignal(bool)
    running_query = pyqtSignal(bool)

    connections: List[ConnectionInfo] = []
    connection: Optional[ConnectionInfo] = None
    tunnel_server: Optional[SSHTunnelForwarder]
    c: Optional[MySQLdb.connections.Connection]

    job = pyqtSignal(
        [str, str, str, dict],
        [str, str, int, dict],
    )

    def __init__(self, connections: List[ConnectionInfo]):
        super().__init__()
        if not connections:
            raise TypeError('Need at least one connection')
        self.connections = connections
        self.queue: deque = deque([])
        self.table_cache: Dict[str, List[str]] = {}
        self.c = None
        self.is_ready = False
        self.tunnel_server = None

    @pyqtSlot(str, str, int, dict)
    @pyqtSlot(str, str, str, dict)
    def enqueue(self, request_type, param_a, param_b=None, more=None):
        while self.c is None:
            self.sleep(1)

        try:
            self.process(request_type, param_a, param_b, more)
        except Exception as err:
            self.error.emit(str(err))

    def longRunning(self) -> None:
        self.connect_to(0)

    def make_ready(self):
        if self.is_ready:
            return
        self.job.connect(self.enqueue)
        self.is_ready = True

    def connect_to(self, connection_id: int):
        connection = self.connections[connection_id]
        self.running_query.emit(True)
        self.disconnect()
        self.info.emit(str(f'Connecting to: {connection}...'))
        tunnel = None
        if connection.ssh_host and connection.ssh_user:
            tunnel = SSHTunnelForwarder(
                (connection.ssh_host, connection.ssh_port),
                ssh_username=connection.ssh_user,
                remote_bind_address=(connection.host, connection.port))
            tunnel.start()

        self.c = MySQLdb.connect(
            host=connection.host if tunnel is None else '127.0.0.1',
            user=connection.user,
            password=connection.password,
            port=connection.port if tunnel is None else tunnel.local_bind_port,
            cursorclass=MySQLdb.cursors.DictCursor
        )
        self.connection = connection
        self.tunnel_server = tunnel
        self.info.emit(str(f'Connected to: {connection}.'))
        self.running_query.emit(False)
        self.make_ready()
        self.job.emit('db_list', '', '', {})

    def disconnect(self):
        if self.c is not None:
            self.c.close()

        if self.tunnel_server is not None:
            self.tunnel_server.stop()

    def process(self, request_type: str, params: str, extra, more) -> None:
        if request_type == 'disconnect':
            self.disconnect()
            self.exit()

        if request_type == 'change_connection':
            self.connect_to(int(params))

        elif request_type == 'query':
            self.send_results(params)

        elif request_type == 'table_contents':
            self.send_results('show columns in `{}`'.format(params))

        elif request_type == 'table_list':
            self._get_table_list(params)

        elif request_type == 'table_data':
            self.send_results('select * from `{}`'.format(params))

        elif request_type == 'db_list':
            if self.connection is None:
                return
            self.db_list_updated.emit(self.get_db_list(), self.connection.label)

        # elif request_type == 'new_connection':
        #     self.new_connection()

        elif request_type == 'get_reference':
            self.get_reference(column=params, value=extra)

        elif request_type == 'commit':
            if self.c is not None:
                self.c.commit()
            else:
                self.error.emit('No connection')

        elif request_type == 'rollback':
            if self.c is not None:
                self.c.rollback()
            else:
                self.error.emit('No connection')

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

    def _split_queries(self, queries: str) -> Iterator[str]:
        queries = queries.split('-- ')[0]
        for query in queries.split(';'):
            if not query.strip():
                continue
            query = self._prepare_query(query)
            if not query:
                continue

            yield query

    def send_results(self, text, params=None):
        c = iter(self.run_query(text, params))
        try:
            first_row = next(c)
        except StopIteration:
            self.query_result.emit([])
            return
        columns = tuple(first_row.keys())
        query_result = ([tuple(first_row.values())] +
                        [tuple(r.values()) for r in c])

        cmd_to_pipe = SQLParser.get_shell_cmd_for_pipe(text)
        if cmd_to_pipe:
            self.info.emit(
                subprocess.check_output(
                    cmd_to_pipe,
                    shell=True,
                    text=True,
                    input='\n'.join([','.join([str(c) for c in r]) for r in query_result])
                )
            )

        self.query_result.emit([columns] + query_result)

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

    def run_query(self, text: str, params=None):

        if self.c is None:
            self.error.emit('No connection')
            return

        with self.c.cursor() as cursor:
            for query in self._split_queries(text):
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

    config = ConfigurationParser(path.expanduser('~/.dibi.ini'))
    connections = config.connections

    connection_required = not bool(connections)

    p = argparse.ArgumentParser()
    p.add_argument('--host', required=connection_required)
    p.add_argument('--user', '-u', required=connection_required)
    p.add_argument('--password', '-p', required=connection_required)
    p.add_argument('--port', '-P', type=int, default=3306)
    p.set_defaults(**conf)
    args = p.parse_args()

    if args.host is not None:
        connections = [ConnectionInfo(**vars(args))] + connections

    def expand(filename: str) -> str:
        return path.join(path.dirname(__file__), filename)

    app = QApplication(sys.argv)
    for font in [
            expand('fonts/Cabin-Bold.ttf'),
            expand('fonts/Cabin-Medium.ttf'),
            expand('fonts/Cabin-Regular.ttf'),
    ]:
        QtGui.QFontDatabase.addApplicationFont(font)

    t = DbThread(connections)
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
