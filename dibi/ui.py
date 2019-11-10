from typing import List, Tuple
from os.path import commonprefix

from PyQt5.QtWidgets import QTableWidget,\
    QTableWidgetItem,\
    QHBoxLayout,\
    QVBoxLayout,\
    QWidget,\
    QLineEdit,\
    QTextEdit, \
    QListView,\
    QMainWindow,\
    QItemDelegate,\
    QSizePolicy,\
    QStackedWidget,\
    QPushButton
from PyQt5.QtCore import pyqtSlot, Qt, QAbstractListModel, QVariant, QEvent, QMargins, QPropertyAnimation, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QTextCursor, QPainter


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
    pass


class VertLabel(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text):
        super().__init__()
        self.text = text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.white)
        painter.translate(10, 10)
        painter.rotate(90)
        painter.drawText(0, 0, self.text)
        painter.end()

    def setText(self, text):
        self.text = text
        self.repaint()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()


class UI(QWidget):
    def __init__(self, thread):
        super().__init__()
        self.t = thread
        self.t.db_list_updated.connect(self.on_dbs_list)
        self.t.query_result.connect(self.on_query_result)
        self.t.use_db.connect(self.on_use_db)
        self.t.error.connect(self.on_error)
        self.t.execute.connect(self.on_query)
        self.t.table_list_updated.connect(self.on_tables_list)

        self.setObjectName('mainbox')
        self.db_list_open = True

        self.log_text = QTextEdit('Initalized' + ('\n' * 4))
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.textbox = QLineEdit(parent=self)
        self.textbox.installEventFilter(self)
        self.textbox.returnPressed.connect(self.on_enter)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.layout.setSpacing(0)

        self.top = QWidget(parent=self)
        self.top.setObjectName('top')
        self.top_layout = QVBoxLayout()
        self.top.setLayout(self.top_layout)
        text_and_button = QHBoxLayout()
        text_and_button.setSpacing(0)
        commit = QPushButton("Commit")
        commit.setObjectName('commit-btn')
        commit.setCursor(Qt.PointingHandCursor)
        commit.clicked.connect(self.on_commit_click)
        rollback = QPushButton("Rollback")
        rollback.setObjectName('rollback-btn')
        rollback.setCursor(Qt.PointingHandCursor)
        rollback.clicked.connect(self.on_rollback_click)
        self.bottom = QWidget(parent=self)
        self.bottom.setObjectName('bottom')

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.bottom.setLayout(self.bottom_layout)

        self.table = Table(parent=self)
        self.table.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self.table_list = ListViewModel([], parent=self)

        self.sidebar = QStackedWidget(parent=self)
        self.sidebar.setObjectName('sidebar')

        self.list = QListView(parent=self.sidebar)
        self.list.setObjectName('db_list')
        self.list.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)
        self.dbs_label = VertLabel("D A T A B A S E S")
        self.dbs_label.setObjectName('database_label')
        self.dbs_label.setCursor(Qt.PointingHandCursor)

        self.sidebar.addWidget(self.list)
        self.sidebar.addWidget(self.dbs_label)
        self.sidebar.setMaximumWidth(200)

        self.dbs_label.clicked.connect(self.on_list_click)
        self.list.doubleClicked.connect(self.on_list_dbl_click)

        self.tablelist = QListView(parent=self)
        self.tablelist.setObjectName('table_list')
        self.tablelist.setModel(self.table_list)
        self.tablelist.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)
        self.tablelist.setMaximumWidth(200)
        self.tablelist.doubleClicked.connect(self.on_tablename_dbl_click)
        self.tablelist.clicked.connect(self.on_tablename_click)

        self.bottom_layout.addWidget(self.sidebar)
        self.bottom_layout.addWidget(self.tablelist)
        self.bottom_layout.addWidget(self.table)

        self.top_layout.addWidget(self.log_text)
        text_and_button.addWidget(self.textbox)
        text_and_button.addWidget(commit)
        text_and_button.addWidget(rollback)
        self.top_layout.addLayout(text_and_button)

        self.layout.addWidget(self.top)
        self.layout.addWidget(self.bottom)
        self.setLayout(self.layout)

        self.history_cursor = 0
        self.history = []

        self.db_list = ListViewModel([], parent=self)
        self.t.job.emit('db_list', '', '', {})
        self.autocomplete_state = []

    def on_dbs_list(self, dbs: List[str]):
        self.db_list = ListViewModel(dbs, parent=self)
        self.list.setModel(self.db_list)

    def on_tables_list(self, tables: List[str]):
        self.close_db_list()
        self.table_list = ListViewModel(tables, parent=self)
        self.tablelist.setModel(self.table_list)

    def on_error(self, error: str):
        self.append_to_status(error)

    def on_query(self, query: str, params):
        self.append_to_status(query + (' ' + str(params) if params else ''))

    def on_query_result(self, results):
        self.table.set_data(results)

    def on_use_db(self, db):
        self.dbs_label.setText(db)
        self.close_db_list()

    def append_to_status(self, text: str):
        lines = self.log_text.toPlainText().split('\n')
        lines.append(text)
        self.log_text.setPlainText('\n'.join(lines))
        self.log_text.moveCursor(QTextCursor.End)

    def prev_command(self):
        self.history_cursor -= 1
        hl = len(self.history)
        if hl > 0:
            self.textbox.setText(self.history[self.history_cursor % hl])

    def eventFilter(self, source, event: QEvent):
        if event.type() == QEvent.KeyPress:
            key = event.key()

            if key == Qt.Key_Tab or key == Qt.Key_Backtab:
                self.autocomplete(event.key() == Qt.Key_Tab)
                return True

            elif key == Qt.Key_Up:
                self.prev_command()
                return True

            elif key == Qt.Key_Down:
                self.prev_command()
                return True

            elif key == Qt.Key_Shift:
                return False

            self.autocomplete_state = []

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

    def autocomplete(self, forward):
        if self.autocomplete_state:
            [words, after_cursor, word, matches, matches, idx] = self.autocomplete_state

            len_matches = len(matches)
            if forward:
                idx += 1
            if not forward:
                idx += len_matches - 1

            idx = idx % len_matches

            self.autocomplete_state = [list(words), after_cursor, word, matches, matches, idx]

            words.append(matches[idx])
            match = matches[idx]
            before_cursor = ' '.join(words)
            self.textbox.setText(before_cursor + after_cursor)
            self.textbox.setCursorPosition(len(before_cursor))
            return

        pos = self.textbox.cursorPosition()
        text = self.textbox.text()
        before_cursor, after_cursor = text[:pos], text[pos:]
        words = before_cursor.split(' ')
        word = words.pop().lower()
        wl = len(word)
        candidates = [s + ' ' for s in self.SQL] + [db for db in self.db_list._data]
        if '.' in word:
            db_name = word.split('.')[0]
            self.t.job.emit('table_list', db_name, '', {})
            tables = self.table_list._data
            candidates += [db_name + '.' + table + ' ' for table in tables]
        else:
            candidates += [table + ' ' for table in self.table_list._data]

        matches = [w for w in candidates if w[:wl % len(w)].lower() == word]
        if len(matches) == 0:
            return

        match = matches[0]
        if len(matches) != 1:
            match = matches[0]
            self.autocomplete_state = [list(words), after_cursor, word, matches, matches, 0]

        words.append(match)
        before_cursor = ' '.join(words)
        self.textbox.setText(before_cursor + after_cursor)
        self.textbox.setCursorPosition(len(before_cursor))

    @pyqtSlot()
    def on_commit_click(self):
        self.append_to_status('COMMIT')
        self.t.job.emit('commit', '', '', {})

    @pyqtSlot()
    def on_rollback_click(self):
        self.append_to_status('ROLLBACK')
        self.t.job.emit('rollback', '', '', {})

    @pyqtSlot()
    def on_list_click(self):
        self.open_db_list()

    @pyqtSlot()
    def on_list_dbl_click(self):
        self.close_db_list()
        selection = self.list.selectedIndexes()[0]
        db = self.db_list.get(selection)
        self.t.job.emit('table_list', db, '', {})

    @pyqtSlot()
    def on_tablename_click(self):
        modifiers = QGuiApplication.queryKeyboardModifiers()
        if modifiers != Qt.AltModifier:
            return
        selection = self.tablelist.selectedIndexes()[0]
        selected_table = self.table_list.get(selection)
        self.t.job.emit('table_contents', selected_table, '', {})

    def open_db_list(self):
        if self.db_list_open:
            return
        self.sidebar.setCurrentIndex(0)
        self.db_list_open = True
        self.anim = QPropertyAnimation(self.sidebar, b'maximumWidth')
        self.anim.setDuration(150)
        self.anim.setEndValue(200)
        self.anim.start()

    def close_db_list(self):
        if not self.db_list_open:
            return
        self.sidebar.setCurrentIndex(1)
        self.db_list_open = False
        self.anim = QPropertyAnimation(self.sidebar, b'maximumWidth')
        self.anim.setDuration(150)
        self.anim.setEndValue(30)
        self.anim.start()

    def on_tablename_dbl_click(self):
        selection = self.tablelist.selectedIndexes()[0]
        selected_table = self.table_list.get(selection)
        self.t.job.emit('table_data', selected_table, '', {})
        self.close_db_list()

    def on_enter(self):
        text = self.textbox.text()
        self.history.append(text)
        self.history_cursor = 0
        self.t.job.emit('query', text, '', {})
        self.textbox.setText('')

    def on_reference_click(self, column_name, value):
        self.t.job.emit('get_reference', column_name, value, {})

    def update_record(self, record, column_name, data):
        self.t.job.emit('update', column_name, str(data), record)


