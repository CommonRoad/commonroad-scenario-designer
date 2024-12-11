from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import CheckableComboBox


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

        self.toolbox.intersection_with_traffic_signs = QCheckBox("Add Traffic Signs")
        self.toolbox.intersection_with_traffic_lights = QCheckBox("Add Traffic Lights")

        self.toolbox.button_three_way_intersection = QPushButton("Add Three-way Intersection")
        self.toolbox.button_four_way_intersection = QPushButton("Add Four-way Intersection")

        label_update_intersection = QLabel("Add/Update/Remove Intersection")
        label_update_intersection.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.toolbox.selected_intersection = QComboBox()

        self.toolbox.intersection_incomings_label = QLabel("Incomings:")
        self.toolbox.intersection_incomings_table = QTableWidget()
        self.toolbox.intersection_incomings_table.setColumnCount(6)
        self.toolbox.intersection_incomings_table.setHorizontalHeaderLabels(
            ["ID", "Lanelets", "Suc. Left", "Suc. Straight", "Suc. Right", "Left Of"]
        )
        self.toolbox.intersection_incomings_table.resizeColumnsToContents()
        self.toolbox.intersection_incomings_table.setMaximumHeight(175)
        self.toolbox.button_add_incoming = QPushButton("Add Incoming")
        self.toolbox.button_add_incoming.setMinimumWidth(135)
        self.toolbox.button_remove_incoming = QPushButton("Remove Incoming")
        self.toolbox.intersection_crossings = CheckableComboBox()

        self.toolbox.button_add_intersection = QPushButton("Add Intersection")
        self.toolbox.button_remove_intersection = QPushButton("Remove Intersection")
        self.toolbox.button_update_intersection = QPushButton("Update Intersection")

        label_intersection_fitting = QLabel("Intersection Fitting")
        label_intersection_fitting.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.toolbox.intersection_lanelet_to_fit = QComboBox()
        self.toolbox.other_lanelet_to_fit = QComboBox()
        self.toolbox.button_fit_intersection = QPushButton("Fit to intersection")
        self.toolbox.intersection_fitting_groupbox = QGroupBox("Intersection fitting")

        intersection_templates_layout = QFormLayout()
        intersection_template_groupbox = QGroupBox()
        intersection_template_groupbox.setLayout(intersection_templates_layout)
        intersection_templates_layout.addRow(label_intersection_templates)
        intersection_templates_layout.addRow("Diameter [m]:", self.toolbox.intersection_diameter)
        intersection_templates_layout.addRow(
            "Lanelet Width [m]:", self.toolbox.intersection_lanelet_width
        )
        intersection_templates_layout.addRow(
            "Incoming Length [m]:", self.toolbox.intersection_incoming_length
        )
        intersection_templates_layout.addRow(
            self.toolbox.intersection_with_traffic_signs,
            self.toolbox.intersection_with_traffic_lights,
        )
        intersection_templates_layout.addRow(self.toolbox.button_three_way_intersection)
        intersection_templates_layout.addRow(self.toolbox.button_four_way_intersection)
        intersection_templates_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_template_groupbox)

        intersection_adding_updating_layout = QFormLayout()
        intersection_adding_updating_groupbox = QGroupBox()
        intersection_adding_updating_groupbox.setLayout(intersection_adding_updating_layout)
        intersection_adding_updating_layout.addRow(label_update_intersection)
        intersection_adding_updating_layout.addRow(
            "Selected Intersection:", self.toolbox.selected_intersection
        )
        intersection_incoming_layout = QFormLayout()
        intersection_incoming_groupbox = QGroupBox()
        intersection_incoming_groupbox.setLayout(intersection_incoming_layout)
        intersection_incoming_layout.addRow(self.toolbox.intersection_incomings_label)
        intersection_incoming_layout.addRow(self.toolbox.intersection_incomings_table)
        intersection_incoming_layout.addRow(
            self.toolbox.button_add_incoming, self.toolbox.button_remove_incoming
        )
        intersection_adding_updating_layout.addRow(intersection_incoming_groupbox)
        intersection_adding_updating_layout.addRow(
            "Crossing Lanelets:", self.toolbox.intersection_crossings
        )
        intersection_adding_updating_layout.addRow(self.toolbox.button_add_intersection)
        intersection_adding_updating_layout.addRow(self.toolbox.button_remove_intersection)
        intersection_adding_updating_layout.addRow(self.toolbox.button_update_intersection)
        intersection_adding_updating_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_adding_updating_groupbox)

        intersection_fitting_layout = QFormLayout()
        intersection_fitting_groupbox = QGroupBox()
        intersection_fitting_groupbox.setLayout(intersection_fitting_layout)
        intersection_fitting_layout.addRow(label_intersection_fitting)
        intersection_fitting_layout.addRow(
            "Incoming Lanelet:", self.toolbox.intersection_lanelet_to_fit
        )
        intersection_fitting_layout.addRow("Preceding Lanelet:", self.toolbox.other_lanelet_to_fit)
        intersection_fitting_layout.addRow(self.toolbox.button_fit_intersection)
        layout_intersection.addWidget(intersection_fitting_groupbox)

        title_intersection = "Intersection"
        return title_intersection, widget_intersection
