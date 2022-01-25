from typing import List
import matplotlib as mpl
import numpy as np
import math
import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from commonroad.geometry.polyline_util import *
from commonroad.geometry.shape import Rectangle, Circle, Polygon
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.obstacle import Obstacle, StaticObstacle, ObstacleType, DynamicObstacle
from commonroad.scenario.trajectory import State, Trajectory

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer import DynamicCanvas
#from crdesigner.ui.gui.mwindow.mwindow import MWindowWrapper

if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMOSimulation

from crdesigner.ui.gui.mwindow.toolboxes.obstacle_toolbox.obstacle_toolbox_ui import ObstacleToolboxUI

from typing import Union
from commonroad.prediction.prediction import Prediction, Occupancy, SetBasedPrediction, TrajectoryPrediction
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.planning.goal import GoalRegion
from commonroad.common.util import Interval, AngleInterval

# try importing RoutePlanner
try:
    from commonroad_route_planner.route_planner import RoutePlanner
    ROUTE_PLANNER = True
except ImportError:
    logging.warning("Cannot import RoutePlanner")
    ROUTE_PLANNER = False


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
        self.init_canvas()
        self.amount_obstacles = 0
        self.canvas = DynamicCanvas()
        #self.viewer = AnimatedViewer(parent, self.callback)

        # for profile visualisation
        self.sel_point = None
        self.xyova = []
        self.pos = []

        if SUMO_AVAILABLE:
            self.sumo_simulation = SUMOSimulation(tmp_folder=tmp_folder)
        else:
            self.sumo_simulation = None

    def init_canvas(self):
        self.obstacle_toolbox_ui.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.obstacle_toolbox_ui.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.obstacle_toolbox_ui.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

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
        self.obstacle_toolbox_ui.button_update_obstacle.clicked.connect(lambda: self.update_obstacle())

        self.obstacle_toolbox_ui.obstacle_state_variable.currentTextChanged.connect(
                lambda: self.plot_obstacle_state_profile())

        self.obstacle_toolbox_ui.button_remove_obstacle.clicked.connect(lambda: self.remove_obstacle())

        self.obstacle_toolbox_ui.button_add_static_obstacle.clicked.connect(lambda: self.add_obstacle())
        
        self.obstacle_toolbox_ui.obstacle_shape.currentTextChanged.connect(
            lambda: self.obstacle_toolbox_ui.toggle_sections())
        
        self.obstacle_toolbox_ui.obstacle_dyn_stat.currentTextChanged.connect(
            lambda: self.obstacle_toolbox_ui.toggle_dynamic_static())

        if SUMO_AVAILABLE:
            self.obstacle_toolbox_ui.button_start_simulation.clicked.connect(lambda: self.start_sumo_simulation())

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
            static_obstacle = StaticObstacle(obstacle_id=obstacle_id,
                                             obstacle_type=ObstacleType(
                                                     self.obstacle_toolbox_ui.obstacle_type.currentText()),
                                             obstacle_shape=Rectangle(
                                                     length=float(self.obstacle_toolbox_ui.obstacle_length.text()),
                                                     width=float(self.obstacle_toolbox_ui.obstacle_width.text())),
                                             initial_state=State(**{'position': np.array(
                                                     [float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                                                      float(self.obstacle_toolbox_ui.obstacle_y_Position.text())]),
                                                 'orientation': math.radians(float(
                                                         self.obstacle_toolbox_ui.obstacle_orientation.text())),
                                                 'time_step': 1}))
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            static_obstacle = StaticObstacle(obstacle_id=obstacle_id,
                                             obstacle_type=ObstacleType(
                                                     self.obstacle_toolbox_ui.obstacle_type.currentText()),
                                             obstacle_shape=Circle(
                                                     radius=float(self.obstacle_toolbox_ui.obstacle_radius.text())),
                                             initial_state=State(**{'position': np.array(
                                                     [float(self.obstacle_toolbox_ui.obstacle_x_Position.text()),
                                                      float(self.obstacle_toolbox_ui.obstacle_y_Position.text())]),
                                                 'orientation': 0, 'time_step': 1}))
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            static_obstacle = StaticObstacle(
                obstacle_id=obstacle_id,

                obstacle_type=ObstacleType(self.obstacle_toolbox_ui.obstacle_type.currentText()),
                obstacle_shape=Polygon(
                    vertices=self.polygon_array()
                ),

                initial_state=State(**{'position': np.array([
                    0,
                    0
                ]),
                'orientation': 0, 
                'time_step': 1
                })
            )
        #set_static_obstacle_color("g")
        self.canvas.set_static_obstacle_color("g")
        self.current_scenario.add_objects(static_obstacle)         
        self.callback(self.current_scenario)
        #self.canvas.draw_scenario(self.current_scenario)
        #self.canvas.draw_obstacle(static_obstacle)
        
    def dynamic_obstacle_details(self, obstacle_id):
        """creates dynamic obstacles"""
        #test code maybe change later
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            dynamic_obstacle = DynamicObstacle(
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
                'velocity': float(self.obstacle_toolbox_ui.obstacle_velocity.text()),
                'acceleration': 0,
                'time_step': 0
                }),
                prediction = TrajectoryPrediction(
                    shape = Rectangle(float(self.obstacle_toolbox_ui.obstacle_length.text()), width = float(self.obstacle_toolbox_ui.obstacle_width.text())),
                    trajectory = Trajectory(
                        initial_time_step = 1,
                        state_list = self.initial_trajectory()
                    )
                )
            )

        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            dynamic_obstacle = DynamicObstacle(
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
                    'time_step': 0,
                    'velocity': float(self.obstacle_toolbox_ui.obstacle_velocity.text()),
                    'acceleration': 0
                }),
                prediction=TrajectoryPrediction(
                    shape=Circle(float(self.obstacle_toolbox_ui.obstacle_radius.text())),
                    trajectory=Trajectory(
                        initial_time_step=1,
                        state_list=self.initial_trajectory()
                    )
                )
            )
        
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            dynamic_obstacle = DynamicObstacle(
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
                    'time_step': 0
                }),
                prediction=TrajectoryPrediction(
                    shape=Polygon(vertices=self.polygon_array()),
                    trajectory=Trajectory(
                        initial_time_step=1,
                        state_list=self.initial_trajectory()
                    )
                )

            )
        self.current_scenario.add_objects(dynamic_obstacle)       
        self.callback(self.current_scenario)

    def initial_trajectory(self):
        #don't know how to get position for polygon
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Polygon":
            initial_position_x = float(self.obstacle_toolbox_ui.obstacle_x_Position.text()) 
            initial_position_y = float(self.obstacle_toolbox_ui.obstacle_y_Position.text())
        else:
            initial_position_x = 0
            initial_position_y = 0

        goal_position_x = float(self.obstacle_toolbox_ui.obstacle_x_Goal_Position.text())
        goal_position_y = float(self.obstacle_toolbox_ui.obstacle_y_Goal_Position.text())
        goal_orientation = 0 #will be set by routeplanner

        velocity = float(self.obstacle_toolbox_ui.obstacle_velocity.text())
        acceleration = 0
        state_list = []
        finished = False

        #if updating positions in profile visualisation
        if self.xyova:
            for j in range(1, len(self.xyova)):
                new_position = np.array([self.xyova[j][0], self.xyova[j][1]])
                new_state = State(**{'position': new_position, 'velocity': self.xyova[j][3],
                'acceleration': self.xyova[j][4], 'orientation': self.xyova[j][2], 'time_step': j})
                state_list.append(new_state)
                
            return state_list

        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            orientation = math.radians(float(self.obstacle_toolbox_ui.obstacle_orientation.text()))
        else:
            orientation = 0

        initial_state = State(**{'position': np.array([
                    initial_position_x,
                    initial_position_y
                ]),
                'orientation': orientation,
                'time_step': 1,
                'yaw_rate': 0,
                'velocity': velocity,
                'slip_angle': 0,
                'acceleration': acceleration
                })
        if self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Rectangle":
            goal_state = [State(**{'position': Rectangle(float(self.obstacle_toolbox_ui.obstacle_length.text()), 
                width = float(self.obstacle_toolbox_ui.obstacle_width.text()), center=np.array([goal_position_x, goal_position_y]), orientation=goal_orientation),
                    'orientation': AngleInterval(-3,3),
                    'time_step': Interval(25, 30),
                    })]
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Circle":
            goal_state = [State(**{'position': Circle(float(self.obstacle_toolbox_ui.obstacle_radius.text()),
                                                      center=np.array([goal_position_x, goal_position_y])),
                                   'orientation': AngleInterval(-3, 3),
                                   'time_step': Interval(25, 30)})]

        # NOTE the polygon doesnt really work, there is no center property, how specify goal state?
        elif self.obstacle_toolbox_ui.obstacle_shape.currentText() == "Polygon":
            goal_state = [State(**{'position': self.polygon_array(),
                                'orientation': AngleInterval(-3, 3),
                                   'time_step': Interval(25, 30)})]
            self.text_browser.append("Warning: Polygons as dynamic obstacles are not currently supported")

        goal_region = GoalRegion(goal_state)
        planning_problem = PlanningProblem(self.amount_obstacles+1, initial_state, goal_region)
        if ROUTE_PLANNER:
            route_planner = RoutePlanner(self.current_scenario, planning_problem,
                                         backend=RoutePlanner.Backend.NETWORKX_REVERSED,
                                         allow_diagonal=True, reach_goal_state=True)
        else:
            text_browser.append("RoutePlanner is needed for adding dynamic obstacles")
            return

        candidate_holder = route_planner.plan_routes()
        # retrieve all routes
        list_routes, num_route_candidates = candidate_holder.retrieve_all_routes()
        print(f"Number of route candidates: {num_route_candidates}")
        # retrieve first route
        route = candidate_holder.retrieve_first_route()
        # resample polyline so we get the right velocity
        trajectory = resample_polyline_with_distance(route.reference_path, velocity * self.current_scenario.dt)

        j = 0
        # route always start at the beginning of the lanelet
        # if start before start position, remove these coordinates from the trajectory
        for i in trajectory:
            remaining_length = math.dist((i[0], i[1]), (initial_position_x, initial_position_y))
            if remaining_length < self.current_scenario.dt * velocity:
                break
            j += 1

        for i in range(0, j+1):
            trajectory = np.delete(trajectory, 0, 0)

        j = 0
        for i in trajectory:
            # so we dont pass our desired goal position
            remaining_length = math.dist((i[0], i[1]), (goal_position_x, goal_position_y))
            if remaining_length < self.current_scenario.dt * velocity:
                i = [goal_position_x, goal_position_y]
                new_position = np.array([goal_position_x, goal_position_y])
                velocity = self.calc_velocity([trajectory[j-1][0], trajectory[j-1][1]], [goal_position_x, goal_position_y])
                finished = True
            else:
                new_position = np.array([i[0], i[1]])
            new_state = State(**{'position': new_position, 'orientation': route.path_orientation[j], 
            'velocity': velocity, 'acceleration': acceleration, 'time_step': j+1})
            state_list.append(new_state)
            j += 1
            if finished:
                # self.trajectory_old = trajectory #for changing speed on an interval
                break

        return state_list

    def polygon_array(self):
        """returns a list of the vertices from the gui menu"""
        vertices = []
        for i in range(self.obstacle_toolbox_ui.amount_vertices):
            if self.obstacle_toolbox_ui.vertices_x[i].text() != "" and \
                    self.obstacle_toolbox_ui.vertices_y[i].text() != "":
                temp = [float(self.obstacle_toolbox_ui.vertices_x[i].text()),
                        float(self.obstacle_toolbox_ui.vertices_y[i].text())]
                vertices.append(temp)

        if len(vertices) < 3:
            self.text_browser.append("At least 3 vertices are needed to create a polygon")
            return

        vertices = np.asarray(vertices)
        return vertices
    
    def get_current_obstacle(self):
        """returns current selected obstacle"""
        obstacle_id = self.get_current_obstacle_id()
        selected_obstacle = self.current_scenario.obstacle_by_id(obstacle_id)
        return selected_obstacle
    
    def get_current_obstacle_id(self):
        return int(self.obstacle_toolbox_ui.selected_obstacle.currentText())

    def add_obstacle(self):
        """creates a static or dynamic obstacle"""
        obstacle_id = self.current_scenario.generate_object_id()
        self.amount_obstacles = self.current_scenario.generate_object_id()

        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Dynamic":
            try:
                self.dynamic_obstacle_details(obstacle_id)
            except Exception as e:
                self.text_browser.append("Error when adding dynamic obstacle")
        elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Static":
            #try:
                self.static_obstacle_details(obstacle_id)
            #except Exception as e:
             #   self.text_browser.append("Error when adding static obstacle")
    
    def update_obstacle(self):
        """updates obstacle by deleting it and then adding it again with same id"""
        
        selected_obstacle = self.get_current_obstacle()
        obstacle_id = self.get_current_obstacle_id()

        if selected_obstacle:
            self.current_scenario.remove_obstacle(selected_obstacle)

        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Static":
            #try:
                self.static_obstacle_details(obstacle_id)
            #except Exception as e:
             #   self.text_browser.append("Error when updating static obstacle")

        elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Dynamic":
            try:
                self.dynamic_obstacle_details(obstacle_id)
                self.xyova.clear()
            except Exception as e:
                self.text_browser.append("Error when updating dynamic obstacle")
        

    def initialize_toolbox(self):
        self.initialize_obstacle_information()

    def calc_velocity(self, point1, point2):
        """calculates velocity based on two points"""
        distance = math.dist(point1, point2)
        velocity = distance / self.current_scenario.dt
        return velocity
    
    def calc_acceleration(self, velocity1, velocity2):
        """calculates acceleration based on the velocity at 2 points"""
        delta_v = velocity2 - velocity1
        acceleration = delta_v / self.current_scenario.dt
        return acceleration

    def initialize_obstacle_information(self):
        """
        Initializes GUI elements with intersection information.
        """
        self.clear_obstacle_fields()

        self.obstacle_toolbox_ui.selected_obstacle.clear()
        self.obstacle_toolbox_ui.selected_obstacle.addItems(
                ["None"] + [str(item) for item in self.collect_obstacle_ids()])
        self.obstacle_toolbox_ui.selected_obstacle.setCurrentIndex(0)

    def delete_point(self):
        """ deletes right clicked point """
        time = []
        profile = []
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()

        if self.sel_point:
            if not self.xyova:
                self.calculate_xyova()
            self.xyova.pop(self.sel_point[0])
            # removes point at specified timestep
            self.pos.pop(self.sel_point[0])

            for i in self.pos:
                time.append(i[0])
                profile.append(i[1])

        self.draw_plot(time, profile, self.xmin, self.xmax, self.ymin, self.ymax)
        if state_variable_name == "x-position":
            self.obstacle_toolbox_ui.obstacle_x_Position.setText(str(self.pos[0][1]))
            self.obstacle_toolbox_ui.obstacle_x_Goal_Position.setText(str(self.pos[-1][1]))
        
        elif state_variable_name == "y-position":
            self.obstacle_toolbox_ui.obstacle_y_Position.setText(str(self.pos[0][1]))
            self.obstacle_toolbox_ui.obstacle_y_Goal_Position.setText(str(self.pos[-1][1]))

        elif state_variable_name == "orientation":
            self.obstacle_toolbox_ui.obstacle_orientation.setText(str(self.pos[0][1]))

        self.sel_point = None
    
    def on_button_press(self, event):
        """"when left or right mouse button is pressed"""
        if event.inaxes is None:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        # if using zoom or move tool (0 is standard cursor)
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return
        self.sel_point = self.selected_point(event)
        # if no point is selected (pressed too far away from point)
        if self.sel_point is None:
            return
        if event.button == 3:
            self.delete_point()
    
    def on_button_release(self, event):
        """Updates obstacle when left mouse button is released"""
        if event.button != 1:
            return
        if self.sel_point is None:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return

        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        i = 0
        k = 1
        # so all not updated changes are saved (when switching profile)
        if self.xyova:
            for j in self.xyova:
                if state_variable_name == "x-position":
                    j[0] = self.pos[i][1]
                    # change value of obstacle_goal_x_position
                    if j[0] == self.xyova[-1][0]:
                        self.obstacle_toolbox_ui.obstacle_x_Goal_Position.setText(str(j[0]))
                    elif j[0] == self.xyova[0][0]:
                        self.obstacle_toolbox_ui.obstacle_x_Position.setText(str(j[0]))
                    # change velocity based on changes in x-position
                    self.xyova[k][3] = self.calc_velocity([self.pos[k-1][1], self.xyova[k-1][1]],
                                                          [self.pos[k][1], self.xyova[k][1]])
                    # change acceleration based on changes in velocity
                    self.xyova[k][4] = self.calc_acceleration(self.xyova[k-1][3], self.xyova[k][3])
                elif state_variable_name == "y-position":
                    j[1] = self.pos[i][1]
                    # change value of obstacle_goal_y_position
                    if j[1] == self.xyova[-1][1]:
                        self.obstacle_toolbox_ui.obstacle_y_Goal_Position.setText(str(j[1]))
                    elif j[1] == self.xyova[0][1]:
                        self.obstacle_toolbox_ui.obstacle_y_Position.setText(str(j[1]))

                    self.xyova[k][3] = self.calc_velocity([self.xyova[k-1][0], self.pos[k-1][1]], 
                        [self.xyova[k][0], self.pos[k][1]])
                    self.xyova[k][4] = self.calc_acceleration(self.xyova[k-1][3], self.xyova[k][3])

                elif state_variable_name == "orientation":
                    j[2] = self.pos[i][1]
                    if j[2] == self.xyova[0][2]:
                        self.obstacle_toolbox_ui.obstacle_orientation.setText(str(j[2]))
                elif state_variable_name == "velocity":
                    j[3] = self.pos[i][1]
                elif state_variable_name == "acceleration":
                    j[4] = self.pos[i][1]
                i += 1
                if k < len(self.xyova) - 1:
                    k += 1
        else:
            self.calculate_xyova()
        
        self.sel_point = None
    
    def on_mouse_move(self, event):
        """update position of selected point by moving mouse
            and holding down left mouse button"""
        if self.sel_point is None:
            return
        if event.button != 1:
            return
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() == "None":
            return
        if self.obstacle_toolbox_ui.figure.canvas.cursor().shape() != 0:
            return
        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == 'Static':
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "velocity":
            return
        if self.obstacle_toolbox_ui.obstacle_state_variable.currentText() == "acceleration":
            return

        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        time = []
        profile = []
    
        self.calculate_pos()
        self.sel_point[1] = event.ydata
        self.pos[self.sel_point[0]][1] = self.sel_point[1]
    
        for i in self.pos:
            time.append(i[0])
            profile.append(i[1])

        self.draw_plot(time, profile, self.xmin, self.xmax, self.ymin, self.ymax)

    def calculate_xyova(self):
        """calculate xyova array which keeps track of not updated changes"""
        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        i = 0
        k = 1

        if state_variable_name == "x-position":
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            o = selected_obstacle.initial_state.__getattribute__("orientation")

            a = selected_obstacle.initial_state.__getattribute__("acceleration")
            v = self.calc_velocity([self.pos[k-1][1], y], [self.pos[k][1], y])
            self.xyova.append([self.pos[i][1], y, o, v, a])
            self.obstacle_toolbox_ui.obstacle_x_Position.setText(str(self.pos[i][1]))

        elif state_variable_name == "y-position":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            o = selected_obstacle.initial_state.__getattribute__("orientation")

            a = selected_obstacle.initial_state.__getattribute__("acceleration")
            v = self.calc_velocity([x, self.pos[k-1][1]], [x, self.pos[k][1]])
            self.xyova.append([x, self.pos[i][1], o, v, a])
            self.obstacle_toolbox_ui.obstacle_y_Position.setText(str(self.pos[i][1]))

        elif state_variable_name == "orientation":
            x = selected_obstacle.initial_state.__getattribute__("position")[0]
            y = selected_obstacle.initial_state.__getattribute__("position")[1]
            v = selected_obstacle.initial_state.__getattribute__("velocity")
            a = selected_obstacle.initial_state.__getattribute__("acceleration")
            self.xyova.append([x, y, self.pos[i][1], v, a])
            self.obstacle_toolbox_ui.obstacle_orientation.setText(str(self.pos[i][1]))
        i += 1
        k += 1

        for state in selected_obstacle.prediction.trajectory.state_list:
            if state_variable_name == "x-position":
                y = state.__getattribute__("position")[1]
                o = state.__getattribute__("orientation")
                
                v_previous = v
                v = self.calc_velocity([self.pos[k-1][1], y], [self.pos[k][1], y])
                a = self.calc_acceleration(v_previous, v)
                # change value of obstacle_goal_x_position
                if (len(selected_obstacle.prediction.trajectory.state_list) + 1 == i and
                   self.pos[i][1]) == state.__getattribute__("position")[0]:
                    self.obstacle_toolbox_ui.obstacle_x_Goal_Position.setText(str(j[0]))

                self.xyova.append([self.pos[i][1], y, o, v, a])
            elif state_variable_name == "y-position":
                x = state.__getattribute__("position")[0]
                o = state.__getattribute__("orientation")

                v_previous = v
                v = self.calc_velocity([x, self.pos[k-1][1]], [x, self.pos[k][1]])
                a = self.calc_acceleration(v_previous, v)
                    #change value of obstacle_goal_y_position
                if (len(selected_obstacle.prediction.trajectory.state_list) == i + 1 and
                    self.pos[i][1]) == state.__getattribute__("position")[1]:
                    self.obstacle_toolbox_ui.obstacle_y_Goal_Position.setText(str(j[1]))
                a = state.__getattribute__("acceleration")
                self.xyova.append([x, self.pos[i][1], o, v, a])

            elif state_variable_name == "orientation":
                x = state.__getattribute__("position")[0]
                y = state.__getattribute__("position")[1]
                v = state.__getattribute__("velocity")
                a = state.__getattribute__("acceleration")
                self.xyova.append([x, y, self.pos[i][1], v, a])
            i += 1
            if k < len(selected_obstacle.prediction.trajectory.state_list): 
                k += 1

    def calculate_pos(self):
        """calculates the self.pos array which is the array that
        contains the data that is displayed in the plot"""
        selected_obstacle = self.get_current_obstacle()
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
        self.pos.clear()
        t = 0
        if self.xyova:
            for i in self.xyova: 
                if state_variable_name == "x-position":
                    x = i[0]
                    self.pos.append([t,x])
                elif state_variable_name == "y-position":
                    y = i[1]
                    self.pos.append([t,y])
                elif state_variable_name == "orientation":
                    o = i[2]
                    self.pos.append([t,o])
                t += 1
        else:

            if state_variable_name == "x-position":
                x = selected_obstacle.initial_state.__getattribute__("position")[0]
                self.pos.append([t,x])
            elif state_variable_name == "y-position":
                y = selected_obstacle.initial_state.__getattribute__("position")[1]
                self.pos.append([t,y])
            elif state_variable_name == "orientation":
                o = selected_obstacle.initial_state.__getattribute__("orientation")
                self.pos.append([t,o])

            for state in selected_obstacle.prediction.trajectory.state_list:
                t = state.__getattribute__("time_step")
                if state_variable_name == "x-position":
                    x = state.__getattribute__("position")[0]
                    self.pos.append([t,x])
                elif state_variable_name == "y-position":
                    y = state.__getattribute__("position")[1]
                    self.pos.append([t,y])
                elif state_variable_name == "orientation":
                    o = state.__getattribute__("orientation")
                    self.pos.append([t,o])

    def on_xlim_change(self, event):
        self.xmin, self.xmax = event.get_xlim()
    
    def on_ylim_change(self, event):
        self.ymin, self.ymax = event.get_ylim()

    def selected_point(self, event):
        """get the time step of the where the point is located"""

        pos = []
        sel_point = None

        self.calculate_pos()

        # calculate nearest point from mouse click
        for i in range(0, len(self.pos)):
            # distance between cursor and points
            distance = math.dist(self.pos[i], [event.xdata, event.ydata])
            if i == 0:
                smallest_distance = distance
            if distance < 1 and distance <= smallest_distance: 
                smallest_distance = distance
                sel_point = self.pos[i]
        return sel_point
        
    def plot_obstacle_state_profile(self):
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"] and not self.update_ongoing:
            obstacle = self.get_current_obstacle()
            state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
            if state_variable_name == "x-position":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("position")[0]]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[0] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("position")[0]]
                        profile += [state.__getattribute__("position")[0]
                                for state in obstacle.prediction.trajectory.state_list]
            elif state_variable_name == "y-position":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("position")[1]]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[1] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("position")[1]]
                        profile += [state.__getattribute__("position")[1]
                                for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "velocity" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[3] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("velocity")]
                    profile += [state.__getattribute__("velocity")
                            for state in obstacle.prediction.trajectory.state_list]

            elif (state_variable_name == "acceleration" and isinstance(obstacle, DynamicObstacle)):
                if self.xyova:
                    profile = [j[4] for j in self.xyova]
                else:
                    profile = [obstacle.initial_state.__getattribute__("acceleration")]
                    profile += [state.__getattribute__("acceleration")
                        for state in obstacle.prediction.trajectory.state_list]
            
            elif state_variable_name == "orientation":
                if isinstance(obstacle, StaticObstacle):
                    profile = [obstacle.initial_state.__getattribute__("orientation")]
                elif isinstance(obstacle, DynamicObstacle):
                    if self.xyova:
                        profile = [j[2] for j in self.xyova]
                    else:
                        profile = [obstacle.initial_state.__getattribute__("orientation")]
                        profile += [state.__getattribute__("orientation")
                                for state in obstacle.prediction.trajectory.state_list]
        
            if isinstance(obstacle, DynamicObstacle):
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

    def update_obstacle_information(self):
        """retrieves obstacle details to the gui when an obstacle is pressed or the id
        is selected in the obstacle toolbox"""
        if self.obstacle_toolbox_ui.selected_obstacle.currentText() not in ["", "None"]:

            self.update_ongoing = True
            obstacle = self.get_current_obstacle()
            if isinstance(obstacle.obstacle_shape, Rectangle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Rectangle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(0)

                self.obstacle_toolbox_ui.obstacle_width.setText(str(obstacle.obstacle_shape.width))
                self.obstacle_toolbox_ui.obstacle_length.setText(str(obstacle.obstacle_shape.length))

                self.obstacle_toolbox_ui.obstacle_x_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[0]))
                self.obstacle_toolbox_ui.obstacle_y_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[1]))
                self.obstacle_toolbox_ui.obstacle_orientation.setText(
                    str(math.degrees(obstacle.initial_state.__getattribute__("orientation"))))

            elif isinstance(obstacle.obstacle_shape, Circle):

                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Circle":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(1)

                self.obstacle_toolbox_ui.obstacle_radius.setText(str(obstacle.obstacle_shape.radius))
                self.obstacle_toolbox_ui.obstacle_x_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[0]))
                self.obstacle_toolbox_ui.obstacle_y_Position.setText(
                    str(obstacle.initial_state.__getattribute__("position")[1]))

            elif isinstance(obstacle.obstacle_shape, Polygon):
                if self.obstacle_toolbox_ui.obstacle_shape.currentText() != "Polygon":
                    self.obstacle_toolbox_ui.obstacle_shape.setCurrentIndex(2)

                    # because numpy array has weird formatting I want to get rid of
                temp = obstacle.obstacle_shape.vertices
                vertices = temp.tolist()

                # remove extra vertice(s) in toolbox
                if len(vertices) - 1 < self.obstacle_toolbox_ui.amount_vertices:
                    j = self.obstacle_toolbox_ui.amount_vertices - (len(vertices) - 1)
                    for i in range(j):
                        self.obstacle_toolbox_ui.remove_vertice(i)

                for i in range(len(vertices) - 1):
                    # adds another vertice if there are too few in the toolbox
                    if i >= self.obstacle_toolbox_ui.amount_vertices:
                        self.obstacle_toolbox_ui.add_vertice()

                    vertice_string_x = str(vertices[i][0])
                    vertice_string_y = str(vertices[i][1])
                    self.obstacle_toolbox_ui.vertices_x[i].setText(vertice_string_x)
                    self.obstacle_toolbox_ui.vertices_y[i].setText(vertice_string_y)
            
            if isinstance(obstacle, DynamicObstacle):

                if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() != "Dynamic":
                    self.obstacle_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(1)

                end_state = len(obstacle.prediction.trajectory.state_list) - 1

                self.obstacle_toolbox_ui.obstacle_x_Goal_Position.setText(str(
                    obstacle.state_at_time(end_state).__getattribute__("position")[0]))
                self.obstacle_toolbox_ui.obstacle_y_Goal_Position.setText(str(
                    obstacle.state_at_time(end_state).__getattribute__("position")[1]))
                self.obstacle_toolbox_ui.obstacle_velocity.setText(str(
                    obstacle.state_at_time(end_state).__getattribute__("velocity")))
            elif self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() != "Static":
                self.obstacle_toolbox_ui.obstacle_dyn_stat.setCurrentIndex(0)

            self.obstacle_toolbox_ui.obstacle_type.setCurrentText(obstacle.obstacle_type.value)
            self.obstacle_toolbox_ui.obstacle_state_variable.clear()
            state_variables = [var for var in obstacle.initial_state.attributes if var not in ["position", "time_step"]]

            if "position" in obstacle.initial_state.attributes:
                state_variables += ["x-position", "y-position"]

            self.obstacle_toolbox_ui.obstacle_state_variable.addItems(state_variables)
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

        if self.obstacle_toolbox_ui.obstacle_dyn_stat.currentText() == "Dynamic":
            self.obstacle_toolbox_ui.obstacle_x_Goal_Position.setText("")
            self.obstacle_toolbox_ui.obstacle_y_Goal_Position.setText("")
            self.obstacle_toolbox_ui.obstacle_velocity.setText("")

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
            try:
                selected_obstacle = self.get_current_obstacle()
                self.current_scenario.remove_obstacle(selected_obstacle)
                self.callback(self.current_scenario)
                self.amount_obstacles -=1
            except Exception as e:
                self.text_browser.append("Error when removing obstacle")

    def draw_plot(self, time, profile, xmin = None, xmax = None, ymin = None, ymax =None):
        """draws the state plot in the obstacle toolbox"""
        state_variable_name = self.obstacle_toolbox_ui.obstacle_state_variable.currentText()
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

        # to get reasonable limits. If the difference is very small: it will be difficult to make changes
        ax.set_ylim([min(profile)-0.5, max(profile)+0.5])
        # if zoomed in the new plot should be drawn with previous x and y limits
        # (so it doesnt zoom out on mouse event if zoomed in)
        if (self.xmin and self.xmax and self.ymin and self.ymax):
            ax.set_xlim([self.xmin, self.xmax])
            ax.set_ylim([self.ymin, self.ymax])
        # refresh canvas
        self.obstacle_toolbox_ui.canvas.draw()
        ax.callbacks.connect('xlim_changed', self.on_xlim_change)
        ax.callbacks.connect('ylim_changed', self.on_ylim_change)
