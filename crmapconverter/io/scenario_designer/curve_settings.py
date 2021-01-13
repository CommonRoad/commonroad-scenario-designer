import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking


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
        self.curve_direction_bool = False

        self.curve_direction = QComboBox()
        self.curve_direction.addItems(["right curve", "left curve"])


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

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)

        self.adjacentCurve = QRadioButton()
        self.adjacentCurve.setText("set ajacent Curve")
        self.adjacentCurve.toggled.connect(self.adjacent_button)

        self.Predecessor = QRadioButton()
        self.Predecessor.setText("set predecessor automatically")
        self.Predecessor.toggled.connect(self.predecessor_button)

        self.pred = QCheckBox("set predecessor automatically")
        self.pred.stateChanged.connect(self.predecessor_button)

        self.lanelet_type = QComboBox()
        enumlist = [e.value for e in LaneletType]
        self.lanelet_type.addItems(enumlist)

        self.roaduser = QComboBox()
        roaduser_list = [r.value for r in RoadUser]
        self.roaduser.addItems(roaduser_list)

        self.line_marking_right = QComboBox()
        line_marking_right_list = [right.value for right in LineMarking]
        self.line_marking_right.addItems(line_marking_right_list)

        self.line_marking_left = QComboBox()
        line_marking_left_list = [left.value for left in LineMarking]
        self.line_marking_left.addItems(line_marking_left_list)

        self.apply_button = QPushButton()
        self.apply_button.setText("apply")
        self.apply_button.clicked.connect(self.apply_button_click)

        self.set_default = QPushButton()
        self.set_default.setText("set default")
        self.set_default.clicked.connect(self.set_default_click)

        layout = QFormLayout()
        layout.addRow("Curve direction", self.curve_direction)
        layout.addRow("Curve radius", self.radius)
        layout.addRow("Curve width", self.width)
        layout.addRow("Curve angle", self.angle)
        layout.addRow("Number of vertices", self.vertices)
        layout.addRow("X position", self.posX)
        layout.addRow("Y position", self.posY)
        #layout.addWidget(self.adjacentCurve)
        layout.addWidget(self.pred)
        layout.addRow("Lanelet type", self.lanelet_type)
        layout.addRow("Roaduser", self.roaduser)
        layout.addRow("Linemarking right", self.line_marking_right)
        layout.addRow("Linemarking left", self.line_marking_left)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)

    def predecessor_button(self):
        self.setPredecessor = self.pred.isChecked()

    def adjacent_button(self):
        if self.adjacentCurve.isChecked() == True:
            self.setadjacent = True
        else:
            self.setadjacent = False

    def apply_button_click(self):
        if self.vertices.text():
            self.number_vertices = int(self.vertices.text())
        else:
            self.number_vertices = 10
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
        self.setPredecessor = self.pred.isChecked()


        #Left curves: set curve_direction_bool to false
        #Todo:
        if self.curve_direction.currentText() == "left curve":
            self.curve_direction_bool = True
        else:
            self.curve_direction_bool = False

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
        self.pred.setChecked(True)
        self.setPredecessor = True
        self.posX.insert("0")
        self.posY.insert("0")

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

    def getLaneletType(self):
        #print(self.lanelet_type.currentText())
        return self.lanelet_type.currentText()

    def getRoadUser(self):
        #print(self.roaduser.currentText())
        return self.roaduser.currentText()

    def getLineMarkingRight(self):
        return self.line_marking_right.currentText()

    def getLineMarkingLeft(self):
        return self.line_marking_left.currentText()

    def getCurveDirection(self):
        return self.curve_direction_bool

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