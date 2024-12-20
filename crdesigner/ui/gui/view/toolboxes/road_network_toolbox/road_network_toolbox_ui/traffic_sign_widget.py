from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont
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
    QTableWidget,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox, PositionButton


class TrafficSignWidget:
    """
    Inherits the traffic_sign widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_traffic_sign_widget(self):
        widget_traffic_sign = QFrame(self.toolbox.tree)
        layout_traffic_sign = QVBoxLayout(widget_traffic_sign)

        label_general = QLabel("Traffic Sign Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.toolbox.x_position_traffic_sign = QLineEdit()
        self.toolbox.x_position_traffic_sign.setValidator(QDoubleValidator())
        self.toolbox.x_position_traffic_sign.setMaxLength(4)
        self.toolbox.x_position_traffic_sign.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.y_position_traffic_sign = QLineEdit()
        self.toolbox.y_position_traffic_sign.setValidator(QDoubleValidator())
        self.toolbox.y_position_traffic_sign.setMaxLength(4)
        self.toolbox.y_position_traffic_sign.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.traffic_sign_virtual_selection = QCheckBox("virtual")

        self.toolbox.selected_traffic_sign = QComboBox()

        self.toolbox.referenced_lanelets_traffic_sign = CheckableComboBox()

        self.toolbox.traffic_sign_element_label = QLabel("Traffic Sign Elements:")
        self.toolbox.traffic_sign_element_table = QTableWidget()
        self.toolbox.traffic_sign_element_table.setColumnCount(2)
        self.toolbox.traffic_sign_element_table.setHorizontalHeaderLabels(
            ["Traffic Sign ID", "Additional Value"]
        )
        self.toolbox.traffic_sign_element_table.resizeColumnsToContents()
        self.toolbox.traffic_sign_element_table.setColumnWidth(0, 180)
        self.toolbox.traffic_sign_element_table.setMaximumHeight(100)
        self.toolbox.button_add_traffic_sign_element = QPushButton("Add Element")
        self.toolbox.button_add_traffic_sign_element.setMinimumWidth(150)
        self.toolbox.button_remove_traffic_sign_element = QPushButton("Remove Element")

        self.toolbox.button_add_traffic_sign = QPushButton("Add")
        self.toolbox.button_update_traffic_sign = QPushButton("Update")
        self.toolbox.button_remove_traffic_sign = QPushButton("Remove")

        traffic_sign_layout = QFormLayout()
        traffic_sign_information_layout = QFormLayout()
        traffic_sign_information_groupbox = QGroupBox()
        traffic_sign_information_groupbox.setLayout(traffic_sign_information_layout)
        traffic_sign_information_layout.addRow(label_general)

        button_traffic_sign_position = PositionButton(
            self.toolbox.x_position_traffic_sign, self.toolbox.y_position_traffic_sign, self.toolbox
        )
        traffic_sign_position = QGridLayout()
        traffic_sign_position.addWidget(QLabel("x: "), 1, 0)
        traffic_sign_position.addWidget(self.toolbox.x_position_traffic_sign, 1, 1)
        traffic_sign_position.addWidget(QLabel("[m]"), 1, 2)
        traffic_sign_position.addWidget(QLabel("y:"), 1, 3)
        traffic_sign_position.addWidget(self.toolbox.y_position_traffic_sign, 1, 4)
        traffic_sign_position.addWidget(QLabel("[m]"), 1, 5)
        traffic_sign_position.addWidget(button_traffic_sign_position, 1, 6)

        traffic_sign_information_layout.addRow(traffic_sign_position)

        traffic_sign_information_layout.addRow(self.toolbox.traffic_sign_virtual_selection)
        traffic_sign_information_layout.addRow(
            "Referenced lanelets", self.toolbox.referenced_lanelets_traffic_sign
        )
        traffic_sign_information_layout.addRow(self.toolbox.traffic_sign_element_label)
        traffic_sign_information_layout.addRow(self.toolbox.traffic_sign_element_table)
        traffic_sign_information_layout.addRow(
            self.toolbox.button_add_traffic_sign_element,
            self.toolbox.button_remove_traffic_sign_element,
        )
        traffic_sign_layout.addRow(self.toolbox.button_add_traffic_sign)
        traffic_sign_layout.addRow("Selected Traffic Sign", self.toolbox.selected_traffic_sign)
        traffic_sign_layout.addRow(self.toolbox.button_update_traffic_sign)
        traffic_sign_layout.addRow(self.toolbox.button_remove_traffic_sign)

        layout_traffic_sign.addWidget(traffic_sign_information_groupbox)
        layout_traffic_sign.addLayout(traffic_sign_layout)

        title_traffic_sign = "Traffic Sign"
        return title_traffic_sign, widget_traffic_sign
