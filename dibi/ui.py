from typing import List, Tuple, Callable, Dict, Union
import json

from PyQt5.QtWidgets import QTableWidget,\
    QTableWidgetItem,\
    QHBoxLayout,\
    QVBoxLayout,\
    QWidget,\
    QLineEdit,\
    QLabel,\
    QTextEdit, \
    QListView,\
    QMainWindow,\
    QItemDelegate,\
    QSizePolicy,\
    QStackedWidget,\
    QPushButton, \
    QFormLayout, \
    QSpinBox
from PyQt5.QtCore import pyqtSlot, Qt, QAbstractListModel, QVariant, QEvent, QMargins, QPropertyAnimation, pyqtSignal, QThread, QModelIndex
from PyQt5.QtGui import QGuiApplication, QTextCursor, QPainter

from dibi.configuration import ConnectionInfo, ConfigurationParser
from dibi.waitingspinnerwidget import QtWaitingSpinner


class NewConnectionEditor(QWidget):
    objectName = 'newConnectionEditor'

    def __init__(self, parent, cb: Callable[[ConnectionInfo], None]):
        super().__init__(parent=parent)
        layout = QFormLayout()
        self.cb = cb
        self.setObjectName(self.objectName)
        self.label = QLineEdit()
        self.host = QLineEdit()
        self.user = QLineEdit()
        self.user.setText('root')
        self.port = QSpinBox()
        self.port.setMaximum(65535)
        self.port.setMinimum(1)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password_cmd = QLineEdit()
        self.sshHost = QLineEdit()
        self.sshUser = QLineEdit()
        self.add = QPushButton('Add connection')
        self.add.setObjectName('addConnectionBtn')
        self.add.setCursor(Qt.PointingHandCursor)
        self.add.clicked.connect(self.on_click)
        self.set_defaults()
        layout.addRow(QLabel("Label:"), self.label)
        layout.addRow(QLabel("Host:"), self.host)
        layout.addRow(QLabel("Port:"), self.port)
        layout.addRow(QLabel("User:"), self.user)
        layout.addRow(QLabel("Password:"), self.password)
        layout.addRow(QLabel("Password command (optional):"), self.password_cmd)
        layout.addRow(QLabel("SSH host (optional):"), self.sshHost)
        layout.addRow(QLabel("SSH user (optional):"), self.sshUser)
        layout.addRow(self.add)
        self.setLayout(layout)

    def set_defaults(self):
        self.label.setText('localhost')
        self.host.setText('127.0.0.1')
        self.port.setValue(3306)
        self.user.setText('')
        self.password.setText('')
        self.password_cmd.setText('')
        self.sshHost.setText('')
        self.sshUser.setText('')

    def set_values_from_connection(self, connection: ConnectionInfo):
        self.label.setText(connection.label)
        self.host.setText(connection.host)
        self.port.setValue(connection.port)
        self.user.setText(connection.user)
        self.password.setText(connection.password if not connection.password_cmd else '')
        self.password_cmd.setText(connection.password_cmd)
        self.sshHost.setText(connection.ssh_host)
        self.sshUser.setText(connection.ssh_user)

    def on_click(self):
        self.cb(
            ConnectionInfo(
                self.label.text(),
                self.host.text(),
                self.port.value(),
                self.user.text(),
                self.password.text(),
                self.password_cmd.text(),
                self.sshHost.text(),
                22,
                self.sshUser.text(),
            )
        )
        self.set_defaults()


