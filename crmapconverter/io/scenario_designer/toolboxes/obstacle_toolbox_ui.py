from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.toolboxes.toolbox_ui import Toolbox

from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import logging

# try to import sumo functionality
try:
    from crmapconverter.sumo_map.config import SumoConfig
    from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
    from sumocr.interface.sumo_simulation import SumoSimulation
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

        self.selected_obstacle = QComboBox()

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

        obstacle_information = QFormLayout()
        obstacle_information.addRow("Obstacle ID", self.selected_obstacle)
        obstacle_information.addRow("Width [m]", self.obstacle_width)
        obstacle_information.addRow("Length [m]", self.obstacle_length)
        obstacle_information.addRow("Type", self.obstacle_type)
        obstacle_information.addRow("Visualized State", self.obstacle_state_variable)
        layout_obstacles.addLayout(obstacle_information)

        self.figure = Figure(figsize=(3, 1))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout_obstacles.addLayout(layout)

        title_obstacle = "Obstacle"
        self.sections.append((title_obstacle, widget_obstacles))

        # --Section SUMO Simulation--
        widget_sumo = SUMOSimulation(self.tree)
        layout_sumo = QGridLayout(widget_sumo)

        self.button_start_simulation = QPushButton()
        self.button_start_simulation.setText("Simulate")
        layout_sumo.addWidget(self.button_start_simulation, 1, 0)

        title_sumo = "Sumo Simulation"
        self.sections.append((title_sumo, widget_sumo))



