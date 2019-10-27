from typing import Dict
from os.path import commonprefix

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QWidget, QLineEdit, QLabel, QListView, QMainWindow
from PyQt5.QtCore import pyqtSlot, Qt, QAbstractListModel, QVariant, QObject, QEvent, QMargins


class ListViewModel(QAbstractListModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, ok):
        return len(self._data)

    def flags(self, QModelIndex):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def get(self, index):
        return self._data[index.row()]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()]
        elif role == Qt.EditRole:
            return self._data[index.row()]
        return QVariant()


class UI(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.layout = QVBoxLayout()

        self.log_text = QLabel('Initalized' + ('\n' * 4))
        self.log_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.textbox = QLineEdit()
        self.textbox.installEventFilter(self)
        self.textbox.returnPressed.connect(self.on_enter)

        self.layout = QVBoxLayout()
        self.bottom = QWidget()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.bottom.setLayout(self.bottom_layout)

        self.table = Table()

        self.db_list = ListViewModel(controller.get_db_list())
        try:
            self.table_list = ListViewModel(controller.get_table_list())
        except Exception:
            self.table_list = ListViewModel([])

        self.list = QListView()
        self.list.setModel(self.db_list)
        self.list.setMaximumWidth(200)
        self.list.doubleClicked.connect(self.on_list_dbl_click)

        self.tablelist = QListView()
        self.tablelist.setModel(self.table_list)
        self.tablelist.setMaximumWidth(200)
        self.tablelist.doubleClicked.connect(self.on_tablename_dbl_click)

        self.bottom_layout.addWidget(self.list)
        self.bottom_layout.addWidget(self.tablelist)
        self.bottom_layout.addWidget(self.table)

        self.layout.addWidget(self.log_text)
        self.layout.addWidget(self.textbox)
        self.layout.addWidget(self.bottom)
        self.setLayout(self.layout)

        self.history_cursor = 0
        self.history = []

    def append_to_status(self, text):
        lines = self.log_text.text().split('\n')
        lines.append(text)
        self.log_text.setText('\n'.join(lines[-5:]))

    def prev_command(self):
        self.history_cursor -= 1
        hl = len(self.history)
        if hl > 0:
            self.textbox.setText(self.history[self.history_cursor % hl])

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.autocomplete()
                return True
            if event.key() == Qt.Key_Up:
                self.prev_command()
                return True
            if event.key() == Qt.Key_Down:
                self.prev_command()
                return True
        return QMainWindow.eventFilter(self, source, event)

    SQL = [
        'USE',
        'SELECT',
        'FROM',
        'IN',
        'WHERE',
        'GROUP',
        'BY',
        'INSERT',
        'UPDATE',
        'TABLE',
        'VALUES',
    ]

    def autocomplete(self):
        pos = self.textbox.cursorPosition()
        text = self.textbox.text()
        before_cursor, after_cursor = text[:pos], text[pos:]
        words = before_cursor.split(' ')
        word = words.pop().lower()
        wl = len(word)
        candidates = [s + ' ' for s in self.SQL] + [db + '.' for db in self.db_list._data]
        if '.' in word:
            db_name = word.split('.')[0]
            try:
                tables = self.get_table_list(db_name)
            except Exception as err:
                print(err)
                tables = self.table_list._data
            print(tables)
            candidates += [db_name + '.' + table + ' ' for table in tables]
        else:
            candidates += [table + ' ' for table in self.table_list._data]

        matches = [w for w in candidates if w[:wl % len(w)].lower() == word]
        if len(matches) == 0:
            return

        match = matches[0]
        if len(matches) != 1:
            match = commonprefix([m.lower() for m in matches])

        words.append(match)
        before_cursor = ' '.join(words)
        self.textbox.setText(before_cursor + after_cursor)
        self.textbox.setCursorPosition(len(before_cursor))

    @pyqtSlot()
    def on_list_dbl_click(self):
        selection = self.list.selectedIndexes()[0]
        try:
            db = self.db_list.get(selection)
            self.controller.text_update(
                'use `{}`'.format(db))
        except Exception as err:
            self.append_to_status(str(err))
        self.get_table_list(db)

    def get_table_list(self, db):
        try:
            tables = self.controller.get_table_list(db)
            self.table_list = ListViewModel(tables)
            self.tablelist.setModel(self.table_list)
            return tables
        except Exception as err:
            self.append_to_status(str(err))

    @pyqtSlot()
    def on_tablename_dbl_click(self):
        print('ok')
        selection = self.tablelist.selectedIndexes()[0]
        try:
            selected_table = self.table_list.get(selection)
            print(selected_table)
            self.set_data(self.controller.text_update(
                'select * from `{}`'.format(selected_table)))
        except Exception as err:
            self.append_to_status(str(err))

    @pyqtSlot()
    def on_enter(self):
        text = self.textbox.text()
        self.history.append(text)
        self.history_cursor = 0
        self.append_to_status(text)
        try:
            self.set_data(self.controller.text_update(text))
        except Exception as err:
            self.append_to_status(str(err))
        self.textbox.setText('')

    def set_data(self, data):
        self.table.set_data(data)


class TableItem(QTableWidgetItem):
    def __init__(self, column_name, record):
        super().__init__(str(record[column_name]))
        self.column_name = column_name
        self.record = record

    def text(self):
        return self.record[self.column_name]


class Table(QTableWidget):
    def __init__(self):
        super().__init__()
        self.doubleClicked.connect(self.on_click)

    def set_data(self, data: Dict[str, Dict]):
        if type(data) != list:
            row_count = data.rowcount
        else:
            row_count = len(data)

        if row_count == 0:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        self.setRowCount(row_count)

        for row, item in enumerate(data):
            column_names = item.keys()
            col_count = len(column_names)
            self.setColumnCount(col_count)
            self.setHorizontalHeaderLabels(column_names)
            for col, (column_name, val) in enumerate(item.items()):
                self.setItem(row, col, TableItem(column_name, item))

        self.resizeColumnsToContents()

    @pyqtSlot()
    def on_click(self):
        print("\n")
        for item in self.selectedItems():
            print(item.row(), item.column(), item.record)
