from commonroad.scenario.traffic_light import TrafficLightDirection
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox, PositionButton


class TrafficLightWidget:
    """
    Inherits the traffic light widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_traffic_light_widget(self):
        widget_traffic_light = QFrame(self.toolbox.tree)
        layout_traffic_light = QVBoxLayout(widget_traffic_light)

        label_general = QLabel("Traffic Light Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.toolbox.x_position_traffic_light = QLineEdit()
        self.toolbox.x_position_traffic_light.setValidator(QDoubleValidator())
        self.toolbox.x_position_traffic_light.setMaxLength(4)
        self.toolbox.x_position_traffic_light.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.y_position_traffic_light = QLineEdit()
        self.toolbox.y_position_traffic_light.setValidator(QDoubleValidator())
        self.toolbox.y_position_traffic_light.setMaxLength(4)
        self.toolbox.y_position_traffic_light.setAlignment(Qt.AlignmentFlag.AlignRight)

        directions = [e.value for e in TrafficLightDirection]
        self.toolbox.traffic_light_directions = QComboBox()
        self.toolbox.traffic_light_directions.addItems(directions)

        self.toolbox.time_offset = QLineEdit()
        self.toolbox.time_offset.setValidator(QIntValidator())
        self.toolbox.time_offset.setMaxLength(4)
        self.toolbox.time_offset.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.time_red = QLineEdit()
        self.toolbox.time_red.setValidator(QIntValidator())
        self.toolbox.time_red.setMaxLength(4)
        self.toolbox.time_red.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.time_red_yellow = QLineEdit()
        self.toolbox.time_red_yellow.setValidator(QIntValidator())
        self.toolbox.time_red_yellow.setMaxLength(4)
        self.toolbox.time_red_yellow.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.time_yellow = QLineEdit()
        self.toolbox.time_yellow.setValidator(QIntValidator())
        self.toolbox.time_yellow.setMaxLength(4)
        self.toolbox.time_yellow.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.time_green = QLineEdit()
        self.toolbox.time_green.setValidator(QIntValidator())
        self.toolbox.time_green.setMaxLength(4)
        self.toolbox.time_green.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.time_inactive = QLineEdit()
        self.toolbox.time_inactive.setValidator(QIntValidator())
        self.toolbox.time_inactive.setMaxLength(4)
        self.toolbox.time_inactive.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.traffic_light_active = QCheckBox("active")

        self.toolbox.referenced_lanelets_traffic_light = CheckableComboBox()

        self.toolbox.selected_traffic_light = QComboBox()

        self.toolbox.button_add_traffic_light = QPushButton("Add")
        self.toolbox.button_update_traffic_light = QPushButton("Update")
        self.toolbox.button_remove_traffic_light = QPushButton("Remove")
        self.toolbox.button_create_traffic_lights = QPushButton(
            "Create Traffic Lights for Referenced Lanelets"
        )

        self.toolbox.traffic_light_cycle_order = QComboBox()
        self.toolbox.traffic_light_cycle_order.addItems(
            ["r-ry-g-y", "g-y-r-ry", "ry-g-y-r", "y-r-ry-g", "r-g", "r-g-in"]
        )

        traffic_light_layout = QFormLayout()
        traffic_light_information_layout = QFormLayout()
        traffic_light_information_groupbox = QGroupBox()
        traffic_light_information_groupbox.setLayout(traffic_light_information_layout)
        traffic_light_information_layout.addRow(label_general)
        button_traffic_light_position = PositionButton(
            self.toolbox.x_position_traffic_light,
            self.toolbox.y_position_traffic_light,
            self.toolbox,
        )
        traffic_light_position = QGridLayout()
        traffic_light_position.addWidget(QLabel("x: "), 1, 0)
        traffic_light_position.addWidget(self.toolbox.x_position_traffic_light, 1, 1)
        traffic_light_position.addWidget(QLabel("[m]"), 1, 2)
        traffic_light_position.addWidget(QLabel("y:"), 1, 3)
        traffic_light_position.addWidget(self.toolbox.y_position_traffic_light, 1, 4)
        traffic_light_position.addWidget(QLabel("[m]"), 1, 5)
        traffic_light_position.addWidget(button_traffic_light_position, 1, 6)
        traffic_light_information_layout.addRow(traffic_light_position)
        traffic_light_information_layout.addRow("Direction", self.toolbox.traffic_light_directions)
        traffic_light_information_layout.addRow("Time offset", self.toolbox.time_offset)
        traffic_light_information_layout.addRow("Time red", self.toolbox.time_red)
        traffic_light_information_layout.addRow("Time red-yellow", self.toolbox.time_red_yellow)
        traffic_light_information_layout.addRow("Time green", self.toolbox.time_green)
        traffic_light_information_layout.addRow("Time yellow", self.toolbox.time_yellow)
        traffic_light_information_layout.addRow("Time inactive", self.toolbox.time_inactive)
        traffic_light_information_layout.addRow(
            "Cycle order:", self.toolbox.traffic_light_cycle_order
        )
        traffic_light_information_layout.addRow(
            "Referenced lanelets", self.toolbox.referenced_lanelets_traffic_light
        )
        traffic_light_information_layout.addRow(self.toolbox.traffic_light_active)
        traffic_light_layout.addRow(self.toolbox.button_add_traffic_light)
        traffic_light_layout.addRow("Selected traffic light", self.toolbox.selected_traffic_light)
        traffic_light_layout.addRow(self.toolbox.button_update_traffic_light)
        traffic_light_layout.addRow(self.toolbox.button_remove_traffic_light)
        traffic_light_layout.addRow(self.toolbox.button_create_traffic_lights)

        layout_traffic_light.addWidget(traffic_light_information_groupbox)
        layout_traffic_light.addLayout(traffic_light_layout)

        title_traffic_light = "Traffic Light"
        return title_traffic_light, widget_traffic_light
