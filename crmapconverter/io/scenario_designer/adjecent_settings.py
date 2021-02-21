from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking


class AdjecentSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adjacent")
        self.setGeometry(100, 100, 500, 300)
        self.forwards_bool = True
        self.adjleft = False
        self.id = None

        self.direction = QComboBox()
        self.direction.addItems(["forwards", "backwards"])

        self.position = QComboBox()
        self.position.addItems(["right", "left"])

        self.lanelet_id = QLineEdit()
        self.lanelet_id.setValidator(QIntValidator())
        self.lanelet_id.setMaxLength(6)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(6)
        self.width.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addRow("Lanelet direction", self.direction)
        layout.addRow("Adjacet position", self.position)
        layout.addRow("Lanelet ID", self.lanelet_id)
        layout.addRow("Constant widht", self.width)
        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_button_click(self):

        if self.direction.currentText() == "backwards":
            self.forwards_bool = False
        else:
            self.forwards_bool = True

        if self.position.currentText() == "left":
            self.adjleft = True
        else:
            self.adjleft = False
        if self.lanelet_id.text():
            self.id = int(self.lanelet_id.text())

        self.close()

    def isAdjacentSideLeft(self):
        return self.adjleft

    def isForwards(self):
        return self.forwards_bool

    def getLaneletId(self):
        return self.id



class ConnectSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect Lanelets")
        self.setGeometry(100, 100, 500, 300)
        self.pred = -1
        self.succ = -1

        self.label = QLabel("Connect two laneletes with an connection lanelet")


        self.predecessor = QLineEdit()
        self.predecessor.setValidator(QIntValidator())
        self.predecessor.setMaxLength(2)
        self.predecessor.setAlignment(Qt.AlignRight)

        self.successor = QLineEdit()
        self.successor.setValidator(QIntValidator())
        self.successor.setMaxLength(2)
        self.successor.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addWidget(self.label)
        layout.addRow("Start Lanelet ID", self.predecessor)
        layout.addRow("Goal Lanelet ID", self.successor)

        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_button_click(self):
        if self.predecessor.text():
            self.pred = int(self.predecessor.text())
        if self.successor.text():
            self.succ = int(self.successor.text())
        self.close()

    def getPredecessor(self):
        return self.pred

    def getSuccessor(self):
        return self.succ

class FitSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fit lanelets")
        self.setGeometry(100, 100, 500, 300)
        self.pred = -1
        self.succ = -1

        self.label = QLabel("Fit two laneletes")

        self.predecessor = QLineEdit()
        self.predecessor.setValidator(QIntValidator())
        self.predecessor.setMaxLength(2)
        self.predecessor.setAlignment(Qt.AlignRight)

        self.successor = QLineEdit()
        self.successor.setValidator(QIntValidator())
        self.successor.setMaxLength(2)
        self.successor.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addWidget(self.label)
        layout.addRow("Predecessor Lanelet ID", self.predecessor)
        layout.addRow("Successor Lanelet ID", self.successor)
        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_button_click(self):
        if self.predecessor.text():
            self.pred = int(self.predecessor.text())
        if self.successor.text():
            self.succ = int(self.successor.text())

        self.close()


    def getPredecessor(self):
        return self.pred

    def getSuccessor(self):
        return self.succ


class RemoveSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remove lanelet")
        self.setGeometry(100, 100, 500, 300)
        self.id = None

        self.label = QLabel("Remove selected lanelet")

        self.lanelet = QLineEdit()
        self.lanelet.setValidator(QIntValidator())
        self.lanelet.setMaxLength(2)
        self.lanelet.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addWidget(self.label)
        layout.addRow("Remove Lanelet ID", self.lanelet)
        layout.addWidget(self.apply_button)
        self.setLayout(layout)

    def apply_button_click(self):
        if self.lanelet.text():
            self.id = int(self.lanelet.text())
        self.close()

    def getLaneletId(self):
        return self.id