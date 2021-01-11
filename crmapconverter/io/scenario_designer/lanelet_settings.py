from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking


class LaneletSettings(QDialog):
    def __init__(self):
        super().__init__()
        self.lanelet_length = 50
        self.lanelet_width = 20
        self.setadjacent = False
        self.setPredecessor = False
        self.setWindowTitle("Lanelet settings")
        self.setGeometry(100, 100, 500, 300)
        self.direction_bool = False


        self.direction = QComboBox()
        self.direction.addItems(["forwards", "backwards"])

        self.length = QLineEdit()
        self.length.setValidator(QIntValidator())
        self.length.setMaxLength(4)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.number_vertices = QLineEdit()
        self.number_vertices.setValidator(QIntValidator())
        self.number_vertices.setMaxLength(2)
        self.number_vertices.setAlignment(Qt.AlignRight)

        self.adjacentLanelet = QRadioButton()
        self.adjacentLanelet.setText("set ajacent lanelet")
        self.adjacentLanelet.toggled.connect(self.adjacent_button)

        self.Predecessor = QRadioButton()
        self.Predecessor.setText("set predecessor automatically")
        self.Predecessor.toggled.connect(self.predecessor_button)

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)

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

        layout.addRow("Lanelet direction", self.direction)
        layout.addRow("Lanelet length", self.length)
        layout.addRow("Lanelet width", self.width)
        #layout.addWidget(self.adjacentLanelet)
        layout.addRow("Number of vertices", self.number_vertices)
        layout.addRow("X position", self.posX)
        layout.addRow("Y position", self.posY)
        layout.addWidget(self.pred)

        #layout.addWidget(self.Predecessor)

        layout.addRow("Lanelet type", self.lanelet_type)
        layout.addRow("Roaduser", self.roaduser)
        layout.addRow("Linemarking right", self.line_marking_right)
        layout.addRow("Linemarking left", self.line_marking_left)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.set_default)

        self.setLayout(layout)

    def predecessor_button(self):
        if self.pred.isChecked():
            self.setPredecessor = True
        else:
            self.setPredecessor = False

    def adjacent_button(self):
        if self.adjacentLanelet.isChecked() == True:
            self.setadjacent = True
        else:
            self.setadjacent = False

    def apply_button_click(self):
        if self.length.text():
            self.lanelet_length = int(self.length.text())
        else:
            self.lanelet_length = 50
        if self.width.text():
            self.lanelet_width = int(self.width.text())
        else:
            self.lanelet_width = 12
        self.setPredecessor = self.pred.isChecked()
        self.getLaneletType()
        if self.direction.currentText() == "backwards":
            self.direction_bool = True
        else:
            self.direction_bool = False

        self.close()

    def set_default_click(self):
        self.length.clear()
        self.width.clear()
        self.length.insert("50")
        self.width.insert("20")
        self.setadjacent = False
        self.adjacentLanelet.setChecked(False)
        self.pred.setChecked(True)
        self.setPredecessor = True
        self.posX.insert("0")
        self.posY.insert("0")
        self.number_vertices.insert("20")

    def showsettings(self):
        self.show()

    def getLanletLength(self):
        return self.lanelet_length

    def getLaneletWidth(self):
        return self.lanelet_width

    def getAdjacentLanelet(self):
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

    def getDirection(self):
        return self.direction_bool

    def getNumVertices(self):
        if self.number_vertices.text():
            return int(self.number_vertices.text())
        else:
            return 20

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