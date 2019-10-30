#!/usr/bin/env python3

import sys
import signal
import re
import argparse

import MySQLdb
import MySQLdb.cursors
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

    def prepare_query(self, query):
        if query[:3].lower() == 'use':
            self.current_db = self.get_db_from_use(query)
        elif query[:6].lower() == 'select':
            query += ' LIMIT 100'
            db, table = self.get_table_from_query(query)
            if db:
                self.current_db = db
            if table:
                self.current_table = table
        return query

    def update_record(self, record, column_name, value):
        if not self.current_table:
            return None
        with self.c.cursor() as cursor:
            cursor.execute('show index from `{}` where non_unique = false or key_name="primary"'.format(self.current_table))

            rows = cursor.fetchall()
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
            if column_name in index:
                raise Exception('Can\'t update index column')
            query = 'update `{}` set `{}` = %s where {}'.format(
                self.current_table, column_name, ' AND '.join([
                    '{} = %s'.format(i) for i in index
                ]))
            params = (value,) + tuple([record[i] for i in index])
            cursor.execute(query, params)
            return query % params

    def commit(self):
        self.c.commit()

    def rollback(self):
        self.c.rollback()

    def split_queries(self, queries):
        for query in queries.split(';'):
            if query.strip():
                yield self.prepare_query(query)

    def text_update(self, text, params=None):
        with self.c.cursor() as cursor:
            for query in self.split_queries(text):
                if query.strip():
                    cursor.execute(query, params)
            return cursor

    def get_db_list(self):
        with self.c.cursor(MySQLdb.cursors.Cursor) as cursor:
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
            try:
                row = cursor.fetchone()
            except Exception as err:
                print('Error finding reference', err)
                return None
            if row is None:
                return None
            query = self.prepare_query('select * from `'+row['referenced_table_name']+'` where `'+row['referenced_column_name']+'` = %s')
            cursor.execute(query, (value, ))
            return cursor

    def get_table_list(self, db):
        try:
            return self.table_cache[db]
        except Exception:
            pass

        with self.c.cursor(MySQLdb.cursors.Cursor) as cursor:
            if db is None:
                cursor.execute('show tables')
            else:
                cursor.execute('show tables in `{}`'.format(db))
            tables = [table[0] for table in cursor]
            if db is not None:
                self.table_cache[db] = tables
            return tables


def dibi():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    p = argparse.ArgumentParser()
    p.add_argument('--host', required=True)
    p.add_argument('--user', '-u', required=True)
    p.add_argument('--password', '-p', required=True)
    p.add_argument('--port', '-P', type=int, default=3306)
    args = p.parse_args()
    c = MySQLdb.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        port=args.port,
        cursorclass=MySQLdb.cursors.DictCursor
    )

    app = QApplication(sys.argv)
    widget = UI(Controller(c))
    widget.show()
    return_code = app.exec_()
    c.close()
    sys.exit(return_code)


if __name__ == "__main__":
    dibi()
