from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QMessageBox, QAction,
                             QLabel, QFileDialog, QDesktopWidget, QVBoxLayout,
                             QSlider, QWidget, QApplication, qApp, QLineEdit, QFormLayout, QPushButton, QDialog, QRadioButton, QCheckBox, QComboBox)
from PyQt5.QtGui import QIcon, QIntValidator, QStandardItemModel
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

        self.roaduser_oneway = CheckableComboBox()
        self.roaduser_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(self.roaduser_oneway_list) - 1):
            self.roaduser_oneway.addItem(self.roaduser_oneway_list[i])
            item = self.roaduser_oneway.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.roaduser_bidirectional = CheckableComboBox()
        self.roaduser_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0,len(self.roaduser_bidirectional_list)-1):
            self.roaduser_bidirectional.addItem(self.roaduser_bidirectional_list[i])
            item = self.roaduser_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

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

        self.type = CheckableComboBox()
        self.enumlist = [e.value for e in LaneletType]
        for i in range(0,len(self.enumlist)-1):
            # adding item
            self.type.addItem(self.enumlist[i])
            item = self.type.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        # adding combo box to the layout
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

        layout.addRow("Lanelet type", self.type)
        layout.addRow("Roaduser oneway", self.roaduser_oneway)
        layout.addRow("Roaduser bidirectional", self.roaduser_bidirectional)
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
        list = self.type.get_checked_items()
        strlist = []
        for i in range(0,len(list)):
            strlist.append(self.enumlist[list[i]])

        print(strlist)
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

    # creating checkable combo box class
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



