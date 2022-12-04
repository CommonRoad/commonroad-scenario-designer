from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from crdesigner.ui.gui.mwindow.toolboxes.toolbox_ui import Toolbox
from crdesigner.ui.gui.mwindow.service_layer import config
from commonroad.scenario.obstacle import ObstacleType
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# try to import sumo functionality
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

class ObstacleProfileToolboxUI(Toolbox):
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

        self.obstacle_state_variable = QComboBox()
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.selected_obstacle = QComboBox()

        self.layout_obstacle_information_groupbox = QFormLayout()
        self.obstacle_information_groupbox = QGroupBox()
        self.obstacle_information_groupbox.setLayout(self.layout_obstacle_information_groupbox)

        layout_obstacle_buttons = QFormLayout()
        layout_obstacle_buttons.addRow("Selected Obstacle ID:", self.selected_obstacle)
        self.layout_obstacles.addLayout(layout_obstacle_buttons)

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

        title_obstacle = "Obstacle Profile"
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

    
    def update_window(self):
        super().update_window()
        if self.remove_vertice_btn:
            if config.DARKMODE:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can-darkmode.png"))
            else:
                for btn in self.remove_vertice_btn:
                    btn.setIcon(QIcon(":icons/iconmonstr-trash-can.svg"))
