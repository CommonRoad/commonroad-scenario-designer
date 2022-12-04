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
        self.obstacle_profile_toolbox_ui.selected_obstacle.currentTextChanged.connect(
                lambda: self.update_obstacle_profile_information())

        self.obstacle_profile_toolbox_ui.obstacle_state_variable.currentTextChanged.connect(
                lambda: self.plot_obstacle_state_profile())

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def init_canvas(self):
        """
        adds functionality to gui elements like buttons, menus etc
        """
        self.obstacle_profile_toolbox_ui.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.obstacle_profile_toolbox_ui.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.obstacle_profile_toolbox_ui.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def initialize_toolbox(self):
        self.initialize_obstacle_profile_information()

    def initialize_obstacle_profile_information(self):
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

    def update_obstacle_profile_information(self):
        """
        retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox
        """

    def on_button_press(self, event):
        """"
        when left or right mouse button is pressed
        """

    def on_button_release(self, event):
        """
        Updates obstacle when left mouse button is released
        if xyova already exists: save changed values to that array
        otherwise create the array and store changes
        """
    
    def on_mouse_move(self, event):
        """
        update position of selected point by moving mouse
        and holding down left mouse button
        """

    def plot_obstacle_state_profile(self):
        """
        Gets the values based on which profile is selected.
        If non updated changes, these values come from the xyova array,
        otherwise directly from the obstacle state_list
        """
        

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

    def draw_plot(self, time, profile, xmin: float = None,
                  xmax: float = None, ymin: float = None, ymax: float = None):
        """
        draws the state plot in the obstacle toolbox
        :param time: time steps
        :param profile: the profile to be drawn, eg orientation
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
        ax.set_ylim([min(profile)-0.5, max(profile)+0.5])
        # if zoomed in the new plot should be drawn with previous x and y limits
        # (so it doesnt zoom out on mouse event if zoomed in)
        if (self.xmin and self.xmax and self.ymin and self.ymax):
            ax.set_xlim([self.xmin, self.xmax])
            ax.set_ylim([self.ymin, self.ymax])
        # refresh canvas
        self.obstacle_profile_toolbox_ui.canvas.draw()
        ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        ax.callbacks.connect('ylim_changed', self.on_ylim_change)

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

        """
    def update_obstacle_information(self):
        retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox
        if self.obstacle_profile_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:

            self.update_ongoing = True
            obstacle = self.get_current_obstacle()
            obstacle_id = self.get_current_obstacle_id()

            if isinstance(obstacle.obstacle_shape, Rectangle):
                if isinstance(obstacle, StaticObstacle):
                    self.obstacle_profile_toolbox_ui.obstacle_x_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[0]))
                    self.obstacle_profile_toolbox_ui.obstacle_y_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[1]))
                    self.obstacle_profile_toolbox_ui.obstacle_orientation.setText(
                        str(math.degrees(obstacle.initial_state.__getattribute__("orientation"))))
                else:
                    self.obstacle_profile_toolbox_ui.obstacle_orientation.setText(
                        str(math.degrees(obstacle.obstacle_shape.__getattribute__("orientation"))))

            elif isinstance(obstacle.obstacle_shape, Circle):
                if isinstance(obstacle, StaticObstacle):
                    self.obstacle_toolbox_ui.obstacle_x_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[0]))
                    self.obstacle_toolbox_ui.obstacle_y_Position.setText(
                        str(obstacle.initial_state.__getattribute__("position")[1]))

            elif isinstance(obstacle.obstacle_shape, Polygon):
                    # because numpy array has weird formatting I want to get rid of
                temp = obstacle.obstacle_shape.vertices
                vertices = temp.tolist()

                # remove extra vertice(s) in toolbox
                if len(vertices) - 1 < self.obstacle_toolbox_ui.amount_vertices:
                    j = self.obstacle_profile_toolbox_ui.amount_vertices - (len(vertices) - 1)
                    for i in range(j):
                        self.obstacle_profile_toolbox_ui.remove_vertice(i)

                for i in range(len(vertices) - 1):
                    # adds another vertice if there are too few in the toolbox
                    if i >= self.obstacle_profile_toolbox_ui.amount_vertices:
                        self.obstacle_profile_toolbox_ui.add_vertice()

                    vertice_string_x = str(vertices[i][0])
                    vertice_string_y = str(vertices[i][1])
                    self.obstacle_profile_toolbox_ui.vertices_x[i].setText(vertice_string_x)
                    self.obstacle_profile_toolbox_ui.vertices_y[i].setText(vertice_string_y)

            if isinstance(obstacle, DynamicObstacle):

                if self.obstacle_profile_toolbox_ui.obstacle_dyn_stat.currentText() != "Dynamic":
                    self.obstacle_profile_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(1)

            elif self.obstacle_profile_toolbox_ui.obstacle_dyn_stat.currentText() != "Static":
                self.obstacle_profile_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(0)

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
            self.clear_obstacle_fields()
            self.obstacle_toolbox_ui.obstacle_state_variable.clear()
            self.obstacle_toolbox_ui.figure.clear()
            self.obstacle_toolbox_ui.canvas.draw()
        """