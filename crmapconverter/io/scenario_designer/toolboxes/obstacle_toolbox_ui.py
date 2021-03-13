from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from crmapconverter.io.scenario_designer.gui_src import CR_Scenario_Designer  # do not remove!!!
from crmapconverter.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation
from crmapconverter.io.scenario_designer.toolboxes.toolbox_ui import Toolbox

from commonroad.scenario.obstacle import ObstacleType

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import random
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


class ObstacleToolbox(Toolbox):
    def __init__(self):
        super().__init__()

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        #  Lanelet Section
        widget_obstacles = QFrame(self.tree)
        layout_obstacles = QVBoxLayout(widget_obstacles)

        self.obstacle_id = QComboBox()

        self.length = QLineEdit()
        self.length.setValidator(QDoubleValidator())
        self.length.setMaxLength(6)
        self.length.setAlignment(Qt.AlignRight)

        self.width = QLineEdit()
        self.width.setValidator(QIntValidator())
        self.width.setMaxLength(4)
        self.width.setAlignment(Qt.AlignRight)

        self.obstacle_type = QComboBox()
        obstalce_type_list = [e.value for e in ObstacleType]
        self.obstacle_type.addItems(obstalce_type_list)

        obstacle_information = QFormLayout()
        obstacle_information.addRow("Obstacle ID", self.obstacle_id)
        obstacle_information.addRow("Width [m]", self.width)
        obstacle_information.addRow("Length [m]", self.length)
        obstacle_information.addRow("Type", self.obstacle_type)
        layout_obstacles.addLayout(obstacle_information)

       # obstacle_buttons = QGridLayout()

        # self.button_add_obstacle = QPushButton()
        # self.add_button.setText("Add")
        # obstacle_buttons.addWidget(self.ed, 0, 0)
        #
        # self.update_button = QPushButton()
        # self.update_button.setText("Update")
        # obstacle_buttons.addWidget(self.update_button, 1, 0)
        #
        # self.remove_button = QPushButton()
        # self.remove_button.setText("Remove")
        # obstacle_buttons.addWidget(self.remove_button, 2, 0)
        #
        # layout_obstacles.addLayout(obstacle_buttons)

        # a figure instance to plot on
        self.figure = Figure(figsize=(3, 1))

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        layout_obstacles.addLayout(layout)

        title_obstacle = "Obstacle"
        self.sections.append((title_obstacle, widget_obstacles))

        # --Section SUMO Simulation--
        widget_sumo = SUMOSimulation(self.tree)
        layout_sumo = QGridLayout(widget_sumo)

        self.button_start_simulation = QPushButton()
        self.button_start_simulation.setText("Simulate")
        self.button_start_simulation.setIcon(QIcon(":/icons/forwards.PNG"))
        layout_sumo.addWidget(self.button_start_simulation, 1, 0)

        title_sumo = "Sumo Simulation"
        self.sections.append((title_sumo, widget_sumo))

    def plot(self):
        ''' plot some random stuff '''
        # random data
        data = [random.random() for i in range(10)]

        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.clear()

        # plot data
        ax.plot(data, 'o-')

        # refresh canvas
        self.canvas.draw()


