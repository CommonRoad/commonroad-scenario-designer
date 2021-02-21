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

        self.close()

    def isAdjacentSideLeft(self):
        return self.adjleft

    def isForwards(self):
        return self.forwards_bool

    def getLaneletId(self):
        if self.lanelet_id.text():
            return int(self.lanelet_id.text())
        else:
            return 0


class ConnectSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connect Lanelets")
        self.setGeometry(100, 100, 500, 300)

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
        self.close()

    def getPredecessor(self):
        if self.predecessor.text():
            return int(self.predecessor.text())
        else:
            return -1

    def getSuccessor(self):
        if self.successor.text():
            return int(self.successor.text())
        else:
            return -1

class FitSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fit lanelets")
        self.setGeometry(100, 100, 500, 300)

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
        self.close()


    def getPredecessor(self):
        if self.predecessor.text():
            return int(self.predecessor.text())
        else:
            return -1

    def getSuccessor(self):
        if self.successor.text():
            return int(self.successor.text())
        else:
            return -1


class RemoveSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remove lanelet")
        self.setGeometry(100, 100, 500, 300)

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
        self.close()

    def getLaneletId(self):
        if self.lanelet.text():
            return int(self.lanelet.text())
        else:
            return 0