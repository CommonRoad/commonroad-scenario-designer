import math

from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QDoubleValidator, QIntValidator
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

from crdesigner.common.logging import logger
from crdesigner.ui.gui.utilities.toolbox_ui import (
    CheckableComboBox,
    CollapsibleArrowBox,
    CollapsibleCheckBox,
    PositionButton,
)


class AddLaneletWidget:
    """
    Inherits the add_lanelet widget setup
    """

    def __init__(self, toolbox):
        self.toolbox = toolbox

    def create_add_lanelet_widget(self):
        widget_lanelets = QFrame(self.toolbox.tree)
        layout_lanelet_adding = QVBoxLayout(widget_lanelets)

        self.toolbox.connecting_radio_button_group = QButtonGroup()

        # place at position section
        self.toolbox.place_at_position = QRadioButton("Place at position")
        self.toolbox.place_at_position.setChecked(False)
        self.toolbox.connecting_radio_button_group.addButton(self.toolbox.place_at_position)
        font = self.toolbox.place_at_position.font()
        font.setBold(True)
        self.toolbox.place_at_position.setFont(font)

        # connect to previous selection section
        self.toolbox.connect_to_previous_selection = QRadioButton("Connect to previously added")
        self.toolbox.connect_to_previous_selection.setChecked(False)
        self.toolbox.connecting_radio_button_group.addButton(
            self.toolbox.connect_to_previous_selection
        )
        font = self.toolbox.connect_to_previous_selection.font()
        font.setBold(True)
        self.toolbox.connect_to_previous_selection.setFont(font)

        # connect to predecessors selection section
        self.toolbox.connect_to_predecessors_selection = QRadioButton("Connect to predecessors")
        self.toolbox.connect_to_predecessors_selection.setChecked(False)
        self.toolbox.connecting_radio_button_group.addButton(
            self.toolbox.connect_to_predecessors_selection
        )
        font = self.toolbox.connect_to_predecessors_selection.font()
        font.setBold(True)
        self.toolbox.connect_to_predecessors_selection.setFont(font)

        # connect to successors section
        self.toolbox.connect_to_successors_selection = QRadioButton("Connect to successors")
        self.toolbox.connect_to_successors_selection.setChecked(False)
        self.toolbox.connecting_radio_button_group.addButton(
            self.toolbox.connect_to_successors_selection
        )
        font = self.toolbox.connect_to_successors_selection.font()
        font.setBold(True)
        self.toolbox.connect_to_successors_selection.setFont(font)

        self.toolbox.adding_method = ""

        self.toolbox.lanelet_adding_groupbox = QGroupBox()
        self.toolbox.layout_lanelet_adding_groupbox = QFormLayout()
        self.toolbox.lanelet_adding_groupbox.setLayout(self.toolbox.layout_lanelet_adding_groupbox)

        self.toolbox.layout_lanelet_adding_groupbox.addRow(self.toolbox.place_at_position)
        self.toolbox.layout_lanelet_adding_groupbox.addRow(
            self.toolbox.connect_to_previous_selection
        )
        self.toolbox.layout_lanelet_adding_groupbox.addRow(
            self.toolbox.connect_to_predecessors_selection
        )
        self.toolbox.layout_lanelet_adding_groupbox.addRow(
            self.toolbox.connect_to_successors_selection
        )

        # Add button
        self.toolbox.button_add_lanelet = QPushButton("Add")
        self.toolbox.layout_lanelet_adding_groupbox.addRow(self.toolbox.button_add_lanelet)

        # this validator always has the format with a dot as decimal separator
        self.toolbox.float_validator = QDoubleValidator()
        self.toolbox.float_validator.setLocale(QLocale("en_US"))

        layout_lanelet_adding.addWidget(self.toolbox.lanelet_adding_groupbox)
        self.toolbox.lanelet_adding_groupbox.setMinimumHeight(1150)

        widget_title = "Add Lanelet"
        return widget_title, widget_lanelets

    @logger.log
    def adjust_add_sections(self):
        self.remove_adding_method_fields()

        # add groupbox of now selected adding method
        if self.toolbox.place_at_position.isChecked():
            self.toolbox.adding_method = "place_at_position"
            self.init_place_at_position_fields()
        elif self.toolbox.connect_to_previous_selection.isChecked():
            self.toolbox.adding_method = "connect_to_previous_selection"
            self.init_connect_to_previous_added_fields()
        elif self.toolbox.connect_to_predecessors_selection.isChecked():
            self.toolbox.adding_method = "connect_to_predecessors_selection"
            self.init_connect_to_predecessors_selection_fields()
        elif self.toolbox.connect_to_successors_selection.isChecked():
            self.toolbox.adding_method = "connect_to_successors_selection"
            self.init_connect_to_successors_selection_fields()

    def init_place_at_position_fields(self):
        self.toolbox.line1 = QFrame()
        self.toolbox.line1.setFrameShape(QFrame.Shape.HLine)

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(0, self.toolbox.line1)

        self.toolbox.lanelet_start_position_x = QLineEdit()
        self.toolbox.lanelet_start_position_x.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_start_position_x.setMaxLength(8)
        self.toolbox.lanelet_start_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.lanelet_start_position_y = QLineEdit()
        self.toolbox.lanelet_start_position_y.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_start_position_y.setMaxLength(8)
        self.toolbox.lanelet_start_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.lanelet_start_position_x.setText("0.0")
        self.toolbox.lanelet_start_position_y.setText("0.0")

        self.toolbox.button_start_position = PositionButton(
            self.toolbox.lanelet_start_position_x,
            self.toolbox.lanelet_start_position_y,
            self.toolbox,
        )

        self.toolbox.lanelet_start_position = QGridLayout()
        self.toolbox.lanelet_start_position.addWidget(QLabel("x: "), 1, 0)
        self.toolbox.lanelet_start_position.addWidget(self.toolbox.lanelet_start_position_x, 1, 1)
        self.toolbox.lanelet_start_position.addWidget(QLabel("[m]"), 1, 2)
        self.toolbox.lanelet_start_position.addWidget(QLabel("y:"), 1, 3)
        self.toolbox.lanelet_start_position.addWidget(self.toolbox.lanelet_start_position_y, 1, 4)
        self.toolbox.lanelet_start_position.addWidget(QLabel("[m]"), 1, 5)
        self.toolbox.lanelet_start_position.addWidget(self.toolbox.button_start_position, 1, 6)

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            2, self.toolbox.lanelet_start_position
        )

        # radio button group for selecting method of end position
        self.toolbox.connecting_radio_button_group_lanelet_end = QButtonGroup()
        self.toolbox.horizontal = QRadioButton("horizontal")
        self.toolbox.horizontal.setChecked(True)
        self.toolbox.connecting_radio_button_group_lanelet_end.addButton(self.toolbox.horizontal)

        self.toolbox.select_end_position = QRadioButton("select end pos")
        self.toolbox.select_end_position.setChecked(False)
        self.toolbox.connecting_radio_button_group_lanelet_end.addButton(
            self.toolbox.select_end_position
        )
        self.toolbox.select_end_position.setToolTip("select end position")

        self.toolbox.rotate = QRadioButton("rotate")
        self.toolbox.rotate.setChecked(False)
        self.toolbox.connecting_radio_button_group_lanelet_end.addButton(self.toolbox.rotate)

        self.toolbox.horizontal.clicked.connect(lambda: self.adjust_end_position_fields())
        self.toolbox.select_end_position.clicked.connect(lambda: self.adjust_end_position_fields())
        self.toolbox.rotate.clicked.connect(lambda: self.adjust_end_position_fields())
        self.toolbox.end_position_method = ""

        self.toolbox.lanelet_end_position_method = QGridLayout()
        self.toolbox.lanelet_end_position_method.addWidget(self.toolbox.horizontal, 1, 0)
        self.toolbox.lanelet_end_position_method.addWidget(self.toolbox.select_end_position, 1, 1)
        self.toolbox.lanelet_end_position_method.addWidget(self.toolbox.rotate, 1, 2)

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            3, self.toolbox.lanelet_end_position_method
        )

        # Lanelet Length and Width
        self.toolbox.lanelet_length = QLineEdit()
        self.toolbox.lanelet_length.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_length.setMaxLength(5)
        self.toolbox.lanelet_length.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.lanelet_length.textChanged.connect(self.update_end_position)
        self.toolbox.length_changed = False

        self.toolbox.lanelet_width = QLineEdit()
        self.toolbox.lanelet_width.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_width.setMaxLength(5)
        self.toolbox.lanelet_width.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            4, "Length [m]", self.toolbox.lanelet_length
        )
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            5, "Width [m]", self.toolbox.lanelet_width
        )

        self.add_curved_fields(6)
        self.add_line_marking_fields(8)
        self.add_neighboring_lanelets_fields(10)
        self.add_advanced_fields(12)

        # seperation line at the end of place at position block
        self.toolbox.line2 = QFrame()
        self.toolbox.line2.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(14, self.toolbox.line2)

    def adjust_end_position_fields(self):
        self.remove_end_position_method_fields()

        if self.toolbox.horizontal.isChecked():
            self.toolbox.end_position_method = "horizontal"

        elif self.toolbox.select_end_position.isChecked():
            self.toolbox.end_position_method = "select_end_position"
            self.toolbox.lanelet_end_position_x = QLineEdit()
            self.toolbox.lanelet_end_position_x.setValidator(self.toolbox.float_validator)
            self.toolbox.lanelet_end_position_x.setMaxLength(8)
            self.toolbox.lanelet_end_position_x.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.toolbox.lanelet_end_position_y = QLineEdit()
            self.toolbox.lanelet_end_position_y.setValidator(self.toolbox.float_validator)
            self.toolbox.lanelet_end_position_y.setMaxLength(8)
            self.toolbox.lanelet_end_position_y.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.toolbox.button_end_position = PositionButton(
                self.toolbox.lanelet_end_position_x,
                self.toolbox.lanelet_end_position_y,
                self.toolbox,
            )
            self.toolbox.button_end_position.setFlat(True)
            self.toolbox.button_start_position.setAutoFillBackground(True)

            self.toolbox.lanelet_select_end_position = QGridLayout()
            self.toolbox.lanelet_select_end_position.addWidget(QLabel("x: "), 1, 0)
            self.toolbox.lanelet_select_end_position.addWidget(
                self.toolbox.lanelet_end_position_x, 1, 1
            )
            self.toolbox.lanelet_select_end_position.addWidget(QLabel("[m]"), 1, 2)
            self.toolbox.lanelet_select_end_position.addWidget(QLabel("y:"), 1, 3)
            self.toolbox.lanelet_select_end_position.addWidget(
                self.toolbox.lanelet_end_position_y, 1, 4
            )
            self.toolbox.lanelet_select_end_position.addWidget(QLabel("[m]"), 1, 5)
            self.toolbox.lanelet_select_end_position.addWidget(
                self.toolbox.button_end_position, 1, 6
            )

            self.toolbox.layout_lanelet_adding_groupbox.insertRow(
                4, self.toolbox.lanelet_select_end_position
            )

            self.toolbox.curved_check_button.button.setDisabled(True)

            self.toolbox.lanelet_end_position_x.setText("10.0")
            self.toolbox.lanelet_end_position_y.setText("0.0")

            self.toolbox.lanelet_end_position_x.textChanged.connect(self.update_length)
            self.toolbox.lanelet_end_position_y.textChanged.connect(self.update_length)
            self.toolbox.lanelet_start_position_x.textChanged.connect(self.update_length)
            self.toolbox.lanelet_start_position_y.textChanged.connect(self.update_length)
            self.toolbox.end_position_x_changed = False
            self.toolbox.end_position_y_changed = False
        elif self.toolbox.rotate.isChecked():
            self.toolbox.end_position_method = "rotate"
            self.toolbox.rotation_angle_end = QLineEdit()
            rotation_validator = QIntValidator()
            rotation_validator.setRange(-180, 180)
            self.toolbox.rotation_angle_end.setValidator(rotation_validator)
            self.toolbox.rotation_angle_end.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.toolbox.lanelet_rotation = QGridLayout()
            self.toolbox.lanelet_rotation.addWidget(self.toolbox.rotation_angle_end, 1, 0)
            self.toolbox.lanelet_rotation.addWidget(QLabel("[deg]"), 1, 1)
            self.toolbox.layout_lanelet_adding_groupbox.insertRow(4, self.toolbox.lanelet_rotation)

            self.toolbox.rotation_angle_end.setText("90")

        self.toolbox.update_window()

    def update_length(self):
        """
        Changes length of lanelet when end position is changed or start position is changed and select end position
        method is checked.
        """
        if self.toolbox.select_end_position.isChecked():
            # check if function is called from update_end_position and return to prevent infinite loop (is called twice
            # from update_end_position since text of both lanelet_end_position_x and lanelet_end_position_y is changed)
            if self.toolbox.end_position_x_changed:
                self.toolbox.end_position_x_changed = False
                return
            if self.toolbox.end_position_y_changed:
                self.toolbox.end_position_y_changed = False
                return
            pos = [
                self.toolbox.lanelet_start_position_x.text(),
                self.toolbox.lanelet_start_position_y.text(),
                self.toolbox.lanelet_end_position_x.text(),
                self.toolbox.lanelet_end_position_y.text(),
            ]
            if any("" == v for v in pos) or any("-" == v for v in pos):
                return
            x = float(self.toolbox.lanelet_start_position_x.text().replace(",", ".")) - float(
                self.toolbox.lanelet_end_position_x.text().replace(",", ".")
            )
            y = float(self.toolbox.lanelet_start_position_y.text().replace(",", ".")) - float(
                self.toolbox.lanelet_end_position_y.text().replace(",", ".")
            )
            self.toolbox.length_changed = True
            self.toolbox.lanelet_length.setText(str(math.sqrt(x**2 + y**2)))

    def update_end_position(self):
        """
        Changes end position of lanelet when length field is changed ans select end position method is checked.
        """
        if self.toolbox.select_end_position.isChecked():
            # check if function is called from update_length and return to prevent infinite loop
            if self.toolbox.length_changed:
                self.toolbox.length_changed = False
                return
            if self.toolbox.lanelet_length.text() == "":
                return
            pos = [
                self.toolbox.lanelet_start_position_x.text(),
                self.toolbox.lanelet_start_position_y.text(),
                self.toolbox.lanelet_end_position_x.text(),
                self.toolbox.lanelet_end_position_y.text(),
            ]
            if any("" == v for v in pos) or any("-" == v for v in pos):
                return

            length_new = float(self.toolbox.lanelet_length.text().replace(",", "."))
            x_start = float(self.toolbox.lanelet_start_position_x.text().replace(",", "."))
            y_start = float(self.toolbox.lanelet_start_position_y.text().replace(",", "."))
            x_end = float(self.toolbox.lanelet_end_position_x.text().replace(",", "."))
            y_end = float(self.toolbox.lanelet_end_position_y.text().replace(",", "."))
            length_old = math.sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)

            x = x_start + (1 / length_old * (x_end - x_start) * length_new)
            y = y_start + (1 / length_old * (y_end - y_start) * length_new)

            self.toolbox.end_position_x_changed = True
            self.toolbox.end_position_y_changed = True
            self.toolbox.lanelet_end_position_x.setText(str(x))
            self.toolbox.lanelet_end_position_y.setText(str(y))

    def init_connect_to_previous_added_fields(self):
        self.toolbox.line1 = QFrame()
        self.toolbox.line1.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(1, self.toolbox.line1)

        self.toolbox.previous_lanelet = QComboBox()
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            3, "Previous Lanelet", self.toolbox.previous_lanelet
        )

        # Lanelet Length and Width
        self.toolbox.lanelet_length = QLineEdit()
        self.toolbox.lanelet_length.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_length.setMaxLength(5)
        self.toolbox.lanelet_length.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.lanelet_width = QLineEdit()
        self.toolbox.lanelet_width.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_width.setMaxLength(5)
        self.toolbox.lanelet_width.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.lanelet_width.setDisabled(True)
        self.toolbox.lanelet_width.setStyleSheet(
            "background-color: "
            + self.toolbox.mwindow.mwindow_ui.colorscheme().second_background
            + "; color: "
            + self.toolbox.mwindow.mwindow_ui.colorscheme().disabled
        )

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            4, "Length [m]", self.toolbox.lanelet_length
        )
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            5, "Width [m]", self.toolbox.lanelet_width
        )

        self.add_curved_fields(6)
        self.add_line_marking_fields(8)
        self.add_neighboring_lanelets_fields(10)
        self.add_advanced_fields(12)

        # seperation line at the end of place at position block
        self.toolbox.line2 = QFrame()
        self.toolbox.line2.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(14, self.toolbox.line2)

    def init_connect_to_predecessors_selection_fields(self):
        self.toolbox.line1 = QFrame()
        self.toolbox.line1.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(2, self.toolbox.line1)

        self.toolbox.predecessors = CheckableComboBox(self.toolbox)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            4, "Predecessors:", self.toolbox.predecessors
        )

        self.init_length_width()

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            5, "Length [m]", self.toolbox.lanelet_length
        )
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            6, "Width [m]", self.toolbox.lanelet_width
        )

        self.add_curved_fields(7)
        self.add_line_marking_fields(9)
        self.add_neighboring_lanelets_fields(11)
        self.add_advanced_fields(13)

        # seperation line at the end of place at position block
        self.toolbox.line2 = QFrame()
        self.toolbox.line2.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(15, self.toolbox.line2)

    def init_connect_to_successors_selection_fields(self):
        self.toolbox.line1 = QFrame()
        self.toolbox.line1.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(3, self.toolbox.line1)

        self.toolbox.successors = CheckableComboBox()
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            5, "Successors:", self.toolbox.successors
        )

        # Lanelet Length and Width
        self.init_length_width()

        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            6, "Length [m]", self.toolbox.lanelet_length
        )
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(
            7, "Width [m]", self.toolbox.lanelet_width
        )

        self.add_curved_fields(8)
        self.add_line_marking_fields(10)
        self.add_neighboring_lanelets_fields(12)
        self.add_advanced_fields(14)

        # seperation line at the end of place at position block
        self.toolbox.line2 = QFrame()
        self.toolbox.line2.setFrameShape(QFrame.Shape.HLine)
        self.toolbox.layout_lanelet_adding_groupbox.insertRow(16, self.toolbox.line2)

    def remove_adding_method_fields(self):
        if self.toolbox.adding_method == "place_at_position":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line1)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(
                self.toolbox.lanelet_start_position
            )
            self.toolbox.button_start_position.remove()
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(
                self.toolbox.lanelet_end_position_method
            )
            if self.toolbox.end_position_method == "select_end_position":
                self.toolbox.layout_lanelet_adding_groupbox.removeRow(
                    self.toolbox.lanelet_select_end_position
                )
                self.toolbox.button_end_position.remove()
            elif self.toolbox.end_position_method == "rotate":
                self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_rotation)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_length)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_width)
            self.toolbox.curved_check_button.remove()
            self.toolbox.line_marking_box.remove()
            self.toolbox.neighboring_lanelets_button.remove()
            self.toolbox.advanced_button.remove()
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line2)

        elif self.toolbox.adding_method == "connect_to_previous_selection":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line1)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.previous_lanelet)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_length)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_width)
            self.toolbox.curved_check_button.remove()
            # del self.toolbox.curved_check_button
            self.toolbox.line_marking_box.remove()
            self.toolbox.neighboring_lanelets_button.remove()
            self.toolbox.advanced_button.remove()
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line2)

        elif self.toolbox.adding_method == "connect_to_predecessors_selection":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.predecessors)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line1)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_length)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_width)
            self.toolbox.curved_check_button.remove()
            # del self.toolbox.curved_check_button
            self.toolbox.line_marking_box.remove()
            self.toolbox.neighboring_lanelets_button.remove()
            self.toolbox.advanced_button.remove()
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line2)

        elif self.toolbox.adding_method == "connect_to_successors_selection":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.successors)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line1)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_length)
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_width)
            self.toolbox.curved_check_button.remove()
            # del self.toolbox.curved_check_button
            self.toolbox.line_marking_box.remove()
            self.toolbox.neighboring_lanelets_button.remove()
            self.toolbox.advanced_button.remove()
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.line2)

        # TODO: Maybe change
        if self.toolbox.curved_check_button is not None:
            self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                False
            )

    def init_length_width(self):
        self.toolbox.lanelet_length = QLineEdit()
        self.toolbox.lanelet_length.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_length.setMaxLength(5)
        self.toolbox.lanelet_length.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.lanelet_width = QLineEdit()
        self.toolbox.lanelet_width.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_width.setMaxLength(5)
        self.toolbox.lanelet_width.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.toolbox.lanelet_width.setDisabled(True)
        self.toolbox.lanelet_width.setStyleSheet(
            "background-color: "
            + self.toolbox.mwindow.mwindow_ui.colorscheme().second_background
            + "; color: "
            + self.toolbox.mwindow.mwindow_ui.colorscheme().disabled
        )

    def remove_end_position_method_fields(self):
        if self.toolbox.end_position_method == "select_end_position":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(
                self.toolbox.lanelet_select_end_position
            )
            self.toolbox.button_end_position.remove()
            self.toolbox.curved_check_button.button.setDisabled(False)
        elif self.toolbox.end_position_method == "rotate":
            self.toolbox.layout_lanelet_adding_groupbox.removeRow(self.toolbox.lanelet_rotation)

    def add_curved_fields(self, index):
        self.toolbox.select_direction = QPushButton("Switch Direction")
        self.toolbox.lanelet_radius = QLineEdit()
        self.toolbox.lanelet_radius.setValidator(self.toolbox.float_validator)
        self.toolbox.lanelet_radius.setMaxLength(6)
        self.toolbox.lanelet_radius.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.lanelet_angle = QLineEdit()
        self.toolbox.lanelet_angle.setMaxLength(6)
        self.toolbox.lanelet_angle.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toolbox.number_vertices = QLineEdit()
        self.toolbox.number_vertices.setValidator(QIntValidator())
        self.toolbox.number_vertices.setMaxLength(2)
        self.toolbox.number_vertices.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout_curved_box = QFormLayout()

        layout_curved_box.addRow(self.toolbox.select_direction)
        layout_curved_box.addRow("Curve radius [m]", self.toolbox.lanelet_radius)
        layout_curved_box.addRow("Curve angle [deg]", self.toolbox.lanelet_angle)
        layout_curved_box.addRow("Number Vertices:", self.toolbox.number_vertices)

        self.toolbox.lanelet_radius.setText("10.0")
        self.toolbox.lanelet_angle.setText("90.0")
        self.toolbox.number_vertices.setText("20")

        # Signals to update the temporary lanelet when the values changed in the toolbox
        self.toolbox.select_direction.clicked.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.change_direction_of_curve()
        )
        self.toolbox.curved_check_button = CollapsibleCheckBox(
            "Curved Lanelet", layout_curved_box, self.toolbox.layout_lanelet_adding_groupbox, index
        )
        self.toolbox.lanelet_radius.textChanged.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_editable_lanelet()
        )
        self.toolbox.lanelet_angle.textChanged.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.draw_editable_lanelet()
        )
        self.toolbox.curved_check_button.button.clicked.connect(
            lambda: self.toolbox.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.display_curved_lanelet(
                self.toolbox.curved_check_button.isChecked(), True
            )
        )

        if self.toolbox.place_at_position.isChecked():
            self.toolbox.curved_check_button.button.clicked.connect(
                lambda: self.disable_curved_select_end_pos()
            )

    def disable_curved_select_end_pos(self):
        self.toolbox.update_window()
        # disable curved or select end position fields if the other one is selected since selecting both does not
        # make sense
        if self.toolbox.curved_check_button.isChecked():
            self.toolbox.select_end_position.setDisabled(True)
        else:
            self.toolbox.select_end_position.setDisabled(False)

    def add_line_marking_fields(self, index):
        self.toolbox.line_marking_left = QComboBox()
        self.toolbox.line_marking_right = QComboBox()

        layout_line_marking = QFormLayout()

        layout_line_marking.addRow("Left:", self.toolbox.line_marking_left)
        layout_line_marking.addRow("Right:", self.toolbox.line_marking_right)

        # stop line section
        layout_stop_line = QFormLayout()

        self.toolbox.line_marking_stop_line = QComboBox()

        self.toolbox.connecting_radio_button_group_stop_line = QButtonGroup()
        self.toolbox.stop_line_beginning = QRadioButton("beginning")
        self.toolbox.stop_line_beginning.setChecked(True)
        self.toolbox.connecting_radio_button_group_stop_line.addButton(
            self.toolbox.stop_line_beginning
        )

        self.toolbox.stop_line_end = QRadioButton("end")
        self.toolbox.stop_line_end.setChecked(False)
        self.toolbox.connecting_radio_button_group_stop_line.addButton(self.toolbox.stop_line_end)

        self.toolbox.stop_line_position = QGridLayout()
        self.toolbox.stop_line_position.addWidget(self.toolbox.stop_line_beginning, 1, 0)
        self.toolbox.stop_line_position.addWidget(self.toolbox.stop_line_end, 1, 1)

        layout_stop_line.addRow("Line marking", self.toolbox.line_marking_stop_line)
        layout_stop_line.addRow(self.toolbox.stop_line_position)

        self.toolbox.stop_line_check_box = CollapsibleCheckBox(
            "Stop Line", layout_stop_line, layout_line_marking, 3
        )

        self.toolbox.line_marking_box = CollapsibleArrowBox(
            "Line marking",
            layout_line_marking,
            self.toolbox.layout_lanelet_adding_groupbox,
            index,
            self.toolbox.mwindow,
            self.toolbox,
        )

    def add_neighboring_lanelets_fields(self, index):
        self.toolbox.adjacent_right = QComboBox()
        self.toolbox.adjacent_right_direction = QButtonGroup()
        self.toolbox.adjacent_right_same_direction = QRadioButton("same direction")
        self.toolbox.adjacent_right_same_direction.setChecked(True)
        self.toolbox.adjacent_right_direction.addButton(self.toolbox.adjacent_right_same_direction)
        self.toolbox.adjacent_right_same_direction.setToolTip(
            "Driving direction of right adjacent lanelet"
        )
        self.toolbox.adjacent_right_opposite_direction = QRadioButton("opposite direction")
        self.toolbox.adjacent_right_opposite_direction.setChecked(False)
        self.toolbox.adjacent_right_direction.addButton(
            self.toolbox.adjacent_right_opposite_direction
        )
        self.toolbox.adjacent_right_opposite_direction.setToolTip(
            "Driving direction of right adjacent lanelet"
        )

        self.toolbox.adjacent_right_direction_line = QGridLayout()
        self.toolbox.adjacent_right_direction_line.addWidget(
            self.toolbox.adjacent_right_same_direction, 1, 0
        )
        self.toolbox.adjacent_right_direction_line.addWidget(
            self.toolbox.adjacent_right_opposite_direction, 1, 1
        )

        self.toolbox.adjacent_left = QComboBox()
        self.toolbox.adjacent_left_direction = QButtonGroup()
        self.toolbox.adjacent_left_same_direction = QRadioButton("same direction")
        self.toolbox.adjacent_left_same_direction.setChecked(True)
        self.toolbox.adjacent_left_direction.addButton(self.toolbox.adjacent_left_same_direction)
        self.toolbox.adjacent_left_same_direction.setToolTip(
            "Driving direction of left adjacent lanelet"
        )
        self.toolbox.adjacent_left_opposite_direction = QRadioButton("opposite direction")
        self.toolbox.adjacent_left_opposite_direction.setChecked(False)
        self.toolbox.adjacent_left_direction.addButton(
            self.toolbox.adjacent_left_opposite_direction
        )
        self.toolbox.adjacent_left_opposite_direction.setToolTip(
            "Driving direction of left adjacent lanelet"
        )

        self.toolbox.adjacent_left_direction_line = QGridLayout()
        self.toolbox.adjacent_left_direction_line.addWidget(
            self.toolbox.adjacent_left_same_direction, 1, 0
        )
        self.toolbox.adjacent_left_direction_line.addWidget(
            self.toolbox.adjacent_left_opposite_direction, 1, 1
        )

        layout_neighboring_lanelets = QFormLayout()
        if not self.toolbox.connect_to_predecessors_selection.isChecked():
            self.toolbox.predecessors = CheckableComboBox()
            layout_neighboring_lanelets.addRow("Predecessors:", self.toolbox.predecessors)
        if not self.toolbox.connect_to_successors_selection.isChecked():
            self.toolbox.successors = CheckableComboBox()
            layout_neighboring_lanelets.addRow("Successors:", self.toolbox.successors)
        layout_neighboring_lanelets.addRow("Adjacent Right:", self.toolbox.adjacent_right)
        layout_neighboring_lanelets.addRow(self.toolbox.adjacent_right_direction_line)
        layout_neighboring_lanelets.addRow("Adjacent Left:", self.toolbox.adjacent_left)
        layout_neighboring_lanelets.addRow(self.toolbox.adjacent_left_direction_line)

        self.toolbox.neighboring_lanelets_button = CollapsibleArrowBox(
            "Neighboring Lanelets",
            layout_neighboring_lanelets,
            self.toolbox.layout_lanelet_adding_groupbox,
            index,
            self.toolbox.mwindow,
            self.toolbox,
        )

    def add_advanced_fields(self, index):
        self.toolbox.lanelet_type = CheckableComboBox()
        self.toolbox.road_user_oneway = CheckableComboBox()
        self.toolbox.road_user_bidirectional = CheckableComboBox()
        self.toolbox.lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.toolbox.lanelet_referenced_traffic_light_ids = CheckableComboBox()

        layout_advanced = QFormLayout()

        layout_advanced.addRow("Lanelet Types:", self.toolbox.lanelet_type)
        layout_advanced.addRow("Users Oneway:", self.toolbox.road_user_oneway)
        layout_advanced.addRow("Users Bidirectional:", self.toolbox.road_user_bidirectional)
        layout_advanced.addRow(
            "Traffic Sign IDs:", self.toolbox.lanelet_referenced_traffic_sign_ids
        )
        layout_advanced.addRow(
            "Traffic Light IDs:", self.toolbox.lanelet_referenced_traffic_light_ids
        )

        self.toolbox.advanced_button = CollapsibleArrowBox(
            "Advanced",
            layout_advanced,
            self.toolbox.layout_lanelet_adding_groupbox,
            index,
            self.toolbox.mwindow,
            self.toolbox,
        )
