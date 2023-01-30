from typing import Union
import matplotlib as mpl

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from commonroad.geometry.polyline_util import *
from commonroad.geometry.shape import Rectangle, Circle, Polygon
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle, StaticObstacle, DynamicObstacle

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.dynamic_canvas import DynamicCanvas

if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

from crdesigner.ui.gui.mwindow.toolboxes.obstacle_profile_toolbox.obstacle_profile_toolbox_ui import \
    ObstacleProfileToolboxUI


class ObstacleProfileToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, callback, tmp_folder, text_browser, mwindow):
        super().__init__("Obstacle Profile Toolbox")

        # slider is used to get the value
        self.current_time = QSlider(Qt.Horizontal)
        self.current_time.setValue(0)
        self.current_time.setMinimum(0)
        self.current_time.setMaximum(99)
        mwindow.animated_viewer_wrapper.cr_viewer.time_step.subscribe(self.current_time.setValue)

        self.current_scenario = current_scenario
        self.callback = callback
        self.obstacle_profile_toolbox_ui = ObstacleProfileToolboxUI(text_browser, mwindow)
        self.adjust_ui()
        self.connect_gui_elements()
        self.tmp_folder = tmp_folder
        self.text_browser = text_browser
        self.update_ongoing = False
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
        self.obstacle_profile_toolbox_ui.obstacle_state_variable.currentTextChanged.connect(
                lambda: self.plot_obstacle_state_profile())

        self.obstacle_profile_toolbox_ui.selected_obstacle.currentTextChanged.connect(
                lambda: self.update_obstacle_information())

        self.current_time.valueChanged.connect(lambda: self.update_animation())

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def initialize_toolbox(self):
        self.initialize_obstacle_profile_information()

    def initialize_obstacle_profile_information(self):
        """
        Initializes GUI elements with intersection information.
        """

        self.obstacle_profile_toolbox_ui.selected_obstacle.clear()
        self.obstacle_profile_toolbox_ui.selected_obstacle.addItems(
                ["None"] + [str(item) for item in self.collect_obstacle_ids()])
        self.obstacle_profile_toolbox_ui.selected_obstacle.setCurrentIndex(0)

    def collect_obstacle_ids(self) -> List[int]:
        """
        Collects IDs of all obstacles within a CommonRoad scenario.
        @return:
        """
        if self.current_scenario is not None:
            return [obs.obstacle_id for obs in self.current_scenario.obstacles]
        else:
            return []

    def get_current_obstacle(self) -> Union[Obstacle, None]:
        """
        :return: current selected obstacle
        """
        obstacle_id = self.get_current_obstacle_id()
        if obstacle_id is not None:
            selected_obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            return selected_obstacle
        else:
            return None

    def get_current_obstacle_id(self) -> Union[int, None]:
        """
        :return: obstacle_id of current selected obstacle
        """
        if self.obstacle_profile_toolbox_ui.selected_obstacle.currentText() != "None":
            return int(self.obstacle_profile_toolbox_ui.selected_obstacle.currentText())
        else:
            return None

    def plot_obstacle_state_profile(self):
        """
        Gets the values based on which profile is selected.
        If non updated changes, these values come from the xyova array,
        otherwise directly from the obstacle state_list
        """
        if self.obstacle_profile_toolbox_ui.selected_obstacle.currentText() not in ["",
                                                                                    "None"] and not self.update_ongoing:
            profile = None
            obstacle = self.get_current_obstacle()
            state_variable_name = self.obstacle_profile_toolbox_ui.obstacle_state_variable.currentText()
            # some simulations do not have their obstacle_states initialized like others and if trying to access them
            # CR will crash
            try:
                if obstacle.initial_state.__getattribute__(state_variable_name):
                    if isinstance(obstacle, DynamicObstacle):
                        if state_variable_name == "velocity":
                            if self.xyova:
                                profile = [j[3] for j in self.xyova]
                            else:
                                profile = [obstacle.initial_state.__getattribute__("velocity")]
                                profile += [state.__getattribute__("velocity") for state in
                                            obstacle.prediction.trajectory.state_list]
                        elif state_variable_name == "acceleration":
                            if self.xyova:
                                profile = [j[4] for j in self.xyova]
                            else:
                                profile = [obstacle.initial_state.__getattribute__("acceleration")]
                                profile += [state.__getattribute__("acceleration") for state in
                                            obstacle.prediction.trajectory.state_list]
                        elif state_variable_name == "yaw_rate":
                            if self.xyova:
                                profile = [j[5] for j in self.xyova]
                            else:
                                profile = [obstacle.initial_state.__getattribute__("yaw_rate")]
                                profile += [state.__getattribute__("yaw_rate") for state in
                                            obstacle.prediction.trajectory.state_list]
                        elif state_variable_name == "slip_angle":
                            if self.xyova:
                                profile = [j[6] for j in self.xyova]
                            else:
                                profile = [obstacle.initial_state.__getattribute__("slip_angle")]
                                profile += [state.__getattribute__("slip_angle") for state in
                                            obstacle.prediction.trajectory.state_list]
                # states which Static and DynamicObstacles share
                if state_variable_name == "x-position":
                    if isinstance(obstacle, StaticObstacle):
                        profile = [obstacle.initial_state.__getattribute__("position")[0]]
                    elif isinstance(obstacle, DynamicObstacle):
                        if self.xyova:
                            profile = [j[0] for j in self.xyova]
                        else:
                            profile = [obstacle.initial_state.__getattribute__("position")[0]]
                            profile += [state.__getattribute__("position")[0] for state in
                                        obstacle.prediction.trajectory.state_list]
                elif state_variable_name == "y-position":
                    if isinstance(obstacle, StaticObstacle):
                        profile = [obstacle.initial_state.__getattribute__("position")[1]]
                    elif isinstance(obstacle, DynamicObstacle):
                        if self.xyova:
                            profile = [j[1] for j in self.xyova]
                        else:
                            profile = [obstacle.initial_state.__getattribute__("position")[1]]
                            profile += [state.__getattribute__("position")[1] for state in
                                        obstacle.prediction.trajectory.state_list]
                elif state_variable_name == "orientation":
                    if isinstance(obstacle, StaticObstacle):
                        profile = [obstacle.initial_state.__getattribute__("orientation")]
                    elif isinstance(obstacle, DynamicObstacle):
                        if self.xyova:
                            profile = [j[2] for j in self.xyova]
                        else:
                            profile = [obstacle.initial_state.__getattribute__("orientation")]
                            profile += [state.__getattribute__("orientation") for state in
                                        obstacle.prediction.trajectory.state_list]
            except:
                print(state_variable_name + " not initialized on")

            if isinstance(obstacle, DynamicObstacle) and not self.obstacle_profile_toolbox_ui.animation.isChecked():
                if self.xyova:
                    time = [i for i in range(0, len(self.xyova))]
                else:
                    time = [obstacle.initial_state.time_step]
                    time += [state.time_step for state in obstacle.prediction.trajectory.state_list]
            else:
                time = [0]

            self.xmin = None
            self.xmax = None
            self.ymin = None
            self.ymax = None

            if profile and self.obstacle_profile_toolbox_ui.animation.isChecked():
                self.animate_plot(profile)
            elif profile:
                self.draw_plot(time, profile)

    @staticmethod
    def resolve_y_label(state_variable_name: str) -> str:
        """
        Creates y-label of state variable.
        @param state_variable_name: State variable from commonroad-io.
        @return: State variable with unit for visualization.
        """
        if state_variable_name == "x-position":
            return "x-position [m]"
        elif state_variable_name == "y-position":
            return "y-position [m]"
        elif state_variable_name == "orientation":
            return "orientation [rad]"
        elif state_variable_name == "velocity":
            return "velocity [m/s]"
        elif state_variable_name == "acceleration":
            return "acceleration [m/s^2]"
        else:
            return ""

    def on_xlim_change(self, event):
        self.xmin, self.xmax = event.get_xlim()

    def on_ylim_change(self, event):
        self.ymin, self.ymax = event.get_ylim()

    def update_obstacle_information(self):
        """
        retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox
        """
        if self.obstacle_profile_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:

            self.update_ongoing = True
            obstacle = self.get_current_obstacle()

            self.obstacle_profile_toolbox_ui.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
            self.obstacle_profile_toolbox_ui.obstacle_state_variable.clear()
            state_variables = [var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]]

            if "position" in obstacle.initial_state.attributes:
                state_variables += ["x-position", "y-position"]

            self.obstacle_profile_toolbox_ui.obstacle_state_variable.addItems(state_variables)
            self.update_ongoing = False
            # clear xyo if switch to another obstacle
            self.xyova.clear()

            self.plot_obstacle_state_profile()

        # if set to "None": clear QLineEdits
        else:
            self.obstacle_profile_toolbox_ui.obstacle_state_variable.clear()
            self.obstacle_profile_toolbox_ui.figure.clear()
            self.obstacle_profile_toolbox_ui.canvas.draw()

    def draw_plot(self, time, profile, xmin: float = None, xmax: float = None, ymin: float = None, ymax: float = None):
        """
        draws the state plot in the obstacle toolbox
        :param time: time steps
        :param profile: the profile to be drawn, eg. orientation
        :param xmin: x lower bound to be drawn
        :param xmax: x upper bound to be drawn
        :param ymin: y lower bound to be drawn
        :param: ymax: y upper bound to be drawn
        """
        state_variable_name = self.obstacle_profile_toolbox_ui.obstacle_state_variable.currentText()
        # clear previous profile
        self.obstacle_profile_toolbox_ui.figure.clear()
        # create an axis
        ax = self.obstacle_profile_toolbox_ui.figure.add_subplot(111)
        # plot data
        ax.plot(time, profile, '.-', markersize=4)
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.1f}'))
        ax.set_xlabel("time [s]")
        ax.set_ylabel(self.resolve_y_label(state_variable_name))
        self.obstacle_profile_toolbox_ui.figure.tight_layout()

        # to get reasonable limits. If the difference is very small: it will be difficult to make changes
        ax.set_ylim([min(profile) - 0.5, max(profile) + 0.5])
        # if zoomed in the new plot should be drawn with previous x and y limits
        # (so it doesn't zoom out on mouse event if zoomed in)
        if self.xmin and self.xmax and self.ymin and self.ymax:
            ax.set_xlim([self.xmin, self.xmax])
            ax.set_ylim([self.ymin, self.ymax])
        # refresh canvas
        self.obstacle_profile_toolbox_ui.canvas.draw()
        ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        ax.callbacks.connect('ylim_changed', self.on_ylim_change)

    def update_animation(self):
        self.plot_obstacle_state_profile()

    def animate_plot(self, profile):
        """
        draws the state plot in the obstacle toolbox
        :param time: time steps
        :param profile: the profile to be drawn, eg orientation
        :param xmin: x lower bound to be drawn
        :param xmax: x upper bound to be drawn
        :param ymin: y lower bound to be drawn
        :param: ymax: y upper bound to be drawn
        """
        time = [i for i in range(0, self.current_time.value() + 1)]

        # there are some scenarios where more time_steps exist than profile values
        # this if case prevents a crash
        if len(time) != len(profile[0:self.current_time.value() + 1]):
            return
        self.draw_plot(time, profile[0:self.current_time.value() + 1])
