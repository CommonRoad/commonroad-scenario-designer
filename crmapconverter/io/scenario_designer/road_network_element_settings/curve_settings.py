import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator, QStandardItemModel
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
        self.posXval = 0
        self.posYval = 0
        self.right = "solid"
        self.left = "solid"

        self.curve_direction = QComboBox()
        self.curve_direction.addItems(["right curve", "left curve"])


        self.radius = QLineEdit()
        self.radius.setValidator(QIntValidator())
        self.radius.setMaxLength(4)
        self.radius.setAlignment(Qt.AlignRight)
        self.radius.clear()
        self.radius.insert(str(self.curve_radius))

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)
        self.width.clear()
        self.width.insert(str(self.curve_width))

        self.angle = QLineEdit()
        self.angle.setValidator(QIntValidator())
        self.angle.setMaxLength(3)
        self.angle.setAlignment(Qt.AlignRight)
        self.angle.clear()
        self.angle.insert(str(self.curve_angle))

        self.vertices = QLineEdit()
        self.vertices.setValidator(QIntValidator())
        self.vertices.setMaxLength(2)
        self.vertices.setAlignment(Qt.AlignRight)
        self.vertices.clear()
        self.vertices.insert((str(self.number_vertices)))

        self.posX = QLineEdit()
        self.posX.setValidator(QIntValidator())
        self.posX.setMaxLength(3)
        self.posX.setAlignment(Qt.AlignRight)
        self.posX.clear()
        self.posX.insert(str(self.posXval))

        self.posY = QLineEdit()
        self.posY.setValidator(QIntValidator())
        self.posY.setMaxLength(3)
        self.posY.setAlignment(Qt.AlignRight)
        self.posY.clear()
        self.posY.insert(str(self.posYval))

        self.adjacentCurve = QRadioButton()
        self.adjacentCurve.setText("set ajacent Curve")
        self.adjacentCurve.toggled.connect(self.adjacent_button)

        self.Predecessor = QRadioButton()
        self.Predecessor.setText("set predecessor automatically")
        self.Predecessor.toggled.connect(self.predecessor_button)

        self.pred = QCheckBox("set predecessor automatically")
        self.pred.stateChanged.connect(self.predecessor_button)

        self.type = CheckableComboBox()
        self.enumlist = [e.value for e in LaneletType]
        for i in range(0, len(self.enumlist) - 1):
            # adding item
            self.type.addItem(self.enumlist[i])
            item = self.type.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.roaduser_oneway = CheckableComboBox()
        self.roaduser_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(self.roaduser_oneway_list) - 1):
            self.roaduser_oneway.addItem(self.roaduser_oneway_list[i])
            item = self.roaduser_oneway.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.roaduser_bidirectional = CheckableComboBox()
        self.roaduser_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(self.roaduser_bidirectional_list) - 1):
            self.roaduser_bidirectional.addItem(self.roaduser_bidirectional_list[i])
            item = self.roaduser_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.line_marking_right = QComboBox()
        line_marking_right_list = [right.value for right in LineMarking]
        self.line_marking_right.addItems(line_marking_right_list)
        self.line_marking_right.setCurrentText(self.right)

        self.line_marking_left = QComboBox()
        line_marking_left_list = [left.value for left in LineMarking]
        self.line_marking_left.addItems(line_marking_left_list)
        self.line_marking_left.setCurrentText(self.left)

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
        layout.addRow("Lanelet type", self.type)
        layout.addRow("Roaduser oneway", self.roaduser_oneway)
        layout.addRow("Roaduser bidirectional", self.roaduser_bidirectional)
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
            self.curve_width = 20
        if self.angle.text():
            self.curve_angle = int(self.angle.text())
        else:
            self.curve_angle = 90

        if self.posX.text():
            self.posXval = int(self.posX.text())
        if self.posY.text():
            self.posYval = int(self.posY.text())
        self.setPredecessor = self.pred.isChecked()

        self.right = self.line_marking_right.currentText()
        self.left = self.line_marking_left.currentText()

        if self.curve_direction.currentText() == "left curve":
            self.curve_direction_bool = True
        else:
            self.curve_direction_bool = False

        self.close()

    def set_default_click(self):
        self.radius.clear()
        self.width.clear()
        self.angle.clear()
        self.posX.clear()
        self.posY.clear()
        self.vertices.clear()
        self.radius.insert("50")
        self.width.insert("20")
        self.angle.insert("90")
        self.vertices.insert("10")
        self.setadjacent = False
        self.adjacentCurve.setChecked(False)
        self.pred.setChecked(False)
        self.setPredecessor = False
        self.posX.insert("0")
        self.posY.insert("0")
        self.line_marking_left.setCurrentText("solid")
        self.line_marking_right.setCurrentText("solid")


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
        list = self.type.get_checked_items()
        strlist = []
        for i in range(0, len(list)):
            strlist.append(self.enumlist[list[i]])
        return strlist

    def getOnewayRoadUser(self):
        list2 = self.roaduser_oneway.get_checked_items()
        strlist2 = []
        for i in range(0, len(list2)):
            strlist2.append(self.roaduser_oneway_list[list2[i]])
        return strlist2

    def getBidirectionalRoadUser(self):
        list3 = self.roaduser_bidirectional.get_checked_items()
        strlist3 = []
        for i in range(0, len(list3)):
            strlist3.append(self.roaduser_bidirectional_list[list3[i]])
        return strlist3

    def getLineMarkingRight(self):
        return self.line_marking_right.currentText()

    def getLineMarkingLeft(self):
        return self.line_marking_left.currentText()

    def getCurveDirection(self):
        return self.curve_direction_bool

    def getPosX(self):
        return self.posXval
        if self.posX.text():
            return int(self.posX.text())
        else:
            return 0

    def getPosY(self):
        return self.posYval
        if self.posY.text():
            return int(self.posY.text())
        else:
            return 0

class CheckableComboBox(QComboBox):
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))

        # when any item get pressed

    def handle_item_pressed(self, index):

        # getting which item is pressed
        item = self.model().itemFromIndex(index)

        # make it check if unchecked and vice-versa
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

            # calling method
        self.check_items()

        # method called by check_items

    def item_checked(self, index):

        # getting item at index
        item = self.model().item(index, 0)

        # return true if checked else false
        return item.checkState() == Qt.Checked



    def get_checked_items(self):
        # blank list
        checkedItems = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checkedItems.append(i)

        return checkedItems

    def check_items(self):
        # blank list
        checkedItems = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checkedItems.append(i)

                # call this method
        self.update_labels(checkedItems)

        # method to update the label

    def update_labels(self, item_list):

        n = ''
        count = 0

        # traversing the list
        for i in item_list:

            # if count value is 0 don't add comma
            if count == 0:
                n += ' % s' % i
                # else value is greater then 0
            # add comma
            else:
                n += ', % s' % i

                # increment count
            count += 1
