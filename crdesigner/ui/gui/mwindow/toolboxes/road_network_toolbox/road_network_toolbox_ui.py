from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import math

from crdesigner.ui.gui.mwindow.service_layer.services.waitingspinnerwidget import QtWaitingSpinner
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import Toolbox, CheckableComboBox, CollapsibleArrowBox, CollapsibleCheckBox, PositionButton

from commonroad.scenario.lanelet import LaneletType, RoadUser, LineMarking
from commonroad.scenario.traffic_light import TrafficLightDirection


class RoadNetworkToolboxUI(Toolbox):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
        """
    def __init__(self, mwindow):
        super().__init__(mwindow)
        self.curved_check_button = None
        self.select_end_position = None
        self.end_position_method = None
        self.lanelet_width = None

    def update(self) -> None:
        super(RoadNetworkToolboxUI, self).update()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        self.sections.append(self.create_add_lanelet_widget())
        self.sections.append(self.create_lanelet_attributes_widget())
        self.sections.append(self.create_lanelet_operations_widget())
        self.sections.append(self.create_traffic_sign_widget())
        self.sections.append(self.create_traffic_light_widget())
        self.sections.append(self.create_intersection_widget())
        self.sections.append(self.create_aerial_image_widget())

    def create_aerial_image_widget(self):
        """
        create the Add aerial image widget
        """
        widget_aerial = QFrame(self.tree)
        layout_aerial_image = QVBoxLayout(widget_aerial)
        label_general = QLabel("Aerial map Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))


        # GroupBox
        self.aerial_image_groupbox = QGroupBox()
        self.layout_aerial_image_groupbox = QFormLayout()
        self.aerial_image_groupbox.setLayout(self.layout_aerial_image_groupbox)
        self.layout_aerial_image_groupbox.addRow(label_general)

        # Add button
        self.button_add_aerial_image = QPushButton("Add")
        # Remove button
        self.button_remove_aerial_image = QPushButton("Remove")

        connecting_radio_button_group_aerial = QButtonGroup()
        self.bing_selection = QRadioButton("Bing maps")
        self.bing_selection.setChecked(True)
        connecting_radio_button_group_aerial.addButton(self.bing_selection)

        self.ldbv_selection = QRadioButton("LDBV maps")
        connecting_radio_button_group_aerial.addButton(self.ldbv_selection)

        self.aerial_selection = QGridLayout()
        self.aerial_selection.addWidget(self.bing_selection, 1, 0)
        self.aerial_selection.addWidget(self.ldbv_selection, 1, 1)

        self.layout_aerial_image_groupbox.addRow(self.aerial_selection)


        validator_latitude = QDoubleValidator(-90.0, 90.0, 1000)
        validator_latitude.setLocale(QLocale("en_US"))
        validator_longitude = QDoubleValidator(-180.0, 180.0, 1000)
        validator_longitude.setLocale(QLocale("en_US"))


        # lat1
        self.northern_bound = QLineEdit()
        self.northern_bound.setValidator(validator_latitude)
        self.northern_bound.setMaxLength(8)
        self.northern_bound.setAlignment(Qt.AlignRight)
        # lon1
        self.western_bound = QLineEdit()
        self.western_bound.setValidator(validator_longitude)
        self.western_bound.setMaxLength(8)
        self.western_bound.setAlignment(Qt.AlignRight)
        # lat2
        self.southern_bound = QLineEdit()
        self.southern_bound.setValidator(validator_latitude)
        self.southern_bound.setMaxLength(8)
        self.southern_bound.setAlignment(Qt.AlignRight)
        # lon2
        self.eastern_bound = QLineEdit()
        self.eastern_bound.setValidator(validator_longitude)
        self.eastern_bound.setMaxLength(8)
        self.eastern_bound.setAlignment(Qt.AlignRight)


        self.layout_aerial_image_groupbox.insertRow(3, "Northern Bound [°]", self.northern_bound)
        self.layout_aerial_image_groupbox.insertRow(4, "Western Bound [°]", self.western_bound)
        self.layout_aerial_image_groupbox.insertRow(5, "Southern Bound [°]", self.southern_bound)
        self.layout_aerial_image_groupbox.insertRow(6, "Eastern Bound [°]", self.eastern_bound)

        # probably move the next 4 lines to init_aerial_widget or something
        self.northern_bound.setText("48.263864")
        self.western_bound.setText("11.655410")
        self.southern_bound.setText("48.261424")
        self.eastern_bound.setText("11.660930")

        self.Spinner = QtWaitingSpinner(self, centerOnParent=True)
        self.Spinner.setInnerRadius(7)
        self.Spinner.setNumberOfLines(10)
        self.Spinner.setLineLength(7)
        self.Spinner.setLineWidth(2)

        self.layout_aerial_image_groupbox.addRow(self.button_add_aerial_image)
        self.layout_aerial_image_groupbox.addRow(self.button_remove_aerial_image)

        layout_aerial_image.addWidget(self.aerial_image_groupbox)

        widget_title = "Add Aerial Image"
        return widget_title, widget_aerial

    def create_add_lanelet_widget(self):
        widget_lanelets = QFrame(self.tree)
        layout_lanelet_adding = QVBoxLayout(widget_lanelets)

        self.connecting_radio_button_group = QButtonGroup()

        # place at position section
        self.place_at_position = QRadioButton("Place at position")
        self.place_at_position.setChecked(False)
        self.connecting_radio_button_group.addButton(self.place_at_position)
        font = self.place_at_position.font()
        font.setBold(True)
        self.place_at_position.setFont(font)

        # connect to previous selection section
        self.connect_to_previous_selection = QRadioButton("Connect to previously added")
        self.connect_to_previous_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_previous_selection)
        font = self.connect_to_previous_selection.font()
        font.setBold(True)
        self.connect_to_previous_selection.setFont(font)

        # connect to predecessors selection section
        self.connect_to_predecessors_selection = QRadioButton("Connect to predecessors")
        self.connect_to_predecessors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_predecessors_selection)
        font = self.connect_to_predecessors_selection.font()
        font.setBold(True)
        self.connect_to_predecessors_selection.setFont(font)


        # connect to successors section
        self.connect_to_successors_selection = QRadioButton("Connect to successors")
        self.connect_to_successors_selection.setChecked(False)
        self.connecting_radio_button_group.addButton(self.connect_to_successors_selection)
        font = self.connect_to_successors_selection.font()
        font.setBold(True)
        self.connect_to_successors_selection.setFont(font)

        self.adding_method = ""

        self.lanelet_adding_groupbox = QGroupBox()
        self.layout_lanelet_adding_groupbox = QFormLayout()
        self.lanelet_adding_groupbox.setLayout(self.layout_lanelet_adding_groupbox)

        self.layout_lanelet_adding_groupbox.addRow(self.place_at_position)
        self.layout_lanelet_adding_groupbox.addRow(self.connect_to_previous_selection)
        self.layout_lanelet_adding_groupbox.addRow(self.connect_to_predecessors_selection)
        self.layout_lanelet_adding_groupbox.addRow(self.connect_to_successors_selection)

        # Add button
        self.button_add_lanelet = QPushButton("Add")
        self.layout_lanelet_adding_groupbox.addRow(self.button_add_lanelet)

        # this validator always has the format with a dot as decimal separator
        self.float_validator = QDoubleValidator()
        self.float_validator.setLocale(QLocale("en_US"))

        layout_lanelet_adding.addWidget(self.lanelet_adding_groupbox)
        self.lanelet_adding_groupbox.setMinimumHeight(1150)

        widget_title = "Add Lanelet"
        return widget_title, widget_lanelets


    def adjust_add_sections(self):
        self.remove_adding_method_fields()

        # add groupbox of now selected adding method
        if self.place_at_position.isChecked():
            self.adding_method = "place_at_position"
            self.init_place_at_position_fields()
        elif self.connect_to_previous_selection.isChecked():
            self.adding_method = "connect_to_previous_selection"
            self.init_connect_to_previous_added_fields()
        elif self.connect_to_predecessors_selection.isChecked():
            self.adding_method = "connect_to_predecessors_selection"
            self.init_connect_to_predecessors_selection_fields()
        elif self.connect_to_successors_selection.isChecked():
            self.adding_method = "connect_to_successors_selection"
            self.init_connect_to_successors_selection_fields()


    def init_place_at_position_fields(self):

        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)

        self.layout_lanelet_adding_groupbox.insertRow(0, self.line1)

        self.lanelet_start_position_x = QLineEdit()
        self.lanelet_start_position_x.setValidator(self.float_validator)
        self.lanelet_start_position_x.setMaxLength(8)
        self.lanelet_start_position_x.setAlignment(Qt.AlignRight)
        self.lanelet_start_position_y = QLineEdit()
        self.lanelet_start_position_y.setValidator(self.float_validator)
        self.lanelet_start_position_y.setMaxLength(8)
        self.lanelet_start_position_y.setAlignment(Qt.AlignRight)

        self.lanelet_start_position_x.setText("0.0")
        self.lanelet_start_position_y.setText("0.0")

        self.button_start_position = PositionButton(self.lanelet_start_position_x, self.lanelet_start_position_y, self)

        self.lanelet_start_position = QGridLayout()
        self.lanelet_start_position.addWidget(QLabel("x: "), 1, 0)
        self.lanelet_start_position.addWidget(self.lanelet_start_position_x, 1, 1)
        self.lanelet_start_position.addWidget(QLabel("[m]"), 1, 2)
        self.lanelet_start_position.addWidget(QLabel("y:"), 1, 3)
        self.lanelet_start_position.addWidget(self.lanelet_start_position_y, 1, 4)
        self.lanelet_start_position.addWidget(QLabel("[m]"), 1, 5)
        self.lanelet_start_position.addWidget(self.button_start_position, 1, 6)

        self.layout_lanelet_adding_groupbox.insertRow(2, self.lanelet_start_position)

        # radio button group for selecting method of end position
        self.connecting_radio_button_group_lanelet_end = QButtonGroup()
        self.horizontal = QRadioButton("horizontal")
        self.horizontal.setChecked(True)
        self.connecting_radio_button_group_lanelet_end.addButton(self.horizontal)

        self.select_end_position = QRadioButton("select end pos")
        self.select_end_position.setChecked(False)
        self.connecting_radio_button_group_lanelet_end.addButton(self.select_end_position)
        self.select_end_position.setToolTip("select end position")

        self.rotate = QRadioButton("rotate")
        self.rotate.setChecked(False)
        self.connecting_radio_button_group_lanelet_end.addButton(self.rotate)

        self.horizontal.clicked.connect(lambda: self.adjust_end_position_fields())
        self.select_end_position.clicked.connect(lambda: self.adjust_end_position_fields())
        self.rotate.clicked.connect(lambda: self.adjust_end_position_fields())
        self.end_position_method = ""

        self.lanelet_end_position_method = QGridLayout()
        self.lanelet_end_position_method.addWidget(self.horizontal, 1, 0)
        self.lanelet_end_position_method.addWidget(self.select_end_position, 1, 1)
        self.lanelet_end_position_method.addWidget(self.rotate, 1, 2)

        self.layout_lanelet_adding_groupbox.insertRow(3, self.lanelet_end_position_method)

        # Lanelet Length and Width
        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(self.float_validator)
        self.lanelet_length.setMaxLength(5)
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_length.textChanged.connect(self.update_end_position)
        self.length_changed = False

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(self.float_validator)
        self.lanelet_width.setMaxLength(5)
        self.lanelet_width.setAlignment(Qt.AlignRight)

        self.layout_lanelet_adding_groupbox.insertRow(4, "Length [m]", self.lanelet_length)
        self.layout_lanelet_adding_groupbox.insertRow(5, "Width [m]", self.lanelet_width)

        self.add_curved_fields(6)
        self.add_line_marking_fields(8)
        self.add_neighboring_lanelets_fields(10)
        self.add_advanced_fields(12)

        # seperation line at the end of place at position block
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(14, self.line2)


    def adjust_end_position_fields(self):
        self.remove_end_position_method_fields()

        if self.horizontal.isChecked():
            self.end_position_method = "horizontal"

        elif self.select_end_position.isChecked():
            self.end_position_method = "select_end_position"
            self.lanelet_end_position_x = QLineEdit()
            self.lanelet_end_position_x.setValidator(self.float_validator)
            self.lanelet_end_position_x.setMaxLength(8)
            self.lanelet_end_position_x.setAlignment(Qt.AlignRight)
            self.lanelet_end_position_y = QLineEdit()
            self.lanelet_end_position_y.setValidator(self.float_validator)
            self.lanelet_end_position_y.setMaxLength(8)
            self.lanelet_end_position_y.setAlignment(Qt.AlignRight)

            self.button_end_position = PositionButton(self.lanelet_end_position_x, self.lanelet_end_position_y, self)
            self.button_end_position.setFlat(True)
            self.button_start_position.setAutoFillBackground(True)

            self.lanelet_select_end_position = QGridLayout()
            self.lanelet_select_end_position.addWidget(QLabel("x: "), 1, 0)
            self.lanelet_select_end_position.addWidget(self.lanelet_end_position_x, 1, 1)
            self.lanelet_select_end_position.addWidget(QLabel("[m]"), 1, 2)
            self.lanelet_select_end_position.addWidget(QLabel("y:"), 1, 3)
            self.lanelet_select_end_position.addWidget(self.lanelet_end_position_y, 1, 4)
            self.lanelet_select_end_position.addWidget(QLabel("[m]"), 1, 5)
            self.lanelet_select_end_position.addWidget(self.button_end_position, 1, 6)

            self.layout_lanelet_adding_groupbox.insertRow(4, self.lanelet_select_end_position)

            self.curved_check_button.button.setDisabled(True)

            self.lanelet_end_position_x.setText("10.0")
            self.lanelet_end_position_y.setText("0.0")

            self.lanelet_end_position_x.textChanged.connect(self.update_length)
            self.lanelet_end_position_y.textChanged.connect(self.update_length)
            self.lanelet_start_position_x.textChanged.connect(self.update_length)
            self.lanelet_start_position_y.textChanged.connect(self.update_length)
            self.end_position_x_changed = False
            self.end_position_y_changed = False
        elif self.rotate.isChecked():
            self.end_position_method = "rotate"
            self.rotation_angle_end = QLineEdit()
            rotation_validator = QIntValidator()
            rotation_validator.setRange(-180, 180)
            self.rotation_angle_end.setValidator(rotation_validator)
            self.rotation_angle_end.setAlignment(Qt.AlignRight)
            self.lanelet_rotation = QGridLayout()
            self.lanelet_rotation.addWidget(self.rotation_angle_end, 1, 0)
            self.lanelet_rotation.addWidget(QLabel("[deg]"), 1, 1)
            self.layout_lanelet_adding_groupbox.insertRow(4, self.lanelet_rotation)

            self.rotation_angle_end.setText("90")

        self.update_window()

    def update_length(self):
        """
        Changes length of lanelet when end position is changed or start position is changed and select end position method is checked.
        """
        if self.select_end_position.isChecked():
            # check if function is called from update_end_position and return to prevent infinite loop (is called twice
            # from update_end_position since text of both lanelet_end_position_x and lanelet_end_position_y is changed)
            if self.end_position_x_changed:
                self.end_position_x_changed = False
                return
            if self.end_position_y_changed:
                self.end_position_y_changed = False
                return
            pos = [self.lanelet_start_position_x.text(), self.lanelet_start_position_y.text(), self.lanelet_end_position_x.text(), self.lanelet_end_position_y.text()]
            if any("" == v for v in pos) or any("-" == v for v in pos):
                return
            x = float(self.lanelet_start_position_x.text().replace(",", ".")) - float(self.lanelet_end_position_x.text().replace(",", "."))
            y = float(self.lanelet_start_position_y.text().replace(",", ".")) - float(self.lanelet_end_position_y.text().replace(",", "."))
            self.length_changed = True
            self.lanelet_length.setText(str(math.sqrt(x**2 + y**2)))


    def update_selected_length(self):
        """
        Changes length of selected lanelet when end position is changed or start position is changed.
        """
        if self.selected_end_position_x_changed:
            self.selected_end_position_x_changed = False
            return
        if self.selected_end_position_y_changed:
            self.selected_end_position_y_changed = False
            return
        pos = [self.selected_lanelet_start_position_x.text(), self.selected_lanelet_start_position_y.text(),
               self.selected_lanelet_end_position_x.text(), self.selected_lanelet_end_position_y.text()]
        if any("" == v for v in pos) or any("-" == v for v in pos):
            return
        x = float(self.selected_lanelet_start_position_x.text().replace(",", ".")) - float(self.selected_lanelet_end_position_x.text().replace(",", "."))
        y = float(self.selected_lanelet_start_position_y.text().replace(",", ".")) - float(self.selected_lanelet_end_position_y.text().replace(",", "."))
        self.selected_length_changed = True
        self.selected_lanelet_length.setText(str(math.sqrt(x**2 + y**2)))

    def update_end_position(self):
        """
        Changes end position of lanelet when length field is changed ans select end position method is checked.
        """
        if self.select_end_position.isChecked():
            # check if function is called from update_length and return to prevent infinite loop
            if self.length_changed:
                self.length_changed = False
                return
            if self.lanelet_length.text() == "":
                return
            pos = [self.lanelet_start_position_x.text(), self.lanelet_start_position_y.text(),
                   self.lanelet_end_position_x.text(), self.lanelet_end_position_y.text()]
            if any("" == v for v in pos) or any("-" == v for v in pos):
                return

            length_new = float(self.lanelet_length.text().replace(",", "."))
            x_start = float(self.lanelet_start_position_x.text().replace(",", "."))
            y_start = float(self.lanelet_start_position_y.text().replace(",", "."))
            x_end = float(self.lanelet_end_position_x.text().replace(",", "."))
            y_end = float(self.lanelet_end_position_y.text().replace(",", "."))
            length_old = math.sqrt((x_start-x_end)**2 + (y_start-y_end)**2)


            x = x_start + (1/length_old * (x_end - x_start) * length_new)
            y = y_start + (1/length_old * (y_end - y_start) * length_new)

            self.end_position_x_changed = True
            self.end_position_y_changed = True
            self.lanelet_end_position_x.setText(str(x))
            self.lanelet_end_position_y.setText(str(y))


    def update_selected_end_position(self):
        """
        Changes end position of selected lanelet when length field is changed ans select end position method is checked.
        """
        if self.selected_length_changed:
            self.selected_length_changed = False
            return
        if self.selected_lanelet_length.text() == "":
            return
        pos = [self.selected_lanelet_start_position_x.text(), self.selected_lanelet_start_position_y.text(),
               self.selected_lanelet_end_position_x.text(), self.selected_lanelet_end_position_y.text()]
        if any("" == v for v in pos) or any("-" == v for v in pos):
            return

        length_new = float(self.selected_lanelet_length.text().replace(",", "."))
        x_start = float(self.selected_lanelet_start_position_x.text().replace(",", "."))
        y_start = float(self.selected_lanelet_start_position_y.text().replace(",", "."))
        x_end = float(self.selected_lanelet_end_position_x.text().replace(",", "."))
        y_end = float(self.selected_lanelet_end_position_y.text().replace(",", "."))
        length_old = math.sqrt((x_start - x_end) ** 2 + (y_start - y_end) ** 2)

        x = x_start + (1 / length_old * (x_end - x_start) * length_new)
        y = y_start + (1 / length_old * (y_end - y_start) * length_new)

        self.selected_end_position_x_changed = True
        self.selected_end_position_y_changed = True
        self.selected_lanelet_end_position_x.setText(str(x))
        self.selected_lanelet_end_position_y.setText(str(y))

    def remove_end_position_method_fields(self):
        if self.end_position_method == "select_end_position":
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_select_end_position)
            self.button_end_position.remove()
            self.curved_check_button.button.setDisabled(False)
        elif self.end_position_method == "rotate":
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_rotation)


    def add_curved_fields(self, index):
        self.lanelet_radius = QLineEdit()
        self.lanelet_radius.setValidator(self.float_validator)
        self.lanelet_radius.setMaxLength(6)
        self.lanelet_radius.setAlignment(Qt.AlignRight)

        self.lanelet_angle = QLineEdit()
        self.lanelet_angle.setMaxLength(6)
        self.lanelet_angle.setAlignment(Qt.AlignRight)

        self.number_vertices = QLineEdit()
        self.number_vertices.setValidator(QIntValidator())
        self.number_vertices.setMaxLength(2)
        self.number_vertices.setAlignment(Qt.AlignRight)

        layout_curved_box = QFormLayout()

        layout_curved_box.addRow("Curve radius [m]", self.lanelet_radius)
        layout_curved_box.addRow("Curve angle [deg]", self.lanelet_angle)
        layout_curved_box.addRow("Number Vertices:", self.number_vertices)

        self.lanelet_radius.setText("10.0")
        self.lanelet_angle.setText("90.0")
        self.number_vertices.setText("20")

        self.curved_check_button = CollapsibleCheckBox("Curved Lanelet", layout_curved_box, self.layout_lanelet_adding_groupbox, index)
        if self.place_at_position.isChecked():
            self.curved_check_button.button.clicked.connect(lambda: self.disable_curved_select_end_pos())

    def disable_curved_select_end_pos(self):
        self.update_window()
        # disable curved or select end position fields if the other one is selected since selecting both does not make sense
        if self.curved_check_button.isChecked():
            self.select_end_position.setDisabled(True)
        else:
            self.select_end_position.setDisabled(False)

    def add_line_marking_fields(self, index):

        self.line_marking_left = QComboBox()
        self.line_marking_right = QComboBox()

        layout_line_marking = QFormLayout()

        layout_line_marking.addRow("Left:", self.line_marking_left)
        layout_line_marking.addRow("Right:", self.line_marking_right)

        # stop line section
        layout_stop_line = QFormLayout()

        self.line_marking_stop_line = QComboBox()

        self.connecting_radio_button_group_stop_line = QButtonGroup()
        self.stop_line_beginning = QRadioButton("beginning")
        self.stop_line_beginning.setChecked(True)
        self.connecting_radio_button_group_stop_line.addButton(self.stop_line_beginning)

        self.stop_line_end = QRadioButton("end")
        self.stop_line_end.setChecked(False)
        self.connecting_radio_button_group_stop_line.addButton(self.stop_line_end)


        self.stop_line_position = QGridLayout()
        self.stop_line_position.addWidget(self.stop_line_beginning, 1, 0)
        self.stop_line_position.addWidget(self.stop_line_end, 1, 1)


        layout_stop_line.addRow("Line marking", self.line_marking_stop_line)
        layout_stop_line.addRow(self.stop_line_position)

        self.stop_line_check_box = CollapsibleCheckBox("Stop Line", layout_stop_line, layout_line_marking, 3)

        self.line_marking_box = CollapsibleArrowBox("Line marking", layout_line_marking,
                                                              self.layout_lanelet_adding_groupbox, index, self.mwindow, self)


    def add_neighboring_lanelets_fields(self, index):

        self.adjacent_right = QComboBox()
        self.adjacent_right_direction = QButtonGroup()
        self.adjacent_right_same_direction = QRadioButton("same direction")
        self.adjacent_right_same_direction.setChecked(True)
        self.adjacent_right_direction.addButton(self.adjacent_right_same_direction)
        self.adjacent_right_same_direction.setToolTip("Driving direction of right adjacent lanelet")
        self.adjacent_right_opposite_direction = QRadioButton("opposite direction")
        self.adjacent_right_opposite_direction.setChecked(False)
        self.adjacent_right_direction.addButton(self.adjacent_right_opposite_direction)
        self.adjacent_right_opposite_direction.setToolTip("Driving direction of right adjacent lanelet")

        self.adjacent_right_direction_line = QGridLayout()
        self.adjacent_right_direction_line.addWidget(self.adjacent_right_same_direction, 1, 0)
        self.adjacent_right_direction_line.addWidget(self.adjacent_right_opposite_direction, 1, 1)

        self.adjacent_left = QComboBox()
        self.adjacent_left_direction = QButtonGroup()
        self.adjacent_left_same_direction = QRadioButton("same direction")
        self.adjacent_left_same_direction.setChecked(True)
        self.adjacent_left_direction.addButton(self.adjacent_left_same_direction)
        self.adjacent_left_same_direction.setToolTip("Driving direction of left adjacent lanelet")
        self.adjacent_left_opposite_direction = QRadioButton("opposite direction")
        self.adjacent_left_opposite_direction.setChecked(False)
        self.adjacent_left_direction.addButton(self.adjacent_left_opposite_direction)
        self.adjacent_left_opposite_direction.setToolTip("Driving direction of left adjacent lanelet")

        self.adjacent_left_direction_line = QGridLayout()
        self.adjacent_left_direction_line.addWidget(self.adjacent_left_same_direction, 1, 0)
        self.adjacent_left_direction_line.addWidget(self.adjacent_left_opposite_direction, 1, 1)

        layout_neighboring_lanelets = QFormLayout()
        if not self.connect_to_predecessors_selection.isChecked():
            self.predecessors = CheckableComboBox()
            layout_neighboring_lanelets.addRow("Predecessors:", self.predecessors)
        if not self.connect_to_successors_selection.isChecked():
            self.successors = CheckableComboBox()
            layout_neighboring_lanelets.addRow("Successors:", self.successors)
        layout_neighboring_lanelets.addRow("Adjacent Right:", self.adjacent_right)
        layout_neighboring_lanelets.addRow(self.adjacent_right_direction_line)
        layout_neighboring_lanelets.addRow("Adjacent Left:", self.adjacent_left)
        layout_neighboring_lanelets.addRow(self.adjacent_left_direction_line)

        self.neighboring_lanelets_button = CollapsibleArrowBox("Neighboring Lanelets", layout_neighboring_lanelets,
                                                                self.layout_lanelet_adding_groupbox, index, self.mwindow, self)


    def add_advanced_fields(self, index):
        self.lanelet_type = CheckableComboBox()
        self.road_user_oneway = CheckableComboBox()
        self.road_user_bidirectional = CheckableComboBox()
        self.lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.lanelet_referenced_traffic_light_ids = CheckableComboBox()

        layout_advanced = QFormLayout()

        layout_advanced.addRow("Lanelet Types:", self.lanelet_type)
        layout_advanced.addRow("Users Oneway:", self.road_user_oneway)
        layout_advanced.addRow("Users Bidirectional:", self.road_user_bidirectional)
        layout_advanced.addRow("Traffic Sign IDs:", self.lanelet_referenced_traffic_sign_ids)
        layout_advanced.addRow("Traffic Light IDs:", self.lanelet_referenced_traffic_light_ids)

        self.advanced_button = CollapsibleArrowBox("Advanced", layout_advanced, self.layout_lanelet_adding_groupbox, index, self.mwindow, self)


    def init_connect_to_previous_added_fields(self):

        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(1, self.line1)

        self.previous_lanelet = QComboBox()
        self.layout_lanelet_adding_groupbox.insertRow(3, "Previous Lanelet", self.previous_lanelet)

        # Lanelet Length and Width
        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(self.float_validator)
        self.lanelet_length.setMaxLength(5)
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(self.float_validator)
        self.lanelet_width.setMaxLength(5)
        self.lanelet_width.setAlignment(Qt.AlignRight)
        self.lanelet_width.setDisabled(True)
        self.lanelet_width.setStyleSheet(
                'background-color: ' + self.mwindow.colorscheme().second_background + '; color: ' +
                self.mwindow.colorscheme().disabled)

        self.layout_lanelet_adding_groupbox.insertRow(4, "Length [m]", self.lanelet_length)
        self.layout_lanelet_adding_groupbox.insertRow(5, "Width [m]", self.lanelet_width)

        self.add_curved_fields(6)
        self.add_line_marking_fields(8)
        self.add_neighboring_lanelets_fields(10)
        self.add_advanced_fields(12)

        # seperation line at the end of place at position block
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(14, self.line2)


    def init_connect_to_predecessors_selection_fields(self):
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(2, self.line1)

        self.predecessors = CheckableComboBox(self)
        self.layout_lanelet_adding_groupbox.insertRow(4, "Predecessors:", self.predecessors)

        # Lanelet Length and Width
        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(self.float_validator)
        self.lanelet_length.setMaxLength(5)
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(self.float_validator)
        self.lanelet_width.setMaxLength(5)
        self.lanelet_width.setAlignment(Qt.AlignRight)
        self.lanelet_width.setDisabled(True)
        self.lanelet_width.setStyleSheet(
                'background-color: ' + self.mwindow.colorscheme().second_background + '; color: ' +
                self.mwindow.colorscheme().disabled)

        self.layout_lanelet_adding_groupbox.insertRow(5, "Length [m]", self.lanelet_length)
        self.layout_lanelet_adding_groupbox.insertRow(6, "Width [m]", self.lanelet_width)

        self.add_curved_fields(7)
        self.add_line_marking_fields(9)
        self.add_neighboring_lanelets_fields(11)
        self.add_advanced_fields(13)

        # seperation line at the end of place at position block
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(15, self.line2)

    def init_connect_to_successors_selection_fields(self):
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(3, self.line1)

        self.successors = CheckableComboBox()
        self.layout_lanelet_adding_groupbox.insertRow(5, "Successors:", self.successors)

        # Lanelet Length and Width
        self.lanelet_length = QLineEdit()
        self.lanelet_length.setValidator(self.float_validator)
        self.lanelet_length.setMaxLength(5)
        self.lanelet_length.setAlignment(Qt.AlignRight)

        self.lanelet_width = QLineEdit()
        self.lanelet_width.setValidator(self.float_validator)
        self.lanelet_width.setMaxLength(5)
        self.lanelet_width.setAlignment(Qt.AlignRight)
        self.lanelet_width.setDisabled(True)
        self.lanelet_width.setStyleSheet(
                'background-color: ' + self.mwindow.colorscheme().second_background + '; color: ' +
                self.mwindow.colorscheme().disabled)

        self.layout_lanelet_adding_groupbox.insertRow(6, "Length [m]", self.lanelet_length)
        self.layout_lanelet_adding_groupbox.insertRow(7, "Width [m]", self.lanelet_width)

        self.add_curved_fields(8)
        self.add_line_marking_fields(10)
        self.add_neighboring_lanelets_fields(12)
        self.add_advanced_fields(14)

        # seperation line at the end of place at position block
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.layout_lanelet_adding_groupbox.insertRow(16, self.line2)

    def remove_adding_method_fields(self):
        if self.adding_method == "place_at_position":
            self.layout_lanelet_adding_groupbox.removeRow(self.line1)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_start_position)
            self.button_start_position.remove()
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_end_position_method)
            if self.end_position_method == "select_end_position":
                self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_select_end_position)
                self.button_end_position.remove()
            elif self.end_position_method == "rotate":
                self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_rotation)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_length)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_width)
            self.curved_check_button.remove()
            self.line_marking_box.remove()
            self.neighboring_lanelets_button.remove()
            self.advanced_button.remove()
            self.layout_lanelet_adding_groupbox.removeRow(self.line2)

        elif self.adding_method == "connect_to_previous_selection":
            self.layout_lanelet_adding_groupbox.removeRow(self.line1)
            self.layout_lanelet_adding_groupbox.removeRow(self.previous_lanelet)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_length)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_width)
            self.curved_check_button.remove()
            # del self.curved_check_button
            self.line_marking_box.remove()
            self.neighboring_lanelets_button.remove()
            self.advanced_button.remove()
            self.layout_lanelet_adding_groupbox.removeRow(self.line2)

        elif self.adding_method == "connect_to_predecessors_selection":
            self.layout_lanelet_adding_groupbox.removeRow(self.predecessors)
            self.layout_lanelet_adding_groupbox.removeRow(self.line1)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_length)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_width)
            self.curved_check_button.remove()
            # del self.curved_check_button
            self.line_marking_box.remove()
            self.neighboring_lanelets_button.remove()
            self.advanced_button.remove()
            self.layout_lanelet_adding_groupbox.removeRow(self.line2)

        elif self.adding_method == "connect_to_successors_selection":
            self.layout_lanelet_adding_groupbox.removeRow(self.successors)
            self.layout_lanelet_adding_groupbox.removeRow(self.line1)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_length)
            self.layout_lanelet_adding_groupbox.removeRow(self.lanelet_width)
            self.curved_check_button.remove()
            # del self.curved_check_button
            self.line_marking_box.remove()
            self.neighboring_lanelets_button.remove()
            self.advanced_button.remove()
            self.layout_lanelet_adding_groupbox.removeRow(self.line2)


    def create_lanelet_attributes_widget(self):
        widget_lanelet_attributes = QFrame(self.tree)
        layout_lanelet_attributes = QVBoxLayout(widget_lanelet_attributes)

        self.lanelet_attributes_groupbox = QGroupBox()
        self.layout_lanelet_attributes_groupbox = QFormLayout()
        self.lanelet_attributes_groupbox.setLayout(self.layout_lanelet_attributes_groupbox)

        self.selected_lanelet_update = QComboBox()
        self.button_remove_lanelet = QPushButton("Remove")

        self.layout_lanelet_attributes_groupbox.addRow("Selected Lanelet", self.selected_lanelet_update)
        self.layout_lanelet_attributes_groupbox.addRow(self.button_remove_lanelet)

        self.add_attribute_fields()

        self.button_update_lanelet = QPushButton("Update")
        self.layout_lanelet_attributes_groupbox.addRow(self.button_update_lanelet)

        layout_lanelet_attributes.addWidget(self.lanelet_attributes_groupbox)
        self.lanelet_attributes_groupbox.setMinimumHeight(1100)

        widget_title = "Lanelet Attributes"

        return widget_title, widget_lanelet_attributes

    def add_attribute_fields(self):
        layout_attributes = QFormLayout()

        self.selected_lanelet_start_position_x = QLineEdit()
        self.selected_lanelet_start_position_x.setValidator(self.float_validator)
        self.selected_lanelet_start_position_x.setMaxLength(8)
        self.selected_lanelet_start_position_x.setAlignment(Qt.AlignRight)
        self.selected_lanelet_start_position_y = QLineEdit()
        self.selected_lanelet_start_position_y.setValidator(self.float_validator)
        self.selected_lanelet_start_position_y.setMaxLength(8)
        self.selected_lanelet_start_position_y.setAlignment(Qt.AlignRight)
        self.selected_button_start_position = PositionButton(self.selected_lanelet_start_position_x, self.selected_lanelet_start_position_y, self)
        self.selected_lanelet_start_position = QGridLayout()
        self.selected_lanelet_start_position.addWidget(QLabel("x: "), 1, 0)
        self.selected_lanelet_start_position.addWidget(self.selected_lanelet_start_position_x, 1, 1)
        self.selected_lanelet_start_position.addWidget(QLabel("[m]"), 1, 2)
        self.selected_lanelet_start_position.addWidget(QLabel("y:"), 1, 3)
        self.selected_lanelet_start_position.addWidget(self.selected_lanelet_start_position_y, 1, 4)
        self.selected_lanelet_start_position.addWidget(QLabel("[m]"), 1, 5)
        self.selected_lanelet_start_position.addWidget(self.selected_button_start_position, 1, 6)

        self.selected_lanelet_end_position_x = QLineEdit()
        self.selected_lanelet_end_position_x.setValidator(self.float_validator)
        self.selected_lanelet_end_position_x.setMaxLength(8)
        self.selected_lanelet_end_position_x.setAlignment(Qt.AlignRight)
        self.selected_lanelet_end_position_y = QLineEdit()
        self.selected_lanelet_end_position_y.setValidator(self.float_validator)
        self.selected_lanelet_end_position_y.setMaxLength(8)
        self.selected_lanelet_end_position_y.setAlignment(Qt.AlignRight)
        self.selected_button_end_position = PositionButton(self.selected_lanelet_end_position_x, self.selected_lanelet_end_position_y, self)
        self.selected_lanelet_end_position = QGridLayout()
        self.selected_lanelet_end_position.addWidget(QLabel("x: "), 1, 0)
        self.selected_lanelet_end_position.addWidget(self.selected_lanelet_end_position_x, 1, 1)
        self.selected_lanelet_end_position.addWidget(QLabel("[m]"), 1, 2)
        self.selected_lanelet_end_position.addWidget(QLabel("y:"), 1, 3)
        self.selected_lanelet_end_position.addWidget(self.selected_lanelet_end_position_y, 1, 4)
        self.selected_lanelet_end_position.addWidget(QLabel("[m]"), 1, 5)
        self.selected_lanelet_end_position.addWidget(self.selected_button_end_position, 1, 6)

        self.selected_end_position_x_changed = False
        self.selected_end_position_y_changed = False
        self.selected_lanelet_end_position_x.textChanged.connect(self.update_selected_length)
        self.selected_lanelet_end_position_y.textChanged.connect(self.update_selected_length)
        self.selected_lanelet_start_position_x.textChanged.connect(self.update_selected_length)
        self.selected_lanelet_start_position_y.textChanged.connect(self.update_selected_length)

        layout_attributes.addRow(self.selected_lanelet_start_position)
        layout_attributes.addRow(self.selected_lanelet_end_position)

        # Lanelet Length and Width
        self.selected_lanelet_length = QLineEdit()
        self.selected_lanelet_length.setValidator(self.float_validator)
        self.selected_lanelet_length.setMaxLength(5)
        self.selected_lanelet_length.setAlignment(Qt.AlignRight)
        self.selected_length_changed = False
        self.selected_lanelet_length.textChanged.connect(self.update_selected_end_position)

        self.selected_lanelet_width = QLineEdit()
        self.selected_lanelet_width.setValidator(self.float_validator)
        self.selected_lanelet_width.setMaxLength(5)
        self.selected_lanelet_width.setAlignment(Qt.AlignRight)

        layout_attributes.addRow("Length [m]", self.selected_lanelet_length)
        layout_attributes.addRow("Width [m]", self.selected_lanelet_width)

        # curved lanelet
        self.selected_lanelet_radius = QLineEdit()
        self.selected_lanelet_radius.setValidator(self.float_validator)
        self.selected_lanelet_radius.setMaxLength(6)
        self.selected_lanelet_radius.setAlignment(Qt.AlignRight)

        self.selected_lanelet_angle = QLineEdit()
        self.selected_lanelet_angle.setMaxLength(6)
        self.selected_lanelet_angle.setAlignment(Qt.AlignRight)

        self.selected_number_vertices = QLineEdit()
        self.selected_number_vertices.setValidator(QIntValidator())
        self.selected_number_vertices.setMaxLength(2)
        self.selected_number_vertices.setAlignment(Qt.AlignRight)

        layout_curved = QFormLayout()
        layout_curved.addRow("Curve radius [m]", self.selected_lanelet_radius)
        layout_curved.addRow("Curve angle [deg]", self.selected_lanelet_angle)
        layout_curved.addRow("Number Vertices:", self.selected_number_vertices)

        self.selected_curved_checkbox = CollapsibleCheckBox("Curved Lanelet", layout_curved, layout_attributes, 4)

        self.add_selected_line_markings(layout_attributes)
        self.add_selected_neighboring_fields(layout_attributes)
        self.add_selected_advanced_fields(layout_attributes)

        self.attributes_button = CollapsibleArrowBox("Lanelet Attributes", layout_attributes, self.layout_lanelet_attributes_groupbox, 3, self.mwindow, self)


    def add_selected_line_markings(self, layout_attributes):
        line_markings = [e.value for e in LineMarking]

        self.selected_line_marking_left = QComboBox()
        self.selected_line_marking_left.addItems(line_markings)

        self.selected_line_marking_right = QComboBox()
        self.selected_line_marking_right.addItems(line_markings)

        layout_line_marking = QFormLayout()

        layout_line_marking.addRow("Left:", self.selected_line_marking_left)
        layout_line_marking.addRow("Right:", self.selected_line_marking_right)

        # stop line section
        self.layout_stop_line = QFormLayout()

        self.selected_line_marking_stop_line = QComboBox()
        line_markings_stop_line = [e.value for e in LineMarking if
                                   e.value not in [LineMarking.UNKNOWN.value, LineMarking.NO_MARKING.value]]
        self.selected_line_marking_stop_line.addItems(line_markings_stop_line)

        self.connecting_radio_button_group_selected_stop_line = QButtonGroup()
        self.selected_stop_line_beginning = QRadioButton("beginn")
        self.selected_stop_line_beginning.setToolTip("beginning")
        self.connecting_radio_button_group_selected_stop_line.addButton(self.selected_stop_line_beginning)
        self.selected_stop_line_beginning.setChecked(True)
        self.selected_stop_line_beginning.clicked.connect(lambda: self.adjust_selected_stop_line_position())

        self.selected_stop_line_end = QRadioButton("end")
        self.connecting_radio_button_group_selected_stop_line.addButton(self.selected_stop_line_end)
        self.selected_stop_line_end.clicked.connect(lambda: self.adjust_selected_stop_line_position())

        self.selected_stop_line_select_position = QRadioButton("select pos")
        self.connecting_radio_button_group_selected_stop_line.addButton(self.selected_stop_line_select_position)
        self.selected_stop_line_select_position.clicked.connect(lambda: self.adjust_selected_stop_line_position())
        self.selected_stop_line_select_position.setToolTip("select position")

        self.selected_stop_line_position = QGridLayout()
        self.selected_stop_line_position.addWidget(self.selected_stop_line_beginning, 1, 0)
        self.selected_stop_line_position.addWidget(self.selected_stop_line_end, 1, 1)
        self.selected_stop_line_position.addWidget(self.selected_stop_line_select_position, 1, 2)
        self.selected_stop_line_select_position_checked_before = False

        self.layout_stop_line.addRow("Line marking", self.selected_line_marking_stop_line)
        self.layout_stop_line.addRow(self.selected_stop_line_position)

        self.selected_stop_line_box = CollapsibleCheckBox("Stop Line", self.layout_stop_line, layout_line_marking, 3)

        self.line_marking_box = CollapsibleArrowBox("Line marking", layout_line_marking, layout_attributes, 6, self.mwindow, self)

    def adjust_selected_stop_line_position(self):

        if self.selected_stop_line_select_position_checked_before:
            self.layout_stop_line.removeRow(self.selected_lanelet_select_stop_line_position)
            self.button_selected_stop_line_start_position.remove()
            self.button_selected_stop_line_end_position.remove()

        if self.selected_stop_line_select_position.isChecked():
            self.selected_stop_line_start_x = QLineEdit()
            self.selected_stop_line_start_x.setValidator(self.float_validator)
            self.selected_stop_line_start_x.setMaxLength(8)
            self.selected_stop_line_start_x.setAlignment(Qt.AlignRight)
            self.selected_stop_line_start_y = QLineEdit()
            self.selected_stop_line_start_y.setValidator(self.float_validator)
            self.selected_stop_line_start_y.setMaxLength(8)
            self.selected_stop_line_start_y.setAlignment(Qt.AlignRight)
            self.selected_stop_line_end_x = QLineEdit()
            self.selected_stop_line_end_x.setValidator(self.float_validator)
            self.selected_stop_line_end_x.setMaxLength(8)
            self.selected_stop_line_end_x.setAlignment(Qt.AlignRight)
            self.selected_stop_line_end_y = QLineEdit()
            self.selected_stop_line_end_y.setValidator(self.float_validator)
            self.selected_stop_line_end_y.setMaxLength(8)
            self.selected_stop_line_end_y.setAlignment(Qt.AlignRight)

            self.button_selected_stop_line_start_position = PositionButton(self.selected_stop_line_start_x, self.selected_stop_line_start_y, self)
            self.button_selected_stop_line_end_position = PositionButton(self.selected_stop_line_end_x, self.selected_stop_line_end_y, self)

            self.selected_lanelet_select_stop_line_position = QGridLayout()
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("Start"), 1, 0)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("x:"), 1, 1)
            self.selected_lanelet_select_stop_line_position.addWidget(self.selected_stop_line_start_x, 1, 2)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 1, 3)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("y:"), 1, 4)
            self.selected_lanelet_select_stop_line_position.addWidget(self.selected_stop_line_start_y, 1, 5)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 1, 6)
            self.selected_lanelet_select_stop_line_position.addWidget(self.button_selected_stop_line_start_position, 1, 7)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("End"), 2, 0)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("x:"), 2, 1)
            self.selected_lanelet_select_stop_line_position.addWidget(self.selected_stop_line_end_x, 2, 2)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 2, 3)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("y:"), 2, 4)
            self.selected_lanelet_select_stop_line_position.addWidget(self.selected_stop_line_end_y, 2, 5)
            self.selected_lanelet_select_stop_line_position.addWidget(QLabel("[m]"), 2, 6)
            self.selected_lanelet_select_stop_line_position.addWidget(self.button_selected_stop_line_end_position, 2, 7)


            self.layout_stop_line.addRow(self.selected_lanelet_select_stop_line_position)
            self.selected_stop_line_select_position_checked_before = True
        else:
            self.selected_stop_line_select_position_checked_before = False

    def add_selected_neighboring_fields(self, layout_attributes):
        self.selected_predecessors = CheckableComboBox()
        self.predecessor_list = []
        for i in range(0, len(self.predecessor_list) - 1):
            self.selected_predecessors.addItem(self.predecessor_list[i])
            item = self.selected_predecessors.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.selected_successors = CheckableComboBox()
        self.successor_list = []
        for i in range(0, len(self.successor_list) - 1):
            self.selected_successors.addItem(self.successor_list[i])
            item = self.selected_successors.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.selected_adjacent_right = QComboBox()
        self.selected_adjacent_right_direction = QButtonGroup()
        self.selected_adjacent_right_same_direction = QRadioButton("same direction")
        self.selected_adjacent_right_same_direction.setChecked(True)
        self.selected_adjacent_right_direction.addButton(self.selected_adjacent_right_same_direction)
        self.selected_adjacent_right_opposite_direction = QRadioButton("opposite direct.")
        self.selected_adjacent_right_opposite_direction.setToolTip("opposite direction")
        self.selected_adjacent_right_opposite_direction.setChecked(False)
        self.selected_adjacent_right_direction.addButton(self.selected_adjacent_right_opposite_direction)

        self.selected_adjacent_right_direction_line = QGridLayout()
        self.selected_adjacent_right_direction_line.addWidget(self.selected_adjacent_right_same_direction, 1, 0)
        self.selected_adjacent_right_direction_line.addWidget(self.selected_adjacent_right_opposite_direction, 1, 1)

        self.selected_adjacent_left = QComboBox()
        self.selected_adjacent_left_direction = QButtonGroup()
        self.selected_adjacent_left_same_direction = QRadioButton("same direction")
        self.selected_adjacent_left_same_direction.setChecked(True)
        self.selected_adjacent_left_direction.addButton(self.selected_adjacent_left_same_direction)
        self.selected_adjacent_left_opposite_direction = QRadioButton("opposite direct.")
        self.selected_adjacent_left_opposite_direction.setToolTip("opposite direction")
        self.selected_adjacent_left_opposite_direction.setChecked(False)
        self.selected_adjacent_left_direction.addButton(self.selected_adjacent_left_opposite_direction)

        self.selected_adjacent_left_direction_line = QGridLayout()
        self.selected_adjacent_left_direction_line.addWidget(self.selected_adjacent_left_same_direction, 1, 0)
        self.selected_adjacent_left_direction_line.addWidget(self.selected_adjacent_left_opposite_direction, 1, 1)

        layout_neighboring_lanelets = QFormLayout()

        layout_neighboring_lanelets.addRow("Predecessors:", self.selected_predecessors)
        layout_neighboring_lanelets.addRow("Successors:", self.selected_successors)
        layout_neighboring_lanelets.addRow("Adjacent Right:", self.selected_adjacent_right)
        layout_neighboring_lanelets.addRow(self.selected_adjacent_right_direction_line)
        layout_neighboring_lanelets.addRow("Adjacent Left:", self.selected_adjacent_left)
        layout_neighboring_lanelets.addRow(self.selected_adjacent_left_direction_line)

        self.selected_neighboring_lanelets_button = CollapsibleArrowBox("Neighboring Lanelets", layout_neighboring_lanelets,
                                                                layout_attributes, 8, self.mwindow, self)

    def add_selected_advanced_fields(self, layout_attributes):
        self.selected_road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.selected_road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.selected_road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.selected_road_user_oneway = CheckableComboBox()
        road_user_oneway_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_oneway_list) - 1):
            self.selected_road_user_oneway.addItem(road_user_oneway_list[i])
            item = self.selected_road_user_oneway.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.selected_road_user_bidirectional = CheckableComboBox()
        road_user_bidirectional_list = [r.value for r in RoadUser]
        for i in range(0, len(road_user_bidirectional_list) - 1):
            self.selected_road_user_bidirectional.addItem(road_user_bidirectional_list[i])
            item = self.selected_road_user_bidirectional.model().item(i, 0)
            item.setCheckState(Qt.Unchecked)

        self.selected_lanelet_type = CheckableComboBox()
        lanelet_type_list = [e.value for e in LaneletType]
        for i in range(0, len(lanelet_type_list) - 1):
            self.selected_lanelet_type.addItem(lanelet_type_list[i])

        self.selected_lanelet_referenced_traffic_sign_ids = CheckableComboBox()
        self.selected_lanelet_referenced_traffic_sign_ids.addItems(["None"])
        self.selected_lanelet_referenced_traffic_light_ids = CheckableComboBox()
        self.selected_lanelet_referenced_traffic_light_ids.addItems(["None"])

        layout_advanced = QFormLayout()

        layout_advanced.addRow("Lanelet Types:", self.selected_lanelet_type)
        layout_advanced.addRow("Users Oneway:", self.selected_road_user_oneway)
        layout_advanced.addRow("Users Bidirectional:", self.selected_road_user_bidirectional)
        layout_advanced.addRow("Traffic Sign IDs:", self.selected_lanelet_referenced_traffic_sign_ids)
        layout_advanced.addRow("Traffic Light IDs:", self.selected_lanelet_referenced_traffic_light_ids)

        self.advanced_button = CollapsibleArrowBox("Advanced", layout_advanced, layout_attributes, 10, self.mwindow, self)

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

        #widget_lanelet_operations.setStyleSheet('background-color:rgb(50,50,50)')
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

        button_traffic_sign_position = PositionButton(self.x_position_traffic_sign, self.y_position_traffic_sign, self)
        traffic_sign_position = QGridLayout()
        traffic_sign_position.addWidget(QLabel("x: "), 1, 0)
        traffic_sign_position.addWidget(self.x_position_traffic_sign, 1, 1)
        traffic_sign_position.addWidget(QLabel("[m]"), 1, 2)
        traffic_sign_position.addWidget(QLabel("y:"), 1, 3)
        traffic_sign_position.addWidget(self.y_position_traffic_sign, 1, 4)
        traffic_sign_position.addWidget(QLabel("[m]"), 1, 5)
        traffic_sign_position.addWidget(button_traffic_sign_position, 1, 6)

        traffic_sign_information_layout.addRow(traffic_sign_position)

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
        button_traffic_light_position = PositionButton(self.x_position_traffic_light, self.y_position_traffic_light, self)
        traffic_light_position = QGridLayout()
        traffic_light_position.addWidget(QLabel("x: "), 1, 0)
        traffic_light_position.addWidget(self.x_position_traffic_light, 1, 1)
        traffic_light_position.addWidget(QLabel("[m]"), 1, 2)
        traffic_light_position.addWidget(QLabel("y:"), 1, 3)
        traffic_light_position.addWidget(self.y_position_traffic_light, 1, 4)
        traffic_light_position.addWidget(QLabel("[m]"), 1, 5)
        traffic_light_position.addWidget(button_traffic_light_position, 1, 6)
        traffic_light_information_layout.addRow(traffic_light_position)
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

    def update_window(self):
        super().update_window()
        if self.place_at_position.isChecked():
            if self.curved_check_button.isChecked():
                self.select_end_position.setStyleSheet('background-color: '+ self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().disabled)
            else:
                self.select_end_position.setStyleSheet('background-color: '+ self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().color)

            if self.select_end_position.isChecked():
                self.curved_check_button.button.setStyleSheet('background-color: '+ self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().disabled)
            else:
                self.curved_check_button.button.setStyleSheet('background-color: '+ self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().color)

        if self.place_at_position.isChecked() or self.connect_to_previous_selection.isChecked() or self.connect_to_predecessors_selection.isChecked() or self.connect_to_successors_selection.isChecked():
            if not self.place_at_position.isChecked():
                self.lanelet_width.setStyleSheet(
                'background-color: ' + self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().disabled)
            else:
                self.lanelet_width.setStyleSheet(
                'background-color: ' + self.mwindow.colorscheme().second_background + '; color: ' + self.mwindow.colorscheme().color)