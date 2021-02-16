# enabling autoreload will reload modules automatically before executing the code, so that
# you can edit the code for your motion planners and execute them right away without reloading

import os
import sys

path_notebook = os.getcwd()
import numpy as np
# add the root folder to python path
sys.path.append(os.path.join(path_notebook, "../../"))

import matplotlib.pyplot as plt
from IPython import display

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.visualization.draw_dispatch_cr import draw_object

from SMP.motion_planner.motion_planner import MotionPlanner, MotionPlannerType
from SMP.maneuver_automaton.maneuver_automaton import ManeuverAutomaton
from SMP.motion_planner.utility import plot_primitives
from commonroad.common.util import Interval, AngleInterval
from commonroad.scenario.trajectory import State
from commonroad.planning import planning_problem
from commonroad.planning import goal
from commonroad.geometry.shape import Rectangle

# uncomment the following lines to use different motion planners

# type_motion_planner = MotionPlannerType.UCS
# type_motion_planner = MotionPlannerType.GBFS
#type_motion_planner = MotionPlannerType.ASTAR
type_motion_planner = MotionPlannerType.STUDENT_EXAMPLE

# your own motion planner can be called by uncommenting next line
# type_motion_planner = MotionPlannerType.STUDENT


# load scenario
#path_scenario = os.path.join(path_notebook, "/home/aaron/Downloads/CR37/commonroad-search/scenarios/exercise/")
#id_scenario = 'USA_Lanker-1_2_T-1'

path_scenario = os.path.join(path_notebook, "/home/aaron/Downloads/CR37/commonroad-map-tool/crmapconverter/")
id_scenario = 'ZAM_Tutorial-1_2_T-3'
#id_scenario = 'ARG_Carcarana-10_1_T-1'

# read in scenario and planning problem set
scenario, planning_problem_set = CommonRoadFileReader(path_scenario + id_scenario + '.xml').open()
# retrieve the first planning problem in the problem set
#planning_problem1 = list(planning_problem_set.planning_problem_dict.values())[0]
lanelet_1 = scenario.lanelet_network.find_lanelet_by_id(1)

goal_region_shape = Rectangle(width=10, length=3, center=np.array([76.5,70]))
goal_region_shape2 = Rectangle(width=3, length=10, center=np.array([15,0]))
goal_region = State(position=goal_region_shape,velocity=Interval(0, 100), time_step=Interval(0,300))
#goal_region2 = State(position=goal_region_shape2,velocity=Interval(0, 100), time_step=Interval(0,300))

initial_state = State(position=np.array([5,0]), velocity=50, orientation=0, yaw_rate=0.01,
                      slip_angle=0, time_step=0)


id = scenario.generate_object_id()

goal = goal.GoalRegion([goal_region])#,goal_region2])
planning_problem2 = planning_problem.PlanningProblem(planning_problem_id=id, initial_state=initial_state,
                                                     goal_region=goal)

planning_problem_set_file = planning_problem_set
planning_problem_set.add_planning_problem(planning_problem=planning_problem2)

# visualize scenario
for i in range(0, 1):
    display.clear_output(wait=True)
    plt.figure(figsize=(10, 10))
    draw_object(scenario, draw_params={'time_begin': i})
    draw_object(planning_problem_set)

    plt.gca().set_aspect('equal')
    plt.show()

# load the xml with stores the motion primitives
name_file_motion_primitives = 'V_0.0_20.0_Vstep_4.0_SA_-1.066_1.066_SAstep_0.18_T_0.5_Model_BMW_320i.xml'
# generate automaton
automaton = ManeuverAutomaton.generate_automaton(name_file_motion_primitives)
# plot motion primitives
#plot_primitives(automaton.list_primitives)

# construct motion planner
motion_planner = MotionPlanner.create(scenario=scenario,
                                      planning_problem=planning_problem2,
                                      automaton=automaton,
                                      motion_planner_type=type_motion_planner)

