from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


class LaneletOperationsWidget:
    """
    Inherits the lanelet operations widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_lanelet_operations_widget(self):
        widget_lanelet_operations = QFrame(self.toolbox.tree)
        layout_lanelet_operations = QVBoxLayout(widget_lanelet_operations)

        self.toolbox.selected_lanelet_one = QComboBox()
        self.toolbox.selected_lanelet_two = QComboBox()

        self.toolbox.adjacent_left_right_button_group = QButtonGroup()
        self.toolbox.create_adjacent_left_selection = QRadioButton("Adjacent left")
        self.toolbox.create_adjacent_left_selection.setChecked(True)
        self.toolbox.adjacent_left_right_button_group.addButton(
            self.toolbox.create_adjacent_left_selection
        )
        self.toolbox.create_adjacent_right_selection = QRadioButton("Adjacent right")
        self.toolbox.create_adjacent_left_selection.setChecked(False)
        self.toolbox.adjacent_left_right_button_group.addButton(
            self.toolbox.create_adjacent_right_selection
        )
        self.toolbox.create_adjacent_same_direction_selection = QCheckBox("Adjacent same direction")
        self.toolbox.create_adjacent_same_direction_selection.setChecked(True)
        self.toolbox.button_create_adjacent = QPushButton("Create adjacent to [1]")
        self.toolbox.button_attach_to_other_lanelet = QPushButton("Fit [1] to [2]")
        self.toolbox.button_connect_lanelets = QPushButton("Connect [1] and [2]")
        self.toolbox.button_merge_lanelets = QPushButton("Merge [1] with successor")

        self.toolbox.button_rotate_lanelet = QPushButton("Rotate")
        self.toolbox.button_rotate_lanelet.setFixedWidth(100)
        self.toolbox.rotation_angle = QSpinBox()
        self.toolbox.rotation_angle.setMinimum(-180)
        self.toolbox.rotation_angle.setMaximum(180)
        self.toolbox.rotation_degree_label = QLabel("[deg]")

        self.toolbox.button_translate_lanelet = QPushButton("Translate")
        self.toolbox.button_translate_lanelet.setFixedWidth(100)
        self.toolbox.translate_x_label = QLabel("x:")
        self.toolbox.x_translation = QLineEdit()
        self.toolbox.x_translation.setMaximumWidth(45)
        self.toolbox.x_translation.setValidator(QDoubleValidator())
        self.toolbox.x_translation.setMaxLength(4)
        self.toolbox.x_translation.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.translate_x_unit_label = QLabel("[m]")
        self.toolbox.translate_y_label = QLabel("y:")
        self.toolbox.y_translation = QLineEdit()
        self.toolbox.y_translation.setMaximumWidth(45)
        self.toolbox.y_translation.setValidator(QDoubleValidator())
        self.toolbox.y_translation.setMaxLength(4)
        self.toolbox.y_translation.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.translate_y_unit_label = QLabel("[m]")

        lanelet_operations_layout = QFormLayout()
        lanelet_operations_selection_groupbox_layout = QFormLayout()
        lanelet_operations_selection_groupbox = QGroupBox()
        lanelet_operations_selection_groupbox.setLayout(
            lanelet_operations_selection_groupbox_layout
        )
        lanelet_operations_selection_groupbox_layout.addRow(
            "[1] Selected lanelet", self.toolbox.selected_lanelet_one
        )
        lanelet_operations_selection_groupbox_layout.addRow(
            "[2] Previously selected", self.toolbox.selected_lanelet_two
        )
        lanelet_operations_layout.addRow(lanelet_operations_selection_groupbox)

        lanelet_operations_adjacency_groupbox_layout = QFormLayout()
        lanelet_operations_adjacency_groupbox = QGroupBox()
        lanelet_operations_adjacency_groupbox.setLayout(
            lanelet_operations_adjacency_groupbox_layout
        )
        lanelet_operations_adjacency_groupbox_layout.addRow(
            self.toolbox.create_adjacent_left_selection,
            self.toolbox.create_adjacent_right_selection,
        )
        lanelet_operations_adjacency_groupbox_layout.addRow(
            self.toolbox.create_adjacent_same_direction_selection
        )
        lanelet_operations_adjacency_groupbox_layout.addRow(self.toolbox.button_create_adjacent)
        lanelet_operations_layout.addRow(lanelet_operations_adjacency_groupbox)

        lanelet_operations_rotation_groupbox_layout = QGridLayout()
        lanelet_operations_rotation_groupbox = QGroupBox()
        lanelet_operations_rotation_groupbox.setLayout(lanelet_operations_rotation_groupbox_layout)
        lanelet_operations_rotation_groupbox_layout.addWidget(
            self.toolbox.button_rotate_lanelet, 0, 0
        )
        lanelet_operations_rotation_groupbox_layout.addWidget(self.toolbox.rotation_angle, 0, 1)
        lanelet_operations_rotation_groupbox_layout.addWidget(
            self.toolbox.rotation_degree_label, 0, 2
        )
        lanelet_operations_layout.addRow(lanelet_operations_rotation_groupbox)

        lanelet_operations_translation_groupbox_layout = QGridLayout()
        lanelet_operations_translation_groupbox = QGroupBox()
        lanelet_operations_translation_groupbox.setLayout(
            lanelet_operations_translation_groupbox_layout
        )
        lanelet_operations_translation_groupbox_layout.addWidget(
            self.toolbox.button_translate_lanelet, 1, 0
        )
        lanelet_operations_translation_groupbox_layout.addWidget(
            self.toolbox.translate_x_label, 1, 1
        )
        lanelet_operations_translation_groupbox_layout.addWidget(self.toolbox.x_translation, 1, 2)
        lanelet_operations_translation_groupbox_layout.addWidget(
            self.toolbox.translate_x_unit_label, 1, 3
        )
        lanelet_operations_translation_groupbox_layout.addWidget(
            self.toolbox.translate_y_label, 1, 4
        )
        lanelet_operations_translation_groupbox_layout.addWidget(self.toolbox.y_translation, 1, 5)
        lanelet_operations_translation_groupbox_layout.addWidget(
            self.toolbox.translate_y_unit_label, 1, 6
        )
        lanelet_operations_layout.addRow(lanelet_operations_translation_groupbox)

        lanelet_operations_layout.addRow(self.toolbox.button_attach_to_other_lanelet)
        lanelet_operations_layout.addRow(self.toolbox.button_connect_lanelets)
        lanelet_operations_layout.addRow(self.toolbox.button_merge_lanelets)
        layout_lanelet_operations.addLayout(lanelet_operations_layout)

        widget_title = "Lanelet Operations"

        # widget_lanelet_operations.setStyleSheet('background-color:rgb(50,50,50)')
        return widget_title, widget_lanelet_operations
