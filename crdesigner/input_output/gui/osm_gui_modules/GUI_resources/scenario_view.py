# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scenario_view.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(418, 488)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.plot_groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.plot_groupBox.setMinimumSize(QtCore.QSize(400, 400))
        self.plot_groupBox.setTitle("")
        self.plot_groupBox.setObjectName("plot_groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.plot_groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.plot_frame = QtWidgets.QVBoxLayout()
        self.plot_frame.setObjectName("plot_frame")
        self.gridLayout_2.addLayout(self.plot_frame, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.plot_groupBox, 0, 0, 1, 1)
        self.b_back = QtWidgets.QPushButton(self.centralwidget)
        self.b_back.setObjectName("b_back")
        self.gridLayout.addWidget(self.b_back, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 418, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Scenario Viewer"))
        self.b_back.setToolTip(_translate("MainWindow", "Go back to start menu"))
        self.b_back.setText(_translate("MainWindow", "Back"))

