import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton)
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt


class CurveSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.curve_radius = 50
        self.curve_width = 20
        self.number_vertices = 10
        self.curve_angle = 90
        self.setadjacent = False
        self.setPredecessor = False
        self.setWindowTitle("Curve settings")
        self.setGeometry(100, 100, 500, 300)

        self.radius = QLineEdit()
        self.radius.setValidator(QIntValidator())
        self.radius.setMaxLength(4)
        self.radius.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.angle = QLineEdit()
        self.angle.setValidator(QIntValidator())
        self.angle.setMaxLength(3)
        self.angle.setAlignment(Qt.AlignRight)

        self.vertices = QLineEdit()
        self.vertices.setValidator(QIntValidator())
        self.vertices.setMaxLength(2)
        self.vertices.setAlignment(Qt.AlignRight)

        self.adjacentCurve = QRadioButton()
        self.adjacentCurve.setText("set ajacent Curve")
        self.adjacentCurve.toggled.connect(self.adjacent_button)

        self.Predecessor = QRadioButton()
        self.Predecessor.setText("set predecessor automatically")
        self.Predecessor.toggled.connect(self.predecessor_button)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        self.set_default = QPushButton()
        self.set_default.setText("set default")
        self.set_default.clicked.connect(self.set_default_click)

        layout = QFormLayout()
        layout.addRow("Curve radius", self.radius)
        layout.addRow("Curve width ", self.width)
        layout.addRow("Curve angle ", self.angle)
        layout.addRow("Number of vertices ", self.vertices)

        layout.addWidget(self.adjacentCurve)
        layout.addWidget(self.Predecessor)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)

    def predecessor_button(self):
        self.setPredecessor = self.Predecessor.isChecked()

    def adjacent_button(self):
        if self.adjacentCurve.isChecked() == True:
            self.setadjacent = True
        else:
            self.setadjacent = False

    def apply_button_click(self):
        if self.radius.text():
            self.curve_radius = int(self.radius.text())
        else:
            self.curve_radius = 50
        if self.width.text():
            self.curve_width = int(self.width.text())
        else:
            self.curve_width = 12
        if self.angle.text():
            self.curve_angle = int(self.angle.text())
        else:
            self.curve_angle = 90
        self.close()

    def set_default_click(self):
        self.radius.clear()
        self.width.clear()
        self.angle.clear()
        self.vertices.clear()
        self.radius.insert("50")
        self.width.insert("20")
        self.angle.insert("90")
        self.vertices.insert("10")
        self.setadjacent = False
        self.adjacentCurve.setChecked(False)
        self.Predecessor.setChecked(True)
        self.setPredecessor = True

    def showsettings(self):
        self.show()

    def getCurveRadius(self):
        return self.curve_radius

    def getCurveWidth(self):
        return self.curve_width

    def getNumberVertices(self):
        return self.number_vertices

    #convert degree to rad
    def getAngle(self):
        return np.deg2rad(self.curve_angle)

    def getAdjacentCurve(self):
        return self.setadjacent

    def getPredecessor(self):
        return self.setPredecessor

