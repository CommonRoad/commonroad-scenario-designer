import math
from typing import Tuple

from commonroad.scenario.scenario import Tag, TimeOfDay, Underground, Weather
from commonroad.scenario.state import InitialState
from commonroad.scenario.traffic_sign import SupportedTrafficSignCountry
from pyparsing import Literal
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from crdesigner.common.config import gui_config
from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox, Toolbox


class ScenarioToolboxUI(Toolbox):
    """
    The UI for the Scenario Toolbox.
    """

    def __init__(self, mwindow):
        """
        Initialize the UI.
        """
        super().__init__(mwindow)
        self.mwindow = mwindow
        self.mwindow_ui = mwindow.mwindow_ui

    def update(self) -> None:
        """Update Scenario Toolbox UI"""
        super(ScenarioToolboxUI, self).update()

    def define_sections(self) -> None:
        """reimplement this to define all your sections and add them as (title, widget) tuples to self.sections"""
        self.sections.append(self.create_planning_problem_overview_widget())
        self.sections.append(self.create_scenario_settings_widget())

    def create_planning_problem_overview_widget(self) -> Tuple[Literal, QFrame]:
        """
        Overview over all planning problems Widgets:
        List with all Planning Problems
        Initial State Attributes of the selected Planning Problem
        Goal States Attributes of the selected Planning Problem
        """
        widget_title = "Planning Problems"
        widget_planning_problem = QFrame(self.tree)
        layout_planning_problem_information = QVBoxLayout(widget_planning_problem)

        layout_planning_problem_groupbox = QFormLayout()
        planning_problem_groupbox = QGroupBox()
        planning_problem_groupbox.setLayout(layout_planning_problem_groupbox)

        label_general = QLabel("Planning Problems")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout_planning_problem_groupbox.addRow(label_general)

        """"Planning Problem List"""
        self.planning_problem_list_label = QLabel("Planning Problems:")
        self.planning_problems_list_table = QTableWidget()
        self.planning_problems_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.planning_problems_list_table_row_count = self.planning_problems_list_table.rowCount()
        self.planning_problems_list_table.setColumnCount(1)
        self.planning_problems_list_table.setHorizontalHeaderLabels(["Planning Problem ID"])
        self.planning_problems_list_table.verticalHeader().hide()
        self.planning_problems_list_table.resizeColumnsToContents()
        self.planning_problems_list_table.setColumnWidth(0, 400)
        self.planning_problems_list_table.setMaximumHeight(150)

        layout_planning_problem_groupbox.addRow(self.planning_problem_list_label)
        layout_planning_problem_groupbox.addRow(self.planning_problems_list_table)

        """Planning Problem Buttons"""
        self.button_add_planning_problems = QPushButton("Add")
        layout_planning_problem_groupbox.addRow(self.button_add_planning_problems)

        self.button_remove_planning_problems = QPushButton("Remove")
        layout_planning_problem_groupbox.addRow(self.button_remove_planning_problems)

        layout_planning_problem_groupbox.addWidget(self.create_initial_state_widget())
        layout_planning_problem_groupbox.addWidget(self.create_goal_states_widget())

        """Add Widgets to overview"""
        layout_planning_problem_information.addWidget(planning_problem_groupbox)

        return widget_title, widget_planning_problem

    def create_scenario_settings_widget(self) -> Tuple[Literal, QFrame]:
        """Creates the scenario settings widget."""
        widget_title = "Scenario Settings"
        widget_scenario_settings = QFrame(self.tree)
        layout_scenario_settings = QVBoxLayout(widget_scenario_settings)

        """Create buttons"""

        self.country = QComboBox()
        country_list = [e.value for e in SupportedTrafficSignCountry]
        self.country.addItems(country_list)

        self.scenario_scene_name = QLineEdit()
        self.scenario_scene_name.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_scene_id = QSpinBox()
        self.scenario_scene_id.setMinimum(1)
        self.scenario_scene_id.setMaximum(999)

        self.scenario_config_id = QSpinBox()
        self.scenario_config_id.setMinimum(1)
        self.scenario_config_id.setMaximum(999)

        self.prediction_type = QComboBox()
        prediction_type_list = ["T", "S", "P"]
        self.prediction_type.addItems(prediction_type_list)

        self.scenario_prediction_id = QSpinBox()
        self.scenario_prediction_id.setMinimum(1)
        self.scenario_prediction_id.setMaximum(999)

        self.cooperative_scenario = QCheckBox("Cooperative Scenario")

        self.scenario_tags = CheckableComboBox()
        tag_list = [e.value for e in Tag]
        self.scenario_tags.addItems(tag_list)

        self.scenario_time_step_size = QLineEdit()
        self.scenario_time_step_size.setMaxLength(4)
        self.scenario_time_step_size.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_author = QLineEdit()
        self.scenario_author.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_affiliation = QLineEdit()
        self.scenario_affiliation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_source = QLineEdit()
        self.scenario_source.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.location_storage_selection = QCheckBox("Store Location")

        self.scenario_geo_name_id = QLineEdit()
        self.scenario_geo_name_id.setValidator(QIntValidator())
        self.scenario_geo_name_id.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_latitude = QLineEdit()
        self.scenario_latitude.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_longitude = QLineEdit()
        self.scenario_longitude.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.scenario_time_of_day = QComboBox()
        time_of_day_list = [e.value for e in TimeOfDay]
        self.scenario_time_of_day.addItems(time_of_day_list)

        self.scenario_weather = QComboBox()
        weather_list = [e.value for e in Weather]
        self.scenario_weather.addItems(weather_list)

        self.scenario_underground = QComboBox()
        underground_list = [e.value for e in Underground]
        self.scenario_underground.addItems(underground_list)

        self.scenario_time_hour = QSpinBox()
        self.scenario_time_hour.setMinimum(0)
        self.scenario_time_hour.setMaximum(23)

        self.scenario_time_minute = QSpinBox()
        self.scenario_time_minute.setMinimum(0)
        self.scenario_time_minute.setMaximum(59)

        self.geo_reference = QComboBox()
        references = [
            gui_config.pseudo_mercator,
            gui_config.utm_default,
            gui_config.lanelet2_default,
            "Enter your own Reference",
        ]
        self.geo_reference.addItems(references)

        self.x_translation = QLineEdit()
        self.x_translation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.y_translation = QLineEdit()
        self.y_translation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.translate_button = QPushButton("Update Scenario")

        """Scenario Settings add Buttons"""
        scenario_settings_groupbox = QGroupBox()

        scenario_information = QFormLayout()
        # scenario_information_groupbox = QGroupBox()
        label_general = QLabel("Scenario Settings")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        scenario_information.addRow(label_general)
        scenario_information.addRow("Country:", self.country)
        scenario_information.addRow("Scene Name:", self.scenario_scene_name)
        scenario_information.addRow("Scene ID:", self.scenario_scene_id)
        scenario_information.addRow("Initial Config ID:", self.scenario_config_id)
        scenario_information.addRow("Prediction Type:", self.prediction_type)
        scenario_information.addRow("Prediction ID:", self.scenario_prediction_id)
        scenario_information.addRow(self.cooperative_scenario)
        scenario_information.addRow("Tags:", self.scenario_tags)
        scenario_information.addRow("Time Step Size:", self.scenario_time_step_size)
        scenario_information.addRow("Author:", self.scenario_author)
        scenario_information.addRow("Affiliation:", self.scenario_affiliation)
        scenario_information.addRow("Source:", self.scenario_source)
        location_groupbox = QGroupBox()
        layout_location_groupbox = QFormLayout()
        location_groupbox.setLayout(layout_location_groupbox)
        layout_location_groupbox.addRow(self.location_storage_selection)
        layout_location_groupbox.addRow("GeoNameID:", self.scenario_geo_name_id)
        layout_location_groupbox.addRow("Latitude:", self.scenario_latitude)
        layout_location_groupbox.addRow("Longitude:", self.scenario_longitude)
        layout_location_groupbox.addRow("Time of Day:", self.scenario_time_of_day)
        layout_location_groupbox.addRow("Weather:", self.scenario_weather)
        layout_location_groupbox.addRow("Underground:", self.scenario_underground)
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time [hh-mm]:"))
        time_layout.addWidget(self.scenario_time_hour)
        time_layout.addWidget(self.scenario_time_minute)
        layout_location_groupbox.addRow(time_layout)

        geo_referencec_groupbox = QGroupBox()
        layout_geo_referencec_groupbox = QFormLayout()
        geo_referencec_groupbox.setLayout(layout_geo_referencec_groupbox)
        layout_geo_referencec_groupbox.addRow("Geo Ref. : ", self.geo_reference)
        layout_geo_referencec_groupbox.addRow("x Translation:", self.x_translation)
        layout_geo_referencec_groupbox.addRow("y Translation:", self.y_translation)
        layout_geo_referencec_groupbox.addRow(self.translate_button)
        layout_location_groupbox.addRow(geo_referencec_groupbox)

        scenario_information.addRow(location_groupbox)

        scenario_settings_groupbox.setLayout(scenario_information)

        layout_scenario_settings.addWidget(scenario_settings_groupbox)

        return widget_title, widget_scenario_settings

    def create_initial_state_widget(self) -> QFrame:
        """
        Create a widget with the following Attributes:
        Position x,y
        Velocity
        Orientation
        YawRate
        SlipAngle
        Time
        Acceleration
        """
        widget_initial_state = QFrame(self.tree)
        layout_initial_state_information = QVBoxLayout(widget_initial_state)

        """
        All Attribute Edits
        """
        layout_initial_state_information_groupbox = QFormLayout()
        initial_state_information_groupbox = QGroupBox()
        initial_state_information_groupbox.setLayout(layout_initial_state_information_groupbox)

        label_general = QLabel("Initial State Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout_initial_state_information_groupbox.addRow(label_general)

        """"Position"""
        self.initial_position_x = QLineEdit()
        self.initial_position_x.setMaxLength(8)
        self.initial_position_x.setFixedWidth(150)
        self.initial_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.initial_position_y = QLineEdit()
        self.initial_position_y.setMaxLength(8)
        self.initial_position_y.setFixedWidth(150)
        self.initial_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)

        lanelet_information_position_layout = QFormLayout()
        lanelet_position_groupbox = QGroupBox()
        lanelet_position_groupbox.setLayout(lanelet_information_position_layout)

        position_information = QGridLayout()
        position_information.addWidget(QLabel("X-Position [m]:"), 1, 0)
        position_information.addWidget(self.initial_position_x, 1, 2)
        position_information.addWidget(QLabel("Y-Position [m]:"), 2, 0)
        position_information.addWidget(self.initial_position_y, 2, 2)

        layout_initial_state_information_groupbox.addRow(position_information)

        """"Velocity"""
        self.initial_velocity = QLineEdit()
        self.initial_velocity.setMaxLength(8)
        self.initial_velocity.setFixedWidth(150)
        self.initial_velocity.setAlignment(Qt.AlignmentFlag.AlignRight)

        velocity_information = QGridLayout()
        velocity_information.addWidget(QLabel("Velocity [m/s]:"), 1, 0)
        velocity_information.addWidget(self.initial_velocity, 1, 2)

        layout_initial_state_information_groupbox.addRow(velocity_information)

        """Orientation"""
        self.initial_orientation = QLineEdit()
        self.initial_orientation.setMaxLength(8)
        self.initial_orientation.setFixedWidth(150)
        self.initial_orientation.setAlignment(Qt.AlignmentFlag.AlignRight)

        orientation_information = QGridLayout()
        orientation_information.addWidget(QLabel("Orientation [deg]:"), 1, 0)
        orientation_information.addWidget(self.initial_orientation, 1, 2)

        layout_initial_state_information_groupbox.addRow(orientation_information)

        """Yaw Rate"""
        self.initial_yawRate = QLineEdit()
        self.initial_yawRate.setMaxLength(8)
        self.initial_yawRate.setFixedWidth(150)
        self.initial_yawRate.setAlignment(Qt.AlignmentFlag.AlignRight)

        yaw_rate_information = QGridLayout()
        yaw_rate_information.addWidget(QLabel("Yaw Rate [deg]:"), 1, 0)
        yaw_rate_information.addWidget(self.initial_yawRate, 1, 2)

        layout_initial_state_information_groupbox.addRow(yaw_rate_information)

        """Slip Angle"""
        self.initial_slipAngle = QLineEdit()
        self.initial_slipAngle.setMaxLength(8)
        self.initial_slipAngle.setFixedWidth(150)
        self.initial_slipAngle.setAlignment(Qt.AlignmentFlag.AlignRight)

        slip_angle_information = QGridLayout()
        slip_angle_information.addWidget(QLabel("Slip Angle [deg]:"), 1, 0)
        slip_angle_information.addWidget(self.initial_slipAngle, 1, 2)

        layout_initial_state_information_groupbox.addRow(slip_angle_information)

        """"Time"""
        self.initial_time = QLineEdit()
        self.initial_time.setValidator(QIntValidator())
        self.initial_time.setMaxLength(8)
        self.initial_time.setFixedWidth(150)
        self.initial_time.setAlignment(Qt.AlignmentFlag.AlignRight)

        time_information = QGridLayout()
        time_information.addWidget(QLabel("Time [s]:"), 1, 0)
        time_information.addWidget(self.initial_time, 1, 2)

        layout_initial_state_information_groupbox.addRow(time_information)

        """Acceleration"""
        self.initial_acceleration = QLineEdit()
        self.initial_acceleration.setMaxLength(8)
        self.initial_acceleration.setFixedWidth(150)
        self.initial_acceleration.setAlignment(Qt.AlignmentFlag.AlignRight)
        acceleration_information = QGridLayout()
        acceleration_information.addWidget(QLabel("Acceleration [m/s2]:"), 1, 0)
        acceleration_information.addWidget(self.initial_acceleration, 1, 2)

        layout_initial_state_information_groupbox.addRow(acceleration_information)

        layout_initial_state_information.addWidget(initial_state_information_groupbox)

        """
        Buttons
        """
        layout_initial_state_selection_buttons = QFormLayout()

        self.button_update_initial_state = QPushButton("Update")
        layout_initial_state_selection_buttons.addRow(self.button_update_initial_state)

        layout_initial_state_information.addLayout(layout_initial_state_selection_buttons)

        return widget_initial_state

    def create_goal_states_widget(self) -> QFrame:
        """
        Create a widget with the following attributes
        Goal States List
        Time
        Velocity
        Orientation
        Position (Rectangle, Circle, Polygon)
        """
        widget_goal_state = QFrame(self.tree)
        layout_goal_state_information = QVBoxLayout(widget_goal_state)

        """
        All Attribute Edits
        """
        self.layout_goal_state_information_groupbox = QFormLayout()
        goal_state_information_groupbox = QGroupBox()
        goal_state_information_groupbox.setLayout(self.layout_goal_state_information_groupbox)
        goal_state_information_groupbox.setFixedHeight(900)
        goal_state_information_groupbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        label_general = QLabel("Goal State Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.layout_goal_state_information_groupbox.insertRow(0, label_general)

        """Goal States List"""
        self.goal_states_list_label = QLabel("Goal States:")
        self.goal_states_list_table = QTableWidget()
        self.goal_states_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.goal_states_list_list_table_row_count = self.goal_states_list_table.rowCount()
        self.goal_states_list_table.setColumnCount(4)
        self.goal_states_list_table.setHorizontalHeaderLabels(
            ["Time", "Position", "Orientation", "Velocity"]
        )
        self.goal_states_list_table.setColumnWidth(0, 80)
        self.goal_states_list_table.setColumnWidth(1, 80)
        self.goal_states_list_table.setColumnWidth(2, 80)
        self.goal_states_list_table.setColumnWidth(3, 80)

        self.layout_goal_state_information_groupbox.insertRow(1, self.goal_states_list_label)
        self.layout_goal_state_information_groupbox.insertRow(2, self.goal_states_list_table)

        """
        Buttons
        """

        self.button_add_goal_state = QPushButton("Add")
        self.layout_goal_state_information_groupbox.insertRow(3, self.button_add_goal_state)

        self.button_remove_goal_state = QPushButton("Remove")
        self.layout_goal_state_information_groupbox.insertRow(4, self.button_remove_goal_state)

        self.button_update_goal_state = QPushButton("Update")
        self.layout_goal_state_information_groupbox.insertRow(5, self.button_update_goal_state)

        """Start & End Time"""
        self.goal_time_start = QLineEdit()
        self.goal_time_start.setValidator(QIntValidator())
        self.goal_time_start.setMaxLength(8)
        self.goal_time_start.setFixedWidth(80)
        self.goal_time_start.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.goal_time_end = QLineEdit()
        self.goal_time_end.setValidator(QIntValidator())
        self.goal_time_end.setMaxLength(8)
        self.goal_time_end.setFixedWidth(80)
        self.goal_time_end.setAlignment(Qt.AlignmentFlag.AlignRight)

        time_information = QGridLayout()
        time_information.setColumnMinimumWidth(1, 110)
        time_information.addWidget(QLabel("Time [s]:"), 1, 1)
        time_information.addWidget(
            self.goal_time_start,
            1,
            2,
        )
        time_information.addWidget(QLabel("-"), 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        time_information.addWidget(self.goal_time_end, 1, 4)

        self.layout_goal_state_information_groupbox.insertRow(6, time_information)

        """Velocity Start & End"""
        self.goal_velocity_start = QLineEdit()
        self.goal_velocity_start.setMaxLength(8)
        self.goal_velocity_start.setFixedWidth(80)
        self.goal_velocity_start.setFixedHeight(24)
        self.goal_velocity_start.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.goal_velocity_end = QLineEdit()
        self.goal_velocity_end.setMaxLength(8)
        self.goal_velocity_end.setFixedWidth(80)
        self.goal_velocity_end.setFixedHeight(24)
        self.goal_velocity_end.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.goal_velocity_selected = QCheckBox()

        velocity_information = QGridLayout()
        velocity_information.setColumnMinimumWidth(1, 110)
        velocity_information.setRowMinimumHeight(1, 10)
        velocity_information.addWidget(self.goal_velocity_selected, 1, 0)
        velocity_information.addWidget(QLabel("Velocity [m/s]:"), 1, 1)
        velocity_information.addWidget(self.goal_velocity_start, 1, 2)
        velocity_information.addWidget(QLabel("-"), 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        velocity_information.addWidget(self.goal_velocity_end, 1, 4)

        self.layout_goal_state_information_groupbox.insertRow(7, velocity_information)

        """Goal Orientation Start & End"""
        self.goal_orientation_start = QLineEdit()
        self.goal_orientation_start.setMaxLength(8)
        self.goal_orientation_start.setFixedWidth(80)
        self.goal_orientation_start.setFixedHeight(24)
        self.goal_orientation_start.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.goal_orientation_end = QLineEdit()
        self.goal_orientation_end.setMaxLength(8)
        self.goal_orientation_end.setFixedWidth(80)
        self.goal_orientation_end.setFixedHeight(24)
        self.goal_orientation_end.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.goal_orientation_selected = QCheckBox()

        orientation_information = QGridLayout()
        orientation_information.setColumnMinimumWidth(1, 110)
        orientation_information.setRowMinimumHeight(1, 10)
        orientation_information.addWidget(self.goal_orientation_selected, 1, 0)
        orientation_information.addWidget(QLabel("Orientation [deg]:"), 1, 1)
        orientation_information.addWidget(self.goal_orientation_start, 1, 2)
        orientation_information.addWidget(QLabel("-"), 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        orientation_information.addWidget(self.goal_orientation_end, 1, 4)

        self.layout_goal_state_information_groupbox.insertRow(8, orientation_information)

        """Position"""
        self.layout_goal_state_information_groupbox.insertRow(9, QLabel("Position:"))

        """Shape Selector"""
        self.type = QComboBox()
        self.type.addItems(["Shape", "Lanelet", "None"])
        lanelet_information_position_layout = QFormLayout()
        lanelet_position_groupbox = QGroupBox()
        lanelet_position_groupbox.setLayout(lanelet_information_position_layout)
        self.layout_goal_state_information_groupbox.insertRow(10, "Type:", self.type)

        layout_goal_state_information.addWidget(goal_state_information_groupbox)

        return widget_goal_state

    def init_goal_state_shape_fields(self) -> None:
        """Initializes the goal state shape fiels."""
        self.goal_states_shape_widget = QWidget()
        self.goal_states_shape_layout = QFormLayout()
        self.goal_states_shape_widget.setLayout(self.goal_states_shape_layout)

        self.goal_states_shape_list_table = QTableWidget()
        self.goal_states_shape_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.goal_states_shape_list_table_row_count = self.goal_states_shape_list_table.rowCount()
        self.goal_states_shape_list_table.setColumnCount(2)
        self.goal_states_shape_list_table.setHorizontalHeaderLabels(["Shape", "Center"])
        self.goal_states_shape_list_table.setColumnWidth(0, 160)
        self.goal_states_shape_list_table.setColumnWidth(1, 160)
        self.goal_states_shape_list_table.setMaximumHeight(150)

        self.goal_states_shape_selector = QComboBox()
        self.goal_states_shape_selector.clear()
        self.goal_states_shape_selector.addItems(["Rectangle", "Circle", "Polygon"])

        self.button_goal_state_position_add_shape = QPushButton("Add")

        self.button_goal_state_position_remove_shape = QPushButton("Remove")

        self.button_goal_state_position_update_shape = QPushButton("Update")

        self.goal_states_shape_layout.addRow(self.goal_states_shape_list_table)
        self.goal_states_shape_layout.addRow(self.button_goal_state_position_add_shape)
        self.goal_states_shape_layout.addRow(self.button_goal_state_position_remove_shape)
        self.goal_states_shape_layout.addRow(self.button_goal_state_position_update_shape)
        self.goal_states_shape_layout.insertRow(
            11, QLabel("Shape:"), self.goal_states_shape_selector
        )

        self.layout_goal_state_information_groupbox.insertRow(12, self.goal_states_shape_widget)

    def remove_goal_state_shape_fields(self) -> None:
        """removes the shape_fields"""
        try:
            self.layout_goal_state_information_groupbox.removeRow(self.goal_states_shape_widget)
        except Exception:
            pass

    def initialize_initial_state(self) -> None:
        """Initializes initial position GUI elements with information."""
        self.initial_position_x.setText("0.0")
        self.initial_position_y.setText("0.0")
        self.initial_velocity.setText("0.0")
        self.initial_orientation.setText("0.0")
        self.initial_yawRate.setText("0.0")
        self.initial_slipAngle.setText("0.0")
        self.initial_time.setText("0")
        self.initial_acceleration.setText("0.0")

    def initialize_goal_state_fields(self) -> None:
        """Initializes the initial goal_state paramters"""
        self.goal_time_start.setText("0")
        self.goal_time_end.setText("0")
        self.goal_velocity_selected.setChecked(False)
        self.goal_velocity_start.setText("0.0")
        self.goal_velocity_end.setText("0.0")
        self.goal_orientation_selected.setChecked(False)
        self.goal_orientation_start.setText("0")
        self.goal_orientation_end.setText("0")
        self.type.setCurrentText("None")

    def set_initial_state_information(self, initial_state: InitialState) -> None:
        """updates initial state widget with data from the selected planning problem

        :param initial_state: InitialState of the pps"""
        if initial_state.has_value("position"):
            self.initial_position_x.setText(str(initial_state.position[0]))
            self.initial_position_y.setText(str(initial_state.position[1]))
        if initial_state.has_value("velocity"):
            self.initial_velocity.setText(str(initial_state.velocity))
        if initial_state.has_value("orientation"):
            self.initial_orientation.setText(str(math.degrees(initial_state.orientation)))
        if initial_state.has_value("yaw_rate"):
            self.initial_yawRate.setText(str(initial_state.yaw_rate))
        if initial_state.has_value("slip_angle"):
            self.initial_slipAngle.setText(str(initial_state.slip_angle))
        if initial_state.has_value("time_step"):
            self.initial_time.setText(str(initial_state.time_step))
        if initial_state.has_value("acceleration"):
            self.initial_acceleration.setText(str(initial_state.acceleration))

    def init_goal_state_lanelet_fields(self) -> None:
        """Lanelet selection"""
        self.goal_states_lanelet_widget = QWidget()
        self.goal_states_lanelet_layout = QFormLayout()
        self.goal_states_lanelet_widget.setLayout(self.goal_states_lanelet_layout)

        self.goal_states_lanelet_list_table = QTableWidget()
        self.goal_states_lanelet_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.goal_states_lanelet_list_table_row_count = (
            self.goal_states_lanelet_list_table.rowCount()
        )
        self.goal_states_lanelet_list_table.setColumnCount(1)
        self.goal_states_lanelet_list_table.setHorizontalHeaderLabels(["Lanelet"])
        self.goal_states_lanelet_list_table.setColumnWidth(0, 350)
        # self.goal_states_lanelet_list_table.setMinimumHeight(150)

        self.button_goal_state_position_remove_lanelet = QPushButton("Remove")

        self.goal_state_position_lanelet_update = QComboBox()
        self.goal_state_position_lanelet_update.clear()
        self.goal_state_position_lanelet_update.setFixedWidth(150)

        self.button_goal_state_position_add_lanelet = QPushButton("Add")
        self.button_goal_state_position_add_lanelet.setFixedWidth(80)

        self.goal_states_lanelet_layout.addRow(self.goal_states_lanelet_list_table)
        self.goal_states_lanelet_layout.addRow(self.button_goal_state_position_remove_lanelet)

        layout_goal_states_lanelet_layout_add = QGridLayout()
        layout_goal_states_lanelet_layout_add.addWidget(
            self.goal_state_position_lanelet_update, 1, 1
        )
        layout_goal_states_lanelet_layout_add.addWidget(
            self.button_goal_state_position_add_lanelet, 1, 2
        )
        goal_states_lanelet_add_widget = QWidget()
        goal_states_lanelet_add_widget.setLayout(layout_goal_states_lanelet_layout_add)
        self.goal_states_lanelet_layout.addRow(goal_states_lanelet_add_widget)

        self.layout_goal_state_information_groupbox.insertRow(11, self.goal_states_lanelet_widget)

    def remove_goal_state_lanelet_fields(self) -> None:
        """Removes the Lanelet fields"""
        try:
            self.layout_goal_state_information_groupbox.removeRow(self.goal_states_lanelet_widget)
        except Exception:
            pass

    def toggle_goal_state_position_type(self) -> None:
        """Toggles the widgets depending on the selected goal state position"""
        if self.type.currentText() == "Shape":
            self.remove_goal_state_shape_fields()
            self.remove_goal_state_lanelet_fields()

            self.init_goal_state_shape_fields()

        elif self.type.currentText() == "Lanelet":
            self.remove_goal_state_shape_fields()
            self.remove_goal_state_lanelet_fields()

            self.init_goal_state_lanelet_fields()

        elif self.type.currentText() == "None":
            self.remove_goal_state_shape_fields()
            self.remove_goal_state_lanelet_fields()

    def init_rectangle_fields(self) -> None:
        """Adds the Rectangle Shape fields"""
        self.rectangle_length = QLineEdit()
        self.rectangle_length.setMaxLength(8)
        self.rectangle_length.setFixedWidth(50)
        self.rectangle_length.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rectangle_width = QLineEdit()
        self.rectangle_width.setMaxLength(8)
        self.rectangle_width.setFixedWidth(50)
        self.rectangle_width.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rectangle_x = QLineEdit()
        self.rectangle_x.setMaxLength(8)
        self.rectangle_x.setFixedWidth(50)
        self.rectangle_x.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rectangle_y = QLineEdit()
        self.rectangle_y.setMaxLength(8)
        self.rectangle_y.setFixedWidth(50)
        self.rectangle_y.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rectangle_orientation = QLineEdit()
        self.rectangle_orientation.setMaxLength(8)
        self.rectangle_orientation.setFixedWidth(50)
        self.rectangle_orientation.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.rectangle_widget = QWidget()
        position_information_rec = QGridLayout()
        position_information_rec.addWidget(QLabel("Length:"), 1, 1)
        position_information_rec.addWidget(self.rectangle_length, 1, 2)
        position_information_rec.addWidget(QLabel("[m]"), 1, 3)
        position_information_rec.addWidget(QLabel("Width:"), 1, 4)
        position_information_rec.addWidget(self.rectangle_width, 1, 5)
        position_information_rec.addWidget(QLabel("[m]"), 1, 6)
        position_information_rec.addWidget(QLabel("X:"), 2, 1)
        position_information_rec.addWidget(self.rectangle_x, 2, 2)
        position_information_rec.addWidget(QLabel("[m]"), 2, 3)
        position_information_rec.addWidget(QLabel("Y:"), 2, 4)
        position_information_rec.addWidget(self.rectangle_y, 2, 5)
        position_information_rec.addWidget(QLabel("[m]"), 2, 6)
        label_orientation = QLabel("Orientation:")
        label_orientation.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        position_information_rec.addWidget(label_orientation, 3, 1, 3, 4)
        position_information_rec.addWidget(self.rectangle_orientation, 3, 5)
        position_information_rec.addWidget(QLabel("[deg]"), 3, 6)
        self.rectangle_widget.setLayout(position_information_rec)
        self.layout_goal_state_information_groupbox.insertRow(12, self.rectangle_widget)

    def remove_rectangle_fields(self) -> None:
        """Removes the Rectangle Shape fields"""
        try:
            self.layout_goal_state_information_groupbox.removeRow(self.rectangle_widget)
        except Exception:
            pass

    def init_circle_fields(self) -> None:
        """Adds the Circle Fields"""
        self.circle_radius = QLineEdit()
        self.circle_radius.setMaxLength(8)
        self.circle_radius.setFixedWidth(50)
        self.circle_radius.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.circle_x = QLineEdit()
        self.circle_x.setMaxLength(8)
        self.circle_x.setFixedWidth(50)
        self.circle_x.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.circle_y = QLineEdit()
        self.circle_y.setMaxLength(8)
        self.circle_y.setFixedWidth(50)
        self.circle_y.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.circle_widget = QWidget()
        position_information_circle = QGridLayout()
        position_information_circle.addWidget(QLabel("Radius:"), 1, 1)
        position_information_circle.addWidget(self.circle_radius, 1, 5)
        position_information_circle.addWidget(QLabel("[m]"), 1, 6)
        position_information_circle.addWidget(QLabel("X:"), 2, 1)
        position_information_circle.addWidget(self.circle_x, 2, 2)
        position_information_circle.addWidget(QLabel("[m]"), 2, 3)
        position_information_circle.addWidget(QLabel("Y:"), 2, 4)
        position_information_circle.addWidget(self.circle_y, 2, 5)
        position_information_circle.addWidget(QLabel("[m]"), 2, 6)
        self.circle_widget.setLayout(position_information_circle)

        self.layout_goal_state_information_groupbox.insertRow(12, self.circle_widget)

    def remove_circle_fields(self) -> None:
        """Removes the Circle Shape fields"""
        try:
            self.layout_goal_state_information_groupbox.removeRow(self.circle_widget)
        except Exception:
            pass

    def init_polygon_fields(self) -> None:
        """Polygon Points"""
        self.vertices_x = []
        self.vertices_y = []
        self.polygon_row = []
        self.remove_vertice_btn = []
        self.polygon_label = []
        self.amount_vertices = 0

        for i in range(3):
            self.add_vertice()

        self.add_vertice_btn = QPushButton("Add Vertice")
        self.add_vertice_btn.clicked.connect(lambda: self.add_vertice())
        self.layout_goal_state_information_groupbox.insertRow(12, self.add_vertice_btn)

    def remove_polygon_fields(self) -> None:
        """Removes the Polygon Shape fields"""
        try:
            for i in range(self.amount_vertices):
                self.layout_goal_state_information_groupbox.removeRow(self.polygon_row[i])

            self.layout_goal_state_information_groupbox.removeRow(self.add_vertice_btn)
        except Exception:
            pass

    def toggle_sections_shape(self) -> None:
        """Show selected shape widget"""
        if self.goal_states_shape_selector.currentText() == "Rectangle":
            self.remove_rectangle_fields()
            self.remove_circle_fields()
            self.remove_polygon_fields()

            self.init_rectangle_fields()

        elif self.goal_states_shape_selector.currentText() == "Circle":
            self.remove_rectangle_fields()
            self.remove_circle_fields()
            self.remove_polygon_fields()

            self.init_circle_fields()

        elif self.goal_states_shape_selector.currentText() == "Polygon":
            self.remove_rectangle_fields()
            self.remove_circle_fields()
            self.remove_polygon_fields()

            self.init_polygon_fields()

    def add_vertice(self) -> None:
        """Add vertices for the polygon shape, i is the place in the array"""
        i = len(self.vertices_x)
        self.polygon_row.append(QHBoxLayout())

        self.polygon_label.append(QLabel("Vertice " + str(i)))

        self.vertices_x.append(QLineEdit())
        self.vertices_x[i].setMaxLength(6)
        self.vertices_x[i].setAlignment(Qt.AlignmentFlag.AlignRight)

        self.vertices_y.append(QLineEdit())
        self.vertices_y[i].setMaxLength(6)
        self.vertices_y[i].setAlignment(Qt.AlignmentFlag.AlignRight)

        self.polygon_row[i].addWidget(self.polygon_label[i])
        self.polygon_row[i].addWidget(self.vertices_x[i])
        self.polygon_row[i].addWidget(self.vertices_y[i])

        self.remove_vertice_btn.append(QPushButton())
        self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))

        self.remove_vertice_btn[i].clicked.connect(lambda: self.remove_vertice())
        self.polygon_row[i].addWidget(self.remove_vertice_btn[i])

        self.layout_goal_state_information_groupbox.insertRow(i + 13, self.polygon_row[i])
        self.amount_vertices = self.amount_vertices + 1

    def remove_vertice(self, i: int = -1) -> None:
        """
        Removes one vertice field

        :param i: index of vertice to be removed
        """
        if len(self.vertices_x) <= 3:
            print("At least 3 vertices are needed to create a polygon")
            return

        if i == -1:
            sending_button = self.sender()
            i = self.remove_vertice_btn.index(sending_button)

        self.layout_goal_state_information_groupbox.removeRow(self.polygon_row[i])
        self.vertices_x.pop(i)
        self.vertices_y.pop(i)
        self.remove_vertice_btn.pop(i)
        self.polygon_label.pop(i)
        self.polygon_row.pop(i)
        self.amount_vertices = self.amount_vertices - 1

        for j in range(self.amount_vertices):
            self.polygon_label[j].setText("Vertice " + str(j))

    def update_window(self):
        super().update_window()
