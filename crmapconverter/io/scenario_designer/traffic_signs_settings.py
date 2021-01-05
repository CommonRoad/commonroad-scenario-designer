from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking
from commonroad.scenario.traffic_sign import *
from commonroad.visualization.traffic_signs.TrafficSignIDGermany import *


class TrafficSignsSettings(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Traffic signs settings")
        self.setGeometry(100, 100, 300, 100)


        self.country = QComboBox()
        enumlist = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(enumlist)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)


        layout = QFormLayout()
        layout.addRow("select country", self.country)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def apply_button_click(self):
        self.selected_country = self.country.currentText()
        self.close()

    def getCountry(self):
        if self.selected_country:
            return self.selected_country
        else:
            return self.country.currentText()

    def showsettings(self):
        self.show()


class TrafficSignsSelection(QDialog):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("Traffic signs")
        self.setGeometry(100, 100, 500, 300)

        self.sign_list = QComboBox()
        enumlist = [e.value for e in TrafficSignIDGermany]
        self.sign_list.addItems(enumlist)
        #self.sign_list.addItem(QIcon(":/101.png"), "TEST")

        self.lanelet_id = QLineEdit()
        self.lanelet_id.setValidator(QIntValidator())
        self.lanelet_id.setMaxLength(3)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.additionalvalue = QLineEdit()
        self.additionalvalue.setValidator(QIntValidator())
        self.additionalvalue.setMaxLength(3)
        self.additionalvalue.setAlignment(Qt.AlignRight)

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)


        layout = QFormLayout()
        layout.addRow("select sign", self.sign_list)
        layout.addRow("select laneletID", self.lanelet_id)
        layout.addRow("speed limit", self.additionalvalue)
        layout.addRow("X position", self.posX)
        layout.addRow("Y position", self.posY)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def apply_button_click(self):
        self.close()

    def getSign(self):
        return self.sign_list.currentText()

    def getLaneletID(self):
        if self.lanelet_id.text():
            return int(self.lanelet_id.text())

    def getAdditionalValues(self):
        if self.additionalvalue.text():
            return self.additionalvalue.text()

    def getPosX(self):
        if self.posX.text():
            return int(self.posX.text())
        else:
            return 0

    def getPosY(self):
        if self.posY.text():
            return int(self.posY.text())
        else:
            return 0