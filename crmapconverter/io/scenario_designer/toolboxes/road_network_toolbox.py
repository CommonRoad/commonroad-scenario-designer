from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer  # do not remove!!!
from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.toolboxes.toolbox import Toolbox, CheckableComboBox, QHLine

from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking
from commonroad.scenario.traffic_sign import *
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
        self.sections.append(self.create_traffic_sign_widget())  # Traffic sign section
        self.sections.append(self.create_traffic_light_widget())
        self.sections.append(self.create_intersection_widget())  # Intersection section

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
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(QDoubleValidator())
        self.lanelet_width.setMaxLength(4)
        self.lanelet_width.setAlignment(Qt.AlignRight)

        line_markings = [e.value for e in LineMarking]
        self.line_marking_left = QComboBox()
        self.line_marking_left.addItems(line_markings)

        self.line_marking_right = QComboBox()
        self.line_marking_right.addItems(line_markings)

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
        self.adjacent_right_same_direction = QCheckBox("Adjacent right same direction")
        self.adjacent_left = QComboBox()
        self.adjacent_left_same_direction = QCheckBox("Adjacent left same direction")

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

        self.lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.lanelet_referenced_traffic_light_ids = CheckableComboBox()

        self.stop_line_start = QLineEdit()
        self.stop_line_start.setValidator(QIntValidator())
        self.stop_line_start.setMaxLength(4)
        self.stop_line_start.setAlignment(Qt.AlignRight)
        self.stop_line_end = QLineEdit()
        self.stop_line_end.setValidator(QIntValidator())
        self.stop_line_end.setMaxLength(4)
        self.stop_line_end.setAlignment(Qt.AlignRight)
        self.line_marking_stop_line = QComboBox()
        self.line_marking_stop_line.addItems(line_markings)

        self.connecting_radio_button_group = QButtonGroup()
        self.connect_to_previous_selection = QRadioButton("Connect to previously added")
        self.connect_to_previous_selection.setChecked(True)
        self.connecting_radio_button_group.addButton(self.connect_to_previous_selection)

        self.connect_to_predecessors_selection = QRadioButton("Connect to predecessors")
        self.connect_to_predecessors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_predecessors_selection)

        self.connect_to_successors_selection = QRadioButton("Connect to successors")
        self.connect_to_successors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_successors_selection)

        self.curved_lanelet_selection = QCheckBox("Add curved lanelet")

        self.button_add_lanelet = QPushButton("Add")

        self.selected_lanelet_one = QComboBox()
        self.selected_lanelet_two = QComboBox()

        self.button_update_lanelet = QPushButton("Update [1]")
        self.adjacent_left_right_button_group = QButtonGroup()
        self.create_adjacent_left_selection = QRadioButton("Adjacent left")
        self.create_adjacent_left_selection.setChecked(True)
        self.adjacent_left_right_button_group.addButton(self.create_adjacent_left_selection)
        self.create_adjacent_right_selection = QRadioButton("Adjacent right")
        self.create_adjacent_left_selection.setChecked(False)
        self.adjacent_left_right_button_group.addButton(self.create_adjacent_right_selection)
        self.create_adjacent_same_direction_selection = QCheckBox("Adjacent same direction")
        self.create_adjacent_same_direction_selection.setChecked(True)
        self.button_create_adjacent = QPushButton("Create adjacent to [1]")
        self.button_remove_lanelet = QPushButton("Remove [1]")
        self.button_fit_to_predecessor = QPushButton("Fit [1] to [2]")
        self.button_connect_lanelets = QPushButton("Connect [1] and [2]")

        self.button_rotate_lanelet = QPushButton("Rotate")
        self.button_rotate_lanelet.setFixedWidth(100)
        self.rotation_angle = QSpinBox()
        self.rotation_angle.setMinimum(-180)
        self.rotation_angle.setMaximum(180)
        self.rotation_degree_label = QLabel("[deg]")

        self.button_translate_lanelet = QPushButton("Translate")
        self.button_translate_lanelet.setFixedWidth(100)
        self.translate_x_label = QLabel("x:")
        self.x_translation = QLineEdit()
        self.x_translation.setValidator(QDoubleValidator())
        self.x_translation.setMaxLength(4)
        self.x_translation.setAlignment(Qt.AlignRight)
        self.translate_x_unit_label = QLabel("[m]")
        self.translate_y_label = QLabel("y:")
        self.y_translation = QLineEdit()
        self.y_translation.setValidator(QDoubleValidator())
        self.y_translation.setMaxLength(4)
        self.y_translation.setAlignment(Qt.AlignRight)
        self.translate_y_unit_label = QLabel("[m]")

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
        lanelet_information.addRow(self.adjacent_right_same_direction)
        lanelet_information.addRow("Adjacent left", self.adjacent_left)
        lanelet_information.addRow(self.adjacent_left_same_direction)
        lanelet_information.addRow("Type", self.lanelet_type)
        lanelet_information.addRow("Users oneway", self.road_user_oneway)
        lanelet_information.addRow("Users bidirectional", self.road_user_bidirectional)
        lanelet_information.addRow("Traffic Sign IDs", self.lanelet_referenced_traffic_sign_ids)
        lanelet_information.addRow("Traffic Light IDs", self.lanelet_referenced_traffic_light_ids)
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
        label_update = QLabel("Lanelet operations")
        label_update.setFont(QFont("Arial", 10, QFont.Bold))
        lanelet_information.addRow(label_update)
        lanelet_information.addRow("[1] Selected lanelet", self.selected_lanelet_one)
        lanelet_information.addRow("[2] Previously selected", self.selected_lanelet_two)
        lanelet_information.addRow(self.button_update_lanelet)
        lanelet_information.addRow(self.create_adjacent_left_selection, self.create_adjacent_right_selection)
        lanelet_information.addRow(self.create_adjacent_same_direction_selection)
        lanelet_information.addRow(self.button_create_adjacent)
        lanelet_information.addRow(self.button_remove_lanelet)
        lanelet_information.addRow(self.button_fit_to_predecessor)
        lanelet_information.addRow(self.button_connect_lanelets)
        layout_lanelets.addLayout(lanelet_information)

        lanelet_rotate_layout = QGridLayout()
        lanelet_rotate_layout.addWidget(self.button_rotate_lanelet, 0, 0)
        lanelet_rotate_layout.addWidget(self.rotation_angle, 0, 1)
        lanelet_rotate_layout.addWidget(self.rotation_degree_label, 0, 2)
        layout_lanelets.addLayout(lanelet_rotate_layout)

        lanelet_translate_layout = QGridLayout()
        lanelet_translate_layout.addWidget(self.button_translate_lanelet, 1, 0)
        lanelet_translate_layout.addWidget(self.translate_x_label, 1, 1)
        lanelet_translate_layout.addWidget(self.x_translation, 1, 2)
        lanelet_translate_layout.addWidget(self.translate_x_unit_label, 1, 3)
        lanelet_translate_layout.addWidget(self.translate_y_label, 1, 4)
        lanelet_translate_layout.addWidget(self.y_translation, 1, 5)
        lanelet_translate_layout.addWidget(self.translate_y_unit_label, 1, 6)
        layout_lanelets.addLayout(lanelet_translate_layout)

        widget_title = "Lanelet"

        return widget_title, widget_lanelets

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
        self.traffic_sign_virtual_selection = QCheckBox("virtual")

        self.selected_traffic_sign = QComboBox()

        self.referenced_lanelets_traffic_sign = CheckableComboBox()

        self.traffic_sign_element_label = QLabel("Traffic Sign Elements:")
        self.traffic_sign_element_table = QTableWidget()
        self.traffic_sign_element_table.setColumnCount(2)
        self.traffic_sign_element_table.setHorizontalHeaderLabels(['Traffic Sign ID', 'Additional Value'])
        self.traffic_sign_element_table.resizeColumnsToContents()
        self.traffic_sign_element_table.setColumnWidth(0, 180)
        self.traffic_sign_element_table.setMaximumHeight(100)
        self.button_add_traffic_sign_element = QPushButton("Add Element")
        self.button_remove_traffic_sign_element = QPushButton("Remove Element")

        self.button_add_traffic_sign = QPushButton("Add Traffic Sign to Scenario")
        self.button_update_traffic_sign = QPushButton("Update Selected Traffic Sign")
        self.button_remove_traffic_sign = QPushButton("Remove Selected Traffic Sign")

        traffic_sign_information = QFormLayout()
        traffic_sign_information.addRow("Country", self.country)
        traffic_sign_information.addRow("X-Position [m]", self.x_position_traffic_sign)
        traffic_sign_information.addRow("Y-Position [m]", self.y_position_traffic_sign)
        traffic_sign_information.addRow(self.traffic_sign_virtual_selection)
        traffic_sign_information.addRow("Selected traffic sign", self.selected_traffic_sign)
        traffic_sign_information.addRow("Referenced lanelets", self.referenced_lanelets_traffic_sign)
        traffic_sign_information.addRow(self.traffic_sign_element_label)
        traffic_sign_information.addRow(self.traffic_sign_element_table)
        traffic_sign_information.addRow(self.button_add_traffic_sign_element, self.button_remove_traffic_sign_element)
        traffic_sign_information.addRow(self.button_add_traffic_sign)
        traffic_sign_information.addRow(self.button_update_traffic_sign)
        traffic_sign_information.addRow(self.button_remove_traffic_sign)

        layout_traffic_sign.addLayout(traffic_sign_information)

        title_traffic_sign = "Traffic Sign"
        return title_traffic_sign, widget_traffic_sign

    def create_traffic_light_widget(self):
        widget_traffic_light = QFrame(self.tree)
        layout_traffic_light = QVBoxLayout(widget_traffic_light)

        self.x_position_traffic_light = QLineEdit()
        self.x_position_traffic_light.setValidator(QDoubleValidator())
        self.x_position_traffic_light.setMaxLength(4)
        self.x_position_traffic_light.setAlignment(Qt.AlignRight)

        self.y_position_traffic_light = QLineEdit()
        self.y_position_traffic_light.setValidator(QDoubleValidator())
        self.y_position_traffic_light.setMaxLength(4)
        self.y_position_traffic_light.setAlignment(Qt.AlignRight)

        directions = [e.value for e in TrafficLightDirection]
        self.traffic_light_directions = QComboBox()
        self.traffic_light_directions.addItems(directions)

        self.time_offset = QLineEdit()
        self.time_offset.setValidator(QIntValidator())
        self.time_offset.setMaxLength(4)
        self.time_offset.setAlignment(Qt.AlignRight)

        self.time_red = QLineEdit()
        self.time_red.setValidator(QIntValidator())
        self.time_red.setMaxLength(4)
        self.time_red.setAlignment(Qt.AlignRight)

        self.time_red_yellow = QLineEdit()
        self.time_red_yellow.setValidator(QIntValidator())
        self.time_red_yellow.setMaxLength(4)
        self.time_red_yellow.setAlignment(Qt.AlignRight)

        self.time_yellow = QLineEdit()
        self.time_yellow.setValidator(QIntValidator())
        self.time_yellow.setMaxLength(4)
        self.time_yellow.setAlignment(Qt.AlignRight)

        self.time_green = QLineEdit()
        self.time_green.setValidator(QIntValidator())
        self.time_green.setMaxLength(4)
        self.time_green.setAlignment(Qt.AlignRight)

        self.time_inactive = QLineEdit()
        self.time_inactive.setValidator(QIntValidator())
        self.time_inactive.setMaxLength(4)
        self.time_inactive.setAlignment(Qt.AlignRight)

        self.traffic_light_active = QCheckBox("active")

        self.referenced_lanelets_traffic_light = CheckableComboBox()

        self.selected_traffic_light = QComboBox()

        self.button_add_traffic_light = QPushButton("Add")
        self.button_update_traffic_light = QPushButton("Update")
        self.button_remove_traffic_light = QPushButton("Remove")

        traffic_light_information = QFormLayout()
        traffic_light_information.addRow("X-Position [m]", self.x_position_traffic_light)
        traffic_light_information.addRow("Y-Position [m]", self.y_position_traffic_light)
        traffic_light_information.addRow("Direction", self.traffic_light_directions)
        traffic_light_information.addRow("Time offset", self.time_offset)
        traffic_light_information.addRow("Time red", self.time_red)
        traffic_light_information.addRow("Time red-yellow", self.time_red_yellow)
        traffic_light_information.addRow("Time green", self.time_green)
        traffic_light_information.addRow("Time yellow", self.time_yellow)
        traffic_light_information.addRow("Time inactive", self.time_inactive)
        traffic_light_information.addRow("Referenced lanelets", self.referenced_lanelets_traffic_light)
        traffic_light_information.addRow("Selected traffic light", self.selected_traffic_light)
        traffic_light_information.addRow(self.traffic_light_active)
        traffic_light_information.addRow(self.button_add_traffic_light)
        traffic_light_information.addRow(self.button_update_traffic_light)
        traffic_light_information.addRow(self.button_remove_traffic_light)

        layout_traffic_light.addLayout(traffic_light_information)

        title_traffic_light = "Traffic Light"
        return title_traffic_light, widget_traffic_light

    def create_intersection_widget(self):
        widget_intersection = QFrame(self.tree)
        layout_intersection = QVBoxLayout(widget_intersection)

        self.intersection_diameter = QLineEdit()
        self.intersection_diameter.setValidator(QIntValidator())
        self.intersection_diameter.setMaxLength(2)
        self.intersection_diameter.setAlignment(Qt.AlignRight)

        self.intersection_lanelet_width = QLineEdit()
        self.intersection_lanelet_width.setValidator(QDoubleValidator())
        self.intersection_lanelet_width.setMaxLength(4)
        self.intersection_lanelet_width.setAlignment(Qt.AlignRight)

        self.intersection_incoming_length = QLineEdit()
        self.intersection_incoming_length.setValidator(QDoubleValidator())
        self.intersection_incoming_length.setMaxLength(4)
        self.intersection_incoming_length.setAlignment(Qt.AlignRight)

        self.button_three_way_intersection = QPushButton("Add Three-way intersection")
        self.button_four_way_intersection = QPushButton("Add Four-way intersection")
        self.button_fit_intersection = QPushButton("Fit to intersection")

        self.selected_intersection_label = QLabel("Selected intersection")
        self.selected_intersection = QComboBox()

        self.intersection_incomings_label = QLabel("Incomings:")
        self.intersection_incomings_table = QTableWidget()
        self.intersection_incomings_table.setColumnCount(5)
        self.intersection_incomings_table.setHorizontalHeaderLabels(['ID', 'Lanelets', 'Suc. Left', 'Suc. Straight',
                                                                     'Suc. Right'])
        self.intersection_incomings_table.resizeColumnsToContents()
        self.intersection_incomings_table.setMaximumHeight(175)
        self.button_add_incoming = QPushButton("Add incoming")
        self.button_remove_incoming = QPushButton("Remove incoming")
        self.intersection_crossings = CheckableComboBox()

        intersection_information = QFormLayout()
        intersection_information.addRow("Diameter [m]", self.intersection_diameter)
        intersection_information.addRow("Lanelet width [m]", self.intersection_lanelet_width)
        intersection_information.addRow("Incoming length [m]", self.intersection_incoming_length)
        intersection_information.addRow(self.button_three_way_intersection)
        intersection_information.addRow(self.button_four_way_intersection)
        intersection_information.addRow(self.button_fit_intersection)
        intersection_information.addRow(self.selected_intersection_label, self.selected_intersection)
        intersection_information.addRow(self.intersection_incomings_label)
        intersection_information.addRow(self.intersection_incomings_table)
        intersection_information.addRow(self.button_add_incoming, self.button_remove_incoming)
        intersection_information.addRow("Crossing lanelets", self.intersection_crossings)

        layout_intersection.addLayout(intersection_information)

        title_intersection = "Intersection"
        return title_intersection, widget_intersection


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

        self.obstacle_id = QComboBox()

        self.length = QLineEdit()
        self.length.setValidator(QDoubleValidator())
        self.length.setMaxLength(6)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.obstacle_type = QComboBox()
        obstalce_type_list = [e.value for e in ObstacleType]
        self.obstacle_type.addItems(obstalce_type_list)

        obstacle_information = QFormLayout()
        obstacle_information.addRow("Obstacle ID", self.obstacle_id)
        obstacle_information.addRow("Width [m]", self.width)
        obstacle_information.addRow("Length [m]", self.length)
        obstacle_information.addRow("Type", self.obstacle_type)
        layout_obstacles.addLayout(obstacle_information)

       # obstacle_buttons = QGridLayout()

        # self.button_add_obstacle = QPushButton()
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
        #  OSM Section
        widget_osm = QFrame(self.tree)
        layout_osm = QVBoxLayout(widget_osm)


        self.osm_conversion_load_osm_file_selection = QRadioButton("Load OSM File")
        self.osm_conversion_download_osm_file_selection = QRadioButton("Download OSM Map")

        self.button_select_osm_file = QPushButton("Select File")

        self.osm_conversion_coordinate_latitude = QLineEdit()
        self.osm_conversion_coordinate_latitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_latitude.setAlignment(Qt.AlignRight)
        self.osm_conversion_coordinate_longitude = QLineEdit()
        self.osm_conversion_coordinate_longitude.setValidator(QDoubleValidator())
        self.osm_conversion_coordinate_longitude.setAlignment(Qt.AlignRight)

        self.osm_download_map_range = QSpinBox()
        self.osm_download_map_range.setMinimum(0)
        self.osm_download_map_range.setMaximum(10000)

        self.osm_conversion_edit_manually_selection = QCheckBox("Edit Scenario Manually")

        self.button_load_osm_edit_state = QPushButton("Select File")
        self.button_start_conversion = QPushButton("Start Conversion")
        #self.button_load_osm_edit_state = QPushButton("Select File")

        osm_conversion_configuration = QFormLayout()
        osm_conversion_configuration.addRow(self.osm_conversion_load_osm_file_selection)
        osm_conversion_configuration.addRow(self.osm_conversion_download_osm_file_selection)
        osm_conversion_configuration.addRow(self.button_select_osm_file)
        osm_conversion_configuration.addRow("Latitude:", self.osm_conversion_coordinate_latitude)
        osm_conversion_configuration.addRow("Longitude:", self.osm_conversion_coordinate_longitude)
        osm_conversion_configuration.addRow("Range:", self.osm_download_map_range)
        osm_conversion_configuration.addRow(self.osm_conversion_edit_manually_selection)
        osm_conversion_configuration.addRow(self.button_load_osm_edit_state)
        osm_conversion_configuration.addRow(self.button_start_conversion)

        layout_osm.addLayout(osm_conversion_configuration)

        title_osm = "OSM Conversion"
        self.sections.append((title_osm, widget_osm))

        #  OpenDRIVE Section
        widget_opendrive = QFrame(self.tree)
        layout_opendrive = QVBoxLayout(widget_opendrive)

        title_opendrive = "OpenDRIVE  Conversion"
        self.sections.append((title_opendrive, widget_opendrive))

        #  Lanelet/Lanelet2 Section
        widget_lanelet2 = QFrame(self.tree)
        layout_lanelet2 = QVBoxLayout(widget_lanelet2)

        title_lanelet2 = "Lanelet/Lanelet2  Conversion"
        self.sections.append((title_lanelet2, widget_lanelet2))

        #  SUMO Section
        widget_sumo = QFrame(self.tree)
        layout_sumo = QVBoxLayout(widget_sumo)

        title_sumo = "SUMO  Conversion"
        self.sections.append((title_sumo, widget_sumo))
