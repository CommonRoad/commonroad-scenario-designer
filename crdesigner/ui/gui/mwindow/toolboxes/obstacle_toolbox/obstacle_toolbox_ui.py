from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import Toolbox, PositionButton
from crdesigner.ui.gui.mwindow.service_layer import config
from commonroad.scenario.obstacle import ObstacleType
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# try to import sumo functionality
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.mwindow.top_bar_wrapper.toolbar_wrapper.toolbar_wrapper import _drawing_mode, _trajectory_mode

if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation


class ObstacleToolboxUI(Toolbox):
    def __init__(self, text_browser, mwindow):
        super().__init__(mwindow)
        self.remove_vertice_btn = []
        self.text_browser = text_browser
        self.change_color = False

    def define_sections(self):
        """defines the sections in the obstacle toolbox
        """
        # this validator always has the format with a dot as decimal separator
        self.float_validator = QDoubleValidator()
        self.float_validator.setLocale(QLocale("en_US"))

        widget_obstacles = QFrame(self.tree)
        self.layout_obstacles = QVBoxLayout()
        widget_obstacles.setLayout(self.layout_obstacles)

        label_general = QLabel("Obstacle Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

        self.obstacle_dyn_stat = QComboBox()
        self.obstacle_dyn_stat.addItem("Static")
        self.obstacle_dyn_stat.addItem("Dynamic")

        # create radio buttons for static/dynamic obstacles
        self.static_dynamic_obstacle_group = QButtonGroup()
        self.static_obstacle_selection = QRadioButton("static")
        self.static_obstacle_selection.setChecked(True)
        self.static_dynamic_obstacle_group.addButton(self.static_obstacle_selection, 0)
        self.dynamic_obstacle_selection = QRadioButton("dynamic")
        self.dynamic_obstacle_selection.setChecked(False)
        self.static_dynamic_obstacle_group.addButton(self.dynamic_obstacle_selection, 1)

        # create text field and label for obstacle ID. Disable the LineEdit until a scenario is loaded
        self.obstacle_id_line_edit = QLineEdit(self)
        self.obstacle_id_line_edit.setEnabled(False)
        #self.obstacle_id_line_edit.setPlaceholderText("Auto")
        self.obstacle_id_line_edit.setToolTip("You can manually enter an ID or leave empty for an automatic ID."
                                              " You must first create a scenario.")
        # create QLabel to visualize the pixmap for ID
        self.obstacle_id_pixmap_label = QLabel(self)
        self.obstacle_id_pixmap_label.setToolTip("Visualizes whether the entered ID is valid.")
        # load the two pixmaps used to visualize whether ID is valid or invalid
        self.obstacle_id_pixmap_valid = QPixmap("/home/til/Downloads/correct.png")
        self.obstacle_id_pixmap_valid = self.obstacle_id_pixmap_valid.scaledToWidth(20)
        self.obstacle_id_pixmap_invalid = QPixmap("/home/til/Downloads/remove.png")
        self.obstacle_id_pixmap_invalid =  self.obstacle_id_pixmap_invalid.scaledToWidth(20)

        self.obstacle_shape = QComboBox()
        self.obstacle_shape.addItem("Rectangle")
        self.obstacle_shape.addItem("Circle")
        self.obstacle_shape.addItem("Polygon")

        self.obstacle_type = QComboBox()
        view = self.obstacle_type.view()
        self.adjust_obstacle_type_dropdown("static")

        self.obstacle_state_variable = QComboBox()
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.selected_obstacle = QComboBox()
        self.button_update_obstacle = QPushButton("Update")
        self.button_remove_obstacle = QPushButton("Remove")
        self.button_add_static_obstacle = QPushButton("Add")

        self.vis_settings_container = QFormLayout()
        self.vis_settings_label = QLabel("Visualization settings")
        self.vis_settings_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.vis_settings_container.addRow(self.vis_settings_label)

        self.color_container = QHBoxLayout()
        self.vis_settings_container.addRow(self.color_container)
        self.color_label = QLabel("Obstacle color:")
        self.color_container.addWidget(self.color_label)
        self.default_color = QCheckBox("Default color")
        self.default_color.setChecked(True)
        self.color_btn = QPushButton("Choose color")
        self.selected_color = QWidget()
        self.selected_color.setStyleSheet("border: 1px solid black")
        self.selected_color.setFixedWidth(25)
        self.selected_color.setFixedHeight(25)

        self.color_container.addWidget(self.default_color)
        self.color_container.addWidget(self.color_btn)
        self.color_container.addWidget(self.selected_color)

        self.layout_obstacle_information_groupbox = QFormLayout()
        self.obstacle_information_groupbox = QGroupBox()
        self.obstacle_information_groupbox.setLayout(self.layout_obstacle_information_groupbox)
        self.layout_obstacle_information_groupbox.insertRow(0, label_general)
        self.layout_obstacle_information_groupbox.insertRow(1, self.static_obstacle_selection,
                                                            self.dynamic_obstacle_selection)
        self.layout_obstacle_information_groupbox.insertRow(2, "Type", self.obstacle_type)
        # horizontal layout for the ID LineEdit and Pixmap that visualizes whether ID is valid
        self.horizontal_layout_obstacle_id = QHBoxLayout()
        self.horizontal_layout_obstacle_id.addWidget(self.obstacle_id_line_edit)
        self.horizontal_layout_obstacle_id.addWidget(self.obstacle_id_pixmap_label)
        self.layout_obstacle_information_groupbox.insertRow(3, "ID", self.horizontal_layout_obstacle_id)

        self.shape_groupbox = QGroupBox()
        self.layout_shape_groupbox = QFormLayout()
        self.shape_groupbox.setLayout(self.layout_shape_groupbox)
        self.shape_label = QLabel("Shape attributes")
        self.shape_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.layout_shape_groupbox.insertRow(0, self.shape_label)
        self.layout_shape_groupbox.insertRow(1, "Shape", self.obstacle_shape)

        self.layout_obstacle_information_groupbox.insertRow(4, self.shape_groupbox)
        self.adjust_obstacle_type_dropdown("Static")
        #self.layout_obstacle_information_groupbox.insertRow(5, "Position", self.position_text_field_layout)

        self.init_rectangle_fields()
        self.init_position()

        layout_obstacle_state_vis_groupbox = QFormLayout()
        obstacle_state_vis_groupbox = QGroupBox()
        obstacle_state_vis_groupbox.setLayout(layout_obstacle_state_vis_groupbox)
        layout_vis_selection = QFormLayout()
        layout_vis_selection.addRow("Visualized State:", self.obstacle_state_variable)
        layout_obstacle_state_vis_groupbox.addRow(layout_vis_selection)
        layout_obstacle_state_vis_groupbox.addWidget(self.toolbar)
        layout_obstacle_state_vis_groupbox.addWidget(self.canvas)
        self.layout_obstacle_information_groupbox.addRow(obstacle_state_vis_groupbox)
        self.layout_obstacles.addWidget(self.obstacle_information_groupbox)

        layout_obstacle_buttons = QFormLayout()
        layout_obstacle_buttons.addRow("Selected Obstacle ID:", self.selected_obstacle)
        layout_obstacle_buttons.addRow(self.button_update_obstacle)
        layout_obstacle_buttons.addRow(self.button_remove_obstacle)
        layout_obstacle_buttons.addRow(self.button_add_static_obstacle)
        self.layout_obstacles.addLayout(layout_obstacle_buttons)
        self.layout_obstacles.addLayout(self.vis_settings_container)

        title_obstacle = "Obstacle"
        self.sections.append((title_obstacle, widget_obstacles))

        # --Section SUMO Simulation-
        if SUMO_AVAILABLE:
            widget_sumo = SUMOSimulation(self.tree)
            layout_sumo = QFormLayout(widget_sumo)

            self.button_start_simulation = QPushButton("Simulate")
            self.sumo_simulation_length = QSpinBox()
            self.sumo_simulation_length.setMinimum(10)
            self.sumo_simulation_length.setMaximum(10000)
            self.sumo_simulation_length.setValue(200)

            layout_sumo.addRow("Number Time Steps:", self.sumo_simulation_length)
            layout_sumo.addRow(self.button_start_simulation)

            title_sumo = "Sumo Simulation"
            self.sections.append((title_sumo, widget_sumo))

    def init_rectangle_fields(self):
        """
        function that creates the fields for the rectangle shape
        """
        self.obstacle_length = QLineEdit()
        self.obstacle_length.setValidator(self.float_validator)
        self.obstacle_length.setMaxLength(6)
        self.obstacle_length.setAlignment(Qt.AlignRight)

        self.obstacle_width = QLineEdit()
        self.obstacle_width.setValidator(self.float_validator)
        self.obstacle_width.setMaxLength(4)
        self.obstacle_width.setAlignment(Qt.AlignRight)

        self.obstacle_orientation = QLineEdit()
        self.obstacle_orientation.setValidator(QIntValidator())
        self.obstacle_orientation.setMaxLength(4)
        self.obstacle_orientation.setAlignment(Qt.AlignRight)

        self.layout_shape_groupbox.insertRow(2, "Width [m]", self.obstacle_width)
        self.layout_shape_groupbox.insertRow(3, "Length [m]", self.obstacle_length)
        self.layout_shape_groupbox.insertRow(4, "Orientation [deg]", self.obstacle_orientation)

    def remove_rectangle_fields(self):
        """
        removes the fields unique to the rectangle shape
        """
        try:
            self.layout_shape_groupbox.removeRow(self.obstacle_width)
            self.layout_shape_groupbox.removeRow(self.obstacle_length)
            self.layout_shape_groupbox.removeRow(self.obstacle_orientation)
        except Exception:
            pass

    def init_circle_fields(self):
        """
        creates the fields for the circle shape
        """
        self.obstacle_radius = QLineEdit()
        self.obstacle_radius.setValidator(self.float_validator)
        self.obstacle_radius.setMaxLength(4)
        self.obstacle_radius.setAlignment(Qt.AlignRight)

        self.layout_shape_groupbox.insertRow(2, "Radius [m]", self.obstacle_radius)

    def remove_circle_fields(self):
        """
        removes the fields for the circle shape
        """
        try:
            self.layout_shape_groupbox.removeRow(self.obstacle_radius)
        except Exception:
            pass

    def remove_polygon_fields(self):
        """
        removes the fields for the polygon shape
        """
        try:
            for i in range(self.amount_vertices):
                self.layout_shape_groupbox.removeRow(self.polygon_row[i])

            self.layout_shape_groupbox.removeRow(self.add_vertice_btn)
        except Exception:
            pass

    def init_position(self):
        """
        adds the position fields
        """
        self.position_x_text_field = QLineEdit(self)
        self.position_x_text_field.setPlaceholderText("X")
        self.position_y_text_field = QLineEdit(self)
        self.position_y_text_field.setPlaceholderText("Y")
        self.button_selected_position = PositionButton(self.position_x_text_field,
                                                                       self.position_y_text_field, self)
        self.position_text_field_layout = QHBoxLayout(self)
        self.position_text_field_layout.addWidget(self.position_x_text_field)
        self.position_text_field_layout.addWidget(self.position_y_text_field)
        self.position_label = QLabel("Position")
        self.position_text_field_layout.addWidget(self.button_selected_position)
        if self.obstacle_shape.currentText() == "Rectangle":
            self.layout_obstacle_information_groupbox.insertRow(5, "Position", self.position_text_field_layout)
        elif self.obstacle_shape.currentText() == "Circle":
            self.layout_obstacle_information_groupbox.insertRow(5, "Position", self.position_text_field_layout)

    def init_waypoints_for_dynamic_obstacle(self):
        # initialize new group box, layout and header label
        self.waypoint_group_box = QGroupBox()
        self.layout_initial_state_group_box = QFormLayout()
        self.waypoint_group_box.setLayout(self.layout_initial_state_group_box)
        self.initial_state_label = QLabel("Build trajectory for dynamic obstacles")
        self.initial_state_label.setFont(QFont("Arial", 9, QFont.Bold))

        self.drawing_mode = QPushButton("Add Waypoint")
        self.drawing_mode.setCheckable(True)
        self.drawing_mode.clicked.connect(lambda: _trajectory_mode(self.mwindow, self.drawing_mode.isChecked()))
        self.waypoint_time_step = QLineEdit(self)
        self.waypoint_time_step.setPlaceholderText("0")
        self.waypoint_time_step.setToolTip("Time step must be an integer.")
        self.waypoint_time_step.setObjectName("time step")
        self.layout_initial_state_group_box.insertRow(0, self.initial_state_label)
        self.layout_initial_state_group_box.insertRow(1, "Position", self.drawing_mode)
        self.layout_initial_state_group_box.insertRow(2, "Time step", self.waypoint_time_step)
        self.layout_obstacle_information_groupbox.insertRow(6, self.waypoint_group_box)


    def init_dynamic_obstacle_fields(self):
        """Initializes edit fields that are specific to dynamic obstacles. Those currently encompass
        position, orientation, time, velocity, yaw rate and slip angle.
        """
        # initialize new group box, layout and header label
        self.initial_state_group_box = QGroupBox()
        self.layout_initial_state_group_box = QFormLayout()
        self.initial_state_group_box.setLayout(self.layout_initial_state_group_box)
        self.initial_state_label = QLabel("Initial state of the dynamic obstacle")
        self.initial_state_label.setFont(QFont("Arial", 9, QFont.Bold))

        # position edit fields, one for each x, y
        self.initial_state_position_layout = QHBoxLayout(self)
        self.initial_state_position_x = QLineEdit(self)
        self.initial_state_position_x.setObjectName("x-position of dynamic obstacle")
        self.initial_state_position_x.setToolTip("Enter initial x-position of obstacle")
        self.initial_state_position_x.setPlaceholderText("X")

        self.initial_state_position_y = QLineEdit(self)
        self.initial_state_position_y.setObjectName("y-position of dynamic obstacle")
        self.initial_state_position_y.setToolTip("Enter initial y-position of obstacle")
        self.initial_state_position_y.setPlaceholderText("Y")

        self.initial_state_position_layout.addWidget(self.initial_state_position_x)
        self.initial_state_position_layout.addWidget(self.initial_state_position_y)

        # orientation edit field
        self.initial_state_orientation = QLineEdit(self)
        self.initial_state_orientation.setPlaceholderText("0.0")
        self.initial_state_orientation.setObjectName("orientation of dynamic obstacle")

        # time edit field
        self.initial_state_time = QLineEdit(self)
        self.initial_state_time.setPlaceholderText("0")
        self.initial_state_time.setToolTip("Time step must be an integer.")
        self.initial_state_time.setObjectName("time of dynamic obstacle")

        # velocity edit field
        self.initial_state_velocity = QLineEdit(self)
        self.initial_state_velocity.setPlaceholderText("50.0")
        self.initial_state_velocity.setObjectName("velocity of dynamic obstacle")

        # yaw rate edit field
        self.initial_state_yaw_rate = QLineEdit(self)
        self.initial_state_yaw_rate.setPlaceholderText("0.0")
        self.initial_state_yaw_rate.setObjectName("yaw rate of dynamic obstacle")

        # slip angle edit field
        self.initial_state_slip_angle = QLineEdit(self)
        self.initial_state_slip_angle.setPlaceholderText("0.0")
        self.initial_state_slip_angle.setObjectName("slip angle of dynamic obstacle")

        # add all edit fields to the group box
        self.layout_initial_state_group_box.insertRow(0, self.initial_state_label)
        self.layout_initial_state_group_box.insertRow(1, "Position", self.initial_state_position_layout)
        self.layout_initial_state_group_box.insertRow(2, "Orientation", self.initial_state_orientation)
        self.layout_initial_state_group_box.insertRow(3, "Time", self.initial_state_time)
        self.layout_initial_state_group_box.insertRow(4, "Velocity", self.initial_state_velocity)
        self.layout_initial_state_group_box.insertRow(5, "Yaw Rate", self.initial_state_yaw_rate)
        self.layout_initial_state_group_box.insertRow(6, "Slip Angle", self.initial_state_slip_angle)

        # add the group box to the obstacle information groupbox
        self.layout_obstacle_information_groupbox.insertRow(5, self.initial_state_group_box)

    def remove_dynamic_obstacle_fields(self):
        """Method to remove the fields related only to dynamic obstacles."""

        self.layout_obstacle_information_groupbox.removeRow(self.initial_state_group_box)
        self.layout_obstacle_information_groupbox.removeRow(self.waypoint_group_box)


    def remove_position(self):
        """
        removes the position fields
        """
        self.layout_obstacle_information_groupbox.removeRow(self.position_text_field_layout)


    def toggle_dynamic_static(self):
        """
        adds/removes fields unique for the dynamic obstacle
        """
        if self.dynamic_obstacle_selection.isChecked():
            self.remove_position()
            self.init_dynamic_obstacle_fields()
            self.init_waypoints_for_dynamic_obstacle()
            self.adjust_obstacle_type_dropdown("Dynamic")
        elif self.static_obstacle_selection.isChecked():
            self.init_position()
            self.remove_dynamic_obstacle_fields()
            self.adjust_obstacle_type_dropdown("Static")

    def toggle_sections(self):
        """
        changes toolbox based on what shapes that are selected
        """
        if self.obstacle_shape.currentText() == "Circle":

            self.remove_rectangle_fields()
            self.remove_polygon_fields()
            self.remove_position()

            self.init_circle_fields()
            self.init_position()

        elif self.obstacle_shape.currentText() == "Rectangle":

            self.remove_circle_fields()
            self.remove_polygon_fields()
            self.remove_position()

            self.init_rectangle_fields()
            self.init_position()

        elif self.obstacle_shape.currentText() == "Polygon":

            self.remove_circle_fields()
            self.remove_rectangle_fields()
            self.remove_position()

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
            self.layout_shape_groupbox.insertRow(len(self.vertices_x) + 2, self.add_vertice_btn)

        if self.obstacle_dyn_stat.currentText() == "Dynamic":
            self.toggle_dynamic_static()

    def adjust_obstacle_type_dropdown(self, selected_type:QComboBox):
        """This method adjusts the obstacle type depending on whether static or dynamic obstacles are selected.
        For example, a parkedVehicle cannot be a dynamic obstacle."""
        self.obstacle_type.clear()
        if selected_type == "Dynamic":
            self.obstacle_type.addItems(
                    ["car", "bus", "truck", "bicycle", "pedestrian", "priorityVehicle", "train", "motorcycle", "taxi",
                     "unknown"])
        elif selected_type == "Static":
            self.obstacle_type.addItems(
                    ["unknown", "parkedVehicle", "constructionZone", "roadBoundary", "building", "pillar",
                     "median_strip"])

    def display_obstacle_id(self, generated_id):
        """This method displays the automatically generated ID as a placeholder text for the obstacle ID.

        :param generated_id: The generated ID.
        :type generated_id: int
        """
        try:
            text = "Auto: " + str(generated_id)
            self.obstacle_id_line_edit.setPlaceholderText(text)
        except Exception:
            pass

    def set_obstacle_id_pixmap(self, valid=True):
        """This method sets the pixmap next to the ID linedit, such that validity of the user-entered ID is visualized.

        :param valid: Whether the ID is valid or not.
        :type valid: bool
        """
        if valid:
            self.obstacle_id_pixmap_label.setPixmap(self.obstacle_id_pixmap_valid)
        else:
            self.obstacle_id_pixmap_label.setPixmap(self.obstacle_id_pixmap_invalid)


    # add vertices for the polygon shape, i is the place in the array
    def add_vertice(self):
        """
        add vertices for the polygon shape, i is the place in the array
        """
        i = len(self.vertices_x)
        self.polygon_row.append(QHBoxLayout())

        self.polygon_label.append(QLabel("Vertice " + str(i)))

        self.vertices_x.append(QLineEdit())
        self.vertices_x[i].setValidator(self.float_validator)
        self.vertices_x[i].setMaxLength(6)
        self.vertices_x[i].setAlignment(Qt.AlignRight)

        self.vertices_y.append(QLineEdit())
        self.vertices_y[i].setValidator(self.float_validator)
        self.vertices_y[i].setMaxLength(6)
        self.vertices_y[i].setAlignment(Qt.AlignRight)

        self.polygon_row[i].addWidget(self.polygon_label[i])
        self.polygon_row[i].addWidget(self.vertices_x[i])
        self.polygon_row[i].addWidget(self.vertices_y[i])

        self.remove_vertice_btn.append(QPushButton())
        if config.DARKMODE:
            self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can-darkmode.png"))
        else:
            self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))

        self.remove_vertice_btn[i].clicked.connect(
            lambda: self.remove_vertice())
        self.polygon_row[i].addWidget(self.remove_vertice_btn[i])

        self.layout_shape_groupbox.insertRow(i + 2, self.polygon_row[i])
        self.amount_vertices = self.amount_vertices + 1

    def remove_vertice(self, i: int = -1):
        """
        removes one vertice field
        :param i: index of vertice to be removed
        """
        if len(self.vertices_x) <= 3:
            self.text_browser.append("At least 3 vertices are needed to create a polygon")
            return
        if i == -1:
            sending_button = self.sender()
            i = self.remove_vertice_btn.index(sending_button)

        self.layout_shape_groupbox.removeRow(self.polygon_row[i])
        self.vertices_x.pop(i)
        self.vertices_y.pop(i)
        self.remove_vertice_btn.pop(i)
        self.polygon_label.pop(i)
        self.polygon_row.pop(i)
        self.amount_vertices = self.amount_vertices - 1

        for j in range(self.amount_vertices):
            self.polygon_label[j].setText("Vertice " + str(j))

    def color_picker(self):
        """
        opens color dialogue window
        """
        self.obstacle_color = QColorDialog.getColor()

        self.default_color.setChecked(False)
        self.selected_color.setStyleSheet(
                "QWidget { border:1px solid black; background-color: %s}" % self.obstacle_color.name())
        self.change_color = True

    def set_default_color(self):
        """
        sets default color for the color display square
        """
        if self.default_color.isChecked():
            self.selected_color.setStyleSheet("QWidget { border:1px solid black; background-color: white}")

    def update_window(self):
        super().update_window()
        if self.remove_vertice_btn:
            if config.DARKMODE:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can-darkmode.png"))
            else:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))
