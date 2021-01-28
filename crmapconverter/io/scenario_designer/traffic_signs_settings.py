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
        self.selected_country = None


        self.country = QComboBox()
        self.enumlist = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(self.enumlist)

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
        if self.selected_country != None:
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

    def getSignNumber(self):
        name = self.sign_list.currentText()
        member = TrafficSignIDGermany.name
        number = member.value
        print(number)
        return

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

class TrafficLightSelection(QDialog):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("Traffic light")
        self.setGeometry(100, 100, 500, 300)
        self.isactive = True
        self.timeRed = 60
        self.timeRedYellow = 10
        self.timeGreen = 60
        self.timeYellow = 10
        self.offset = 0
        self.X = 0
        self.Y = 0
        self.id = None

        self.direction = QComboBox()
        enumlist = [e.name for e in TrafficLightDirection]
        self.direction.addItems(enumlist)
        self.direction.setCurrentIndex(len(enumlist)-1)
        #self.sign_list.addItem(QIcon(":/101.png"), "TEST")

        self.lanelet_id = QLineEdit()
        self.lanelet_id.setValidator(QIntValidator())
        self.lanelet_id.setMaxLength(3)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.further_lanelet_id = QPushButton("add further lanelet IDs")
        self.further_lanelet_id.clicked.connect(self.addButton)
        self.num = 2

        self.time_offset = QLineEdit()
        self.time_offset.setValidator(QIntValidator())
        self.time_offset.setMaxLength(3)
        self.time_offset.setAlignment(Qt.AlignRight)
        self.time_offset.insert(str(self.offset))

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)
        self.posX.insert(str(self.X))

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)
        self.posY.insert(str(self.Y))

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)


        self.active = QRadioButton()
        self.active.toggled.connect(self.active_button)
        self.active.setChecked(True)

        self.red = QLineEdit()
        self.red.setValidator(QIntValidator())
        self.red.setMaxLength(3)
        self.red.setAlignment(Qt.AlignRight)
        self.red.insert(str(self.timeRed))

        self.red_yellow = QLineEdit()
        self.red_yellow.setValidator(QIntValidator())
        self.red_yellow.setMaxLength(3)
        self.red_yellow.setAlignment(Qt.AlignRight)
        self.red_yellow.insert(str(self.timeRedYellow))

        self.green = QLineEdit()
        self.green.setValidator(QIntValidator())
        self.green.setMaxLength(3)
        self.green.setAlignment(Qt.AlignRight)
        self.green.insert(str(self.timeGreen))

        self.yellow = QLineEdit()
        self.yellow.setValidator(QIntValidator())
        self.yellow.setMaxLength(3)
        self.yellow.setAlignment(Qt.AlignRight)
        self.yellow.insert(str(self.timeYellow))

        layout = QFormLayout()
        layout.addRow("corresponding lanelet ID", self.lanelet_id)
        layout.addRow("select direction", self.direction)
        layout.addRow("time offset", self.time_offset)
        layout.addRow("active", self.active)
        layout.addRow("X position", self.posX)
        layout.addRow("Y position", self.posY)
        layout.addRow("time red", self.red)
        layout.addRow("time red-yellow", self.red_yellow)
        layout.addRow("time green", self.green)
        layout.addRow("time yellow", self.yellow)



        #layout.addRow("TODO: cycle options", test=2)

        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def addButton(self):
        return

    def active_button(self):
        if self.active.isCheckable() == True:
            self.isactive = True
        else:
            self.isactive = False

    def get_isactive(self):
        return self.isactive

    def apply_button_click(self):
        if self.posX.text():
            self.X = int(self.posX.text())
        if self.posY.text():
            self.Y = int(self.posY.text())
        if self.time_offset.text():
            self.offset = int(self.time_offset.text())
        if self.red.text():
            self.timeRed = int(self.red.text())
        if self.yellow.text():
            self.timeYellow = int(self.yellow.text())
        if self.red_yellow.text():
            self.timeRedYellow = int(self.red_yellow.text())
        if self.green.text():
            self.timeGreen = int(self.green.text())
        self.close()

    def getDirection(self):
        return self.direction.currentText()

    def getTimeOffset(self):
        return self.offset

    def getLaneletID(self):
        if self.lanelet_id.text():
            return int(self.lanelet_id.text())
        else:
            return None

    def getPosX(self):
        return self.X

    def getPosY(self):
        return self.Y

    def getRed(self):
        return self.timeRed

    def getRed_Yellow(self):
        return self.timeRedYellow

    def getGreen(self):
        return self.timeGreen

    def getYellow(self):
        return self.timeYellow


