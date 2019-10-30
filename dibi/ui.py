from typing import Dict
from os.path import commonprefix

from PyQt5.QtWidgets import QTableWidget,\
    QTableWidgetItem,\
    QHBoxLayout,\
    QVBoxLayout,\
    QWidget,\
    QLineEdit,\
    QLabel,\
    QListView,\
    QMainWindow,\
    QItemDelegate,\
    QPushButton
from PyQt5.QtCore import pyqtSlot, Qt, QAbstractListModel, QVariant, QEvent, QMargins, QSize
import PyQt5.QtGui


class ListViewModel(QAbstractListModel):
    def __init__(self, data, parent):
        super().__init__(parent=parent)
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


class ItemDelegate(QItemDelegate):
    def sizeHint(self, yes, no):
        return QSize(0, 26)


class UI(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setObjectName('mainbox')

        self.setStyleSheet('font-family: monospace;')

        self.log_text = QLabel('Initalized' + ('\n' * 4))
        self.log_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.textbox = QLineEdit(parent=self)
        self.textbox.installEventFilter(self)
        self.textbox.returnPressed.connect(self.on_enter)

        self.layout = QVBoxLayout()
        text_and_button = QHBoxLayout()
        commit = QPushButton("Commit")
        commit.clicked.connect(self.on_commit_click)
        rollback = QPushButton("Rollback")
        rollback.clicked.connect(self.on_rollback_click)
        self.bottom = QWidget(parent=self)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.bottom.setLayout(self.bottom_layout)

        self.table = Table(self.controller, parent=self)

        self.db_list = ListViewModel(controller.get_db_list(), parent=self)
        try:
            self.table_list = ListViewModel(controller.get_table_list(), parent=self)
        except Exception:
            self.table_list = ListViewModel([], parent=self)

        self.list = QListView(parent=self)
        self.list.setAlternatingRowColors(True)
        self.list.setItemDelegate(ItemDelegate(self.list))
        self.list.setModel(self.db_list)
        self.list.setMaximumWidth(200)
        self.list.doubleClicked.connect(self.on_list_dbl_click)

        self.tablelist = QListView(parent=self)
        self.tablelist.setItemDelegate(ItemDelegate(self.tablelist))
        self.tablelist.setAlternatingRowColors(True)
        self.tablelist.setModel(self.table_list)
        self.tablelist.setMaximumWidth(200)
        self.tablelist.doubleClicked.connect(self.on_tablename_dbl_click)

        self.bottom_layout.addWidget(self.list)
        self.bottom_layout.addWidget(self.tablelist)
        self.bottom_layout.addWidget(self.table)

        self.layout.addWidget(self.log_text)
        text_and_button.addWidget(self.textbox)
        text_and_button.addWidget(commit)
        text_and_button.addWidget(rollback)
        self.layout.addLayout(text_and_button)

        self.layout.addWidget(self.bottom)
        self.setLayout(self.layout)

        self.history_cursor = 0
        self.history = []

    def append_to_status(self, text: str):
        lines = self.log_text.text().split('\n')
        lines.append(text)
        self.log_text.setText('\n'.join(lines[-5:]))

    def prev_command(self):
        self.history_cursor -= 1
        hl = len(self.history)
        if hl > 0:
            self.textbox.setText(self.history[self.history_cursor % hl])

    def eventFilter(self, source, event: QEvent):
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
                tables = self.get_table_list(db_name) or []
            except Exception as err:
                print(err)
                tables = self.table_list._data
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
    def on_commit_click(self):
        self.append_to_status('COMMIT')
        self.controller.commit()

    @pyqtSlot()
    def on_rollback_click(self):
        self.append_to_status('ROLLBACK')
        self.controller.rollback()

    @pyqtSlot()
    def on_list_dbl_click(self):
        selection = self.list.selectedIndexes()[0]
        try:
            db = self.db_list.get(selection)
            query = 'use `{}`'.format(db)
            self.append_to_status(query)
            self.controller.text_update(query)
        except Exception as err:
            self.append_to_status(str(err))
        self.get_table_list(db)

    def get_table_list(self, db):
        try:
            tables = self.controller.get_table_list(db)
            self.table_list = ListViewModel(tables, parent=self)
            self.tablelist.setModel(self.table_list)
            return tables
        except Exception as err:
            self.append_to_status(str(err))

    @pyqtSlot()
    def on_tablename_dbl_click(self):
        selection = self.tablelist.selectedIndexes()[0]
        try:
            selected_table = self.table_list.get(selection)
            query = 'select * from `{}`'.format(selected_table)
            self.append_to_status(query)
            self.set_data(self.controller.text_update(query))
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
    def __init__(self, controller, parent):
        super().__init__(parent=parent)
        self.controller = controller
        self.parent = parent
        self.doubleClicked.connect(self.on_dbl_click)
        self.cellClicked.connect(self.on_click)
        self.cellChanged.connect(self.on_change)
        self.setStyleSheet('font-family: sans')

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
    def on_change(self):
        for item in self.selectedItems():
            try:
                if item.data(0) != item.record[item.column_name]:
                    query = self.controller.update_record(item.record, item.column_name, item.data(0))
                    if query:
                        self.parent.append_to_status(query)
            except Exception as err:
                print('ERROR')
                print(err)

    @pyqtSlot()
    def on_click(self):
        modifiers = PyQt5.QtGui.QGuiApplication.queryKeyboardModifiers()
        if modifiers != Qt.AltModifier:
            return
        selected = self.selectedItems()
        for item in selected:
            try:
                referenced_data = self.controller.get_reference(item.column_name, item.record[item.column_name])
                if referenced_data is not None:
                    self.set_data(referenced_data)
            except Exception as err:
                print(err)
        return True

    @pyqtSlot()
    def on_dbl_click(self):
        pass
        # for item in self.selectedItems():
        #     print(item.row(), item.column(), item.record)
