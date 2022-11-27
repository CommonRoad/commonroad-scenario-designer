from typing import Union
import matplotlib as mpl

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from commonroad.geometry.polyline_util import *
from commonroad.geometry.shape import Rectangle, Circle, Polygon
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle, StaticObstacle, ObstacleType, DynamicObstacle
from commonroad.scenario.trajectory import Trajectory
from commonroad.scenario.state import InitialState, State, PMState, KSState

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.dynamic_canvas import DynamicCanvas

if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

from crdesigner.ui.gui.mwindow.toolboxes.obstacle_profile_toolbox.obstacle_profile_toolbox_ui import ObstacleProfileToolboxUI

from commonroad.prediction.prediction import TrajectoryPrediction

class ObstacleProfileToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, callback, tmp_folder, text_browser, mwindow):
        super().__init__("Obstacle Profile Toolbox")

        self.current_scenario = current_scenario
        self.callback = callback 
        self.obstacle_profile_toolbox_ui = ObstacleProfileToolboxUI(text_browser, mwindow)
        self.adjust_ui()
        self.connect_gui_elements()
        self.tmp_folder = tmp_folder
        self.text_browser = text_browser
        self.update_ongoing = False
        self.init_canvas()
        self.amount_obstacles = 0
        self.canvas = DynamicCanvas()
        self.obstacle_color = None

        # for profile visualisation
        self.sel_point = None
        self.xyova = []
        self.pos = []
        self.temp_obstacle = None

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=tmp_folder)
        else:
            self.sumo_simulation = None

    def adjust_ui(self):
        """
        Updates GUI properties like width, etc.
        """
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.obstacle_profile_toolbox_ui)
        self.obstacle_profile_toolbox_ui.setMinimumWidth(450)    

    def connect_gui_elements(self):
        """
        adds functionality to gui elements like buttons, menus etc
        """

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def init_canvas(self):
        """
        adds functionality to gui elements like buttons, menus etc
        """