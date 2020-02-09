from PyQt5 import QtCore, QtGui, QtWidgets
from typing import List, Dict, Tuple, Union, Optional, Any
import json

from dibi.configuration import ConnectionInfo
from dibi.db import DbThread


_translate = QtCore.QCoreApplication.translate


class Ui_main(object):
    _connections: List[ConnectionInfo] = []

    def setupUi(self, main):
        main.setObjectName("main")
        main.resize(734, 504)
        font = QtGui.QFont()
        font.setFamily("Inter")
        main.setFont(font)
        main.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        main.setStyleSheet("#main {\n"
                           "background: #fff\n"
                           "}\n"
                           "\n"
                           "")
        self.horizontalLayout = QtWidgets.QHBoxLayout(main)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabs = QtWidgets.QTabWidget(main)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.tabs.setFont(font)
        self.tabs.setAutoFillBackground(False)
        self.tabs.setStyleSheet("\n"
                                "#tabs QTabBar::tab-bar {\n"
                                "alignment: left;\n"
                                "}\n"
                                "\n"
                                "#tabs QTabBar::close-button {\n"
                                " left: -10px;\n"
                                "    subcontrol-origin: content;\n"
                                "    image: url(:/icons/rollback.png);\n"
                                "width: 14px;\n"
                                "height: 14px;\n"
                                "}\n"
                                "\n"
                                "#tabs QTabBar::tab {\n"
                                "border-top-left-radius: 4px;\n"
                                "border-top-right-radius: 4px;\n"
                                "border: none;\n"
                                "padding: 3px 7px;\n"
                                "margin-right: 5px;\n"
                                "    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 1 #f0f0f0, stop: 0 #ffffff);\n"
                                "}\n"
                                "\n"
                                "#tabs QTabBar::tab:selected, \n"
                                "#tabs QTabBar::tab:hover {\n"
                                "\n"
                                "background: #f0f0f0;\n"
                                "}\n"
                                "QTabBar::tab:!selected {\n"
                                "    margin-top: 2px; \n"
                                "}\n"
                                "\n"
                                "#tabs::pane {\n"
                                "border: none;\n"
                                "}\n"
                                "")
        self.tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self.tabs.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.tabs.setIconSize(QtCore.QSize(12, 12))
        self.tabs.setDocumentMode(False)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setTabBarAutoHide(True)
        self.tabs.setObjectName("tabs")
        self.new_connection = QtWidgets.QWidget()
        self.new_connection.setStyleSheet("#new_connection {\n"
                                          "background: #f5f5f5; \n"
                                          "border-top-right-radius: 14px;\n"
                                          "border-bottom-right-radius: 14px;\n"
                                          "border-bottom-left-radius: 14px;\n"
                                          "}")
        self.new_connection.setObjectName("new_connection")
        self.gridLayout = QtWidgets.QGridLayout(self.new_connection)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.gridLayout.setContentsMargins(-1, -1, 9, 9)
        self.gridLayout.setHorizontalSpacing(8)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 23, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(137, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 2, 3, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(138, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 0, 4, 1)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 0, 1, 1, 1)
        self.connection_list = QtWidgets.QFrame(self.new_connection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connection_list.sizePolicy().hasHeightForWidth())
        self.connection_list.setSizePolicy(sizePolicy)
        self.connection_list.setStyleSheet("\n"
                                           "#connection_list {\n"
                                           "border-bottom-right-radius: 15px;\n"
                                           "border-top-right-radius: 15px;\n"
                                           "background: #fff;\n"
                                           "}\n"
                                           "\n"
                                           "QToolboxButton {\n"
                                           "border: none;\n"
                                           "background: transparent;\n"
                                           "}\n"
                                           "\n"
                                           ".connection QLabel {\n"
                                           "color: #333;\n"
                                           "padding: 3px 3px;\n"
                                           "font-size: 10pt;\n"
                                           "}\n"
                                           "\n"
                                           ".connection QLabel:hover {\n"
                                           "text-decoration: underline;\n"
                                           "background: #f5f5f5;\n"
                                           "color:#000;\n"
                                           "}\n"
                                           "")
        self.connection_list.setObjectName("connection_list")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.connection_list)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout.setContentsMargins(14, 14, 14, 14)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.connections_label = QtWidgets.QLabel(self.connection_list)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(75)
        font.setKerning(True)
        self.connections_label.setFont(font)
        self.connections_label.setStyleSheet("color: #666")
        self.connections_label.setObjectName("connections_label")
        self.verticalLayout.addWidget(self.connections_label)
        self.line_3 = QtWidgets.QFrame(self.connection_list)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.verticalLayout.addWidget(self.line_3)
        # TODO
        self.connection_list_widgets = QtWidgets.QWidget()
        self.verticalLayout.addWidget(self.connection_list_widgets)
        self.gridLayout.addWidget(self.connection_list, 1, 2, 2, 1)
        self.connection_edit_frame = QtWidgets.QFrame(self.new_connection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connection_edit_frame.sizePolicy().hasHeightForWidth())
        self.connection_edit_frame.setSizePolicy(sizePolicy)
        self.connection_edit_frame.setStyleSheet("#connection_edit_frame {\n"
                                                 "background: #Fff;\n"
                                                 "padding: 10px 14px;\n"
                                                 "border-radius: 15px;\n"
                                                 "border-top-right-radius: 0;\n"
                                                 "}")
        self.connection_edit_frame.setObjectName("connection_edit_frame")
        self.formLayout = QtWidgets.QFormLayout(self.connection_edit_frame)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.formLayout.setHorizontalSpacing(20)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.lineEdit = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit.setText("")
        self.lineEdit.setObjectName("lineEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lineEdit)
        self.label_2 = QtWidgets.QLabel(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lineEdit_2)
        self.label_3 = QtWidgets.QLabel(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_3.setMinimumSize(QtCore.QSize(0, 0))
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.lineEdit_3)
        self.label_4 = QtWidgets.QLabel(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.lineEdit_4 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_4.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineEdit_4.setClearButtonEnabled(False)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.lineEdit_4)
        self.label_5 = QtWidgets.QLabel(self.connection_edit_frame)
        self.label_5.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.label_5)
        self.lineEdit_5 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.lineEdit_5)
        self.line = QtWidgets.QFrame(self.connection_edit_frame)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.formLayout.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.line)
        self.label_6 = QtWidgets.QLabel(self.connection_edit_frame)
        self.label_6.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.lineEdit_6 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_6.setObjectName("lineEdit_6")
        self.formLayout.setWidget(7, QtWidgets.QFormLayout.FieldRole, self.lineEdit_6)
        self.label_7 = QtWidgets.QLabel(self.connection_edit_frame)
        self.label_7.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.lineEdit_7 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_7.setObjectName("lineEdit_7")
        self.formLayout.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.lineEdit_7)
        self.label_8 = QtWidgets.QLabel(self.connection_edit_frame)
        self.label_8.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_8.setObjectName("label_8")
        self.formLayout.setWidget(9, QtWidgets.QFormLayout.LabelRole, self.label_8)
        self.lineEdit_8 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_8.setObjectName("lineEdit_8")
        self.formLayout.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.lineEdit_8)
        self.line_2 = QtWidgets.QFrame(self.connection_edit_frame)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.formLayout.setWidget(10, QtWidgets.QFormLayout.SpanningRole, self.line_2)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.formLayout.setItem(11, QtWidgets.QFormLayout.LabelRole, spacerItem4)
        self.pushButton = QtWidgets.QPushButton(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.formLayout.setWidget(11, QtWidgets.QFormLayout.FieldRole, self.pushButton)
        self.label_9 = QtWidgets.QLabel(self.connection_edit_frame)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_9.setObjectName("label_9")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_9)
        self.lineEdit_9 = QtWidgets.QLineEdit(self.connection_edit_frame)
        self.lineEdit_9.setObjectName("lineEdit_9")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.lineEdit_9)
        self.gridLayout.addWidget(self.connection_edit_frame, 1, 1, 4, 1)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem5, 3, 2, 1, 1)
        self.tabs.addTab(self.new_connection, "")
        # TODO

        self.horizontalLayout.addWidget(self.tabs)
        self.actionbla = QtWidgets.QAction(main)
        self.actionbla.setCheckable(True)
        self.actionbla.setObjectName("actionbla")

        self.retranslateUi(main)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        QtCore.QMetaObject.connectSlotsByName(main)

    def retranslateUi(self, main):
        main.setWindowTitle(_translate("main", "Form"))
        self.connections_label.setText(_translate("main", "CONNECTIONS"))
        self.label.setText(_translate("main", "Label"))
        self.lineEdit.setPlaceholderText(_translate("main", "My connection"))
        self.label_2.setText(_translate("main", "Host"))
        self.lineEdit_2.setText(_translate("main", "127.0.0.1"))
        self.label_3.setText(_translate("main", "User"))
        self.lineEdit_3.setText(_translate("main", "root"))
        self.label_4.setText(_translate("main", "Password"))
        self.lineEdit_4.setPlaceholderText(_translate("main", "Password"))
        self.label_5.setText(_translate("main", "Password command"))
        self.lineEdit_5.setPlaceholderText(_translate("main", "echo password"))
        self.label_6.setText(_translate("main", "SSH host"))
        self.label_7.setText(_translate("main", "SSH user"))
        self.label_8.setText(_translate("main", "SSH key"))
        self.pushButton.setText(_translate("main", "Add connection"))
        self.label_9.setText(_translate("main", "Port"))
        self.lineEdit_9.setText(_translate("main", "3306"))
        self.tabs.setTabText(self.tabs.indexOf(self.new_connection), _translate("main", "Connections"))
        self.actionbla.setText(_translate("main", "bla"))
        self.actionbla.setShortcut(_translate("main", "Alt+Shift+C"))

    def setConnections(self, connections: List[ConnectionInfo]):
        self._connections = connections
        self.renderConnections()

    def renderConnections(self):
        layout = QtWidgets.QVBoxLayout(self.connection_list_widgets)
        for connection in self._connections:
            widget = ConnectionListLabel(parent=self.connection_list_widgets)
            widget.renderConnectionLabel(connection)
            widget.open_connection.connect(self.openConnection)
            layout.addWidget(widget)

    def close_tab(self, index: int):
        if index < 1:
            return
        self.tabs.children()[index].close()
        self.tabs.removeTab(index)

    def openConnection(self, connection: ConnectionInfo):
        connection_tab = ConnectionTab()
        connection_tab.render()
        self.tabs.addTab(connection_tab, "")
        new_tab_index = self.tabs.indexOf(connection_tab)
        self.tabs.setTabText(new_tab_index, connection.label)
        self.tabs.setCurrentIndex(new_tab_index)
        connection_tab.open_connection(connection)
        connection_tab.focus_input()
        self.tabs.tabCloseRequested