class TableItem(QTableWidgetItem):
    def __init__(self, column_name, idx, record):
        super().__init__(str(record[column_name]))
        self.column_name = column_name
        self.record = record

    def text(self):
        return self.record[self.column_name]


class Table(QTableWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.setShowGrid(False)
        self.setCornerButtonEnabled(False)
        self.cellClicked.connect(self.on_click)
        self.itemChanged.connect(self.on_change)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft and Qt.AlignVCenter)

    def set_data(self, data: List[Tuple]):
        self.clear()
        row_count = len(data)

        if row_count == 0:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        self.setRowCount(row_count - 1)

        i = iter(data)
        header = next(i)

        self.setColumnCount(len(header))
        self.setHorizontalHeaderLabels(header)

        for row, item in enumerate(i):
            for col, val in enumerate(item):
                record = dict(zip(header, item))
                self.setItem(row, col, TableItem(header[col], col, record))
        self.resizeColumnsToContents()

    def on_change(self):
        for item in self.selectedItems():
            if item.data(0) != item.record[item.column_name]:
                self.parent.update_record(item.record, item.column_name, item.data(0))
                return

    def on_click(self):
        modifiers = QGuiApplication.queryKeyboardModifiers()
        if modifiers != Qt.AltModifier:
            return
        selected = self.selectedItems()
        for item in selected:
            self.parent.on_reference_click(item.column_name, str(item.record[item.column_name]))
            return
