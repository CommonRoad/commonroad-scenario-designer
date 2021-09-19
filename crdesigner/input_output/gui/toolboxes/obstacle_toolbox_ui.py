from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crdesigner.input_output.gui.toolboxes.toolbox_ui import Toolbox

from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import logging

# try to import sumo functionality
try:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from sumocr.interface.sumo_simulation import SumoSimulation
    from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMOSimulation
    SUMO_AVAILABLE = True
except ImportError:
    logging.warning("Cannot import SUMO, simulation will not be offered in Scenario Designer")
    SUMO_AVAILABLE = False


class ObstacleToolboxUI(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  Lanelet Section
        widget_obstacles = QFrame(self.tree)
        layout_obstacles = QVBoxLayout(widget_obstacles)

        label_general = QLabel("Obstacle Attributes")
        label_general.setFont(QFont("Arial", 11, QFont.Bold))

        self.obstacle_length = QLineEdit()
        self.obstacle_length.setValidator(QDoubleValidator())
        self.obstacle_length.setMaxLength(6)
        self.obstacle_length.setAlignment(Qt.AlignRight)

        self.obstacle_width = QLineEdit()
        self.obstacle_width.setValidator(QIntValidator())
        self.obstacle_width.setMaxLength(4)
        self.obstacle_width.setAlignment(Qt.AlignRight)

        self.obstacle_type = QComboBox()
        obstalce_type_list = [e.value for e in ObstacleType]
        self.obstacle_type.addItems(obstalce_type_list)

        self.obstacle_state_variable = QComboBox()
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.selected_obstacle = QComboBox()
        self.button_update_obstacle = QPushButton("Update")
        self.button_remove_obstacle = QPushButton("Remove")

        layout_obstacle_information_groupbox = QFormLayout()
        obstacle_information_groupbox = QGroupBox()
        obstacle_information_groupbox.setLayout(layout_obstacle_information_groupbox)
        layout_obstacle_information_groupbox.addRow(label_general)
        layout_obstacle_information_groupbox.addRow("Width [m]", self.obstacle_width)
        layout_obstacle_information_groupbox.addRow("Length [m]", self.obstacle_length)
        layout_obstacle_information_groupbox.addRow("Type", self.obstacle_type)
        layout_obstacle_state_vis_groupbox = QFormLayout()
        obstacle_state_vis_groupbox = QGroupBox()
        obstacle_state_vis_groupbox.setLayout(layout_obstacle_state_vis_groupbox)
        layout_vis_selection = QFormLayout()
        layout_vis_selection.addRow("Visualized State:", self.obstacle_state_variable)
        layout_obstacle_state_vis_groupbox.addRow(layout_vis_selection)
        layout_obstacle_state_vis_groupbox.addWidget(self.toolbar)
        layout_obstacle_state_vis_groupbox.addWidget(self.canvas)
        layout_obstacle_information_groupbox.addRow(obstacle_state_vis_groupbox)
        layout_obstacles.addWidget(obstacle_information_groupbox)

        layout_obstacle_buttons = QFormLayout()
        layout_obstacle_buttons.addRow("Selected Obstacle ID:", self.selected_obstacle)
        layout_obstacle_buttons.addRow(self.button_update_obstacle)
        layout_obstacle_buttons.addRow(self.button_remove_obstacle)
        layout_obstacles.addLayout(layout_obstacle_buttons)

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



