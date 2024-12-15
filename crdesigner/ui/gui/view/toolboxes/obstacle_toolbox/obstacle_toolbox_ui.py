import math
from typing import Optional

from commonroad.geometry.shape import Circle, Polygon, Rectangle
from commonroad.scenario.obstacle import (
    DynamicObstacle,
    Obstacle,
    ObstacleType,
    StaticObstacle,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt6.QtCore import QLocale, Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from crdesigner.common.config.gui_config import gui_config
from crdesigner.common.logging import logger
from crdesigner.ui.gui.model.scenario_model import ScenarioModel

# try to import sumo functionality
from crdesigner.ui.gui.utilities.toolbox_ui import Toolbox


class ObstacleToolboxUI(Toolbox):
    def __init__(self, scenario_model: ScenarioModel, text_browser, mwindow):
        self.position_initialized = False
        super().__init__(mwindow)
        self.scenario_model = scenario_model
        self.remove_vertice_btn = []
        self.text_browser = text_browser
        self.change_color = False

        self.obstacle_spec = gui_config.OBSTACLE_SPECS

    def define_sections(self):
        """defines the sections in the obstacle toolbox"""
        # this validator always has the format with a dot as decimal separator
        self.float_validator = QDoubleValidator()
        self.float_validator.setLocale(QLocale("en_US"))

        widget_obstacles = QFrame(self.tree)
        self.layout_obstacles = QVBoxLayout()
        widget_obstacles.setLayout(self.layout_obstacles)

        label_general = QLabel("Obstacle Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.obstacle_dyn_stat = QComboBox()
        self.obstacle_dyn_stat.addItem("Static")
        self.obstacle_dyn_stat.addItem("Dynamic")

        self.obstacle_shape = QComboBox()
        self.obstacle_shape.addItem("Rectangle")
        self.obstacle_shape.addItem("Circle")
        self.obstacle_shape.addItem("Polygon")

        self.obstacle_type = QComboBox()
        obstalce_type_list = [e.value for e in ObstacleType]
        self.obstacle_type.addItems(obstalce_type_list)

        self.selected_obstacle = QComboBox()
        self.button_update_obstacle = QPushButton("Update")
        self.button_remove_obstacle = QPushButton("Remove")
        self.button_add_static_obstacle = QPushButton("Add")

        self.vis_settings_container = QFormLayout()
        self.vis_settings_label = QLabel("Visualization settings")
        self.vis_settings_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
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
        self.layout_obstacle_information_groupbox.insertRow(
            1, "Static/Dynamic", self.obstacle_dyn_stat
        )
        self.layout_obstacle_information_groupbox.insertRow(2, "Type", self.obstacle_type)

        self.shape_groupbox = QGroupBox()
        self.layout_shape_groupbox = QFormLayout()
        self.shape_groupbox.setLayout(self.layout_shape_groupbox)
        self.shape_label = QLabel("Shape attributes")
        self.shape_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.layout_shape_groupbox.insertRow(0, self.shape_label)
        self.layout_shape_groupbox.insertRow(1, "Shape", self.obstacle_shape)

        self.layout_obstacle_information_groupbox.insertRow(3, self.shape_groupbox)

        self.init_rectangle_fields()
        self.init_position()

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

        # --Section Obstacle Profile-
        widget_obstacle_profiles = QFrame(self.tree)
        self.layout_obstacle_profiles = QVBoxLayout()
        widget_obstacle_profiles.setLayout(self.layout_obstacle_profiles)

        state_profile_groupbox = QGroupBox()  # 1
        self.layout_profile_state_groupbox = QFormLayout()
        state_profile_groupbox.setLayout(self.layout_profile_state_groupbox)

        self.figure_profile = Figure(figsize=(5, 4))
        self.canvas_profile = FigureCanvas(self.figure_profile)
        self.toolbar_profile = NavigationToolbar(self.canvas_profile, self)

        self.selected_obstacle_profile = QListWidget()
        self.selected_obstacle_profile.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.selected_obstacle_profile.hide()
        self.expand_selected_obstacle = QPushButton("Show Selected Obstacles", self)
        self.expand_selected_obstacle.setStyleSheet(
            "background-color:"
            + self.mwindow.mwindow_ui.colorscheme().highlight
            + "; color:"
            + self.mwindow.mwindow_ui.colorscheme().highlight_text
            + "; font-size:"
            + self.mwindow.mwindow_ui.colorscheme().font_size
        )

        self.layout_profile_state_groupbox.addWidget(self.expand_selected_obstacle)
        self.layout_profile_state_groupbox.addWidget(self.selected_obstacle_profile)
        self.layout_profile_state_groupbox.addWidget(self.toolbar_profile)

        layout_obstacle_profile_state_vis_groupbox = QFormLayout()
        self.obstacle_profile_state_vis_groupbox = QGroupBox()
        self.obstacle_profile_state_vis_groupbox.setLayout(
            layout_obstacle_profile_state_vis_groupbox
        )
        layout_profile_vis_selection = QFormLayout()
        self.obstacle_profile_state_variable = QComboBox()
        layout_profile_vis_selection.addRow(
            "Visualized State:", self.obstacle_profile_state_variable
        )
        layout_obstacle_profile_state_vis_groupbox.addRow(layout_profile_vis_selection)
        layout_obstacle_profile_state_vis_groupbox.addWidget(self.toolbar_profile)
        layout_obstacle_profile_state_vis_groupbox.addWidget(self.canvas_profile)

        self.layout_obstacle_profiles.addWidget(state_profile_groupbox)
        self.layout_obstacle_profiles.addWidget(self.obstacle_profile_state_vis_groupbox)

        title_obstacle_profile = "Obstacle Profiles"
        self.sections.append((title_obstacle_profile, widget_obstacle_profiles))

    def initialize_obstacle_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.clear_obstacle_fields()

        self.selected_obstacle.clear()
        self.selected_obstacle.addItems(
            ["None"] + [str(item) for item in self.scenario_model.collect_obstacle_ids()]
        )
        self.selected_obstacle.setCurrentIndex(0)

        self.selected_obstacle_profile.clear()
        self.selected_obstacle_profile.addItems(
            [str(item) for item in self.scenario_model.collect_obstacle_ids()]
        )

        self.init_obstacle_defaults()

    def init_obstacle_defaults(self):
        selected_obs_spec = self.obstacle_spec.get(self.obstacle_type.currentText())
        if selected_obs_spec is None:
            return

        self.obstacle_shape.setCurrentText(selected_obs_spec["shape"])

        if self.obstacle_shape.currentText() == "Rectangle":
            self.obstacle_length.setText(selected_obs_spec["length"])
            self.obstacle_orientation.setText("0")
            self.obstacle_width.setText(selected_obs_spec["width"])
        elif self.obstacle_shape.currentText() == "Circle":
            self.obstacle_radius.setText(selected_obs_spec["radius"])
        elif self.obstacle_shape.currentText() == "Polygon":
            for lineEdit in self.vertices_x:
                lineEdit.setText("0")
            for lineEdit in self.vertices_y:
                lineEdit.setText("0")
        if (
            self.obstacle_dyn_stat.currentText() == "Static"
            and not self.obstacle_shape.currentText() == "Polygon"
        ):
            self.obstacle_x_Position.setText("0.5")
            self.obstacle_y_Position.setText("0.5")

    def update_obstacle_information_ui(self, obstacle: Optional[Obstacle] = None):
        """
        Updates the obstacle related information in the obstacle Toolbox

        :param obstacle: obstacle which information should be displayed in the toolbox.
        """
        if isinstance(obstacle, StaticObstacle):
            self.init_position()

        if isinstance(obstacle.obstacle_shape, Rectangle):
            if self.obstacle_shape.currentText() != "Rectangle":
                self.obstacle_shape.setCurrentIndex(0)

            self.obstacle_width.setText(str(obstacle.obstacle_shape.width))
            self.obstacle_length.setText(str(obstacle.obstacle_shape.length))
            if isinstance(obstacle, StaticObstacle):
                self.obstacle_x_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[0])
                )
                self.obstacle_y_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[1])
                )
                self.obstacle_orientation.setText(
                    str(math.degrees(obstacle.initial_state.__getattribute__("orientation")))
                )
            else:
                self.obstacle_orientation.setText(
                    str(math.degrees(obstacle.obstacle_shape.__getattribute__("orientation")))
                )

        elif isinstance(obstacle.obstacle_shape, Circle):
            if self.obstacle_shape.currentText() != "Circle":
                self.obstacle_shape.setCurrentIndex(1)

            self.obstacle_radius.setText(str(obstacle.obstacle_shape.radius))
            if isinstance(obstacle, StaticObstacle):
                self.obstacle_x_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[0])
                )
                self.obstacle_y_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[1])
                )

        elif isinstance(obstacle.obstacle_shape, Polygon):
            if self.obstacle_shape.currentText() != "Polygon":
                self.obstacle_shape.setCurrentIndex(2)

                # because numpy array has weird formatting I want to get rid of
            temp = obstacle.obstacle_shape.vertices
            vertices = temp.tolist()

            # remove extra vertice(s) in toolbox
            if len(vertices) - 1 < self.amount_vertices:
                j = self.amount_vertices - (len(vertices) - 1)
                for i in range(j):
                    self.remove_vertice(i)

            for i in range(len(vertices) - 1):
                # adds another vertice if there are too few in the toolbox
                if i >= self.amount_vertices:
                    self.add_vertice()

                vertice_string_x = str(vertices[i][0])
                vertice_string_y = str(vertices[i][1])
                self.vertices_x[i].setText(vertice_string_x)
                self.vertices_y[i].setText(vertice_string_y)

        if isinstance(obstacle, DynamicObstacle):
            if self.obstacle_dyn_stat.currentText() != "Dynamic":
                self.obstacle_dyn_stat.setCurrentIndex(1)

        elif self.obstacle_dyn_stat.currentText() != "Static":
            self.obstacle_dyn_stat.setCurrentIndex(0)

        self.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
        self.obstacle_profile_state_variable.clear()
        state_variables = [
            var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]
        ]

        if "position" in obstacle.initial_state.attributes:
            state_variables += ["x-position", "y-position"]

        self.obstacle_profile_state_variable.addItems(state_variables)

        if obstacle is None:
            self.obstacle_type.setCurrentIndex(0)
            self.selected_obstacle.setCurrentIndex(0)

    def clear_obstacle_fields(self):
        """
        clears the obstacle QLineEdits
        """
        if self.obstacle_shape.currentText() == "Circle":
            self.obstacle_radius.setText("")

        elif self.obstacle_shape.currentText() == "Rectangle":
            self.obstacle_width.setText("")
            self.obstacle_length.setText("")
            self.obstacle_orientation.setText("")

        elif self.obstacle_shape.currentText() == "Polygon":
            for i in range(self.amount_vertices):
                self.vertices_x[i].setText("")
                self.vertices_y[i].setText("")
        if (
            self.obstacle_dyn_stat.currentText() == "Static"
            and self.obstacle_shape.currentText() != "Polygon"
        ):
            self.obstacle_x_Position.setText("")
            self.obstacle_y_Position.setText("")
        if not self.default_color.isChecked():
            self.default_color.setChecked(True)

    def init_rectangle_fields(self):
        """
        function that creates the fields for the rectangle shape
        """
        self.obstacle_length = QLineEdit()
        self.obstacle_length.setValidator(self.float_validator)
        self.obstacle_length.setMaxLength(6)
        self.obstacle_length.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.obstacle_width = QLineEdit()
        self.obstacle_width.setValidator(self.float_validator)
        self.obstacle_width.setMaxLength(4)
        self.obstacle_width.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.obstacle_orientation = QLineEdit()
        self.obstacle_orientation.setValidator(QIntValidator())
        self.obstacle_orientation.setMaxLength(4)
        self.obstacle_orientation.setAlignment(Qt.AlignmentFlag.AlignRight)

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
        self.obstacle_radius.setAlignment(Qt.AlignmentFlag.AlignRight)

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
        if not self.position_initialized:
            self.obstacle_x_Position = QLineEdit()
            self.obstacle_x_Position.setValidator(self.float_validator)
            self.obstacle_x_Position.setMaxLength(4)
            self.obstacle_x_Position.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.obstacle_y_Position = QLineEdit()
            self.obstacle_y_Position.setValidator(self.float_validator)
            self.obstacle_y_Position.setMaxLength(4)
            self.obstacle_y_Position.setAlignment(Qt.AlignmentFlag.AlignRight)

            if self.obstacle_shape.currentText() == "Rectangle":
                self.layout_obstacle_information_groupbox.insertRow(
                    4, "X-Position", self.obstacle_x_Position
                )
                self.layout_obstacle_information_groupbox.insertRow(
                    5, "Y-Position", self.obstacle_y_Position
                )
            elif self.obstacle_shape.currentText() == "Circle":
                self.layout_obstacle_information_groupbox.insertRow(
                    4, "X-Position", self.obstacle_x_Position
                )
                self.layout_obstacle_information_groupbox.insertRow(
                    5, "Y-Position", self.obstacle_y_Position
                )
            self.position_initialized = True

    def remove_position(self):
        """
        removes the position fields
        """
        try:
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_x_Position)
            self.layout_obstacle_information_groupbox.removeRow(self.obstacle_y_Position)
            self.position_initialized = False
        except Exception:
            pass

    def init_polygon_fields(self):
        """
        changes toolbox based on what shapes that are selected
        """
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

    @logger.log
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
        self.vertices_x[i].setAlignment(Qt.AlignmentFlag.AlignRight)

        self.vertices_y.append(QLineEdit())
        self.vertices_y[i].setValidator(self.float_validator)
        self.vertices_y[i].setMaxLength(6)
        self.vertices_y[i].setAlignment(Qt.AlignmentFlag.AlignRight)

        self.polygon_row[i].addWidget(self.polygon_label[i])
        self.polygon_row[i].addWidget(self.vertices_x[i])
        self.polygon_row[i].addWidget(self.vertices_y[i])

        self.remove_vertice_btn.append(QPushButton())
        if gui_config.DARKMODE:
            self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can-darkmode.png"))
        else:
            self.remove_vertice_btn[i].setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))

        self.remove_vertice_btn[i].clicked.connect(lambda: self.remove_vertice())
        self.polygon_row[i].addWidget(self.remove_vertice_btn[i])

        self.layout_shape_groupbox.insertRow(i + 2, self.polygon_row[i])
        self.amount_vertices = self.amount_vertices + 1

    @logger.log
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
            "QWidget { border:1px solid black; background-color: %s}" % self.obstacle_color.name()
        )
        self.change_color = True

    @logger.log
    def set_default_color(self):
        """
        sets default color for the color display square
        """
        if self.default_color.isChecked():
            self.selected_color.setStyleSheet(
                "QWidget { border:1px solid black; background-color: white}"
            )

    def update_window(self):
        super().update_window()
        if self.remove_vertice_btn:
            if gui_config.DARKMODE:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can-darkmode.png"))
            else:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))