class DeleteTrafficElement(QDialog):
    def __init__(self):
        super().__init__()

        self.id = 0

        self.element_id = QLineEdit()
        self.element_id.setValidator(QIntValidator())
        self.element_id.setMaxLength(3)
        self.element_id.setAlignment(Qt.AlignRight)

        self.lanelet_id = QLineEdit()
        self.lanelet_id.setValidator(QIntValidator())
        self.lanelet_id.setMaxLength(3)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addRow("Lanelet ID", self.lanelet_id)
        layout.addRow("Traffic Element ID", self.element_id)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def apply_button_click(self):
        if self.element_id.text():
            self.id = int(self.element_id.text())
        self.close()

    def getTrafficElement(self):
        return self.id

    def getLaneletId(self):
        if self.lanelet_id.text():
            return int(self.lanelet_id.text())
        else:
            return None

class EditTrafficLight(QDialog):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("edit Traffic light")
        self.setGeometry(100, 100, 500, 300)
        self.isactive = True
        self.timeRed = 60
        self.timeRedYellow = 10
        self.timeGreen = 60
        self.timeYellow = 10
        self.offset = 0
        self.X = 0
        self.Y = 0
        self.id = None

        self.direction = QComboBox()
        enumlist = [e.name for e in TrafficLightDirection]
        self.direction.addItems(enumlist)
        self.direction.setCurrentIndex(len(enumlist)-1)
        #self.sign_list.addItem(QIcon(":/101.png"), "TEST")

        self.lanelet_id = QLineEdit()
        self.lanelet_id.setValidator(QIntValidator())
        self.lanelet_id.setMaxLength(3)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.further_lanelet_id = QPushButton("add further lanelet IDs")
        self.further_lanelet_id.clicked.connect(self.addButton)
        self.num = 2

        self.time_offset = QLineEdit()
        self.time_offset.setValidator(QIntValidator())
        self.time_offset.setMaxLength(3)
        self.time_offset.setAlignment(Qt.AlignRight)
        self.time_offset.insert(str(self.offset))

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)
        self.posX.insert(str(self.X))

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)
        self.posY.insert(str(self.Y))

        self.apply_button = QPushButton()
        self.apply_button.setText("edit")
        self.apply_button.clicked.connect(self.apply_button_click)


        self.active = QRadioButton()
        self.active.toggled.connect(self.active_button)
        self.active.setChecked(True)

        self.red = QLineEdit()
        self.red.setValidator(QIntValidator())
        self.red.setMaxLength(3)
        self.red.setAlignment(Qt.AlignRight)
        self.red.insert(str(self.timeRed))

        self.red_yellow = QLineEdit()
        self.red_yellow.setValidator(QIntValidator())
        self.red_yellow.setMaxLength(3)
        self.red_yellow.setAlignment(Qt.AlignRight)
        self.red_yellow.insert(str(self.timeRedYellow))

        self.green = QLineEdit()
        self.green.setValidator(QIntValidator())
        self.green.setMaxLength(3)
        self.green.setAlignment(Qt.AlignRight)
        self.green.insert(str(self.timeGreen))

        self.yellow = QLineEdit()
        self.yellow.setValidator(QIntValidator())
        self.yellow.setMaxLength(3)
        self.yellow.setAlignment(Qt.AlignRight)
        self.yellow.insert(str(self.timeYellow))

        layout = QFormLayout()
        layout.addRow("traffic light id", self.lanelet_id)
        layout.addRow("select direction", self.direction)
        layout.addRow("time offset", self.time_offset)
        layout.addRow("active", self.active)
        layout.addRow("X position", self.posX)
        layout.addRow("Y position", self.posY)
        layout.addRow("time red", self.red)
        layout.addRow("time red-yellow", self.red_yellow)
        layout.addRow("time green", self.green)
        layout.addRow("time yellow", self.yellow)



        #layout.addRow("TODO: cycle options", test=2)

        layout.addWidget(self.apply_button)

        self.setLayout(layout)

    def addButton(self):
        return

    def active_button(self):
        if self.active.isCheckable() == True:
            self.isactive = True
        else:
            self.isactive = False

    def get_isactive(self):
        return self.isactive

    def apply_button_click(self):
        if self.posX.text():
            self.X = int(self.posX.text())
        if self.posY.text():
            self.Y = int(self.posY.text())
        if self.time_offset.text():
            self.offset = int(self.time_offset.text())
        if self.red.text():
            self.timeRed = int(self.red.text())
        if self.yellow.text():
            self.timeYellow = int(self.yellow.text())
        if self.red_yellow.text():
            self.timeRedYellow = int(self.red_yellow.text())
        if self.green.text():
            self.timeGreen = int(self.green.text())
        self.close()

    def getDirection(self):
        return self.direction.currentText()

    def getTimeOffset(self):
        return self.offset

    def getLaneletID(self):
        if self.lanelet_id.text():
            return int(self.lanelet_id.text())
        else:
            return None

    def getPosX(self):
        return self.X

    def getPosY(self):
        return self.Y

    def getRed(self):
        return self.timeRed

    def getRed_Yellow(self):
        return self.timeRedYellow

    def getGreen(self):
        return self.timeGreen

    def getYellow(self):
        return self.timeYellow



