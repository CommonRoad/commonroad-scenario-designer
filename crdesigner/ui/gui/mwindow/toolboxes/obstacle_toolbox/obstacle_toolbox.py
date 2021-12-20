from typing import List
import matplotlib as mpl
import numpy as np
import math

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.geometry.shape import Rectangle, Circle, Polygon
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle, StaticObstacle, ObstacleType, DynamicObstacle
from commonroad.scenario.trajectory import State
from commonroad.prediction.prediction import Prediction

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

from crdesigner.ui.gui.mwindow.toolboxes.obstacle_toolbox.obstacle_toolbox_ui import ObstacleToolboxUI


class ObstacleToolbox(QDockWidget):
    def __init__(self, current_scenario: Scenario, callback, tmp_folder, text_browser):
        super().__init__("Obstacle Toolbox")

        self.current_scenario = current_scenario
        self.callback = callback
        self.obstacle_toolbox_ui = ObstacleToolboxUI(text_browser)
        self.adjust_ui()
        self.connect_gui_elements()
        self.tmp_folder = tmp_folder
        self.text_browser = text_browser
        self.update_ongoing = False

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=tmp_folder)
        else:
            self.sumo_simulation = None

    def adjust_ui(self):
        """Updates GUI properties like width, etc."""
        self.setFloating(True)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWidget(self.obstacle_toolbox_ui)
        self.obstacle_toolbox_ui.setMinimumWidth(450)

    def connect_gui_elements(self):
        """adds functionality to gui elements like buttons, menus etc"""
        self.initialize_obstacle_information()

        self.obstacle_toolbox_ui.selected_obstacle.currentTextChanged.connect(
            lambda: self.update_obstacle_information())
        self.obstacle_toolbox_ui.button_update_obstacle.clicked.connect(
            lambda: self.update_obstacle())

        self.obstacle_toolbox_ui.obstacle_state_variable.currentTextChanged.connect(
            lambda: self.plot_obstacle_state_profile())

        self.obstacle_toolbox_ui.button_remove_obstacle.clicked.connect(
            lambda: self.remove_obstacle())

        self.obstacle_toolbox_ui.button_add_static_obstacle.clicked.connect(
           lambda: self.add_static_obstacle())
        
        self.obstacle_toolbox_ui.obstacle_shape.currentTextChanged.connect(
            lambda: self.obstacle_toolbox_ui.toggle_sections())

        if SUMO_AVAILABLE:
            self.obstacle_toolbox_ui.button_start_simulation.clicked.connect(
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

    def refresh_toolbox(self, scenario: Scenario):
        self.current_scenario = scenario
        self.initialize_toolbox()

    def static_obstacle_details(self, obstacle_id):
        """Creates static obstacles"""
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            static_obstacle = StaticObstacle(
                obstacle_id = obstacle_id,

                obstacle_type = ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape = Rectangle(
                    length = float(self.obstacle_toolbox_ui.obstacle_length.text()),
                    width = float(self.obstacle_toolbox_ui.obstacle_width.text()) 
                ),

                initial_state = State(**{'position': np.array([
                    float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                    float(self.obstacle_toolbox_ui.obstacle_y_Position.text())
                ]),
                'orientation': math.radians(float(self.obstacle_toolbox_ui.obstacle_orientation.text())),
                'time_step': 1
                })
            )

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            static_obstacle = StaticObstacle(
                obstacle_id = obstacle_id,

                obstacle_type = ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape = Circle(
                    radius = float(self.obstacle_toolbox_ui.obstacle_radius.text())
                ),

                initial_state = State(**{'position': np.array([
                    float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                    float(self.obstacle_toolbox_ui.obstacle_y_Position.text())
                ]),
                'orientation': 0,
                'time_step': 1
                })
            )
        
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            static_obstacle = StaticObstacle(
                obstacle_id = obstacle_id,

                obstacle_type = ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape = Polygon(
                    
                    vertices = self.polygon_array()
                ),

                initial_state = State(**{'position': np.array([
                    0,
                    0
                ]),
                'orientation': 0, 
                'time_step': 1
                })
            )

        self.current_scenario.add_objects(static_obstacle)
        self.callback(self.current_scenario)
    
    def polygon_array(self):
        """returns a list of the vertices from the gui menu"""
        vertices = []
        for i in range(self.obstacle_toolbox_ui.amount_vertices):
            if self.obstacle_toolbox_ui.vertices_x[i].text() != "" and self.obstacle_toolbox_ui.vertices_y[i].text() != "":
                temp = [float(self.obstacle_toolbox_ui.vertices_x[i].text()), float(self.obstacle_toolbox_ui.vertices_y[i].text())]
                vertices.append(temp)
        
        if len(vertices) < 3:
            self.text_browser.append("At least 3 vertices are needed to create a polygon")  
            return

        vertices = np.asarray(vertices)
        return vertices

    def add_static_obstacle(self):
        """creates the static obstacle"""
        try:
            obstacle_id = self.current_scenario.generate_object_id()
            self.static_obstacle_details(obstacle_id)
        except:
            self.text_browser.append("Error when adding static obstacle")
    
    def update_obstacle(self):
        """updates obstacle by deleting it and then adding it again with same id"""
        try:
            obstacle_id = int(self.obstacle_toolbox_ui.selected_obstacle.currentText())
            selected_obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            self.current_scenario.remove_obstacle(selected_obstacle)
            self.static_obstacle_details(obstacle_id)
        except:
            self.text_browser.append("Error: when updating obstacle")

    def initialize_toolbox(self):
        self.initialize_obstacle_information()

    def initialize_obstacle_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.clear_obstacle_fields()

        self.obstacle_toolbox_ui.selected_obstacle.clear()
        self.obstacle_toolbox_ui.selected_obstacle.addItems(
            ["None"] + [str(item) for item in self.collect_obstacle_ids()])
        self.obstacle_toolbox_ui.selected_obstacle.setCurrentIndex(0)

    def plot_obstacle_state_profile(self):
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"] and not self.update_ongoing:
            obstacle_id = int(self.obstacle_toolbox_ui.selected_obstacle.currentText())
            obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
            if state_variable_name == "x-position":
                profile = [obstacle.initial_state.__getattribute__("position")[0]]
                if isinstance(obstacle, DynamicObstacle):
                    profile += [state.__getattribute__("position")[0]
                                for state in obstacle.prediction.trajectory.state_list]
            elif state_variable_name == "y-position":
                profile = [obstacle.initial_state.__getattribute__("position")[1]]
                if isinstance(obstacle, DynamicObstacle):
                    profile += [state.__getattribute__("position")[1]
                                for state in obstacle.prediction.trajectory.state_list]
            else:
                profile = [obstacle.initial_state.__getattribute__(state_variable_name)]
                if isinstance(obstacle, DynamicObstacle):
                    profile += [state.__getattribute__(state_variable_name)
                                for state in obstacle.prediction.trajectory.state_list]
            time = [obstacle.initial_state.time_step]
            if isinstance(obstacle, DynamicObstacle):
                time += [state.time_step for state in obstacle.prediction.trajectory.state_list]

            # clear previous profile
            self.obstacle_toolbox_ui.figure.clear()

            # create an axis
            ax = self.obstacle_toolbox_ui.figure.add_subplot(111)

            # plot data
            ax.plot(time, profile, '.-', markersize=4)
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.1f}'))
            ax.set_xlabel("time [s]")
            ax.set_ylabel(self.resolve_y_label(state_variable_name))
            self.obstacle_toolbox_ui.figure.tight_layout()
            # refresh canvas
            self.obstacle_toolbox_ui.canvas.draw()

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

    def update_obstacle_information(self):
        """retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox"""
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:
            self.update_ongoing = True
            obstacle_id = int(self.obstacle_toolbox_ui.selected_obstacle.currentText())
            obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            if isinstance(obstacle.obstacle_shape, Rectangle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Rectangle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(0)
            

                self.obstacle_toolbox_ui.obstacle_width.setText(str(obstacle.obstacle_shape.width))
                self.obstacle_toolbox_ui.obstacle_length.setText(str(obstacle.obstacle_shape.length))

                self.obstacle_toolbox_ui.obstacle_x_Position.setText(str(obstacle.initial_state.__getattribute__("position")[0]))
                self.obstacle_toolbox_ui.obstacle_y_Position.setText(str(obstacle.initial_state.__getattribute__("position")[1]))
                self.obstacle_toolbox_ui.obstacle_orientation.setText(str(math.degrees(obstacle.initial_state.__getattribute__("orientation"))))

            elif isinstance(obstacle.obstacle_shape, Circle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Circle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(1)

                self.obstacle_toolbox_ui.obstacle_radius.setText(str(obstacle.obstacle_shape.radius))
                self.obstacle_toolbox_ui.obstacle_x_Position.setText(str(obstacle.initial_state.__getattribute__("position")[0]))
                self.obstacle_toolbox_ui.obstacle_y_Position.setText(str(obstacle.initial_state.__getattribute__("position")[1]))

            elif isinstance(obstacle.obstacle_shape, Polygon):
                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Polygon":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(2)
                
                #because numpy array has weird formatting I want to get rid of
                temp = obstacle.obstacle_shape.vertices
                vertices = temp.tolist()
                
                #remove extra vertice(s) in toolbox
                if len(vertices) - 1 < self.obstacle_toolbox_ui.amount_vertices:
                    j = self.obstacle_toolbox_ui.amount_vertices - (len(vertices) - 1)
                    for i in range(j):
                        self.obstacle_toolbox_ui.remove_vertice(i)

                for i in range(len(vertices) - 1):
                    #adds another vertice if there are too few in the toolbox
                    if i >= self.obstacle_toolbox_ui.amount_vertices:
                        self.obstacle_toolbox_ui.add_vertice()

                    vertice_string_x = str(vertices[i][0])
                    vertice_string_y = str(vertices[i][1])
                    self.obstacle_toolbox_ui.vertices_x[i].setText(vertice_string_x)
                    self.obstacle_toolbox_ui.vertices_y[i].setText(vertice_string_y)
                
            self.obstacle_toolbox_ui.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
            self.obstacle_toolbox_ui.obstacle_state_variable.clear()
            state_variables = [var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]]

            if "position" in obstacle.initial_state.attributes:
                state_variables += ["x-position", "y-position"]
            self.obstacle_toolbox_ui.obstacle_state_variable.addItems(state_variables)
            self.update_ongoing = False
            self.plot_obstacle_state_profile()

        #if set to "None": clear QLineEdits 
        else:
            self.clear_obstacle_fields()

    def clear_obstacle_fields(self):
        """clears the obstacle QLineEdits"""
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            self.obstacle_toolbox_ui.obstacle_radius.setText("")
            self.obstacle_toolbox_ui.obstacle_x_Position.setText("")
            self.obstacle_toolbox_ui.obstacle_y_Position.setText("")

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            self.obstacle_toolbox_ui.obstacle_width.setText("")
            self.obstacle_toolbox_ui.obstacle_length.setText("")
            self.obstacle_toolbox_ui.obstacle_orientation.setText("")
            self.obstacle_toolbox_ui.obstacle_x_Position.setText("")
            self.obstacle_toolbox_ui.obstacle_y_Position.setText("")
        
        
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            for i in range(self.obstacle_toolbox_ui.amount_vertices):
                self.obstacle_toolbox_ui.vertices_x[i].setText("")
                self.obstacle_toolbox_ui.vertices_y[i].setText("")

    def start_sumo_simulation(self):
        num_time_steps = self.obstacle_toolbox_ui.sumo_simulation_length.value()
        self.sumo_simulation.set_simulation_length(num_time_steps)
        self.sumo_simulation.simulate()
        self.callback(self.sumo_simulation.simulated_scenario.value)

    def remove_obstacle(self):
        """
        Removes the selected obstacle from the scenario.
        """
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:
            obstacle_id = int(self.obstacle_toolbox_ui.selected_obstacle.currentText())
            obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
            self.current_scenario.remove_obstacle(obstacle)
            self.callback(self.current_scenario)