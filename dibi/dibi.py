#!/usr/bin/env python3

import sys
import signal
import re
import argparse

import MySQLdb
import MySQLdb.cursors
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui
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

    def columns(self, table):
        with self.c.cursor() as cursor:
            if not self.current_db:
                return None
            cursor.execute('show columns in `{}`'.format(table))
            return cursor

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
    font-family: Cabin;
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

QPushButton, QLineEdit {
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
padding: 6px 7px;
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
    padding: 0 10px;
    text-align: center;
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
    widget = UI(Controller(c))
    # widget.show()

    window = QMainWindow()
    window.layout().setSpacing(0)
    window.setCentralWidget(widget)
    # window.layout().addWidget(widget)
    window.show()
    return_code = app.exec_()
    c.close()
    sys.exit(return_code)


if __name__ == "__main__":
    dibi()