class ConnectionManager(QWidget):
    connections: List[ConnectionInfo]

    def __init__(self, parent, new_connection_editor: NewConnectionEditor, on_delete: Callable[[int], None]):
        super().__init__(parent=parent)
        self.connections = []
        self.setObjectName('connectionManager')
        top_layout = QHBoxLayout()
        self.new_connection_editor = new_connection_editor
        top_layout.addWidget(new_connection_editor)
        self.connection_list = QListView(parent=self)
        self.delete_button = QPushButton('Delete')

        self.connection_list.clicked.connect(self.on_connection_change)

        def on_delete_click(_):
            try:
                selected = self.connection_list.selectedIndexes().pop()
            except IndexError:
                return
            if self.delete_button.text() == 'Delete':
                self.delete_button.setText(f'Press again to delete "{selected.data()}"')
                self.delete_button.setStyleSheet('background-color: #F33')
                return
            on_delete(selected.row())
            self.delete_button.setText('Delete')
            self.delete_button.setStyleSheet('')

        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setObjectName('deleteConnectionBtn')
        self.delete_button.clicked.connect(on_delete_click)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.connection_list)
        right_layout.addWidget(self.delete_button)
        right_layout.addStretch()

        self.connection_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        top_layout.addLayout(right_layout)
        save_connections = QPushButton('Save connections', parent=self)
        save_connections.setObjectName('saveConnectionsBtn')
        save_connections.setCursor(Qt.PointingHandCursor)

        def on_save_connections(_):
            config = ConfigurationParser()
            config.save(self.connections)

        save_connections.clicked.connect(on_save_connections)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(save_connections)
        self.setLayout(layout)

    def on_connection_change(self, index):
        connection = self.connections[index.row()]
        self.new_connection_editor.set_values_from_connection(connection)
        self.delete_button.setText('Delete')
        self.delete_button.setStyleSheet('')

    def update_connections(self, connections: List[ConnectionInfo]):
        self.connections = connections
        self.connection_list.setModel(
            ListViewModel([c.label for c in connections], parent=self)
        )


class CellEditorContainer(QWidget):
    objectName = 'cellEditorContainer'

    def __init__(self, parent):
        super().__init__(parent=parent)
        layout = QVBoxLayout()
        self.setStyleSheet('background: #ffffff')
        layout.setContentsMargins(QMargins(0, 0, 0, 0))
        layout.setSpacing(0)
        self.cb = None
        self.cancelCb = None
        self.cellEditor = CellEditor()
        layout.addWidget(self.cellEditor)

        bottom_layout = QHBoxLayout()

        save = QPushButton("Save")
        save.setObjectName('save-change-btn')
        save.setCursor(Qt.PointingHandCursor)
        self.save = save

        set_null = QPushButton("Set to NULL")
        set_null.setObjectName('save-change-btn')
        set_null.setCursor(Qt.PointingHandCursor)
        self.set_null = set_null

        cancel = QPushButton("Cancel")
        cancel.setObjectName('cancel-change-btn')
        cancel.setCursor(Qt.PointingHandCursor)
        self.cancel = cancel

        bottom_layout.addWidget(self.save)
        bottom_layout.addWidget(self.set_null)
        bottom_layout.addWidget(self.cancel)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        self.save.clicked.connect(self.onSaveClick)
        self.set_null.clicked.connect(self.onSetNullClick)
        self.cancel.clicked.connect(self.onCancelClick)

    def setText(self, text):
        self.cellEditor.setText(text)

    def onSaveClick(self):
        if self.cb is not None:
            self.cb(self.cellEditor.toPlainText())

    def onSetNullClick(self):
        if self.cb is not None:
            self.cb(None)

    def onCancelClick(self):
        if self.cancelCb is not None:
            self.cancelCb()

    def setCancelCallback(self, cb):
        self.cancelCb = cb
        self.cellEditor.setCancelCallback(cb)

    def setCallback(self, cb):
        self.cb = cb
        self.cellEditor.setCallback(cb)


class CellEditor(QTextEdit):
    cb = None
    cancelCb = None
    installed = False

    def setCallback(self, cb: Callable) -> None:
        if not self.installed:
            self.installEventFilter(self)
            self.installed = True
        self.cb = cb

    def setCancelCallback(self, cb: Callable) -> None:
        if not self.installed:
            self.installEventFilter(self)
            self.installed = True
        self.cancelCb = cb

    def eventFilter(self, source, event):
        if self.cb is None or event.type() != QEvent.KeyPress:
            return QMainWindow.eventFilter(self, source, event)

        key = event.key()
        modifiers = QGuiApplication.queryKeyboardModifiers()

        if key == Qt.Key_Escape and self.cancelCb is not None:
            self.cancelCb()
            self.cancelCb = None
            self.cb = None
            return True

        if key == Qt.Key_Return and modifiers == Qt.ControlModifier and self.cb is not None:
            self.cb(self.toPlainText())
            self.cancelCb = None
            self.cb = None
            return True
        return QMainWindow.eventFilter(self, source, event)


class ListViewModel(QAbstractListModel):
    def __init__(self, data: List[str], parent: QWidget):
        super().__init__(parent=parent)
        self._data = data

    def rowCount(self, ok):
        return len(self._data)

    def flags(self, _: QModelIndex):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def get(self, index: QModelIndex) -> str:
        return self._data[index.row()]

    def data(self, index: QModelIndex, role: int) -> str:
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


