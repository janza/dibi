import re
import subprocess
from os import path
from typing import List, Dict, Iterator, Optional, Tuple, Union, Any
from collections import deque
import json

import sqlparse
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import QtCore
import MySQLdb
import MySQLdb.cursors
import MySQLdb.connections
import sshtunnel

from dibi.configuration import ConnectionInfo


sshtunnel.SSH_TIMEOUT = 10


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

    def __init__(self):
        self.variables = {}

    def handle_placeholders(self, query: str):
        q, = sqlparse.parse(query)
        b = [i for i in q if not i.is_whitespace]
        if len(b) > 2 and b[1].value == ':=':
            self.variables[b[0].value] = self._token_str(b[2:])
            b = b[2:]

        placeholders = self._get_placeholders(b)

        if not placeholders:
            yield None, self._token_str(b)
            return

        cache: Dict[str, List[Any]] = {}

        for placeholder in placeholders:
            if placeholder not in cache and placeholder in self.variables:
                def put_result(results: List[Any]):
                    cache[placeholder] = results
                yield put_result, self.variables[placeholder]

        for key, values in cache.items():
            for value in values:
                yield None, ' '.join(
                    str(self._replace_placeholder(i, key, value))
                    for i in b)

    def _token_str(self, statements: List[sqlparse.sql.Statement]) -> str:
        return ' '.join(str(t) for t in statements)

    def _get_placeholders(self, statements: List[sqlparse.sql.Statement]):
        r = []
        for s in statements:
            if str(s.ttype) == 'Token.Name.Placeholder' and s.value[1:] in self.variables.keys():
                r.append(s.value[1:])
        return r

    def _replace_placeholder(self, statement: sqlparse.sql.Statement, name: str, value: Any):
        if str(statement.ttype) == 'Token.Name.Placeholder' and statement.value[1:] == name:
            return value
        return str(statement)


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
    ready_to_connect = pyqtSignal()

    connection: Optional[ConnectionInfo] = None
    tunnel_server: Optional[sshtunnel.SSHTunnelForwarder]
    c: Optional[MySQLdb.connections.Connection]

    job = pyqtSignal(
        [str, str, str, dict],
        [str, str, int, dict],
    )

    def __init__(self):
        super().__init__()
        self.queue: deque = deque([])
        self.table_cache: Dict[str, List[str]] = {}
        self.c = None
        self.is_ready = False
        self.tunnel_server = None
        self.variables: Dict[str, List[Tuple]] = {}
        self.sql_parser = SQLParser()
        self.destroyed.connect(self.disconnect)

    @pyqtSlot(str, str, int, dict)
    @pyqtSlot(str, str, str, dict)
    def enqueue(self, request_type, param_a, param_b=None, more=None):
        try:
            self.process(request_type, param_a, param_b, more)
        except Exception as err:
            self.error.emit(str(err))

    def longRunning(self) -> None:
        self.make_ready()

    def make_ready(self):
        if self.is_ready:
            return
        self.job.connect(self.enqueue)
        self.is_ready = True
        self.ready_to_connect.emit()

    def connect_to_info(self, connection: ConnectionInfo):
        self.running_query.emit(True)
        self.disconnect()
        self.info.emit(str(f'Connecting to: {connection}...'))
        if connection.ssh_host and connection.ssh_user:
            self.tunnel_server = sshtunnel.SSHTunnelForwarder(
                (connection.ssh_host, connection.ssh_port),
                ssh_username=connection.ssh_user,
                ssh_pkey=path.expanduser('~/.ssh/id_rsa'),
                remote_bind_address=(connection.host, connection.port))
            try:
                self.tunnel_server.start()
            except Exception as err:
                self.error.emit(str(err))
                return

        try:
            self.c = MySQLdb.connect(
                host=connection.host if self.tunnel_server is None else '127.0.0.1',
                user=connection.user,
                password=connection.get_password(),
                port=connection.port if self.tunnel_server is None else self.tunnel_server.local_bind_port,
                cursorclass=MySQLdb.cursors.DictCursor
            )
        except Exception as err:
            self.error.emit(str(err))
            return
        self.connection = connection
        self.info.emit(str(f'Connected to: {connection}.'))
        self.running_query.emit(False)
        self.job.emit('db_list', '', '', {})
        self.run_query('SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')

    def disconnect(self):
        print('Disconnecting', self.connection)
        print(self.c)
        if self.c is not None:
            print('Closing db connection')
            self.c.close()
            print('Closed db connection')

        if self.tunnel_server is not None:
            print('Closing tunnel')
            self.tunnel_server.stop()
            print('Closed tunnel')

        print('Disconnected')

    def process(self, request_type: str, params: str, extra, more) -> None:
        if request_type == 'disconnect':
            self.disconnect()
            self.exit()

        elif request_type == 'connect':
            self.connect_to_info(ConnectionInfo(**more))

        elif self.c is None:
            self.error.emit('No active connection')

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

        elif request_type == 'get_reference':
            self.get_reference(column=params, value=extra)

        elif request_type == 'commit':
            self.c.commit()

        elif request_type == 'rollback':
            self.c.rollback()

        elif request_type == 'update':
            self.update_record(record=more, column_name=params, value=json.loads(extra))

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
        # queries = queries.split('-- ')[0]
        for query in sqlparse.split(queries):
            if query[-1] == ';':
                query = query[:-1]
            if not query.strip():
                continue
            query = self._prepare_query(query)
            if not query:
                continue

            yield query

    def send_results(self, text, params=None):
        columns: Tuple = tuple()
        query_result: List[Tuple] = list()
        for query in self._split_queries(text):
            for put_result, query in self.sql_parser.handle_placeholders(str(query)):
                c = iter(self.run_query(query, params))
                if put_result is not None:
                    put_result([next(iter(r.values())) for r in c if r])
                    continue

                try:
                    first_row = next(c)
                except StopIteration:
                    self.query_result.emit([])
                    return
                returned_columns = tuple(first_row.keys())

                pad: Tuple = tuple()
                if columns != returned_columns:
                    pad = len(columns) * (None,)
                    columns += returned_columns

                first_row_values = tuple(first_row.values())
                rest_values = [tuple(r.values()) for r in c]
                results = ([pad + first_row_values] +
                           [pad + r for r in rest_values])

                query_result += results

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
        return [
            db['Database']
            for db in self.run_query('show databases')
            if db['Database'] not in ('information_schema', 'mysql', 'performance_schema')
        ]

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

    def run_query(self, query: str, params=None):

        if self.c is None:
            self.error.emit('No connection')
            return

        with self.c.cursor() as cursor:
            self.running_query.emit(True)
            self.execute.emit(query, params or ())
            cursor.execute(query, params)
            self.running_query.emit(False)

            return cursor
