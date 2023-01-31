# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets, QtGui
import crdesigner.ui.gui.mwindow.service_layer.gui_resources.gui_settings_ui as gui
import crdesigner.ui.gui.mwindow.service_layer.gui_resources.sumo_settings_ui as sumo
import crdesigner.ui.gui.mwindow.service_layer.gui_resources.osm_settings_ui as osm

HEIGHT = 25
COLUMNS = 2
WIDTHF = 280
WIDTHM = 390
FACTOR = 0.7

class Ui_Settings(object):
    def setupUi(self, Settings, mwindow):
        self.mwindow = mwindow
        self.settings = Settings
        self.settings.setObjectName("Settings")
        self.settings.resize(int(1820 * FACTOR), int(1150 * FACTOR))
        self.centralwidget = QtWidgets.QWidget(Settings)
        self.centralwidget.setObjectName("centralwidget")
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.centralwidget.setObjectName("centralLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.centralLayout.addWidget(self.tabWidget)
        self.tabBar = QtWidgets.QTabBar()
        self.tabWidget.setTabBar(self.tabBar)


        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frameLayout = QtWidgets.QHBoxLayout(self.frame)
        self.frame.setLayout(self.frameLayout)
        self.frame.setMaximumSize(int(1700*FACTOR), 43)
        self.frame.setMinimumSize(int(1700*FACTOR), 43)

        self.button_cancel = QtWidgets.QPushButton(self.frame)
        self.button_cancel.setObjectName("button_cancel")
        self.button_cancel.setMaximumSize(150, 40)

        self.button_ok = QtWidgets.QPushButton(self.frame)
        self.button_ok.setObjectName("button_ok")
        self.button_ok.setMaximumSize(150, 40)

        # button set to default
        self.button_settodefault = QtWidgets.QPushButton(self.frame)
        self.button_settodefault.setObjectName("button_set_to_default")
        self.button_settodefault.setMaximumSize(150, 40)

        self.space = QtWidgets.QLabel()
        self.frameLayout.addWidget(self.space)
        self.frameLayout.addWidget(self.button_cancel)
        self.frameLayout.addWidget(self.button_ok)
        self.frameLayout.addWidget(self.button_settodefault)

        self.centralLayout.addWidget(self.frame)

        Settings.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Settings)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 990, 23))
        self.menubar.setObjectName("menubar")
        Settings.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Settings)
        self.statusbar.setObjectName("statusbar")
        Settings.setStatusBar(self.statusbar)

        #adding different setting tabs
        self.gui_settings = gui.UIGUISettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.gui_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.gui_settings.scrollArea, "GUI")

        self.sumo_settings = sumo.Ui_SUMOSettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.sumo_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.sumo_settings.scrollArea, "SUMO")

        self.osm_settings = osm.Ui_OSMSettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.osm_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.osm_settings.scrollArea, "OSM")

        self.update_window()
        self.retranslateUi(Settings)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Settings"))
        self.button_ok.setText(_translate("MainWindow", "Ok"))
        self.button_cancel.setText(_translate("MainWindow", "Cancel"))
        # set to default
        self.button_settodefault.setText(_translate("MainWindow", "Set to default"))

        self.gui_settings.retranslateUi(self.tabWidget)
        self.sumo_settings.retranslateUi(self.tabWidget)
        self.osm_settings.retranslateUi(self.tabWidget)

    def update_window(self):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(self.mwindow.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(self.mwindow.colorscheme().second_background))
        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.mwindow.colorscheme().background))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.mwindow.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(self.mwindow.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(self.mwindow.colorscheme().color))
        p.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(self.mwindow.colorscheme().background))

        self.settings.setPalette(p)

        p.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(self.mwindow.colorscheme().highlight))
        p.setColor(QtGui.QPalette.ColorRole.Foreground, QtGui.QColor(self.mwindow.colorscheme().highlight_text))
        p.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(self.mwindow.colorscheme().highlight_text))
        self.tabBar.setPalette(p)
        self.button_ok.setPalette(p)
        self.button_cancel.setPalette(p)
        # set_to_default_button
        self.button_settodefault.setPalette(p)



