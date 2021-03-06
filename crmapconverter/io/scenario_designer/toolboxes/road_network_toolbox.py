from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer  # do not remove!!!
from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.toolboxes.toolbox import Toolbox, CheckableComboBox, QHLine

from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import random
import logging

# try to import sumo functionality
try:
    from crmapconverter.sumo_map.config import SumoConfig
    from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
    from sumocr.interface.sumo_simulation import SumoSimulation
    SUMO_AVAILABLE = True
except ImportError:
    logging.warning("Cannot import SUMO, simulation will not be offered in Scenario Designer")
    SUMO_AVAILABLE = False


class RoadNetworkToolbox(Toolbox):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        self.sections.append(self.create_lanelet_widget())  # Lanelet Section
        self.sections.append(self.create_lanelet_operations_widget())  # Lanelet Operations section
        self.sections.append(self.create_traffic_sign_widget())  # Traffic sign section
        self.sections.append(self.create_traffic_light_widget())
        self.sections.append(self.create_intersection_widget())  # Intersection section

    def create_intersection_widget(self):
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
        return title_intersection, widget_intersection

    def create_traffic_light_widget(self):
        widget_traffic_light = QFrame(self.tree)
        layout_traffic_light = QGridLayout(widget_traffic_light)
        self.button_traffic_light = QPushButton()
        self.button_traffic_light.setText("traffic light")
        layout_traffic_light.addWidget(self.button_traffic_light, 1, 0)
        self.edit_button_traffic_light = QPushButton()
        self.edit_button_traffic_light.setText("edit traffic light")
        layout_traffic_light.addWidget(self.edit_button_traffic_light, 1, 1)
        title_traffic_light = "Traffic Light"
        return title_traffic_light, widget_traffic_light

    def create_traffic_sign_widget(self):
        widget_traffic_sign = QFrame(self.tree)
        layout_traffic_sign = QVBoxLayout(widget_traffic_sign)

        self.country = QComboBox()
        country_list = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(country_list)

        self.x_position_traffic_sign = QLineEdit()
        self.x_position_traffic_sign.setValidator(QDoubleValidator())
        self.x_position_traffic_sign.setMaxLength(4)
        self.x_position_traffic_sign.setAlignment(Qt.AlignRight)

        self.y_position_traffic_sign = QLineEdit()
        self.y_position_traffic_sign.setValidator(QDoubleValidator())
        self.y_position_traffic_sign.setMaxLength(4)
        self.y_position_traffic_sign.setAlignment(Qt.AlignRight)

        traffic_sign_information = QFormLayout()

        label_general = QLabel("General parameters")
        label_general.setFont(QFont("Arial", 10, QFont.Bold))
        traffic_sign_information.addRow("Country", self.country)
        traffic_sign_information.addRow("X-Position [m]", self.x_position_traffic_sign)
        traffic_sign_information.addRow("Y-Position [m]", self.y_position_traffic_sign)

        layout_traffic_sign.addLayout(traffic_sign_information)

        title_traffic_sign = "Traffic Sign"
        return title_traffic_sign, widget_traffic_sign

    def create_lanelet_operations_widget(self):
        widget_lanelet_operations = QFrame(self.tree)
        layout_lanelet_operations = QGridLayout(widget_lanelet_operations)
        # First lanelet
        self.lanelet_one_text = QLabel()
        self.lanelet_one_text.setText("[1] Selected lanelet:")
        layout_lanelet_operations.addWidget(self.lanelet_one_text, 0, 0)
        self.lanelet_one = QComboBox()
        layout_lanelet_operations.addWidget(self.lanelet_one, 0, 1)
        # Second lanelet
        self.lanelet_two_text = QLabel()
        self.lanelet_two_text.setText("[2] Previously selected:")
        layout_lanelet_operations.addWidget(self.lanelet_two_text, 1, 0)
        self.lanelet_two = QComboBox()
        layout_lanelet_operations.addWidget(self.lanelet_two, 1, 1)
        # Fit to Predecessor
        self.button_fit_to_predecessor = QPushButton()
        self.button_fit_to_predecessor.setText("Fit [1] to [2]")
        self.button_fit_to_predecessor.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_fit_to_predecessor, 2, 0)
        # connect lanelets
        self.button_connect_lanelets = QPushButton()
        self.button_connect_lanelets.setText("Connect [1] and [2]")
        self.button_connect_lanelets.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_connect_lanelets, 2, 1)
        # adjacent
        self.button_adjacent = QPushButton()
        self.button_adjacent.setText("Create adjacent")
        self.button_adjacent.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_adjacent, 3, 0)
        # remove lanelet
        self.button_remove_lanelet = QPushButton()
        self.button_remove_lanelet.setText("Remove")
        self.button_remove_lanelet.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_remove_lanelet, 3, 1)
        # rotate lanelet
        self.button_rotate_lanelet = QPushButton()
        self.button_rotate_lanelet.setText("Rotate")
        self.button_rotate_lanelet.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_rotate_lanelet, 4, 0)
        # translate lanelet
        self.button_translate_lanelet = QPushButton()
        self.button_translate_lanelet.setText("Translate")
        self.button_translate_lanelet.setIcon(QIcon(":/gui_src/forwards.PNG"))
        layout_lanelet_operations.addWidget(self.button_translate_lanelet, 5, 0)

        title_lanelet_operations = "Lanelet Operations"
        return title_lanelet_operations, widget_lanelet_operations

    def create_lanelet_widget(self):
        widget_lanelets = QFrame(self.tree)
        layout_lanelets = QVBoxLayout(widget_lanelets)

        self.x_position_lanelet_start = QLineEdit()
        self.x_position_lanelet_start.setValidator(QDoubleValidator())
        self.x_position_lanelet_start.setMaxLength(4)
        self.x_position_lanelet_start.setAlignment(Qt.AlignRight)

        self.y_position_lanelet_start = QLineEdit()
        self.y_position_lanelet_start.setValidator(QDoubleValidator())
        self.y_position_lanelet_start.setMaxLength(4)
        self.y_position_lanelet_start.setAlignment(Qt.AlignRight)

        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(QDoubleValidator())
        self.lanelet_length.setMaxLength(4)
        self.lanelet_length.setText("10.0")
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(QDoubleValidator())
        self.lanelet_width.setMaxLength(4)
        self.lanelet_width.setAlignment(Qt.AlignRight)

        line_markings = [e.value for e in LineMarking]
        self.line_marking_left = QComboBox()
        for i in range(0, len(line_markings) - 1):
            self.line_marking_left.addItem(line_markings[i])
        self.line_marking_right = QComboBox()
        for i in range(0, len(line_markings) - 1):
            self.line_marking_right.addItem(line_markings[i])

        self.number_vertices = QLineEdit()
        self.number_vertices.setValidator(QIntValidator())
        self.number_vertices.setMaxLength(2)
        self.number_vertices.setAlignment(Qt.AlignRight)

        self.lanelet_radius = QLineEdit()
        self.lanelet_radius.setValidator(QDoubleValidator())
        self.lanelet_radius.setMaxLength(4)
        self.lanelet_radius.setAlignment(Qt.AlignRight)

        self.lanelet_angle = QLineEdit()
        self.lanelet_angle.setValidator(QIntValidator())
        self.lanelet_angle.setMaxLength(4)
        self.lanelet_angle.setAlignment(Qt.AlignRight)

        self.road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.predecessors = CheckableComboBox()
        self.predecessor_list = []
        for i in range(0, len(self.predecessor_list) - 1):
            self.predecessors.addItem(self.predecessor_list[i])
            item = self.predecessors.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.successors = CheckableComboBox()
        self.successor_list = []
        for i in range(0, len(self.successor_list) - 1):
            self.successors.addItem(self.successor_list[i])
            item = self.successors.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.adjacent_right = QComboBox()
        self.adjacent_left = QComboBox()

        self.road_user_oneway = CheckableComboBox()
        road_user_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_oneway_list) - 1):
            self.road_user_oneway.addItem(road_user_oneway_list[i])
            item = self.road_user_oneway.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.lanelet_type = CheckableComboBox()
        lanelet_type_list = [e.value for e in LaneletType]
        for i in range(0, len(lanelet_type_list) - 1):
            self.lanelet_type.addItem(lanelet_type_list[i])
            item = self.lanelet_type.model().item(i, 0)

        self.traffic_sign_ids = QLineEdit()
        self.traffic_sign_ids.setAlignment(Qt.AlignRight)

        self.traffic_light_ids = QLineEdit()
        self.traffic_light_ids.setAlignment(Qt.AlignRight)

        self.stop_line_start = QLineEdit()
        self.stop_line_start.setValidator(QIntValidator())
        self.stop_line_start.setMaxLength(4)
        self.stop_line_start.setAlignment(Qt.AlignRight)
        self.stop_line_end = QLineEdit()
        self.stop_line_end.setValidator(QIntValidator())
        self.stop_line_end.setMaxLength(4)
        self.stop_line_end.setAlignment(Qt.AlignRight)
        self.line_marking_stop_line = CheckableComboBox()
        for i in range(0, len(line_markings) - 1):
            self.line_marking_stop_line.addItem(line_markings[i])

        self.connect_to_previous_selection = QRadioButton("Connect to previously added")
        self.connect_to_previous_selection.setChecked(True)

        self.connect_to_predecessors_selection = QRadioButton("Connect to predecessors")
        self.connect_to_predecessors_selection.setChecked(False)

        self.connect_to_successors_selection = QRadioButton("Connect to successors")
        self.connect_to_successors_selection.setChecked(False)

        self.curved_lanelet_selection = QCheckBox()
        self.curved_lanelet_selection.setText("Add curved lanelet")

        self.select_from_all_lanelets = QComboBox()

        self.button_add_lanelet = QPushButton()
        self.button_add_lanelet.setText("Add")
        self.button_update_lanelet = QPushButton()
        self.button_update_lanelet.setText("Update")
        lanelet_information = QFormLayout()

        label_general = QLabel("General parameters")
        label_general.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_general)
        lanelet_information.addRow("X-Position start [m]", self.x_position_lanelet_start)
        lanelet_information.addRow("Y-Position start [m]", self.y_position_lanelet_start)
        lanelet_information.addRow("Width [m]", self.lanelet_width)
        lanelet_information.addRow("Line marking left", self.line_marking_left)
        lanelet_information.addRow("Line marking right", self.line_marking_right)
        lanelet_information.addRow("Number vertices", self.number_vertices)
        lanelet_information.addRow("Predecessors", self.predecessors)
        lanelet_information.addRow("Successors", self.successors)
        lanelet_information.addRow("Adjacent right", self.adjacent_right)
        lanelet_information.addRow("Adjacent left", self.adjacent_left)
        lanelet_information.addRow("Type", self.lanelet_type)
        lanelet_information.addRow("Users oneway", self.road_user_oneway)
        lanelet_information.addRow("Users bidirectional", self.road_user_bidirectional)
        lanelet_information.addRow("Traffic Sign IDs", self.traffic_sign_ids)
        lanelet_information.addRow("Traffic Light IDs", self.traffic_light_ids)
        lanelet_information.addRow("Stop line start", self.stop_line_start)
        lanelet_information.addRow("Stop line end", self.stop_line_end)
        lanelet_information.addRow("Stop line marking", self.line_marking_stop_line)
        lanelet_information.addRow(QHLine())
        label_straight = QLabel("Straight lanelet parameters")
        label_straight.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_straight)
        lanelet_information.addRow("Length [m]", self.lanelet_length)
        lanelet_information.addRow(QHLine())
        label_curved = QLabel("Curved lanelet parameters")
        label_curved.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_curved)
        lanelet_information.addRow("Curve radius [m]", self.lanelet_radius)
        lanelet_information.addRow("Curve angle [deg]", self.lanelet_angle)
        lanelet_information.addRow(QHLine())
        label_adding = QLabel("Add lanelet")
        label_adding.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_adding)
        lanelet_information.addRow(self.curved_lanelet_selection)
        lanelet_information.addRow(self.connect_to_previous_selection)
        lanelet_information.addRow(self.connect_to_predecessors_selection)
        lanelet_information.addRow(self.connect_to_successors_selection)
        lanelet_information.addRow(self.button_add_lanelet)
        lanelet_information.addRow(QHLine())
        label_update = QLabel("Update lanelet")
        label_update.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_update)
        lanelet_information.addRow("Select lanelet", self.select_from_all_lanelets)
        lanelet_information.addRow(self.button_update_lanelet)
        layout_lanelets.addLayout(lanelet_information)
        widget_title = "Lanelet"

        return widget_title, widget_lanelets


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
        widget_sumo = SUMOSimulation(self.tree)
        layout_sumo = QGridLayout(widget_sumo)

        self.button_start_simulation = QPushButton()
        self.button_start_simulation.setText("Simulate")
        self.button_start_simulation.setIcon(QIcon(":/icons/forwards.PNG"))
        layout_sumo.addWidget(self.button_start_simulation, 1, 0)

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