class ConnectionListLabel(QtWidgets.QWidget):
    open_connection = QtCore.pyqtSignal(ConnectionInfo)
    removed = QtCore.pyqtSignal(ConnectionInfo)
    edited = QtCore.pyqtSignal(ConnectionInfo)

    def renderConnectionLabel(self, connection: ConnectionInfo):
        self.connection = QtWidgets.QHBoxLayout(self)
        self.connection.setContentsMargins(0, 0, 0, 0)
        self.connection.setSpacing(0)
        self.connection.setObjectName("connection")
        self.connection_label = QtWidgets.QPushButton(self.parent())
        self.connection_label.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.connection_label.setObjectName("connection_label")
        self.connection_label.setText(connection.label)
        self.connection.addWidget(self.connection_label)
        self.edit = QtWidgets.QToolButton(self.parent())
        self.edit.setMinimumSize(QtCore.QSize(12, 12))
        self.edit.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.edit.setStyleSheet("border: none")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/edit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.edit.setIcon(icon)
        self.edit.setIconSize(QtCore.QSize(12, 12))
        self.edit.setObjectName("edit")
        self.connection.addWidget(self.edit)
        self.close = QtWidgets.QToolButton(self.parent())
        self.close.setMinimumSize(QtCore.QSize(12, 12))
        self.close.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.close.setStyleSheet("border:none")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close.setIcon(icon1)
        self.close.setIconSize(QtCore.QSize(12, 12))
        self.close.setObjectName("close")
        self.connection.addWidget(self.close)

        self.edit.setText('...')
        self.close.setText('...')

        self.connection_label.clicked.connect(lambda _: self.open_connection.emit(connection))
        self.edit.clicked.connect(lambda _: self.edited.emit(connection))
        self.close.clicked.connect(lambda _: self.removed.emit(connection))


