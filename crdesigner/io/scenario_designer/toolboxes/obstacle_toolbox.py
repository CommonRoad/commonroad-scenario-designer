from typing import List
import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.geometry.shape import Rectangle
from commonroad.scenario.scenario import Scenario

from crdesigner.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE

if SUMO_AVAILABLE:
    from crdesigner.io.scenario_designer.toolboxes.gui_sumo_simulation import SUMOSimulation

from crdesigner.io.scenario_designer.toolboxes.obstacle_toolbox_ui import ObstacleToolboxUI


class ObstacleToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, callback):
        super().__init__("Obstacle Toolbox")

        self.current_scenario = current_scenario
        self.callback = callback
        self.obstacle_toolbox = ObstacleToolboxUI()
        self.adjust_ui()
        self.connect_gui_elements()

        if SUMO_AVAILABLE:
            self.sumo_box = SUMOSimulation()
        else:
            self.sumo_box = None

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.obstacle_toolbox)
        self.obstacle_toolbox.setMinimumWidth(375)

    def connect_gui_elements(self):
        self.initialize_obstacle_information()

        self.obstacle_toolbox.selected_obstacle.currentTextChanged.connect(
            lambda: self.update_obstacle_information())
        self.obstacle_toolbox.obstacle_state_variable.currentTextChanged.connect(
            lambda: self.plot_obstacle_state_profile())

        self.obstacle_toolbox.button_start_simulation.clicked.connect(
            lambda: self.start_sumo_simulation())

    def collect_obstacle_ids(self) -> List[int]:
        """
        Collects IDs of all obstacles within a CommonRoad scenario.
        @return:
        """
        if self.current_scenario is not None:
            return [obs.obstacle_id for obs in self.current_scenario.obstacles]
        else:
            return []

    def update_scenario(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def initialize_toolbox(self):
        self.initialize_obstacle_information()

    def initialize_obstacle_information(self):
        """
        Initializes GUI elements with intersection information.
        """

        self.obstacle_toolbox.obstacle_width.setText("")
        self.obstacle_toolbox.obstacle_length.setText("")
        self.obstacle_toolbox.selected_obstacle.clear()
        self.obstacle_toolbox.selected_obstacle.addItems(
            ["None"] + [str(item) for item in self.collect_obstacle_ids()])
        self.obstacle_toolbox.selected_obstacle.setCurrentIndex(0)

    def plot_obstacle_state_profile(self):
        if self.obstacle_toolbox.selected_obstacle.currentText() not in ["", "None"]:
            obstacle_id = int(self.obstacle_toolbox.selected_obstacle.currentText())
            obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            state_variable_name = self.obstacle_toolbox.obstacle_state_variable.currentText()
            if state_variable_name == "x-position":
                profile = [obstacle.initial_state.__getattribute__("position")[0]]
                profile += [state.__getattribute__("position")[0]
                            for state in obstacle.prediction.trajectory.state_list]
            elif state_variable_name == "y-position":
                profile = [obstacle.initial_state.__getattribute__("position")[1]]
                profile += [state.__getattribute__("position")[1]
                            for state in obstacle.prediction.trajectory.state_list]
            else:
                profile = [obstacle.initial_state.__getattribute__(state_variable_name)]
                profile += [state.__getattribute__(state_variable_name)
                            for state in obstacle.prediction.trajectory.state_list]
            time = [obstacle.initial_state.time_step]
            time += [state.time_step for state in obstacle.prediction.trajectory.state_list]

            # create an axis
            ax = self.obstacle_toolbox.figure.add_subplot(111)

            # discards the old graph
            ax.clear()

            # plot data
            ax.plot(time, profile, 'o-')

            # refresh canvas
            self.obstacle_toolbox.canvas.draw()

    def update_obstacle_information(self):
        if self.obstacle_toolbox.selected_obstacle.currentText() not in ["", "None"]:
            obstacle_id = int(self.obstacle_toolbox.selected_obstacle.currentText())
            obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            if isinstance(obstacle.obstacle_shape, Rectangle):
                self.obstacle_toolbox.obstacle_width.setText(str(obstacle.obstacle_shape.width))
                self.obstacle_toolbox.obstacle_length.setText(str(obstacle.obstacle_shape.length))
            else:
                self.obstacle_toolbox.obstacle_width.setText("")
                self.obstacle_toolbox.obstacle_length.setText("")
            self.obstacle_toolbox.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
            state_variables = [var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]]
            if "position" in obstacle.initial_state.attributes:
                state_variables += ["x-position", "y-position"]
            self.obstacle_toolbox.obstacle_state_variable.addItems(state_variables)
            self.plot_obstacle_state_profile()

    def start_sumo_simulation(self):
        self.sumo_box.simulate()
        self.callback(self.sumo_box.simulated_scenario.value)

