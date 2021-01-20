from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator, QStandardItemModel
from PyQt5.QtCore import Qt
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking


class XCrossing(QDialog):
    def __init__(self):
        super().__init__()
        self.diameter = 80
        self.lanelet_width = 20
        self.setadjacent = False
        self.setPredecessor = False
        self.setWindowTitle("XCrossing settings")
        self.setGeometry(100, 100, 500, 300)


        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.diameter_crossing = QLineEdit()
        self.diameter_crossing.setValidator(QIntValidator())
        self.diameter_crossing.setMaxLength(4)
        self.diameter_crossing.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        self.set_default = QPushButton()
        self.set_default.setText("set default")
        self.set_default.clicked.connect(self.set_default_click)

        layout = QFormLayout()

        layout.addRow("Lanelet width", self.width)
        #layout.addWidget(self.adjacentLanelet)
        layout.addRow("Diameter Crossing", self.diameter_crossing)

        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)



    def apply_button_click(self):
        if self.width.text():
            self.lanelet_width = int(self.width.text())
        else:
            self.lanelet_width = 20

        if self.diameter_crossing.text():
            self.diameter = int(self.diameter_crossing.text())
        else:
            self.diameter = 80

        self.close()

    def set_default_click(self):
        self.diameter_crossing.clear()
        self.width.clear()
        self.diameter_crossing.insert("80")
        self.width.insert("20")



    def getWidth(self):
        return self.lanelet_width

    def getDiameter(self):
        return self.diameter


class TCrossing(QDialog):
    def __init__(self):
        super().__init__()
        self.diameter = 80
        self.lanelet_width = 20
        self.setadjacent = False
        self.setPredecessor = False
        self.setWindowTitle("TCrossing settings")
        self.setGeometry(100, 100, 500, 300)


        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.diameter_crossing = QLineEdit()
        self.diameter_crossing.setValidator(QIntValidator())
        self.diameter_crossing.setMaxLength(4)
        self.diameter_crossing.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        self.set_default = QPushButton()
        self.set_default.setText("set default")
        self.set_default.clicked.connect(self.set_default_click)

        layout = QFormLayout()

        layout.addRow("Lanelet width", self.width)
        #layout.addWidget(self.adjacentLanelet)
        layout.addRow("Diameter Crossing", self.diameter_crossing)

        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)



    def apply_button_click(self):
        if self.width.text():
            self.lanelet_width = int(self.width.text())
        else:
            self.lanelet_width = 20

        if self.diameter_crossing.text():
            self.diameter = int(self.diameter_crossing.text())
        else:
            self.diameter = 80

        self.close()

    def set_default_click(self):
        self.diameter_crossing.clear()
        self.width.clear()
        self.diameter_crossing.insert("80")
        self.width.insert("20")



    def getWidth(self):
        return self.lanelet_width

    def getDiameter(self):
        return self.diameter



class FitIntersection(QDialog):
    def __init__(self):
        super().__init__()
        self.predecessor = QLineEdit()
        self.predecessor.setValidator(QIntValidator())
        self.predecessor.setMaxLength(4)
        self.predecessor.setAlignment(Qt.AlignRight)

        self.successor = QLineEdit()
        self.successor.setValidator(QIntValidator())
        self.successor.setMaxLength(4)
        self.successor.setAlignment(Qt.AlignRight)

        self.intersectionID = QLineEdit()
        self.intersectionID.setValidator(QIntValidator())
        self.intersectionID.setMaxLength(4)
        self.intersectionID.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addRow("Predecessor ID", self.predecessor)
        layout.addRow("Sucessor ID", self.successor)
        layout.addRow("Intersection ID", self.intersectionID)

        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)