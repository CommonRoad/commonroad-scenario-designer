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
    QSpinBox,
    QTableWidget,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import PositionButton


class IntersectionsWidget:
    """
    Inherits the intersection widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_intersection_widget(self):
        widget_intersection = QFrame(self.toolbox.tree)
        layout_intersection = QVBoxLayout(widget_intersection)

        label_intersection_templates = QLabel("Intersection Templates")
        label_intersection_templates.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.toolbox.intersection_diameter = QLineEdit()
        self.toolbox.intersection_diameter.setValidator(QIntValidator())
        self.toolbox.intersection_diameter.setMaxLength(2)
        self.toolbox.intersection_diameter.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.intersection_lanelet_width = QLineEdit()
        self.toolbox.intersection_lanelet_width.setValidator(QDoubleValidator())
        self.toolbox.intersection_lanelet_width.setMaxLength(4)
        self.toolbox.intersection_lanelet_width.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.intersection_incoming_length = QLineEdit()
        self.toolbox.intersection_incoming_length.setValidator(QDoubleValidator())
        self.toolbox.intersection_incoming_length.setMaxLength(4)
        self.toolbox.intersection_incoming_length.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.intersection_start_position_x = QLineEdit()
        self.toolbox.intersection_start_position_x.setValidator(self.toolbox.float_validator)
        self.toolbox.intersection_start_position_x.setMaxLength(8)
        self.toolbox.intersection_start_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.intersection_start_position_y = QLineEdit()
        self.toolbox.intersection_start_position_y.setValidator(self.toolbox.float_validator)
        self.toolbox.intersection_start_position_y.setMaxLength(8)
        self.toolbox.intersection_start_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.intersection_start_position_x.setText("0.0")
        self.toolbox.intersection_start_position_y.setText("0.0")

        self.toolbox.button_start_position = PositionButton(
            self.toolbox.intersection_start_position_x, self.toolbox.intersection_start_position_y, self.toolbox
        )
        self.toolbox.intersection_with_traffic_signs = QCheckBox("Add Traffic Signs")
        self.toolbox.intersection_with_traffic_lights = QCheckBox("Add Traffic Lights")

        self.toolbox.button_three_way_intersection = QPushButton("Add Three-way Intersection")
        self.toolbox.button_four_way_intersection = QPushButton("Add Four-way Intersection")

        label_update_intersection = QLabel("Add/Update/Remove Intersection")
        label_update_intersection.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.toolbox.selected_intersection = QComboBox()

        self.toolbox.intersection_incomings_label = QLabel("Incomings:")
        self.toolbox.intersection_incomings_table = QTableWidget()
        self.toolbox.intersection_incomings_table.setColumnCount(5)
        self.toolbox.intersection_incomings_table.setHorizontalHeaderLabels(
            ["ID", "Lanelets", "Out. Left", "Out. Straight", "Out. Right"]
        )
        self.toolbox.intersection_incomings_table.resizeColumnsToContents()
        self.toolbox.intersection_incomings_table.setMaximumHeight(175)
        self.toolbox.button_add_incoming = QPushButton("Add Incoming")
        self.toolbox.button_add_incoming.setMinimumWidth(135)
        self.toolbox.button_remove_incoming = QPushButton("Remove Incoming")

        self.toolbox.intersection_outgoings_label = QLabel("Outgoings:")
        self.toolbox.intersection_outgoings_table = QTableWidget()
        self.toolbox.intersection_outgoings_table.setColumnCount(3)
        self.toolbox.intersection_outgoings_table.setHorizontalHeaderLabels(["ID", "Lanelets", "Inc. Group"])
        self.toolbox.intersection_outgoings_table.resizeColumnsToContents()
        self.toolbox.intersection_outgoings_table.setMaximumHeight(175)
        self.toolbox.button_add_outgoing = QPushButton("Add Outgoing")
        self.toolbox.button_add_outgoing.setMinimumWidth(135)
        self.toolbox.button_remove_outgoing = QPushButton("Remove Outgoing")

        self.toolbox.intersection_crossings_label = QLabel("Crossings:")
        self.toolbox.intersection_crossings_table = QTableWidget()
        self.toolbox.intersection_crossings_table.setColumnCount(4)
        self.toolbox.intersection_crossings_table.setHorizontalHeaderLabels(
            ["ID", "Lanelets", "Inc. Group", "Out. Group"]
        )
        self.toolbox.intersection_crossings_table.resizeColumnsToContents()
        self.toolbox.intersection_crossings_table.setMaximumHeight(175)
        self.toolbox.button_add_crossing = QPushButton("Add Crossing")
        self.toolbox.button_add_crossing.setMinimumWidth(135)
        self.toolbox.button_remove_crossing = QPushButton("Remove Crossing")

        self.toolbox.button_add_intersection = QPushButton("Add Intersection")
        self.toolbox.button_remove_intersection = QPushButton("Remove Intersection")
        self.toolbox.button_update_intersection = QPushButton("Update Intersection")

        label_intersection_fitting = QLabel("Intersection Fitting")
        label_intersection_fitting.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.toolbox.intersection_lanelet_to_fit = QComboBox()
        self.toolbox.other_lanelet_to_fit = QComboBox()
        self.toolbox.button_fit_intersection = QPushButton("Fit to intersection")
        self.toolbox.intersection_fitting_groupbox = QGroupBox("Intersection fitting")

        self.toolbox.button_rotate_intersection = QPushButton("Rotate")
        self.toolbox.button_rotate_intersection.setMinimumWidth(120)
        self.toolbox.intersection_rotation_angle = QSpinBox()
        self.toolbox.intersection_rotation_angle.setMinimum(-180)
        self.toolbox.intersection_rotation_angle.setMaximum(180)

        self.toolbox.intersection_rotate = QGridLayout()
        self.toolbox.intersection_rotate.addWidget(QLabel("angle: "), 1, 0)
        self.toolbox.intersection_rotate.addWidget(self.toolbox.intersection_rotation_angle, 1, 1)
        self.toolbox.intersection_rotate.addWidget(QLabel("[deg]"), 1, 2)

        self.toolbox.button_translate_intersection = QPushButton("Translate")
        self.toolbox.button_translate_intersection.setMinimumWidth(120)
        self.toolbox.intersection_x_translation = QLineEdit()
        self.toolbox.intersection_x_translation.setMaximumWidth(45)
        self.toolbox.intersection_x_translation.setValidator(QDoubleValidator())

        self.toolbox.intersection_y_translation = QLineEdit()
        self.toolbox.intersection_y_translation.setMaximumWidth(45)
        self.toolbox.intersection_y_translation.setValidator(QDoubleValidator())

        self.toolbox.intersection_translate = QGridLayout()
        self.toolbox.intersection_translate.addWidget(QLabel("x: "), 1, 0)
        self.toolbox.intersection_translate.addWidget(self.toolbox.intersection_x_translation, 1, 1)
        self.toolbox.intersection_translate.addWidget(QLabel("y: "), 1, 2)
        self.toolbox.intersection_translate.addWidget(self.toolbox.intersection_y_translation, 1, 3)

        intersection_templates_layout = QFormLayout()
        intersection_template_groupbox = QGroupBox()
        intersection_template_groupbox.setLayout(intersection_templates_layout)
        intersection_templates_layout.addRow(label_intersection_templates)
        intersection_templates_layout.addRow("Diameter [m]:", self.toolbox.intersection_diameter)
        intersection_templates_layout.addRow("Lanelet Width [m]:", self.toolbox.intersection_lanelet_width)
        intersection_templates_layout.addRow("Incoming Length [m]:", self.toolbox.intersection_incoming_length)

        self.toolbox.intersection_start_position = QGridLayout()
        self.toolbox.intersection_start_position.addWidget(QLabel("x: "), 1, 0)
        self.toolbox.intersection_start_position.addWidget(self.toolbox.intersection_start_position_x, 1, 1)
        self.toolbox.intersection_start_position.addWidget(QLabel("[m]"), 1, 2)
        self.toolbox.intersection_start_position.addWidget(QLabel("y:"), 1, 3)
        self.toolbox.intersection_start_position.addWidget(self.toolbox.intersection_start_position_y, 1, 4)
        self.toolbox.intersection_start_position.addWidget(QLabel("[m]"), 1, 5)
        self.toolbox.intersection_start_position.addWidget(self.toolbox.button_start_position, 1, 6)
        intersection_templates_layout.addRow(self.toolbox.intersection_start_position)
        intersection_templates_layout.addRow(
            self.toolbox.intersection_with_traffic_signs, self.toolbox.intersection_with_traffic_lights
        )
        intersection_templates_layout.addRow(
            self.toolbox.intersection_with_traffic_signs, self.toolbox.intersection_with_traffic_lights
        )
        intersection_templates_layout.addRow(self.toolbox.button_three_way_intersection)
        intersection_templates_layout.addRow(self.toolbox.button_four_way_intersection)
        intersection_templates_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_template_groupbox)

        intersection_adding_updating_layout = QFormLayout()
        intersection_adding_updating_groupbox = QGroupBox()
        intersection_adding_updating_groupbox.setLayout(intersection_adding_updating_layout)
        intersection_adding_updating_layout.addRow(label_update_intersection)
        intersection_adding_updating_layout.addRow("Selected Intersection:", self.toolbox.selected_intersection)
        intersection_incoming_layout = QFormLayout()
        intersection_incoming_groupbox = QGroupBox()
        intersection_incoming_groupbox.setLayout(intersection_incoming_layout)
        intersection_incoming_layout.addRow(self.toolbox.intersection_incomings_label)
        intersection_incoming_layout.addRow(self.toolbox.intersection_incomings_table)
        intersection_incoming_layout.addRow(self.toolbox.button_add_incoming, self.toolbox.button_remove_incoming)
        intersection_adding_updating_layout.addRow(intersection_incoming_groupbox)

        intersection_outgoing_layout = QFormLayout()
        intersection_outgoing_groupbox = QGroupBox()
        intersection_outgoing_groupbox.setLayout(intersection_outgoing_layout)
        intersection_outgoing_layout.addRow(self.toolbox.intersection_outgoings_label)
        intersection_outgoing_layout.addRow(self.toolbox.intersection_outgoings_table)
        intersection_outgoing_layout.addRow(self.toolbox.button_add_outgoing, self.toolbox.button_remove_outgoing)
        intersection_adding_updating_layout.addRow(intersection_outgoing_groupbox)

        intersection_crossing_layout = QFormLayout()
        intersection_crossing_groupbox = QGroupBox()
        intersection_crossing_groupbox.setLayout(intersection_crossing_layout)
        intersection_crossing_layout.addRow(self.toolbox.intersection_crossings_label)
        intersection_crossing_layout.addRow(self.toolbox.intersection_crossings_table)
        intersection_crossing_layout.addRow(self.toolbox.button_add_crossing, self.toolbox.button_remove_crossing)
        intersection_adding_updating_layout.addRow(intersection_crossing_groupbox)

        intersection_adding_updating_layout.addRow(self.toolbox.button_add_intersection)
        intersection_adding_updating_layout.addRow(self.toolbox.button_remove_intersection)
        intersection_adding_updating_layout.addRow(self.toolbox.button_update_intersection)
        intersection_adding_updating_layout.addRow(
            self.toolbox.button_rotate_intersection, self.toolbox.intersection_rotate
        )
        intersection_adding_updating_layout.addRow(
            self.toolbox.button_translate_intersection, self.toolbox.intersection_translate
        )
        intersection_adding_updating_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_adding_updating_groupbox)

        intersection_fitting_layout = QFormLayout()
        intersection_fitting_groupbox = QGroupBox()
        intersection_fitting_groupbox.setLayout(intersection_fitting_layout)
        intersection_fitting_layout.addRow(label_intersection_fitting)
        intersection_fitting_layout.addRow("Incoming Lanelet:", self.toolbox.intersection_lanelet_to_fit)
        intersection_fitting_layout.addRow("Preceding Lanelet:", self.toolbox.other_lanelet_to_fit)
        intersection_fitting_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_fitting_groupbox)

        title_intersection = "Intersection"
        return title_intersection, widget_intersection