class StringList(QtCore.QAbstractListModel):
    def __init__(self, data: List[str], parent: QtCore.QObject = None):
        super().__init__(parent=parent)
        self.list = data
        self.parent = parent

    def rowCount(self, parent: QtCore.QModelIndex):
        return len(self.list)

    def data(self, index: QtCore.QModelIndex, role: int):
        return self.list[index.row()]


class ConnectionTab(QtWidgets.QWidget):
    _dbs: List[str] = []
    editing_record: Optional[Dict[str, str]] = None
    editing_column: Optional[str] = None

    def close(self):
        self.t.job.emit('disconnect', '', '', {})

    def on_dbs_list(self, dbs: List[str]):
        self.comboBox.clear()
        self._dbs = dbs
        for db in dbs:
            self.comboBox.addItem(db, db)
        self.textEdit.setDbList(dbs)

    def on_db_selected(self, index: int):
        if index < 0:
            return
        try:
            db = self._dbs[index]
        except KeyError:
            return
        self.t.job.emit('table_list', db, '', {})

    def on_query_result(self, results):
        self.tableWidget.set_data(results)

    def on_use_db(self, db: str):
        try:
            self.comboBox.setCurrentIndex(self._dbs.index(db))
        except ValueError:
            return

    def on_error(self, error: str):
        self.textBrowser.append(f'<span style="color: red">{error}</span>')

    def on_info(self, info: str):
        self.textBrowser.append(info)

    def on_query_op(self, isRunning: bool):
        pass

    def on_query(self, query):
        self.textBrowser.append(query)

    def on_tables_list(self, tables: List[str]):
        self.listView.clear()
        self.tables_list = tables
        for table in tables:
            self.listView.addItem(table)
        self.textEdit.setTables(tables)

    def on_table_dblclick(self, item: QtCore.QModelIndex):
        try:
            table = self.tables_list[item.row()]
        except KeyError:
            return
        self.t.job.emit('table_data', table, '', {})

    def on_table_click(self, item: QtCore.QModelIndex):
        modifiers = QtGui.QGuiApplication.queryKeyboardModifiers()
        if modifiers != QtCore.Qt.AltModifier:
            return
        try:
            table = self.tables_list[item.row()]
        except KeyError:
            return
        self.t.job.emit('table_contents', table, '', {})

    def open_connection(self, connection: ConnectionInfo):
        self.connection = connection

        self.t = DbThread()
        self.t.ready_to_connect.connect(self.on_ready_to_connect)
        self.t.db_list_updated.connect(self.on_dbs_list)
        self.t.query_result.connect(self.on_query_result)
        self.t.use_db.connect(self.on_use_db)
        self.t.error.connect(self.on_error)
        self.t.info.connect(self.on_info)
        self.t.execute.connect(self.on_query)
        self.t.table_list_updated.connect(self.on_tables_list)
        self.t.running_query.connect(self.on_query_op)
        t = QtCore.QThread()
        self.t.moveToThread(t)
        t.started.connect(self.t.longRunning)
        t.start()
        self._t = t

    def on_ready_to_connect(self):
        self.t.job.emit('connect', '', '', self.connection.toDict())

    def on_goto_reference(self, column_name: str, value: Union[str, int]):
        self.t.job.emit('get_reference', column_name, value, {})

    def on_edit_cell(self, column_name: str, record: Dict[str, str]):
        self.stackedWidget.setCurrentIndex(1)
        self.editpage.set_text(str(record[column_name]))
        self.editing_record = record
        self.editing_column = column_name

    def on_edit_cell_save(self, value: str):
        if self.editing_column is None or self.editing_column is None:
            return
        self.t.job.emit('update', self.editing_column, json.dumps(value), dict(self.editing_record))
        self.stackedWidget.setCurrentIndex(0)
        self.tableWidget.updateRecord(self.editing_record, value)

    def on_edit_cell_null(self):
        if self.editing_column is None or self.editing_column is None:
            return
        self.t.job.emit('update', self.editing_column, json.dumps(None), dict(self.editing_record))
        self.stackedWidget.setCurrentIndex(0)

    def on_edit_cell_cancel(self):
        self.stackedWidget.setCurrentIndex(0)

    def on_commit(self):
        self.t.job.emit('commit', '', '', {})

    def on_rollback(self):
        self.t.job.emit('rollback', '', '', {})

    def request_tables(self, db_name: str):
        self.t.job.emit('table_list', db_name, '', {})

    def run_query(self, query: str):
        self.t.job.emit('query', query, '', {})

    def render(self):
        self.setStyleSheet("#connection_tab {\n"
                           "background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.9 #f5f5f5, stop: 0 #f0f0f0);\n"
                           "}")
        self.setObjectName("connection_tab")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.main_splitter = QtWidgets.QSplitter(self)
        self.main_splitter.setStyleSheet("QSplitter::handle {\n"
                                         "    image: none;\n"
                                         "}\n"
                                         "\n"
                                         "QSplitter::handle:pressed {\n"
                                         "    image: none;\n"
                                         "}")
        self.main_splitter.setLineWidth(0)
        self.main_splitter.setOrientation(QtCore.Qt.Vertical)
        self.main_splitter.setOpaqueResize(True)
        self.main_splitter.setChildrenCollapsible(True)
        self.main_splitter.setObjectName("main_splitter")
        self.layoutWidget = QtWidgets.QWidget(self.main_splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.tables = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.tables.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.tables.setContentsMargins(0, 0, 0, 0)
        self.tables.setObjectName("tables")
        self.tables_and_buttons = QtWidgets.QWidget(self.layoutWidget)
        self.tables_and_buttons.setMinimumSize(QtCore.QSize(100, 0))
        self.tables_and_buttons.setMaximumSize(QtCore.QSize(150, 16777215))
        self.tables_and_buttons.setStyleSheet("QPushButton {\n"
                                              "background: rgba(255,255,255,1);\n"
                                              "border: 1px solid #ddd;\n"
                                              "border-top: none;\n"
                                              "height: 24px;\n"
                                              "}")
        self.tables_and_buttons.setObjectName("tables_and_buttons")
        self.dataviews = QtWidgets.QVBoxLayout(self.tables_and_buttons)
        self.dataviews.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)
        self.dataviews.setContentsMargins(0, 0, 0, 0)
        self.dataviews.setSpacing(0)
        self.dataviews.setObjectName("dataviews")
        self.comboBox = QtWidgets.QComboBox(self.tables_and_buttons)
        self.comboBox.setMaximumSize(QtCore.QSize(150, 16777215))
        self.comboBox.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.comboBox.setStyleSheet("QComboBox {\n"
                                    "    background: #fff;\n"
                                    "    border: none;\n"
                                    "border: 1px solid #ddd;\n"
                                    "padding: 5px;\n"
                                    "}\n"
                                    "\n"
                                    "QComboBox::drop-down {\n"
                                    "    border: none;\n"
                                    "}\n"
                                    "")
        self.comboBox.setFrame(False)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.currentIndexChanged.connect(self.on_db_selected)
        self.dataviews.addWidget(self.comboBox)
        self.listView = QtWidgets.QListWidget(self.tables_and_buttons)
        self.listView.setMinimumSize(QtCore.QSize(100, 0))
        self.listView.setMaximumSize(QtCore.QSize(150, 16777215))
        self.listView.setStyleSheet("QListView {\n"
                                    "background: rgba(255,255,255,1);\n"
                                    "border: 1px solid #ddd;\n"
                                    "border-top: none;\n"
                                    "}")
        self.listView.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.listView.setFrameShadow(QtWidgets.QFrame.Raised)
        self.listView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.listView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.listView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.listView.setSelectionRectVisible(True)
        self.listView.setObjectName("listView")
        self.listView.doubleClicked.connect(self.on_table_dblclick)
        self.listView.clicked.connect(self.on_table_click)
        self.dataviews.addWidget(self.listView)
        self.pushButton_2 = QtWidgets.QPushButton(self.tables_and_buttons)
        self.pushButton_2.setStyleSheet("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/commit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.clicked.connect(self.on_commit)
        self.dataviews.addWidget(self.pushButton_2)
        self.pushButton_3 = QtWidgets.QPushButton(self.tables_and_buttons)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/rollback.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_3.setIcon(icon3)
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_3.clicked.connect(self.on_rollback)
        self.dataviews.addWidget(self.pushButton_3)
        self.tables.addWidget(self.tables_and_buttons)
        self.stackedWidget = QtWidgets.QStackedWidget(self.layoutWidget)
        self.stackedWidget.setObjectName("stackedWidget")
        self.tablepage = QtWidgets.QWidget()
        self.tablepage.setObjectName("tablepage")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.tablepage)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.tableWidget = TableWidget(self.tablepage)
        self.tableWidget.render()
        self.tableWidget.goto_reference.connect(self.on_goto_reference)
        self.tableWidget.edit_cell.connect(self.on_edit_cell)
        self.horizontalLayout_3.addWidget(self.tableWidget)
        self.stackedWidget.addWidget(self.tablepage)
        self.editpage = EditPage()
        self.editpage.render()
        self.stackedWidget.addWidget(self.editpage)
        self.tables.addWidget(self.stackedWidget)
        self.layoutWidget1 = QtWidgets.QWidget(self.main_splitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.textBrowser = QtWidgets.QTextBrowser(self.layoutWidget1)
        self.textBrowser.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setFamily("Monospace")
        font.setPointSize(8)
        self.textBrowser.setFont(font)
        self.textBrowser.setStyleSheet("background: rgba(250,255,252,1);\n"
                                       "font-size: 8pt;\n"
                                       "border: 1px solid rgba(0,0,0,0.1);\n"
                                       "border-bottom: none")
        self.textBrowser.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.textBrowser.setFrameShadow(QtWidgets.QFrame.Raised)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.textEdit = InputBox(self.layoutWidget1)
        self.verticalLayout_2.addWidget(self.textEdit)
        self.horizontalLayout_2.addWidget(self.main_splitter)

        self.pushButton_2.setText('Commit')
        self.pushButton_3.setText('Rollback')
        self.textBrowser.setHtml('')
        self.textEdit.setPlainText('')

        self.editpage.saved.connect(self.on_edit_cell_save)
        self.editpage.nulled.connect(lambda: self.on_edit_cell_null())
        self.editpage.canceled.connect(self.on_edit_cell_cancel)
        self.textEdit.need_tables.connect(self.request_tables)
        self.textEdit.query.connect(self.run_query)

    def focus_input(self):
        self.textEdit.setFocus()


class InputBox(QtWidgets.QPlainTextEdit):
    need_tables = QtCore.pyqtSignal(str)
    query = QtCore.pyqtSignal(str)

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self.setMaximumSize(QtCore.QSize(16777215, 24))
        self.setBaseSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setFamily("monospace")
        font.setPointSize(8)
        self.setFont(font)
        self.setStyleSheet("QPlainTextEdit {\n"
                           "font-family: monospace;\n"
                           "background: rgba(255,255,255,0.8);\n"
                           "border: none;\n"
                           "border: 1px solid rgba(0,0,0,0.1);\n"
                           "font-size: 8pt;\n"
                           "}")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setObjectName("textEdit")
        self.installEventFilter(self)
        self.autocomplete_state: List[Any] = []
        self.tables_list: List[str] = []
        self.db_list: List[str] = []
        self.history_cursor: int = 0
        self.history: List[str] = []

    def setTables(self, tables: List[str]):
        self.tables_list = tables

    def setDbList(self, dbs: List[str]):
        self.db_list = dbs

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

    def prev_command(self, inc: int = -1) -> None:
        self.history_cursor += inc
        hl = len(self.history)
        if hl > 0:
            prev_query = self.history[self.history_cursor % hl]
            self.setPlainText(prev_query)
            cursor = self.textCursor()
            cursor.setPosition(len(prev_query))
            self.setTextCursor(cursor)

    def eventFilter(self, source, event: QtCore.QEvent):
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()

            is_ctrl = False
            if QtGui.QGuiApplication.queryKeyboardModifiers() == QtCore.Qt.ControlModifier:
                is_ctrl = True

            if source == self:
                if key == QtCore.Qt.Key_Return:
                    text = self.toPlainText()
                    self.history.append(text)
                    self.history_cursor = 0
                    self.query.emit(text)
                    self.setPlainText('')
                    return True

                if (key == QtCore.Qt.Key_Tab or key == QtCore.Qt.Key_Backtab) and not is_ctrl:
                    self.autocomplete(event.key() == QtCore.Qt.Key_Tab)
                    return True

                elif key == QtCore.Qt.Key_Up:
                    self.prev_command()
                    return True

                elif key == QtCore.Qt.Key_Down:
                    self.prev_command(+1)
                    return True

                elif key == QtCore.Qt.Key_Shift:
                    return False

            self.autocomplete_state = []

        return QtWidgets.QMainWindow.eventFilter(self, source, event)

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
            self.setPlainText(before_cursor + after_cursor)
            cursor = self.textCursor()
            cursor.setPosition(len(before_cursor))
            self.setTextCursor(cursor)
            return

        pos = self.textCursor().position()
        text = self.toPlainText()
        before_cursor, after_cursor = text[:pos], text[pos:]
        words = before_cursor.split(' ')
        word = words.pop().lower()
        wl = len(word)
        candidates = [s + ' ' for s in self.SQL] + [db for db in self.db_list]
        if '.' in word:
            db_name = word.split('.')[0]
            self.need_tables.emit(db_name)
            tables = self.tables_list
            candidates += [db_name + '.' + table + ' ' for table in tables]
        else:
            candidates += [table + ' ' for table in self.tables_list]

        matches = [w for w in candidates if w[:wl % len(w)].lower() == word]
        if len(matches) == 0:
            return

        match = matches[0]
        if len(matches) != 1:
            match = matches[0]
            self.autocomplete_state = [list(words), after_cursor, word, matches, matches, 0]

        words.append(match)
        before_cursor = ' '.join(words)
        self.setPlainText(before_cursor + after_cursor)
        cursor = self.textCursor()
        cursor.setPosition(len(before_cursor))
        self.setTextCursor(cursor)


class EditPage(QtWidgets.QWidget):
    saved = QtCore.pyqtSignal(str)
    nulled = QtCore.pyqtSignal()
    canceled = QtCore.pyqtSignal()

    def render(self):
        self.setObjectName("editpage")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit.setStyleSheet("border: 1px solid #ddd;")
        self.plainTextEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.plainTextEdit.setFrameShadow(QtWidgets.QFrame.Plain)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout_3.addWidget(self.plainTextEdit)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem6)
        self.pushButton_6 = QtWidgets.QPushButton(self)
        self.pushButton_6.setObjectName("null")
        self.pushButton_6.clicked.connect(self.on_null_click)
        self.horizontalLayout_5.addWidget(self.pushButton_6)
        self.pushButton_5 = QtWidgets.QPushButton(self)
        self.pushButton_5.setObjectName("save")
        self.pushButton_5.clicked.connect(self.on_save_click)
        self.horizontalLayout_5.addWidget(self.pushButton_5)
        self.pushButton_4 = QtWidgets.QPushButton(self)
        self.pushButton_4.setObjectName("cancel")
        self.pushButton_4.clicked.connect(self.on_cancel_click)
        self.horizontalLayout_5.addWidget(self.pushButton_4)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.pushButton_6.setText("Set NULL")
        self.pushButton_5.setText("Save")
        self.pushButton_4.setText("Cancel")

        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() != QtCore.QEvent.KeyPress:
            return QtWidgets.QMainWindow.eventFilter(self, source, event)

        key = event.key()
        modifiers = QtGui.QGuiApplication.queryKeyboardModifiers()

        if key == QtCore.Qt.Key_Escape:
            self.on_cancel_click()
            return True

        if key == QtCore.Qt.Key_Return and modifiers == QtCore.Qt.ControlModifier:
            self.on_save_click()
            return True

        return QtWidgets.QMainWindow.eventFilter(self, source, event)

    def set_text(self, text: str):
        self.plainTextEdit.setPlainText(text)

    def on_cancel_click(self):
        self.canceled.emit()

    def on_save_click(self):
        self.saved.emit(self.plainTextEdit.toPlainText())

    def on_null_click(self):
        self.nulled.emit()


