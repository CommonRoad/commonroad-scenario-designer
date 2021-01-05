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
        self.lanelet_id.setMaxLength(2)
        self.lanelet_id.setAlignment(Qt.AlignRight)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        layout = QFormLayout()
        layout.addRow("Lanelet direction", self.direction)
        layout.addRow("Adjacet position", self.position)
        layout.addRow("Lanelet ID", self.lanelet_id)
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