# solve for solution
list_paths_primitives, _, _ = motion_planner.execute_search()
#print(list_paths_primitives)

from commonroad.scenario.trajectory import State, Trajectory
from SMP.motion_planner.utility import create_trajectory_from_list_states

trajectory_solution = create_trajectory_from_list_states(list_paths_primitives)

from SMP.motion_planner.utility import visualize_solution

#visualize_solution(scenario, planning_problem_set, trajectory_solution)

from commonroad.common.solution import Solution, PlanningProblemSolution, \
    VehicleModel, VehicleType, CostFunction

# create PlanningProblemSolution object
kwarg = {'planning_problem_id': planning_problem2.planning_problem_id,
         'vehicle_model': VehicleModel.KS,  # used vehicle model, change if needed
         'vehicle_type': VehicleType.BMW_320i,  # used vehicle type, change if needed
         'cost_function': CostFunction.SA1,  # cost funtion, DO NOT use JB1
         'trajectory': trajectory_solution}

planning_problem_solution = PlanningProblemSolution(**kwarg)

# create Solution object
kwarg = {'scenario_id': scenario.scenario_id,
         'planning_problem_solutions': [planning_problem_solution]}

solution = Solution(**kwarg)

from commonroad_dc.feasibility.solution_checker import valid_solution

valid_solution(scenario, planning_problem_set, solution)

from commonroad.common.solution import CommonRoadSolutionWriter

dir_output = "/home/aaron/Downloads/CR37/commonroad-search/outputs/solutions"
#solution_KS2:SA1:ZAM_1_2_T-3:2020a.xml

# write solution to a CommonRoad XML file
csw = CommonRoadSolutionWriter(solution)
csw.write_to_file(output_path=dir_output, overwrite=True)



# import necesary classes from different modules
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.trajectory import Trajectory
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_writer import OverwriteExistingFile

# initial state has a time step of 0
dynamic_obstacle_initial_state = initial_state

# generate the states for the obstacle for time steps 1 to 40 by assuming constant velocity
"""state_list = []
for i in range(1, 41):
    # compute new position
    new_position = np.array([dynamic_obstacle_initial_state.position[0] + scenario.dt * i * 22, 0])
    # create new state
    new_state = State(position = new_position, velocity = 22,orientation = 0.02, time_step = i)
    # add new state to state_list
    state_list.append(new_state)"""

state_list = trajectory_solution.state_list
print(trajectory_solution.final_state)

# create the trajectory of the obstacle, starting at time step 1
dynamic_obstacle_trajectory = Trajectory(1, state_list)

# create the prediction using the trajectory and the shape of the obstacle
dynamic_obstacle_shape = Rectangle(width = 1.8, length = 4.3)
dynamic_obstacle_prediction = TrajectoryPrediction(dynamic_obstacle_trajectory, dynamic_obstacle_shape)

# generate the dynamic obstacle according to the specification
dynamic_obstacle_id = scenario.generate_object_id()
dynamic_obstacle_type = ObstacleType.CAR
dynamic_obstacle = DynamicObstacle(dynamic_obstacle_id,
                                   dynamic_obstacle_type,
                                   dynamic_obstacle_shape,
                                   dynamic_obstacle_initial_state,
                                   dynamic_obstacle_prediction)

# add dynamic obstacle to the scenario
scenario.add_objects(dynamic_obstacle)

for i in range(0, 1):
    # uncomment to clear previous graph
    # display.clear_output(wait=True)

    plt.figure(figsize=(25, 10))
    draw_object(scenario, draw_params={'time_begin': i})
    draw_object(planning_problem_set)
    plt.gca().set_aspect('equal')
    plt.show()


author = 'Max Mustermann'
affiliation = 'Technical University of Munich, Germany'
source = ''

fw = CommonRoadFileWriter(scenario, planning_problem_set_file, author, affiliation, source) #planning_problem_set

filename = "ZAM_Tutorial-1_2_T-4.xml"
fw.write_to_file(filename, OverwriteExistingFile.ALWAYS)