class TableWidget(QtWidgets.QTableWidget):
    goto_reference = QtCore.pyqtSignal(str, str)
    edit_cell = QtCore.pyqtSignal(str, dict)

    def update_record(self, record: Dict[str, str]):
        self.dataChanged

    def render(self):
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(400, 300))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.setFont(font)
        self.setStyleSheet("QTableWidget {\n"
                           "    background: rgba(255,255,255,1);\n"
                           "    color: #272343;\n"
                           "border: 1px solid #ddd;\n"
                           "    selection-background-color: #131C26;\n"
                           "    selection-color: #fff;\n"
                           "font-size: 8pt;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QTableCornerButton::section,\n"
                           "QTableWidget QHeaderView,\n"
                           "QTableWidget QHeaderView::section\n"
                           "{\n"
                           "    color: #131C26;\n"
                           "font-size: 8pt;\n"
                           "    background: rgba(255,255,255,1);\n"
                           "}\n"
                           "\n"
                           "QHeaderView::section {\n"
                           "    border-style: none;\n"
                           "\n"
                           "}\n"
                           "\n"
                           "QTableWidget QTableCornerButton::section {\n"
                           "    /* background: #272343; */\n"
                           "    border-style: none;\n"
                           "    border-bottom: 1px solid #ddd;\n"
                           "    border-right: 1px solid #ddd;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QHeaderView {\n"
                           "    font-weight: bold;\n"
                           "border-radius: 10px;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QHeaderView::section:selected {\n"
                           "    background: #fff;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QHeaderView::section:checked {\n"
                           "    background: transparent;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QHeaderView::section:hover:!selected {\n"
                           "    background: #fff;\n"
                           "}\n"
                           "\n"
                           "QTableWidget QHeaderView::section::item {\n"
                           "    padding: 0 4px;\n"
                           "}\n"
                           "\n"
                            "QHeaderView::section:vertical::item {\n"
                            "    border-bottom: 1px solid #ddd;\n"
                            "}\n"
                            "\n"
                            "QHeaderView::section:horizontal::item {\n"
                            "    border-right: 1px solid #ddd;\n"
                            "}\n"
                            "\n"
                            "QTableWidget QHeaderView::item {\n"
                            "    color: #131C26;\n"
                            "    font-weight: bold;\n"
                            "    text-align: right;\n"
                            "    padding: 0 4px;\n"
                            "}\n"
                            "\n"
                            "QTableWidget QHeaderView::item:hover:!selected {\n"
                            "    background: rgba(250,250,250,0.8);\n"
                            "}\n"
                            "\n"
                            "QTableWidget QHeaderView::item:active {\n"
                            "    background: rgba(250,250,250,0.8);\n"
                            "}\n"
                            "\n"
                            "QTableWidget QHeaderView::item:active {\n"
                            "    background: rgba(250,250,250,0.8);\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item {\n"
                            "    border-right: 1px solid #ddd;\n"
                            "    border-bottom: 1px solid #ddd;\n"
                            "    color: #272343;\n"
                            "    background: rgba(250,250,250,0.9);\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:hover {\n"
                            "    background: rgba(250,250,250,1);\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:selected:!active {\n"
                            "    color: #fff;\n"
                            "    background: rgba(250,250,250,1);\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:focus {\n"
                            "    color: #1B4060;\n"
                            "    background-color: #fff;\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:active {\n"
                            "    color: #1B4060;\n"
                            "    background-color: #fff;\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:selected:active {\n"
                            "    color: #fff;\n"
                            "    background-color: #1B4060;\n"
                            "}\n"
                            "\n"
                            "QTableWidget::item:selected {\n"
                            "    color: #fff;\n"
                            "    background-color: #1B4060;\n"
                            "}\n"
                            "\n"
                            "")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Raised)
        self.setShowGrid(False)
        self.setObjectName("tableWidget")
        self.cellClicked.connect(self.on_click)
        self.cellDoubleClicked.connect(self.on_dbl_click)

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

    def on_click(self):
        modifiers = QtGui.QGuiApplication.queryKeyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            selected = self.selectedItems()
            for item in selected:
                self.goto_reference.emit(item.column_name, str(item.record[item.column_name]))
                return

    def on_dbl_click(self):
        selected = self.selectedItems()
        for item in selected:
            self.edit_cell.emit(item.column_name, item.record)
            return

    def updateRecord(self, record, newValue: str):
        selected = self.selectedItems()
        for item in selected:
            item.record[item.column_name] = newValue
            item.setText(item.text())


class TableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, column_name: str, idx: int, record: Dict['str', 'str']):
        self.column_name = column_name
        self.record = record
        text = self.text()
        super().__init__(text)

        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def text(self) -> str:
        if self.record[self.column_name] is None:
            return ''
        return str(self.record[self.column_name])
