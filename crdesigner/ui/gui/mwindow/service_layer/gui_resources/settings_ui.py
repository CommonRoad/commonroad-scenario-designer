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
WIDTHM = 360
FACTOR = 0.65

class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(1750 * FACTOR, 1100 * FACTOR)
        self.centralwidget = QtWidgets.QWidget(Settings)
        self.centralwidget.setObjectName("centralwidget")
        self.centralLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.centralwidget.setObjectName("centralLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.centralLayout.addWidget(self.tabWidget)

        #color scheme
        #Settings.setStyleSheet('background-color:rgb(50,50,50); color:rgb(250,250,250);font-size: 13pt')

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

        self.space = QtWidgets.QLabel()
        self.frameLayout.addWidget(self.space)
        self.frameLayout.addWidget(self.button_cancel)
        self.frameLayout.addWidget(self.button_ok)
        
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
        self.gui_settings = gui.Ui_GUISettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.gui_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.gui_settings.scrollArea, "GUI")

        self.sumo_settings = sumo.Ui_SUMOSettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.sumo_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.sumo_settings.scrollArea, "SUMO")

        self.osm_settings = osm.Ui_OSMSettings(HEIGHT, COLUMNS, WIDTHF, WIDTHM, FACTOR)
        self.osm_settings.setupUi(self.tabWidget)
        self.tabWidget.addTab(self.osm_settings.scrollArea, "OSM")

        self.retranslateUi(Settings)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Settings"))
        self.button_ok.setText(_translate("MainWindow", "Ok"))
        self.button_cancel.setText(_translate("MainWindow", "Cancel"))

        self.gui_settings.retranslateUi(self.tabWidget)
        self.sumo_settings.retranslateUi(self.tabWidget)
        self.osm_settings.retranslateUi(self.tabWidget)

