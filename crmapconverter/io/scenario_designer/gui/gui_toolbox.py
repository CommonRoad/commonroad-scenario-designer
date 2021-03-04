from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer  # do not remove!!!

from commonroad.scenario.lanelet import LaneletType, RoadUser
from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import random


class SectionExpandButton(QPushButton):
    """a QPushbutton that can expand or collapse its section"""

    def __init__(self, item, text="", parent=None):
        super().__init__(text, parent)
        self.section = item
        self.setStyleSheet("background-color: rgb(198, 198, 198);")
        self.section.setExpanded(True)
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        """toggle expand/collapse of section by clicking"""
        if self.section.isExpanded():
            self.section.setExpanded(False)
        else:
            self.section.setExpanded(True)


def update_labels(item_list):

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
        checked_items = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checked_items.append(i)

        return checked_items

    def check_items(self):
        # blank list
        checked_items = []

        # traversing the items
        for i in range(self.count()):

            # if item is checked add it to the list
            if self.item_checked(i):
                checked_items.append(i)

                # call this method
        update_labels(checked_items)

        # method to update the label


class Toolbox(QWidget):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """

    def __init__(self):
        super().__init__()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.tree.setIndentation(0)
        self.setGeometry(0, 0, 250, 500)
        self.spacerItem = QSpacerItem(
            0, 50, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # layout.addItem(self.spacerItem)

        self.sections = []
        self.define_sections()
        self.add_sections()

    def add_sections(self):
        """adds a collapsible sections for every
            (title, widget) tuple in self.sections
            """
        for (title, widget) in self.sections:
            button1 = self.add_button(title)
            section1 = self.add_widget(button1, widget)
            button1.addChild(section1)

    def selection_change(self):
        self.lb.setText(self.save_menu.currentText())

    def add_button(self, title):
        """creates a QTreeWidgetItem containing a button
        to expand or collapse its section
        """
        item = QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        self.tree.setItemWidget(item, 0, SectionExpandButton(item, text=title))
        return item

    def add_widget(self, button, widget):
        """creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        """
        section = QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section


class RoadNetworkToolbox(Toolbox):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """
    button_forwards = None

    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  Lanelet Section
        widget_lanelets = QFrame(self.tree)
        layout_lanelets = QVBoxLayout(widget_lanelets)

        self.laneletID = QLineEdit()
        self.laneletID.setReadOnly(True)
        self.laneletID.setValidator(QIntValidator())
        self.laneletID.setAlignment(Qt.AlignRight)

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

        self.radius = QLineEdit()
        self.radius.setValidator(QIntValidator())
        self.radius.setMaxLength(4)
        self.radius.setAlignment(Qt.AlignRight)

        self.angle = QLineEdit()
        self.angle.setValidator(QIntValidator())
        self.angle.setMaxLength(4)
        self.angle.setAlignment(Qt.AlignRight)

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

        self.type = CheckableComboBox()
        self.enumlist = [e.value for e in LaneletType]
        for i in range(0, len(self.enumlist) - 1):
            # adding item
            self.type.addItem(self.enumlist[i])
            item = self.type.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.traffic_sign_ids = QLineEdit()
        self.traffic_sign_ids.setAlignment(Qt.AlignRight)

        self.traffic_light_ids = QLineEdit()
        self.traffic_light_ids.setAlignment(Qt.AlignRight)



        lanelet_information = QFormLayout()
        lanelet_information.addRow("Lanelet ID", self.laneletID)
        lanelet_information.addRow("Width [m]", self.width)
        lanelet_information.addRow("Length [m]", self.length)
        lanelet_information.addRow("Number vertices", self.number_vertices)
        lanelet_information.addRow("Curve radius [m]", self.radius)
        lanelet_information.addRow("Curve angle [rad]", self.angle)
        lanelet_information.addRow("Type", self.type)
        lanelet_information.addRow("User oneway", self.roaduser_oneway)
        lanelet_information.addRow("User bidirectional", self.roaduser_bidirectional)
        lanelet_information.addRow("Traffic Sign IDs", self.traffic_sign_ids)
        lanelet_information.addRow("Traffic Light IDs", self.traffic_light_ids)

        layout_lanelets.addLayout(lanelet_information)

        lanelet_buttons = QGridLayout()

        self.refresh_button = QPushButton()
        self.refresh_button.setText("refresh")
        lanelet_buttons.addWidget(self.refresh_button, 0, 0)

        self.edit_button = QPushButton()
        self.edit_button.setText("edit")
        lanelet_buttons.addWidget(self.edit_button, 1, 0)

        layout_lanelets.addLayout(lanelet_buttons)

        title_lanelets = "Lanelet"
        self.sections.append((title_lanelets, widget_lanelets))

        # Lanelet operations
        widget_lanelet_operations = QFrame(self.tree)
        layout_lanelet_operations = QGridLayout(widget_lanelet_operations)


        # self.button_forwards = QPushButton()
        # self.button_forwards.setText("straight")
        # self.button_forwards.setIcon(QIcon(":/forwards.PNG"))
        # layout_lanelet_operations.addWidget(self.button_forwards)

        # self.button_lanelet_settings = QPushButton()
        # self.button_lanelet_settings.setText("edit straight")
        # layout_lanelet_operations.addWidget(self.button_lanelet_settings)

        # self.button_turn_right = QPushButton()
        # self.button_turn_right.setText("curve")
        # layout_lanelet_operations.addWidget(self.button_turn_right)
        # self.button_turn_right.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # self.button_curve_settings = QPushButton()
        # self.button_curve_settings.setText("edit curve")
        # layout_lanelet_operations.addWidget(self.button_curve_settings)
        # self.button_curve_settings.setIcon(QIcon(":/gui_src/forwards.PNG"))

        #Fit to Predecessor
        self.button_fit_to_predecessor = QPushButton()
        self.button_fit_to_predecessor.setText("fit to predecessor")
        layout_lanelet_operations.addWidget(self.button_fit_to_predecessor)
        self.button_fit_to_predecessor.setIcon(QIcon(":/gui_src/forwards.PNG"))

        #adjacent
        self.button_adjacent = QPushButton()
        self.button_adjacent.setText("create adjacent lanelet")
        layout_lanelet_operations.addWidget(self.button_adjacent)
        self.button_adjacent.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # connect lanelets
        self.button_connect_lanelets = QPushButton()
        self.button_connect_lanelets.setText("connect two lanelets")
        layout_lanelet_operations.addWidget(self.button_connect_lanelets)
        self.button_connect_lanelets.setIcon(QIcon(":/gui_src/forwards.PNG"))

        # remove lanelet
        self.button_remove_lanelet = QPushButton()
        self.button_remove_lanelet.setText("remove lanelet")
        layout_lanelet_operations.addWidget(self.button_remove_lanelet)
        self.button_remove_lanelet.setIcon(QIcon(":/gui_src/forwards.PNG"))

        title_lanelet_operations = "Lanelet Operations"
        self.sections.append((title_lanelet_operations, widget_lanelet_operations))

        # Traffic sign section
        widget_traffic_sign = QFrame(self.tree)
        layout_traffic_sign = QGridLayout(widget_traffic_sign)

        self.button_traffic_signs = QPushButton()
        self.button_traffic_signs.setText("traffic sign")
        layout_traffic_sign.addWidget(self.button_traffic_signs, 0, 0)

        self.button_traffic_signs_settings = QPushButton()
        self.button_traffic_signs_settings.setText("traffic sign settings")
        layout_traffic_sign.addWidget(self.button_traffic_signs_settings, 0, 1)

        self.delete_traffic_sign = QPushButton()
        self.delete_traffic_sign.setText("delete traffic sign")
        layout_traffic_sign.addWidget(self.delete_traffic_sign,2,0)

        layout_traffic_sign.addItem(self.spacerItem)
        title_traffic_sign = "Traffic Sign"
        self.sections.append((title_traffic_sign, widget_traffic_sign))

        # Traffic light section
        widget_traffic_light = QFrame(self.tree)
        layout_traffic_light = QGridLayout(widget_traffic_light)

        self.button_traffic_light = QPushButton()
        self.button_traffic_light.setText("traffic light")
        layout_traffic_light.addWidget(self.button_traffic_light, 1, 0)

        self.edit_button_traffic_light = QPushButton()
        self.edit_button_traffic_light.setText("edit traffic light")
        layout_traffic_light.addWidget(self.edit_button_traffic_light, 1, 1)

        title_traffic_light = "Traffic Light"
        self.sections.append((title_traffic_light, widget_traffic_light))

        #--Section intersections--
        widget_intersection = QFrame(self.tree)
        layout_intersection = QGridLayout(widget_intersection)

        self.button_X = QPushButton()
        self.button_X.setText("X - crossing")
        self.button_X.setIcon(QIcon(":/icons/forwards.PNG"))
        layout_intersection.addWidget(self.button_X, 1, 0)

        self.button_T = QPushButton()
        self.button_T.setText("T - crossing")
        layout_intersection.addWidget(self.button_T, 1, 1)
        self.button_T.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_T_3 = QPushButton()
        self.button_T_3.setText("fit to intersection")
        layout_intersection.addWidget(self.button_T_3, 2, 0)
        self.button_T_3.setIcon(QIcon(":/gui_src/forwards.PNG"))

        title_intersection = "Intersections"
        self.sections.append((title_intersection, widget_intersection))


