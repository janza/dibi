#!/usr/bin/env python3

import sys
import signal
import re
import argparse

import MySQLdb
import MySQLdb.cursors
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from dibi.ui import UI

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


class DbThread(QThread):
    db_list_updated = pyqtSignal(list)
    table_list_updated = pyqtSignal(list)
    error = pyqtSignal(str)
    query_result = pyqtSignal(list)
    execute = pyqtSignal(str, tuple)
    use_db = pyqtSignal(str)

    job = pyqtSignal(
        [str, str, str, dict],
        [str, str, int, dict],
    )

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.queue = deque([])
        self.table_cache = {}

    def __del__(self):
        self.wait()

    @pyqtSlot(str, str, int, dict)
    @pyqtSlot(str, str, str, dict)
    def enqueue(self, request_type, param_a, param_b=None, more=None):
        try:
            self.process(request_type, param_a, param_b, more)
        except Exception as err:
            self.error.emit(str(err))

    def run(self):
        self.job.connect(self.enqueue)
        self.c = MySQLdb.connect(
            host=self.args.host,
            user=self.args.user,
            password=self.args.password,
            port=self.args.port,
            cursorclass=MySQLdb.cursors.DictCursor
        )

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
                '{} = %s'.format(i) for i in index
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

    def run_query(self, text, params=None):
        with self.c.cursor() as cursor:
            for query in self._split_queries(text):
                if query.strip():
                    self.execute.emit(query, params or ())
                    cursor.execute(query, params)
            return cursor

    def get_db_list(self):
        with self.c.cursor(MySQLdb.cursors.Cursor) as cursor:
            cursor.execute('show databases')
            return [db[0] for db in cursor]

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
            return None

        self.send_results(
            'select * from `{}` where `{}` = %s'
            .format(
                row['referenced_table_name'], row['referenced_column_name']
            ), (value, ))


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
    for font in [
            './static/Cabin/Cabin-Bold.ttf',
            './static/Cabin/Cabin-Medium.ttf',
            './static/Cabin/Cabin-Regular.ttf',
    ]:
        QtGui.QFontDatabase.addApplicationFont(font)


    app.setStyleSheet('''
QMainWindow {
    padding: 0;
    margin: 0;
}

QScrollBar:vertical {
background: #E3E8EB;
border: none;
width: 10px;
margin: 0;
}

QScrollBar::handle:vertical {
background: #C3CED9;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
background: none;
}

QScrollBar::sub-line:vertical,
QScrollBar::add-line:vertical {
height: 0;
background: none;
}


QWidget {
    color: #131C26;
    font-family: Cabin, Overpass, Sans;
    font-weight: 500;
    background: #f5f5f5;
    font-size: 14px;
    padding: 0;
    margin: 0;
    border-width: 0;
    border-style: solid;
    border-color: #f00;
}

#top {
    background: #C3CED9;
    border-bottom: 1px solid #8FA1B3;
}

QTextEdit {
    background: transparent;
}

QPushButton, QLineEdit, QLabel {
font-size: 14px;
line-height: 14px;
    color: #131C26;
    padding: 7px 15px;
 background-color: rgba(255,255,255,50%);
border-style: solid;
border-color: #62778C;
border-width: 1px;
}

QPushButton {
    font-weight: bold;
    text-transform: uppercase;
}

QPushButton:hover {

color: #fff;
 background-color: #62778C;
}

#commit-btn {
border-right-width: 0px;
border-left-width: 0px;
}

#rollback-btn {
border-left-width: 0px;
border-top-right-radius: 3px;
border-bottom-right-radius: 3px;
}

QLineEdit {
 border-right-width: 0;
 border-left-width: 0;
padding: 6px 7px;
}

QLabel {
 border-right-width: 0;
 padding: 6px 5px;
    color: #E3E8EB;
    background: #2B506B;
border-top-left-radius: 3px;
border-bottom-left-radius: 3px;
}

QListView {
    selection-background-color: transparent;
    show-decoration-selected: 0;
    selection-color: transparent;
    outline: 0;
    padding: 7px 0;
    border: none;
    font-weight: normal;
    color: #E3E8EB;
    background: #2B506B;
}

#sidebar {
    color: #E3E8EB;
    background: #2B506B;
}

#database_label {
    font-weight: bold;
}

#table_list {
    show-decoration-selected: 0;
    background: #E3E8EB;
    color: #2B506B;
    border-right: 1px solid #8FA1B3;
}

QListView::item {
    padding: 0px 5px;
    margin-bottom: 1px;
    border: 0px;
    width: auto;
}

#table_list::item {
    margin-right: 10px;
}

#db_list::item {
    margin-right: 0;
}

#db_list::item:hover:!selected {
    background: #3D5F78;
}

#db_list::item:selected,
#db_list::item:selected:active
#db_list::item:selected:!active {
    background: #E3E8EB;
    color: #2B506B;
}

#table_list::item:selected,
#table_list::item:selected:active
#table_list::item:selected:!active {
    color: #E3E8EB;
    background: #2B506B;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

#table_list::item:hover:!selected {
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    background: #BECAD1;
    font-weight: bold;
    text-transform: uppercase;
}

QTableWidget {
    background: #fff;
    color: #131C26;
}

QTableWidget QTableCornerButton::section,
QTableWidget QHeaderView,
QTableWidget QHeaderView::section
{
    color: #131C26;
    background: #fff;
}

QTableWidget QHeaderView {
    font-weight: bold;
    text-transform: uppercase;
}

QTableWidget QHeaderView::section {
    border: none;
    text-align: center;
    padding: 0 5px;
}


QTableWidget QHeaderView::item {
    color: #131C26;
    font-weight: bold;
    padding-left: 3px;
    text-align: right;
    border-top: 1px solid #ddd;
}

QTableWidget::item {
    border-left-width: 0px;
    border-right-width: 0px;
    background: #fff;
}

QTableWidget::item:alternate {
    background: #f5f5f5;
}

QTableWidget::item:hover {
    background: #E3E8EB;
}

QTableWidget::item:first {
    border-top: 1px solid #000;
}

QTableWidget::item:selected:!active {
    color: #fff;
    background-color: #1B4060;
}

QTableWidget::item:focus {
    color: #1B4060;
    background-color: #fff;
    border: none;
}

QTableWidget::item:active {
    color: #1B4060;
    background-color: #fff;
    border: none;
}

QTableWidget::item:selected:active {
    color: #fff;
    background-color: #1B4060;
}

QTableWidget::item:selected {
    color: #fff;
    background-color: #1B4060;
}

''')
    t = DbThread(args)
    t.start()
    widget = UI(t)

    window = QMainWindow()
    window.layout().setSpacing(0)
    window.setCentralWidget(widget)
    window.show()
    return_code = app.exec_()
    c.close()
    sys.exit(return_code)


if __name__ == "__main__":
    dibi()