class ConnectionButton(QPushButton):
    def __init__(self, label: str, index: int, on_click_cb: Callable):
        super().__init__(label)
        self.clicked.connect(lambda x: on_click_cb(index))
        self.setObjectName('connection-btn')
        self.setCursor(Qt.PointingHandCursor)


class UI(QWidget):
    def __init__(self, thread, connections: List[ConnectionInfo]):
        super().__init__()
        self.connection = ''
        self.connections = connections
        self.t = thread
        self.t.db_list_updated.connect(self.on_dbs_list)
        self.t.query_result.connect(self.on_query_result)
        self.t.use_db.connect(self.on_use_db)
        self.t.error.connect(self.on_error)
        self.t.info.connect(self.on_info)
        self.t.execute.connect(self.on_query)
        self.t.table_list_updated.connect(self.on_tables_list)
        self.t.running_query.connect(self.on_query_op)
        t = QThread()
        self.t.moveToThread(t)
        t.started.connect(self.t.longRunning)
        t.start()
        self._t = t

        self.setObjectName('mainbox')
        self.db_list_open = False
        self.table_list_open = False

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)

        self.db_label_input = QLabel('')
        self.db_label_input.setObjectName('connection_db_label')
        self.textbox = QLineEdit(parent=self)
        self.textbox.setObjectName('query_editor')
        self.textbox.returnPressed.connect(self.run_query)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.layout.setSpacing(0)

        self.top = QWidget(parent=self)
        self.top.setObjectName('top')
        self.top_layout = QVBoxLayout()
        self.top_layout.setSpacing(0)
        self.top_layout.setContentsMargins(QMargins(0, 0, 0, 0))
        self.top.setLayout(self.top_layout)
        text_and_button = QHBoxLayout()
        text_and_button.setSpacing(0)

        self.spinner = QtWaitingSpinner(self, False)
        self.spinner.setInnerRadius(-1)
        self.spinner.setObjectName('spinner')
        self.spinner.setColor('#353b48')
        self.spinner.setBgColor('#E3E8EB')
        self.spinner.setNumberOfLines(16)
        self.spinner.setRevolutionsPerSecond(1.2)
        self.spinner.setLineWidth(2.5)
        self.spinner.setLineLength(12)
        self.spinner.setRoundness(10)
        self.spinner.setPadding(5)

        run = QPushButton("Run")
        run.setObjectName('run-btn')
        run.setCursor(Qt.PointingHandCursor)
        run.clicked.connect(self.run_query)

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
        self.table_list.setProperty(b'maximumWidth', 0)

        self.sidebar = QStackedWidget(parent=self)
        self.sidebar.setObjectName('sidebar')
        self.sidebar.setProperty(b'maximumWidth', 0)

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

        self.cellEditorContainer = CellEditorContainer(parent=self)

        self.connection_manager = ConnectionManager(
            self,
            NewConnectionEditor(self, self.onNewConnection),
            self.on_delete_connection
        )
        self.connection_manager.update_connections(self.connections)

        self.table_and_editor = QStackedWidget(parent=self)
        self.table_and_editor.addWidget(self.table)
        self.table_and_editor.addWidget(self.cellEditorContainer)
        self.table_and_editor.addWidget(self.connection_manager)

        self.bottom_layout.addWidget(self.table_and_editor)

        self.connection_buttons = QHBoxLayout()
        self.render_connection_buttons()

        self.top_layout.addLayout(self.connection_buttons)
        self.top_layout.addWidget(self.log_text)
        text_and_button.addWidget(self.db_label_input)
        text_and_button.addWidget(self.textbox)
        text_and_button.addWidget(run)
        text_and_button.addWidget(commit)
        text_and_button.addWidget(rollback)
        self.top_layout.addLayout(text_and_button)

        self.layout.addWidget(self.bottom)
        self.layout.addWidget(self.top)
        self.setLayout(self.layout)

        self.history_cursor = 0
        self.history = []

        self.db_list = ListViewModel([], parent=self)
        self.autocomplete_state = []

        self.installEventFilter(self)
        self.textbox.installEventFilter(self)
        if self.connections:
            self.change_connection(0)

    def on_delete_connection(self, index: int):
        self.connections.pop(index)
        self.connection_manager.update_connections(self.connections)
        self.render_connection_buttons()

    def render_connection_buttons(self) -> None:
        connection_buttons_count = self.connection_buttons.count()
        is_first_time = not bool(connection_buttons_count)
        for i in reversed(range(connection_buttons_count)):
            if not isinstance(self.connection_buttons.itemAt(i).widget(), ConnectionButton):
                continue
            w = self.connection_buttons.takeAt(i).widget()
            if isinstance(w, ConnectionButton):
                w.deleteLater()

        if is_first_time:
            new_connection_btn = QPushButton('Manage Connections ...', parent=self)
            new_connection_btn.setObjectName('connection-btn')
            new_connection_btn.setCursor(Qt.PointingHandCursor)
            new_connection_btn.clicked.connect(self.on_new_connection)
            self.connection_buttons.addWidget(new_connection_btn)

        for idx, connection in enumerate(self.connections):
            btn = ConnectionButton(connection.label, idx, self.change_connection)
            self.connection_buttons.insertWidget(1 + idx, btn)

        if is_first_time:
            self.connection_buttons.addWidget(self.spinner)
            self.connection_buttons.addStretch()

    def on_query_op(self, isRunning: bool) -> None:
        if not isRunning:
            self.spinner.stop()
            return

        self.spinner.start()

    def on_dbs_list(self, dbs: List[str], connection: str) -> None:
        self.db_list = ListViewModel(dbs, parent=self)
        self.connection = connection
        self.update_db_label('')
        self.list.setModel(self.db_list)
        self.open_db_list()

    def on_new_connection(self):
        self.close_db_list()
        self.close_table_list()
        self.table_and_editor.setCurrentIndex(2)

    def onNewConnection(self, connectionInfo: ConnectionInfo):
        self.connections.append(connectionInfo)
        self.connection_manager.update_connections(self.connections)
        self.render_connection_buttons()

    def saveConnections(self):
        pass

    def on_tables_list(self, tables: List[str]) -> None:
        self.close_db_list()
        self.table_list = ListViewModel(tables, parent=self)
        self.tablelist.setModel(self.table_list)
        self.open_table_list()

    def on_error(self, error: str) -> None:
        self.append_to_status('<span style="color: red">' + error + '</span>')
        self.spinner.stop()

    def on_info(self, info: str) -> None:
        self.append_to_status('<span style="color: black">' + info + '</span>')

    def on_query(self, query: str, params) -> None:
        p = ''
        if params:
            p = ' <table style="border-color: red; border-style: solid" border="1px solid red"><tr><td>'
            p += '</td><td>'.join([str(param) for param in params])
            p += '</td></tr></table>'
        self.append_to_status(query + p)

    def on_query_result(self, results) -> None:
        self.close_cell_editor()
        self.table.set_data(results)

    def update_db_label(self, db: str):
        text = self.connection
        if db:
            text = f'{text}.{db}'
        self.dbs_label.setText(text)
        self.db_label_input.setText(text)

    def on_use_db(self, db: str) -> None:
        self.update_db_label(db)
        self.close_db_list()

    def append_to_status(self, text: str) -> None:
        # lines = self.log_text.toHtml()
        self.log_text.insertHtml(text + '<br>')
        self.log_text.moveCursor(QTextCursor.End)

    def prev_command(self, inc: int = -1) -> None:
        self.history_cursor += inc
        hl = len(self.history)
        if hl > 0:
            self.textbox.setText(self.history[self.history_cursor % hl])

    def change_connection(self, connection_id: int) -> None:
        self.t.job.emit('connect', '', '', self.connections[connection_id].toDict())

    def eventFilter(self, source, event: QEvent):
        if event.type() == QEvent.KeyPress:
            key = event.key()

            if source == self.textbox:
                if key == Qt.Key_Tab or key == Qt.Key_Backtab:
                    self.autocomplete(event.key() == Qt.Key_Tab)
                    return True

                elif key == Qt.Key_Up:
                    self.prev_command()
                    return True

                elif key == Qt.Key_Down:
                    self.prev_command(+1)
                    return True

                elif key == Qt.Key_Shift:
                    return False

            elif key >= Qt.Key_0 and key <= Qt.Key_9:
                if QGuiApplication.queryKeyboardModifiers() == Qt.ControlModifier:
                    number = key - Qt.Key_0
                    self.change_connection(number)
                    return True

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
        self.append_to_status('<strong style="color: green">COMMIT</strong>')
        self.t.job.emit('commit', '', '', {})

    @pyqtSlot()
    def on_rollback_click(self):
        self.append_to_status('<strong style="color: red">ROLLBACK</strong>')
        self.t.job.emit('rollback', '', '', {})

    @pyqtSlot()
    def on_list_click(self) -> None:
        self.open_db_list()

    @pyqtSlot()
    def on_list_dbl_click(self) -> None:
        self.close_db_list()
        selection = self.list.selectedIndexes()[0]
        db = self.db_list.get(selection)
        self.t.job.emit('table_list', db, '', {})

    @pyqtSlot()
    def on_tablename_click(self) -> None:
        modifiers = QGuiApplication.queryKeyboardModifiers()
        if modifiers != Qt.AltModifier:
            return
        selection = self.tablelist.selectedIndexes()[0]
        selected_table = self.table_list.get(selection)
        self.t.job.emit('table_contents', selected_table, '', {})

    def open_db_list(self) -> None:
        if self.db_list_open:
            return
        self.sidebar.setCurrentIndex(0)
        self.db_list_open = True
        self.anim = QPropertyAnimation(self.sidebar, b'maximumWidth')
        self.anim.setDuration(150)
        self.anim.setEndValue(200)
        self.anim.start()
        self.close_table_list()

    def close_db_list(self) -> None:
        if not self.db_list_open:
            return
        self.sidebar.setCurrentIndex(1)
        self.db_list_open = False
        self.anim = QPropertyAnimation(self.sidebar, b'maximumWidth')
        self.anim.setDuration(150)
        self.anim.setEndValue(30)
        self.anim.start()

    def open_table_list(self) -> None:
        if self.table_list_open:
            return
        self.table_list_open = True
        self.tableanim = QPropertyAnimation(self.tablelist, b'maximumWidth')
        self.tableanim.setDuration(150)
        self.tableanim.setEndValue(200)
        self.tableanim.start()

    def close_table_list(self) -> None:
        if not self.table_list_open:
            return
        self.table_list_open = False
        self.tableanim = QPropertyAnimation(self.tablelist, b'maximumWidth')
        self.tableanim.setDuration(150)
        self.tableanim.setEndValue(0)
        self.tableanim.start()

    def show_cell_editor(self, text: str, cb: Callable) -> None:
        self.table_and_editor.setCurrentIndex(1)
        self.cellEditorContainer.setText(str(text))

        def onEditDone(text):
            cb(text)
            self.close_cell_editor()

        def onCancel():
            self.close_cell_editor()

        self.cellEditorContainer.setCallback(onEditDone)
        self.cellEditorContainer.setCancelCallback(onCancel)

    def close_cell_editor(self) -> None:
        self.table_and_editor.setCurrentIndex(0)

    def on_tablename_dbl_click(self) -> None:
        selection = self.tablelist.selectedIndexes()[0]
        selected_table = self.table_list.get(selection)
        self.t.job.emit('table_data', selected_table, '', {})
        self.close_db_list()

    def run_query(self) -> None:
        text = self.textbox.text()
        self.history.append(text)
        self.history_cursor = 0
        self.t.job.emit('query', text, '', {})
        self.textbox.setText('')

    def on_reference_click(self, column_name: str, value: str) -> None:
        self.t.job.emit('get_reference', column_name, value, {})

    def update_record(self, record: Dict['str', 'str'], column_name: str, data: Union[str, int, None]) -> None:
        self.t.job.emit('update', column_name, json.dumps(data), dict(record))


class TableItem(QTableWidgetItem):
    def __init__(self, column_name: str, idx: int, record: Dict['str', 'str']):
        self.column_name = column_name
        self.record = record
        text = self.text()
        super().__init__(text)

        self.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        # self.setFlags(Qt.ItemIsSelectable)

    def text(self) -> str:
        if self.record[self.column_name] is None:
            return ''
        return str(self.record[self.column_name])


class Table(QTableWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.parent = parent
        self.cellClicked.connect(self.on_click)
        self.cellDoubleClicked.connect(self.on_dbl_click)
        self.itemChanged.connect(self.on_change)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft and Qt.AlignVCenter)
        self.setShowGrid(False)

    def set_data(self, data: List[Tuple]) -> None:
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
        if modifiers == Qt.AltModifier:
            selected = self.selectedItems()
            for item in selected:
                self.parent.on_reference_click(item.column_name, str(item.record[item.column_name]))
                return

    def on_dbl_click(self):
        selected = self.selectedItems()
        for item in selected:
            def on_update(newValue):
                self.parent.update_record(item.record, item.column_name, newValue)
                item.record[item.column_name] = newValue
                item.setText(item.text())
            self.parent.show_cell_editor(item.text(), on_update)

            return