class ObstacleToolbox(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  Lanelet Section
        widget_obstacles = QFrame(self.tree)
        layout_obstacles = QVBoxLayout(widget_obstacles)

        self.obstacle_ID = QLineEdit()
        self.obstacle_ID.setReadOnly(True)
        self.obstacle_ID.setValidator(QIntValidator())
        self.obstacle_ID.setAlignment(Qt.AlignRight)

        self.length = QLineEdit()
        self.length.setValidator(QIntValidator())
        self.length.setMaxLength(4)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.type = CheckableComboBox()
        self.enumlist = [e.value for e in ObstacleType]
        for i in range(0, len(self.enumlist) - 1):
            # adding item
            self.type.addItem(self.enumlist[i])
            item = self.type.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        obstacle_information = QFormLayout()
        obstacle_information.addRow("Obstacle ID", self.obstacle_ID)
        obstacle_information.addRow("Width [m]", self.width)
        obstacle_information.addRow("Length [m]", self.length)
        obstacle_information.addRow("Type", self.type)
        layout_obstacles.addLayout(obstacle_information)

        obstacle_buttons = QGridLayout()

        # self.add_button = QPushButton()
        # self.add_button.setText("Add")
        # obstacle_buttons.addWidget(self.ed, 0, 0)
        #
        # self.update_button = QPushButton()
        # self.update_button.setText("Update")
        # obstacle_buttons.addWidget(self.update_button, 1, 0)
        #
        # self.remove_button = QPushButton()
        # self.remove_button.setText("Remove")
        # obstacle_buttons.addWidget(self.remove_button, 2, 0)
        #
        # layout_obstacles.addLayout(obstacle_buttons)

        # a figure instance to plot on
        self.figure = Figure(figsize=(3, 1))

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        layout_obstacles.addLayout(layout)

        title_obstacle = "Obstacle"
        self.sections.append((title_obstacle, widget_obstacles))

        # --Section SUMO Simulation--
        widget_sumo = QFrame(self.tree)
        layout_sumo = QGridLayout(widget_sumo)

        self.button_X = QPushButton()
        self.button_X.setText("X - crossing")
        self.button_X.setIcon(QIcon(":/icons/forwards.PNG"))
        layout_sumo.addWidget(self.button_X, 1, 0)

        self.button_T = QPushButton()
        self.button_T.setText("T - crossing")
        layout_sumo.addWidget(self.button_T, 1, 1)
        self.button_T.setIcon(QIcon(":/gui_src/forwards.PNG"))

        self.button_T_3 = QPushButton()
        self.button_T_3.setText("fit to intersection")
        layout_sumo.addWidget(self.button_T_3, 2, 0)
        self.button_T_3.setIcon(QIcon(":/gui_src/forwards.PNG"))

        title_sumo = "Sumo Simulation"
        self.sections.append((title_sumo, widget_sumo))


    def plot(self):
        ''' plot some random stuff '''
        # random data
        data = [random.random() for i in range(10)]

        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.clear()

        # plot data
        ax.plot(data, 'o-')

        # refresh canvas
        self.canvas.draw()


class MapConversionToolbox(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  Lanelet Section
        widget_conversion = QFrame(self.tree)
        layout_conversion = QVBoxLayout(widget_conversion)


        # self.add_button = QPushButton()
        # self.add_button.setText("Add")
        # obstacle_buttons.addWidget(self.ed, 0, 0)
        #
        # self.update_button = QPushButton()
        # self.update_button.setText("Update")
        # obstacle_buttons.addWidget(self.update_button, 1, 0)
        #
        # self.remove_button = QPushButton()
        # self.remove_button.setText("Remove")
        # obstacle_buttons.addWidget(self.remove_button, 2, 0)
        #
        # layout_obstacles.addLayout(obstacle_buttons)

        # a figure instance to plot on
        self.figure = Figure(figsize=(3, 1))

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        layout_conversion.addLayout(layout)


        title_obstacle = "Map Conversion"
        self.sections.append((title_obstacle, widget_conversion))


    def plot(self):
        ''' plot some random stuff '''
        # random data
        data = [random.random() for i in range(10)]

        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.clear()

        # plot data
        ax.plot(data, 'o-')

        # refresh canvas
        self.canvas.draw()