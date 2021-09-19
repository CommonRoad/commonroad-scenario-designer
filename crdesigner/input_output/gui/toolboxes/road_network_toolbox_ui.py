from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


from crdesigner.input_output.gui.toolboxes.toolbox_ui import Toolbox, CheckableComboBox, QHLine

from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking
from commonroad.scenario.traffic_sign import *


class RoadNetworkToolboxUI(Toolbox):
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
        self.sections.append(self.create_lanelet_widget())
        self.sections.append(self.create_lanelet_operations_widget())
        self.sections.append(self.create_traffic_sign_widget())
        self.sections.append(self.create_traffic_light_widget())
        self.sections.append(self.create_intersection_widget())

    def create_lanelet_widget(self):
        label_general = QLabel("Lanelet Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

        self.x_position_lanelet_start = QLineEdit()
        self.x_position_lanelet_start.setValidator(QDoubleValidator())
        self.x_position_lanelet_start.setMaxLength(8)
        self.x_position_lanelet_start.setAlignment(Qt.AlignRight)

        self.y_position_lanelet_start = QLineEdit()
        self.y_position_lanelet_start.setValidator(QDoubleValidator())
        self.y_position_lanelet_start.setMaxLength(8)
        self.y_position_lanelet_start.setAlignment(Qt.AlignRight)

        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(QDoubleValidator())
        self.lanelet_length.setMaxLength(5)
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(QDoubleValidator())
        self.lanelet_width.setMaxLength(5)
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
        self.lanelet_radius.setMaxLength(6)
        self.lanelet_radius.setAlignment(Qt.AlignRight)

        self.lanelet_angle = QLineEdit()
        self.lanelet_angle.setMaxLength(6)
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

        self.lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.lanelet_referenced_traffic_light_ids = CheckableComboBox()

        label_stop_line = QLabel("Stop Line")
        label_stop_line.setFont(QFont("Arial", 10, QFont.Bold))
        self.stop_line_start_x = QLineEdit()
        self.stop_line_start_x.setValidator(QDoubleValidator())
        self.stop_line_start_x.setMaxLength(8)
        self.stop_line_start_x.setAlignment(Qt.AlignRight)
        self.stop_line_start_y = QLineEdit()
        self.stop_line_start_y.setValidator(QDoubleValidator())
        self.stop_line_start_y.setMaxLength(8)
        self.stop_line_start_y.setAlignment(Qt.AlignRight)
        self.stop_line_end_x = QLineEdit()
        self.stop_line_end_x.setValidator(QDoubleValidator())
        self.stop_line_end_x.setMaxLength(8)
        self.stop_line_end_x.setAlignment(Qt.AlignRight)
        self.stop_line_end_y = QLineEdit()
        self.stop_line_end_y.setValidator(QDoubleValidator())
        self.stop_line_end_y.setMaxLength(8)
        self.stop_line_end_y.setAlignment(Qt.AlignRight)
        self.line_marking_stop_line = QComboBox()
        line_markings_stop_line = [e.value for e in LineMarking if e.value not in [LineMarking.UNKNOWN.value,
                                                                         LineMarking.NO_MARKING.value]]
        self.line_marking_stop_line.addItems(line_markings_stop_line)
        self.stop_line_at_end = QCheckBox("Stop line at end of lanelet")

        label_add = QLabel("Add Lanelet")
        label_add.setFont(QFont("Arial", 11, QFont.Bold))

        self.connecting_radio_button_group = QButtonGroup()
        self.connect_to_previous_selection = QRadioButton("Connect to previously added")
        self.connect_to_previous_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_previous_selection)

        self.connect_to_predecessors_selection = QRadioButton("Connect to predecessors")
        self.connect_to_predecessors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_predecessors_selection)

        self.connect_to_successors_selection = QRadioButton("Connect to successors")
        self.connect_to_successors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_successors_selection)

        self.place_at_defined_position = QRadioButton("Place at position")
        self.place_at_defined_position.setChecked(True)
        self.connecting_radio_button_group.addButton(self.place_at_defined_position)

        self.curved_lanelet_selection = QCheckBox("Curved Lanelet")

        self.button_add_lanelet = QPushButton("Add")

        self.selected_lanelet_update = QComboBox()

        self.button_update_lanelet = QPushButton("Update")
        self.button_remove_lanelet = QPushButton("Remove")

        widget_lanelets = QFrame(self.tree)
        layout_lanelet_information = QVBoxLayout(widget_lanelets)

        layout_lanelet_information_groupbox = QFormLayout()
        lanelet_information_groupbox = QGroupBox()
        lanelet_information_groupbox.setLayout(layout_lanelet_information_groupbox)
        lanelet_information_1 = QFormLayout()
        lanelet_information_1.addRow(label_general)
        lanelet_information_1.addRow("X-Position Start [m]:", self.x_position_lanelet_start)
        lanelet_information_1.addRow("Y-Position Start [m]:", self.y_position_lanelet_start)
        lanelet_information_1.addRow("Line marking Left:", self.line_marking_left)
        lanelet_information_1.addRow("Line marking Right:", self.line_marking_right)
        lanelet_information_1.addRow("Predecessors:", self.predecessors)
        lanelet_information_1.addRow("Successors:", self.successors)
        lanelet_information_1.addRow("Adjacent Right:", self.adjacent_right)
        lanelet_information_1.addRow(self.adjacent_right_same_direction)
        lanelet_information_1.addRow("Adjacent Left:", self.adjacent_left)
        lanelet_information_1.addRow(self.adjacent_left_same_direction)
        lanelet_information_1.addRow("Lanelet Types:", self.lanelet_type)
        lanelet_information_1.addRow("Users Oneway:", self.road_user_oneway)
        lanelet_information_1.addRow("Users Bidirectional:", self.road_user_bidirectional)
        lanelet_information_1.addRow("Traffic Sign IDs:", self.lanelet_referenced_traffic_sign_ids)
        lanelet_information_1.addRow("Traffic Light IDs:", self.lanelet_referenced_traffic_light_ids)
        layout_lanelet_information_groupbox.addRow(lanelet_information_1)
        layout_lanelet_information.addWidget(lanelet_information_groupbox)

        lanelet_information_stop_line_layout = QFormLayout()
        lanelet_stop_line_groupbox = QGroupBox()
        lanelet_stop_line_groupbox.setLayout(lanelet_information_stop_line_layout)

        lanelet_information_3 = QFormLayout()
        lanelet_information_3.addRow(label_stop_line)
        lanelet_information_3.addRow("Stop line marking", self.line_marking_stop_line)
        lanelet_information_3.addRow(self.stop_line_at_end)
        lanelet_information_stop_line_layout.addRow(lanelet_information_3)
        lanelet_information_2 = QGridLayout()
        lanelet_information_2.addWidget(QLabel("Start"), 1, 0)
        lanelet_information_2.addWidget(QLabel("x:"), 1, 1)
        lanelet_information_2.addWidget(self.stop_line_start_x, 1, 2)
        lanelet_information_2.addWidget(QLabel("[m]"), 1, 3)
        lanelet_information_2.addWidget(QLabel("y:"), 1, 4)
        lanelet_information_2.addWidget(self.stop_line_start_y, 1, 5)
        lanelet_information_2.addWidget(QLabel("[m]"), 1, 6)
        lanelet_information_2.addWidget(QLabel("End"), 2, 0)
        lanelet_information_2.addWidget(QLabel("x:"), 2, 1)
        lanelet_information_2.addWidget(self.stop_line_end_x, 2, 2)
        lanelet_information_2.addWidget(QLabel("[m]"), 2, 3)
        lanelet_information_2.addWidget(QLabel("y:"), 2, 4)
        lanelet_information_2.addWidget(self.stop_line_end_y, 2, 5)
        lanelet_information_2.addWidget(QLabel("[m]"), 2, 6)
        lanelet_information_stop_line_layout.addRow(lanelet_information_2)
        layout_lanelet_information_groupbox.addRow(lanelet_stop_line_groupbox)

        layout_lanelet_adding_groupbox = QFormLayout()
        lanelet_adding_groupbox = QGroupBox()
        lanelet_adding_groupbox.setLayout(layout_lanelet_adding_groupbox)
        layout_lanelet_adding_groupbox.addRow(label_add)
        layout_lanelet_adding_groupbox.addRow(self.curved_lanelet_selection)
        layout_lanelet_adding_groupbox.addRow("Length [m]", self.lanelet_length)
        layout_lanelet_adding_groupbox.addRow("Width [m]", self.lanelet_width)
        layout_lanelet_adding_groupbox.addRow("Curve radius [m]", self.lanelet_radius)
        layout_lanelet_adding_groupbox.addRow("Curve angle [deg]", self.lanelet_angle)
        layout_lanelet_adding_groupbox.addRow("Number Vertices:", self.number_vertices)
        layout_lanelet_adding_groupbox.addRow(self.place_at_defined_position)
        layout_lanelet_adding_groupbox.addRow(self.connect_to_previous_selection)
        layout_lanelet_adding_groupbox.addRow(self.connect_to_predecessors_selection)
        layout_lanelet_adding_groupbox.addRow(self.connect_to_successors_selection)
        layout_lanelet_adding_groupbox.addRow(self.button_add_lanelet)

        layout_lanelet_information.addWidget(lanelet_adding_groupbox)

        layout_lanelet_selection_update = QFormLayout()
        layout_lanelet_selection_update.addRow("Selected lanelet", self.selected_lanelet_update)
        layout_lanelet_selection_update.addRow(self.button_update_lanelet)
        layout_lanelet_selection_update.addRow(self.button_remove_lanelet)
        layout_lanelet_information.addLayout(layout_lanelet_selection_update)

        widget_title = "Lanelet"

        return widget_title, widget_lanelets

    def create_lanelet_operations_widget(self):
        widget_lanelet_operations = QFrame(self.tree)
        layout_lanelet_operations = QVBoxLayout(widget_lanelet_operations)

        self.selected_lanelet_one = QComboBox()
        self.selected_lanelet_two = QComboBox()

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
        self.button_attach_to_other_lanelet = QPushButton("Fit [1] to [2]")
        self.button_connect_lanelets = QPushButton("Connect [1] and [2]")
        self.button_merge_lanelets = QPushButton("Merge [1] with successor")

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
        self.x_translation.setMaximumWidth(45)
        self.x_translation.setValidator(QDoubleValidator())
        self.x_translation.setMaxLength(4)
        self.x_translation.setAlignment(Qt.AlignRight)
        self.translate_x_unit_label = QLabel("[m]")
        self.translate_y_label = QLabel("y:")
        self.y_translation = QLineEdit()
        self.y_translation.setMaximumWidth(45)
        self.y_translation.setValidator(QDoubleValidator())
        self.y_translation.setMaxLength(4)
        self.y_translation.setAlignment(Qt.AlignRight)
        self.translate_y_unit_label = QLabel("[m]")

        lanelet_operations_layout = QFormLayout()
        lanelet_operations_selection_groupbox_layout = QFormLayout()
        lanelet_operations_selection_groupbox = QGroupBox()
        lanelet_operations_selection_groupbox.setLayout(lanelet_operations_selection_groupbox_layout)
        lanelet_operations_selection_groupbox_layout.addRow("[1] Selected lanelet", self.selected_lanelet_one)
        lanelet_operations_selection_groupbox_layout.addRow("[2] Previously selected", self.selected_lanelet_two)
        lanelet_operations_layout.addRow(lanelet_operations_selection_groupbox)

        lanelet_operations_adjacency_groupbox_layout = QFormLayout()
        lanelet_operations_adjacency_groupbox = QGroupBox()
        lanelet_operations_adjacency_groupbox.setLayout(lanelet_operations_adjacency_groupbox_layout)
        lanelet_operations_adjacency_groupbox_layout.addRow(self.create_adjacent_left_selection,
                                                            self.create_adjacent_right_selection)
        lanelet_operations_adjacency_groupbox_layout.addRow(self.create_adjacent_same_direction_selection)
        lanelet_operations_adjacency_groupbox_layout.addRow(self.button_create_adjacent)
        lanelet_operations_layout.addRow(lanelet_operations_adjacency_groupbox)

        lanelet_operations_rotation_groupbox_layout = QGridLayout()
        lanelet_operations_rotation_groupbox = QGroupBox()
        lanelet_operations_rotation_groupbox.setLayout(lanelet_operations_rotation_groupbox_layout)
        lanelet_operations_rotation_groupbox_layout.addWidget(self.button_rotate_lanelet, 0, 0)
        lanelet_operations_rotation_groupbox_layout.addWidget(self.rotation_angle, 0, 1)
        lanelet_operations_rotation_groupbox_layout.addWidget(self.rotation_degree_label, 0, 2)
        lanelet_operations_layout.addRow(lanelet_operations_rotation_groupbox)

        lanelet_operations_translation_groupbox_layout = QGridLayout()
        lanelet_operations_translation_groupbox = QGroupBox()
        lanelet_operations_translation_groupbox.setLayout(lanelet_operations_translation_groupbox_layout)
        lanelet_operations_translation_groupbox_layout.addWidget(self.button_translate_lanelet, 1, 0)
        lanelet_operations_translation_groupbox_layout.addWidget(self.translate_x_label, 1, 1)
        lanelet_operations_translation_groupbox_layout.addWidget(self.x_translation, 1, 2)
        lanelet_operations_translation_groupbox_layout.addWidget(self.translate_x_unit_label, 1, 3)
        lanelet_operations_translation_groupbox_layout.addWidget(self.translate_y_label, 1, 4)
        lanelet_operations_translation_groupbox_layout.addWidget(self.y_translation, 1, 5)
        lanelet_operations_translation_groupbox_layout.addWidget(self.translate_y_unit_label, 1, 6)
        lanelet_operations_layout.addRow(lanelet_operations_translation_groupbox)

        lanelet_operations_layout.addRow(self.button_attach_to_other_lanelet)
        lanelet_operations_layout.addRow(self.button_connect_lanelets)
        lanelet_operations_layout.addRow(self.button_merge_lanelets)
        layout_lanelet_operations.addLayout(lanelet_operations_layout)

        widget_title = "Lanelet Operations"

        return widget_title, widget_lanelet_operations

    def create_traffic_sign_widget(self):
        widget_traffic_sign = QFrame(self.tree)
        layout_traffic_sign = QVBoxLayout(widget_traffic_sign)

        label_general = QLabel("Traffic Sign Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

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
        self.button_add_traffic_sign_element.setMinimumWidth(150)
        self.button_remove_traffic_sign_element = QPushButton("Remove Element")

        self.button_add_traffic_sign = QPushButton("Add")
        self.button_update_traffic_sign = QPushButton("Update")
        self.button_remove_traffic_sign = QPushButton("Remove")

        traffic_sign_layout = QFormLayout()
        traffic_sign_information_layout = QFormLayout()
        traffic_sign_information_groupbox = QGroupBox()
        traffic_sign_information_groupbox.setLayout(traffic_sign_information_layout)
        traffic_sign_information_layout.addRow(label_general)
        traffic_sign_information_layout.addRow("X-Position [m]", self.x_position_traffic_sign)
        traffic_sign_information_layout.addRow("Y-Position [m]", self.y_position_traffic_sign)
        traffic_sign_information_layout.addRow(self.traffic_sign_virtual_selection)
        traffic_sign_information_layout.addRow("Referenced lanelets", self.referenced_lanelets_traffic_sign)
        traffic_sign_information_layout.addRow(self.traffic_sign_element_label)
        traffic_sign_information_layout.addRow(self.traffic_sign_element_table)
        traffic_sign_information_layout.addRow(self.button_add_traffic_sign_element,
                                               self.button_remove_traffic_sign_element)
        traffic_sign_layout.addRow(self.button_add_traffic_sign)
        traffic_sign_layout.addRow("Selected Traffic Sign", self.selected_traffic_sign)
        traffic_sign_layout.addRow(self.button_update_traffic_sign)
        traffic_sign_layout.addRow(self.button_remove_traffic_sign)

        layout_traffic_sign.addWidget(traffic_sign_information_groupbox)
        layout_traffic_sign.addLayout(traffic_sign_layout)

        title_traffic_sign = "Traffic Sign"
        return title_traffic_sign, widget_traffic_sign

    def create_traffic_light_widget(self):
        widget_traffic_light = QFrame(self.tree)
        layout_traffic_light = QVBoxLayout(widget_traffic_light)

        label_general = QLabel("Traffic Light Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

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
        self.button_create_traffic_lights = QPushButton("Create Traffic Lights for Referenced Lanelets")

        self.traffic_light_cycle_order = QComboBox()
        self.traffic_light_cycle_order.addItems(["r-ry-g-y", "g-y-r-ry", "ry-g-y-r", "y-r-ry-g", "r-g", "r-g-in"])

        traffic_light_layout = QFormLayout()
        traffic_light_information_layout = QFormLayout()
        traffic_light_information_groupbox = QGroupBox()
        traffic_light_information_groupbox.setLayout(traffic_light_information_layout)
        traffic_light_information_layout.addRow(label_general)
        traffic_light_information_layout.addRow("X-Position [m]", self.x_position_traffic_light)
        traffic_light_information_layout.addRow("Y-Position [m]", self.y_position_traffic_light)
        traffic_light_information_layout.addRow("Direction", self.traffic_light_directions)
        traffic_light_information_layout.addRow("Time offset", self.time_offset)
        traffic_light_information_layout.addRow("Time red", self.time_red)
        traffic_light_information_layout.addRow("Time red-yellow", self.time_red_yellow)
        traffic_light_information_layout.addRow("Time green", self.time_green)
        traffic_light_information_layout.addRow("Time yellow", self.time_yellow)
        traffic_light_information_layout.addRow("Time inactive", self.time_inactive)
        traffic_light_information_layout.addRow("Cycle order:", self.traffic_light_cycle_order)
        traffic_light_information_layout.addRow("Referenced lanelets", self.referenced_lanelets_traffic_light)
        traffic_light_information_layout.addRow(self.traffic_light_active)
        traffic_light_layout.addRow(self.button_add_traffic_light)
        traffic_light_layout.addRow("Selected traffic light", self.selected_traffic_light)
        traffic_light_layout.addRow(self.button_update_traffic_light)
        traffic_light_layout.addRow(self.button_remove_traffic_light)
        traffic_light_layout.addRow(self.button_create_traffic_lights)

        layout_traffic_light.addWidget(traffic_light_information_groupbox)
        layout_traffic_light.addLayout(traffic_light_layout)
# >>>>>>> develop

        title_traffic_light = "Traffic Light"
        return title_traffic_light, widget_traffic_light

    def create_intersection_widget(self):
        widget_intersection = QFrame(self.tree)
        layout_intersection = QVBoxLayout(widget_intersection)

        label_intersection_templates = QLabel("Intersection Templates")
        label_intersection_templates.setFont(QFont("Arial", 11, QFont.Bold))

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

        self.intersection_with_traffic_signs = QCheckBox("Add Traffic Signs")
        self.intersection_with_traffic_lights = QCheckBox("Add Traffic Lights")

        self.button_three_way_intersection = QPushButton("Add Three-way Intersection")
        self.button_four_way_intersection = QPushButton("Add Four-way Intersection")

        label_update_intersection = QLabel("Add/Update/Remove Intersection")
        label_update_intersection.setFont(QFont("Arial", 11, QFont.Bold))

        self.selected_intersection = QComboBox()

        self.intersection_incomings_label = QLabel("Incomings:")
        self.intersection_incomings_table = QTableWidget()
        self.intersection_incomings_table.setColumnCount(6)
        self.intersection_incomings_table.setHorizontalHeaderLabels(['ID', 'Lanelets', 'Suc. Left', 'Suc. Straight',
                                                                     'Suc. Right', 'Left Of'])
        self.intersection_incomings_table.resizeColumnsToContents()
        self.intersection_incomings_table.setMaximumHeight(175)
        self.button_add_incoming = QPushButton("Add Incoming")
        self.button_add_incoming.setMinimumWidth(135)
        self.button_remove_incoming = QPushButton("Remove Incoming")
        self.intersection_crossings = CheckableComboBox()

        self.button_add_intersection = QPushButton("Add Intersection")
        self.button_remove_intersection = QPushButton("Remove Intersection")
        self.button_update_intersection = QPushButton("Update Intersection")

        label_intersection_fitting = QLabel("Intersection Fitting")
        label_intersection_fitting.setFont(QFont("Arial", 11, QFont.Bold))
        self.intersection_lanelet_to_fit = QComboBox()
        self.other_lanelet_to_fit = QComboBox()
        self.button_fit_intersection = QPushButton("Fit to intersection")
        self.intersection_fitting_groupbox = QGroupBox("Intersection fitting")

        intersection_templates_layout = QFormLayout()
        intersection_template_groupbox = QGroupBox()
        intersection_template_groupbox.setLayout(intersection_templates_layout)
        intersection_templates_layout.addRow(label_intersection_templates)
        intersection_templates_layout.addRow("Diameter [m]:", self.intersection_diameter)
        intersection_templates_layout.addRow("Lanelet Width [m]:", self.intersection_lanelet_width)
        intersection_templates_layout.addRow("Incoming Length [m]:", self.intersection_incoming_length)
        intersection_templates_layout.addRow(self.intersection_with_traffic_signs,
                                             self.intersection_with_traffic_lights)
        intersection_templates_layout.addRow(self.button_three_way_intersection)
        intersection_templates_layout.addRow(self.button_four_way_intersection)
        intersection_templates_layout.addRow(self.button_fit_intersection)
        layout_intersection.addWidget(intersection_template_groupbox)

        intersection_adding_updating_layout = QFormLayout()
        intersection_adding_updating_groupbox = QGroupBox()
        intersection_adding_updating_groupbox.setLayout(intersection_adding_updating_layout)
        intersection_adding_updating_layout.addRow(label_update_intersection)
        intersection_adding_updating_layout.addRow("Selected Intersection:", self.selected_intersection)
        intersection_incoming_layout = QFormLayout()
        intersection_incoming_groupbox = QGroupBox()
        intersection_incoming_groupbox.setLayout(intersection_incoming_layout)
        intersection_incoming_layout.addRow(self.intersection_incomings_label)
        intersection_incoming_layout.addRow(self.intersection_incomings_table)
        intersection_incoming_layout.addRow(self.button_add_incoming, self.button_remove_incoming)
        intersection_adding_updating_layout.addRow(intersection_incoming_groupbox)
        intersection_adding_updating_layout.addRow("Crossing Lanelets:", self.intersection_crossings)
        intersection_adding_updating_layout.addRow(self.button_add_intersection)
        intersection_adding_updating_layout.addRow(self.button_remove_intersection)
        intersection_adding_updating_layout.addRow(self.button_update_intersection)
        intersection_adding_updating_layout.addRow(self.button_fit_intersection)
        layout_intersection.addWidget(intersection_adding_updating_groupbox)

        intersection_fitting_layout = QFormLayout()
        intersection_fitting_groupbox = QGroupBox()
        intersection_fitting_groupbox.setLayout(intersection_fitting_layout)
        intersection_fitting_layout.addRow(label_intersection_fitting)
        intersection_fitting_layout.addRow("Incoming Lanelet:", self.intersection_lanelet_to_fit)
        intersection_fitting_layout.addRow("Preceding Lanelet:", self.other_lanelet_to_fit)
        intersection_fitting_layout.addRow(self.button_fit_intersection)
        layout_intersection.addWidget(intersection_fitting_groupbox)

        title_intersection = "Intersection"
        return title_intersection, widget_intersection
