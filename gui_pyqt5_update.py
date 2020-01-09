# -*- coding: utf-8 -*-

# This file is a partial update of the previous GUI using PyQt5. It is not operational
# and was written as an intermediate format for the conversion into Tkinter format

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(960, 902)
        palette = QtGui.QPalette()



        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(30, 170, 200))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        MainWindow.setPalette(palette)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/tum_logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setAutoFillBackground(True)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(0, -20, 960, 210))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/head.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        #Button1
        self.but1 = QtWidgets.QLabel(self.centralwidget)
        self.but1.setGeometry(QtCore.QRect(35, 355, 235, 235))
        self.but1.setPixmap(QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/drawable-xxxhdpi/Groupe 1.png"))
        self.but1.setScaledContents(True)
        self.but1.setWordWrap(True)
        self.but1.setObjectName("but1")

        # Button2
        self.but2 = QtWidgets.QLabel(self.centralwidget)
        self.but2.setGeometry(QtCore.QRect(349, 355, 235, 235))
        self.but2.setPixmap(
            QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/drawable-xxxhdpi/Groupe 2.png"))
        self.but2.setScaledContents(True)
        self.but2.setWordWrap(True)
        self.but2.setObjectName("but2")

        # Button3
        self.but3 = QtWidgets.QLabel(self.centralwidget)
        self.but3.setGeometry(QtCore.QRect(623, 355, 300, 235))
        self.but3.setPixmap(
            QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/drawable-xxxhdpi/Groupe 3.png"))
        self.but3.setScaledContents(True)
        self.but3.setWordWrap(True)
        self.but3.setObjectName("but3")
        #self.but3.clicked.connect(self.setupUi(self,MainWindow))

        # Button4
        self.but4 = QtWidgets.QLabel(self.centralwidget)
        self.but4.setGeometry(QtCore.QRect(190, 635, 235, 235))
        self.but4.setPixmap(
            QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/drawable-xxxhdpi/Groupe 4.png"))
        self.but4.setScaledContents(True)
        self.but4.setWordWrap(True)
        self.but4.setObjectName("but4")

        # Button5
        self.but5 = QtWidgets.QLabel(self.centralwidget)
        self.but5.setGeometry(QtCore.QRect(531, 635, 235, 235))
        self.but5.setPixmap(
            QtGui.QPixmap("C:/Users/ryanz/Desktop/Autonomous driving/design/drawable-xxxhdpi/Groupe 5.png"))
        self.but5.setScaledContents(True)
        self.but5.setWordWrap(True)
        self.but5.setObjectName("but5")

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 51, 89))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Background, brush)

        MainWindow.setPalette(palette)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Common Road Converter"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

