import math

from commonroad.scenario.lanelet import LaneletType, LineMarking, RoadUser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from crdesigner.ui.gui.utilities.toolbox_ui import (
    CheckableComboBox,
    CollapsibleArrowBox,
    CollapsibleCheckBox,
    PositionButton,
)


class LaneletAttributesWidget:
    """
    Inherits the lanelet attributes widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_lanelet_attributes_widget(self):
        widget_lanelet_attributes = QFrame(self.toolbox.tree)
        layout_lanelet_attributes = QVBoxLayout(widget_lanelet_attributes)

        self.toolbox.lanelet_attributes_groupbox = QGroupBox()
        self.toolbox.layout_lanelet_attributes_groupbox = QFormLayout()
        self.toolbox.lanelet_attributes_groupbox.setLayout(
            self.toolbox.layout_lanelet_attributes_groupbox
        )

        self.toolbox.selected_lanelet_update = QComboBox()
        self.toolbox.button_remove_lanelet = QPushButton("Remove")

        self.toolbox.layout_lanelet_attributes_groupbox.addRow(
            "Selected Lanelet", self.toolbox.selected_lanelet_update
        )
        self.toolbox.layout_lanelet_attributes_groupbox.addRow(self.toolbox.button_remove_lanelet)

        self.add_attribute_fields()

        self.toolbox.button_update_lanelet = QPushButton("Update")
        self.toolbox.layout_lanelet_attributes_groupbox.addRow(self.toolbox.button_update_lanelet)

        layout_lanelet_attributes.addWidget(self.toolbox.lanelet_attributes_groupbox)
        self.toolbox.lanelet_attributes_groupbox.setMinimumHeight(1100)

        widget_title = "Lanelet Attributes"

        return widget_title, widget_lanelet_attributes

    def add_attribute_fields(self):
        layout_attributes = QFormLayout()

        self.toolbox.selected_lanelet_start_position_x = QLineEdit()
        self.toolbox.selected_lanelet_start_position_x.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_start_position_x.setMaxLength(8)
        self.toolbox.selected_lanelet_start_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.selected_lanelet_start_position_y = QLineEdit()
        self.toolbox.selected_lanelet_start_position_y.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_start_position_y.setMaxLength(8)
        self.toolbox.selected_lanelet_start_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.selected_button_start_position = PositionButton(
            self.toolbox.selected_lanelet_start_position_x,
            self.toolbox.selected_lanelet_start_position_y,
            self.toolbox,
        )
        self.toolbox.selected_lanelet_start_position = QGridLayout()
        self.toolbox.selected_lanelet_start_position.addWidget(QLabel("x: "), 1, 0)
        self.toolbox.selected_lanelet_start_position.addWidget(
            self.toolbox.selected_lanelet_start_position_x, 1, 1
        )
        self.toolbox.selected_lanelet_start_position.addWidget(QLabel("[m]"), 1, 2)
        self.toolbox.selected_lanelet_start_position.addWidget(QLabel("y:"), 1, 3)
        self.toolbox.selected_lanelet_start_position.addWidget(
            self.toolbox.selected_lanelet_start_position_y, 1, 4
        )
        self.toolbox.selected_lanelet_start_position.addWidget(QLabel("[m]"), 1, 5)
        self.toolbox.selected_lanelet_start_position.addWidget(
            self.toolbox.selected_button_start_position, 1, 6
        )

        self.toolbox.selected_lanelet_end_position_x = QLineEdit()
        self.toolbox.selected_lanelet_end_position_x.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_end_position_x.setMaxLength(8)
        self.toolbox.selected_lanelet_end_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.selected_lanelet_end_position_y = QLineEdit()
        self.toolbox.selected_lanelet_end_position_y.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_end_position_y.setMaxLength(8)
        self.toolbox.selected_lanelet_end_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.selected_button_end_position = PositionButton(
            self.toolbox.selected_lanelet_end_position_x,
            self.toolbox.selected_lanelet_end_position_y,
            self.toolbox,
        )
        self.toolbox.selected_lanelet_end_position = QGridLayout()
        self.toolbox.selected_lanelet_end_position.addWidget(QLabel("x: "), 1, 0)
        self.toolbox.selected_lanelet_end_position.addWidget(
            self.toolbox.selected_lanelet_end_position_x, 1, 1
        )
        self.toolbox.selected_lanelet_end_position.addWidget(QLabel("[m]"), 1, 2)
        self.toolbox.selected_lanelet_end_position.addWidget(QLabel("y:"), 1, 3)
        self.toolbox.selected_lanelet_end_position.addWidget(
            self.toolbox.selected_lanelet_end_position_y, 1, 4
        )
        self.toolbox.selected_lanelet_end_position.addWidget(QLabel("[m]"), 1, 5)
        self.toolbox.selected_lanelet_end_position.addWidget(
            self.toolbox.selected_button_end_position, 1, 6
        )

        self.toolbox.selected_end_position_x_changed = False
        self.toolbox.selected_end_position_y_changed = False
        self.toolbox.selected_lanelet_end_position_x.textChanged.connect(
            self.update_selected_length
        )
        self.toolbox.selected_lanelet_end_position_y.textChanged.connect(
            self.update_selected_length
        )
        self.toolbox.selected_lanelet_start_position_x.textChanged.connect(
            self.update_selected_length
        )
        self.toolbox.selected_lanelet_start_position_y.textChanged.connect(
            self.update_selected_length
        )

        layout_attributes.addRow(self.toolbox.selected_lanelet_start_position)
        layout_attributes.addRow(self.toolbox.selected_lanelet_end_position)

        # Lanelet Length and Width
        self.toolbox.selected_lanelet_length = QLineEdit()
        self.toolbox.selected_lanelet_length.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_length.setMaxLength(5)
        self.toolbox.selected_lanelet_length.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.selected_length_changed = False
        self.toolbox.selected_lanelet_length.textChanged.connect(self.update_selected_end_position)

        self.toolbox.selected_lanelet_width = QLineEdit()
        self.toolbox.selected_lanelet_width.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_width.setMaxLength(5)
        self.toolbox.selected_lanelet_width.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout_attributes.addRow("Length [m]", self.toolbox.selected_lanelet_length)
        layout_attributes.addRow("Width [m]", self.toolbox.selected_lanelet_width)

        # curved lanelet
        self.toolbox.selected_select_direction = QPushButton("Switch Direction")
        self.toolbox.selected_lanelet_radius = QLineEdit()
        self.toolbox.selected_lanelet_radius.setValidator(self.toolbox.float_validator)
        self.toolbox.selected_lanelet_radius.setMaxLength(6)
        self.toolbox.selected_lanelet_radius.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.selected_lanelet_angle = QLineEdit()
        self.toolbox.selected_lanelet_angle.setMaxLength(6)
        self.toolbox.selected_lanelet_angle.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.selected_number_vertices = QLineEdit()
        self.toolbox.selected_number_vertices.setValidator(QIntValidator())
        self.toolbox.selected_number_vertices.setMaxLength(2)
        self.toolbox.selected_number_vertices.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout_curved = QFormLayout()
        layout_curved.addRow(self.toolbox.selected_select_direction)
        layout_curved.addRow("Curve radius [m]", self.toolbox.selected_lanelet_radius)
        layout_curved.addRow("Curve angle [deg]", self.toolbox.selected_lanelet_angle)
        layout_curved.addRow("Number Vertices:", self.toolbox.selected_number_vertices)

        self.toolbox.selected_select_direction.clicked.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.change_direction_of_curve()
        )
        self.toolbox.selected_lanelet_radius.textChanged.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_editable_lanelet()
        )
        self.toolbox.selected_lanelet_angle.textChanged.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_editable_lanelet()
        )
        self.toolbox.selected_curved_checkbox = CollapsibleCheckBox(
            "Curved Lanelet", layout_curved, layout_attributes, 4
        )
        self.toolbox.selected_curved_checkbox.button.clicked.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                self.toolbox.selected_curved_checkbox.isChecked(), False
            )
        )

        self.add_selected_line_markings(layout_attributes)
        self.add_selected_neighboring_fields(layout_attributes)
        self.add_selected_advanced_fields(layout_attributes)

        self.toolbox.attributes_button = CollapsibleArrowBox(
            "Lanelet Attributes",
            layout_attributes,
            self.toolbox.layout_lanelet_attributes_groupbox,
            3,
            self.toolbox.mwindow,
            self.toolbox,
        )

    def add_selected_line_markings(self, layout_attributes):
        line_markings = [e.value for e in LineMarking]

        self.toolbox.selected_line_marking_left = QComboBox()
        self.toolbox.selected_line_marking_left.addItems(line_markings)

        self.toolbox.selected_line_marking_right = QComboBox()
        self.toolbox.selected_line_marking_right.addItems(line_markings)

        layout_line_marking = QFormLayout()

        layout_line_marking.addRow("Left:", self.toolbox.selected_line_marking_left)
        layout_line_marking.addRow("Right:", self.toolbox.selected_line_marking_right)

        # stop line section
        self.toolbox.layout_stop_line = QFormLayout()

        self.toolbox.selected_line_marking_stop_line = QComboBox()
        line_markings_stop_line = [
            e.value
            for e in LineMarking
            if e.value not in [LineMarking.UNKNOWN.value, LineMarking.NO_MARKING.value]
        ]
        self.toolbox.selected_line_marking_stop_line.addItems(line_markings_stop_line)

        self.toolbox.connecting_radio_button_group_selected_stop_line = QButtonGroup()
        self.toolbox.selected_stop_line_beginning = QRadioButton("beginn")
        self.toolbox.selected_stop_line_beginning.setToolTip("beginning")
        self.toolbox.connecting_radio_button_group_selected_stop_line.addButton(
            self.toolbox.selected_stop_line_beginning
        )
        self.toolbox.selected_stop_line_beginning.setChecked(True)
        self.toolbox.selected_stop_line_beginning.clicked.connect(
            lambda: self.adjust_selected_stop_line_position()
        )

        self.toolbox.selected_stop_line_end = QRadioButton("end")
        self.toolbox.connecting_radio_button_group_selected_stop_line.addButton(
            self.toolbox.selected_stop_line_end
        )
        self.toolbox.selected_stop_line_end.clicked.connect(
            lambda: self.adjust_selected_stop_line_position()
        )

        self.toolbox.selected_stop_line_select_position = QRadioButton("select pos")
        self.toolbox.connecting_radio_button_group_selected_stop_line.addButton(
            self.toolbox.selected_stop_line_select_position
        )
        self.toolbox.selected_stop_line_select_position.clicked.connect(
            lambda: self.adjust_selected_stop_line_position()
        )
        self.toolbox.selected_stop_line_select_position.setToolTip("select position")

        self.toolbox.selected_stop_line_position = QGridLayout()
        self.toolbox.selected_stop_line_position.addWidget(
            self.toolbox.selected_stop_line_beginning, 1, 0
        )
        self.toolbox.selected_stop_line_position.addWidget(
            self.toolbox.selected_stop_line_end, 1, 1
        )
        self.toolbox.selected_stop_line_position.addWidget(
            self.toolbox.selected_stop_line_select_position, 1, 2
        )
        self.toolbox.selected_stop_line_select_position_checked_before = False

        self.toolbox.layout_stop_line.addRow(
            "Line marking", self.toolbox.selected_line_marking_stop_line
        )
        self.toolbox.layout_stop_line.addRow(self.toolbox.selected_stop_line_position)

        self.toolbox.selected_stop_line_box = CollapsibleCheckBox(
            "Stop Line", self.toolbox.layout_stop_line, layout_line_marking, 3
        )

        self.toolbox.line_marking_box = CollapsibleArrowBox(
            "Line marking",
            layout_line_marking,
            layout_attributes,
            6,
            self.toolbox.mwindow,
            self.toolbox,
        )

    def adjust_selected_stop_line_position(self):
        if self.toolbox.selected_stop_line_select_position_checked_before:
            self.toolbox.layout_stop_line.removeRow(
                self.toolbox.selected_lanelet_select_stop_line_position
            )
            self.toolbox.button_selected_stop_line_start_position.remove()
            self.toolbox.button_selected_stop_line_end_position.remove()

        if self.toolbox.selected_stop_line_select_position.isChecked():
            self.toolbox.selected_stop_line_start_x = QLineEdit()
            self.toolbox.selected_stop_line_start_x.setValidator(self.toolbox.float_validator)
            self.toolbox.selected_stop_line_start_x.setMaxLength(8)
            self.toolbox.selected_stop_line_start_x.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.toolbox.selected_stop_line_start_y = QLineEdit()
            self.toolbox.selected_stop_line_start_y.setValidator(self.toolbox.float_validator)
            self.toolbox.selected_stop_line_start_y.setMaxLength(8)
            self.toolbox.selected_stop_line_start_y.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.toolbox.selected_stop_line_end_x = QLineEdit()
            self.toolbox.selected_stop_line_end_x.setValidator(self.toolbox.float_validator)
            self.toolbox.selected_stop_line_end_x.setMaxLength(8)
            self.toolbox.selected_stop_line_end_x.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.toolbox.selected_stop_line_end_y = QLineEdit()
            self.toolbox.selected_stop_line_end_y.setValidator(self.toolbox.float_validator)
            self.toolbox.selected_stop_line_end_y.setMaxLength(8)
            self.toolbox.selected_stop_line_end_y.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.toolbox.button_selected_stop_line_start_position = PositionButton(
                self.toolbox.selected_stop_line_start_x,
                self.toolbox.selected_stop_line_start_y,
                self.toolbox,
            )
            self.toolbox.button_selected_stop_line_end_position = PositionButton(
                self.toolbox.selected_stop_line_end_x,
                self.toolbox.selected_stop_line_end_y,
                self.toolbox,
            )

            self.toolbox.selected_lanelet_select_stop_line_position = QGridLayout()
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("Start"), 1, 0)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("x:"), 1, 1)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.selected_stop_line_start_x, 1, 2
            )
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 1, 3)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("y:"), 1, 4)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.selected_stop_line_start_y, 1, 5
            )
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 1, 6)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.button_selected_stop_line_start_position, 1, 7
            )
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("End"), 2, 0)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("x:"), 2, 1)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.selected_stop_line_end_x, 2, 2
            )
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 2, 3)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("y:"), 2, 4)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.selected_stop_line_end_y, 2, 5
            )
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 2, 6)
            self.toolbox.selected_lanelet_select_stop_line_position.addWidget(
                self.toolbox.button_selected_stop_line_end_position, 2, 7
            )

            self.toolbox.layout_stop_line.addRow(
                self.toolbox.selected_lanelet_select_stop_line_position
            )
            self.toolbox.selected_stop_line_select_position_checked_before = True
        else:
            self.toolbox.selected_stop_line_select_position_checked_before = False

    def add_selected_neighboring_fields(self, layout_attributes):
        self.toolbox.selected_predecessors = CheckableComboBox()
        self.toolbox.predecessor_list = []
        for i in range(0, len(self.toolbox.predecessor_list) - 1):
            self.toolbox.selected_predecessors.addItem(self.toolbox.predecessor_list[i])
            item = self.toolbox.selected_predecessors.model().item(i, 0)
            item.setCheckState(Qt.CheckState.Unchecked)

        self.toolbox.selected_successors = CheckableComboBox()
        self.toolbox.successor_list = []
        for i in range(0, len(self.toolbox.successor_list) - 1):
            self.toolbox.selected_successors.addItem(self.toolbox.successor_list[i])
            item = self.toolbox.selected_successors.model().item(i, 0)
            item.setCheckState(Qt.CheckState.Unchecked)

        self.toolbox.selected_adjacent_right = QComboBox()
        self.toolbox.selected_adjacent_right_direction = QButtonGroup()
        self.toolbox.selected_adjacent_right_same_direction = QRadioButton("same direction")
        self.toolbox.selected_adjacent_right_same_direction.setChecked(True)
        self.toolbox.selected_adjacent_right_direction.addButton(
            self.toolbox.selected_adjacent_right_same_direction
        )
        self.toolbox.selected_adjacent_right_opposite_direction = QRadioButton("opposite direct.")
        self.toolbox.selected_adjacent_right_opposite_direction.setToolTip("opposite direction")
        self.toolbox.selected_adjacent_right_opposite_direction.setChecked(False)
        self.toolbox.selected_adjacent_right_direction.addButton(
            self.toolbox.selected_adjacent_right_opposite_direction
        )

        self.toolbox.selected_adjacent_right_direction_line = QGridLayout()
        self.toolbox.selected_adjacent_right_direction_line.addWidget(
            self.toolbox.selected_adjacent_right_same_direction, 1, 0
        )
        self.toolbox.selected_adjacent_right_direction_line.addWidget(
            self.toolbox.selected_adjacent_right_opposite_direction, 1, 1
        )

        self.toolbox.selected_adjacent_left = QComboBox()
        self.toolbox.selected_adjacent_left_direction = QButtonGroup()
        self.toolbox.selected_adjacent_left_same_direction = QRadioButton("same direction")
        self.toolbox.selected_adjacent_left_same_direction.setChecked(True)
        self.toolbox.selected_adjacent_left_direction.addButton(
            self.toolbox.selected_adjacent_left_same_direction
        )
        self.toolbox.selected_adjacent_left_opposite_direction = QRadioButton("opposite direct.")
        self.toolbox.selected_adjacent_left_opposite_direction.setToolTip("opposite direction")
        self.toolbox.selected_adjacent_left_opposite_direction.setChecked(False)
        self.toolbox.selected_adjacent_left_direction.addButton(
            self.toolbox.selected_adjacent_left_opposite_direction
        )

        self.toolbox.selected_adjacent_left_direction_line = QGridLayout()
        self.toolbox.selected_adjacent_left_direction_line.addWidget(
            self.toolbox.selected_adjacent_left_same_direction, 1, 0
        )
        self.toolbox.selected_adjacent_left_direction_line.addWidget(
            self.toolbox.selected_adjacent_left_opposite_direction, 1, 1
        )

        layout_neighboring_lanelets = QFormLayout()

        layout_neighboring_lanelets.addRow("Predecessors:", self.toolbox.selected_predecessors)
        layout_neighboring_lanelets.addRow("Successors:", self.toolbox.selected_successors)
        layout_neighboring_lanelets.addRow("Adjacent Right:", self.toolbox.selected_adjacent_right)
        layout_neighboring_lanelets.addRow(self.toolbox.selected_adjacent_right_direction_line)
        layout_neighboring_lanelets.addRow("Adjacent Left:", self.toolbox.selected_adjacent_left)
        layout_neighboring_lanelets.addRow(self.toolbox.selected_adjacent_left_direction_line)

        self.toolbox.selected_neighboring_lanelets_button = CollapsibleArrowBox(
            "Neighboring Lanelets",
            layout_neighboring_lanelets,
            layout_attributes,
            8,
            self.toolbox.mwindow,
            self.toolbox,
        )

    def add_selected_advanced_fields(self, layout_attributes):
        self.toolbox.selected_road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.toolbox.selected_road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.toolbox.selected_road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.CheckState.Unchecked)

        self.toolbox.selected_road_user_oneway = CheckableComboBox()
        road_user_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_oneway_list) - 1):
            self.toolbox.selected_road_user_oneway.addItem(road_user_oneway_list[i])
            item = self.toolbox.selected_road_user_oneway.model().item(i, 0)
            item.setCheckState(Qt.CheckState.Unchecked)

        self.toolbox.selected_road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.toolbox.selected_road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.toolbox.selected_road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.CheckState.Unchecked)

        self.toolbox.selected_lanelet_type = CheckableComboBox()
        lanelet_type_list = [e.value for e in LaneletType]
        for i in range(0, len(lanelet_type_list) - 1):
            self.toolbox.selected_lanelet_type.addItem(lanelet_type_list[i])

        self.toolbox.selected_lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.toolbox.selected_lanelet_referenced_traffic_sign_ids.addItems(["None"])
        self.toolbox.selected_lanelet_referenced_traffic_light_ids = CheckableComboBox()
        self.toolbox.selected_lanelet_referenced_traffic_light_ids.addItems(["None"])

        layout_advanced = QFormLayout()

        layout_advanced.addRow("Lanelet Types:", self.toolbox.selected_lanelet_type)
        layout_advanced.addRow("Users Oneway:", self.toolbox.selected_road_user_oneway)
        layout_advanced.addRow(
            "Users Bidirectional:", self.toolbox.selected_road_user_bidirectional
        )
        layout_advanced.addRow(
            "Traffic Sign IDs:", self.toolbox.selected_lanelet_referenced_traffic_sign_ids
        )
        layout_advanced.addRow(
            "Traffic Light IDs:", self.toolbox.selected_lanelet_referenced_traffic_light_ids
        )

        self.toolbox.advanced_button = CollapsibleArrowBox(
            "Advanced", layout_advanced, layout_attributes, 10, self.toolbox.mwindow, self.toolbox
        )

    def update_selected_length(self):
        """
        Changes length of selected lanelet when end position is changed or start position is changed.
        """
        if self.toolbox.selected_end_position_x_changed:
            self.toolbox.selected_end_position_x_changed = False
            return
        if self.toolbox.selected_end_position_y_changed:
            self.toolbox.selected_end_position_y_changed = False
            return
        pos = [
            self.toolbox.selected_lanelet_start_position_x.text(),
            self.toolbox.selected_lanelet_start_position_y.text(),
            self.toolbox.selected_lanelet_end_position_x.text(),
            self.toolbox.selected_lanelet_end_position_y.text(),
        ]
        if any("" == v for v in pos) or any("-" == v for v in pos):
            return
        x = float(self.toolbox.selected_lanelet_start_position_x.text().replace(",", ".")) - float(
            self.toolbox.selected_lanelet_end_position_x.text().replace(",", ".")
        )
        y = float(self.toolbox.selected_lanelet_start_position_y.text().replace(",", ".")) - float(
            self.toolbox.selected_lanelet_end_position_y.text().replace(",", ".")
        )
        self.toolbox.selected_length_changed = True
        self.toolbox.selected_lanelet_length.setText(str(math.sqrt(x**2 + y**2)))

    def update_selected_end_position(self):
        """
        Changes end position of selected lanelet when length field is changed ans select end position method is checked.
        """
        if self.toolbox.selected_length_changed:
            self.toolbox.selected_length_changed = False
            return
        if self.toolbox.selected_lanelet_length.text() == "":
            return
        pos = [
            self.toolbox.selected_lanelet_start_position_x.text(),
            self.toolbox.selected_lanelet_start_position_y.text(),
            self.toolbox.selected_lanelet_end_position_x.text(),
            self.toolbox.selected_lanelet_end_position_y.text(),
        ]
        if any("" == v for v in pos) or any("-" == v for v in pos):
            return

        length_new = float(self.toolbox.selected_lanelet_length.text().replace(",", "."))
        x_start = float(self.toolbox.selected_lanelet_start_position_x.text().replace(",", "."))
        y_start = float(self.toolbox.selected_lanelet_start_position_y.text().replace(",", "."))
        x_end = float(self.toolbox.selected_lanelet_end_position_x.text().replace(",", "."))
        y_end = float(self.toolbox.selected_lanelet_end_position_y.text().replace(",", "."))
        length_old = math.sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)

        x = x_start + (1 / length_old * (x_end - x_start) * length_new)
        y = y_start + (1 / length_old * (y_end - y_start) * length_new)

        self.toolbox.selected_end_position_x_changed = True
        self.toolbox.selected_end_position_y_changed = True
        self.toolbox.selected_lanelet_end_position_x.setText(str(x))
        self.toolbox.selected_lanelet_end_position_y.setText(str(y))
