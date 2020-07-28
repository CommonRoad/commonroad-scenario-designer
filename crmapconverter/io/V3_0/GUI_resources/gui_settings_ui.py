# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(400, 150)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 956, 1182))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.label_autofocus = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_autofocus.setObjectName("label_autofocus")
        self.gridLayout_2.addWidget(self.label_autofocus, 0, 0, 1, 1)
        
        self.chk_autofocus = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_autofocus.setText("")
        self.chk_autofocus.setObjectName("chk_autofocus")
        self.gridLayout_2.addWidget(self.chk_autofocus, 0, 2, 1, 1)
        
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_3.setObjectName("gridLayout_3")
        # self.botton_restore_defaults = QtWidgets.QPushButton(self.frame)
        # self.botton_restore_defaults.setObjectName("botton_restore_defaults")
        # self.gridLayout_3.addWidget(self.botton_restore_defaults, 0, 0, 1, 1)
        self.botton_close = QtWidgets.QPushButton(self.frame)
        self.botton_close.setObjectName("botton_close")
        self.gridLayout_3.addWidget(self.botton_close, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 990, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "GUI Settings"))

        self.label_autofocus.setText(_translate("MainWindow", "autofocus"))
        self.label_autofocus.setToolTip(_translate("MainWindow", 
            "activate zoom reset when selecting an item from the list"))
        
        # self.botton_restore_defaults.setText(_translate("MainWindow", "Restore Defaults"))
        self.botton_close.setText(_translate("MainWindow", "Appy and close"))

