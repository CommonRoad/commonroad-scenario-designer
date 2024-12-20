import copy

from commonroad.common.validity import ValidTypes
from commonroad.geometry.shape import Circle, Polygon, Rectangle, Shape
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.scenario.scenario import Scenario
from pyproj import CRS, Transformer


def transform_shape(shape: Shape, transformer: Transformer) -> Shape:
    """
    Function that transforms a shape.

    :param shape: Shape that is to be transformed.
    :param transformer: Transformer that transforms the shape.
    :return: Transformed shape.
    """
    shape_copy = copy.deepcopy(shape)
    if isinstance(shape_copy, Rectangle) or isinstance(shape_copy, Circle):
        shape_copy.center[0], shape_copy.center[1] = transformer.transform(
            shape_copy.center[0], shape_copy.center[1]
        )
    elif isinstance(shape_copy, Polygon):
        for vertex in shape_copy.vertices:
            vertex[0], vertex[1] = transformer.transform(vertex[0], vertex[1])
    return shape_copy


def project_planning_problem_set(
    planning_problem_set: PlanningProblemSet, proj_string_from: str, proj_string_to: str
) -> PlanningProblemSet:
    """
    Function that performs a projection onto the planning problem set.

    :param planning_problem_set: PlanningProblemSet that needs to be projected (if not None)
    :param proj_string_from: Source projection.
    :param proj_string_to: Target projection.
    :return: Projected planning problem set.
    """
    crs_from = CRS(proj_string_from)
    crs_to = CRS(proj_string_to)
    transformer = Transformer.from_proj(crs_from, crs_to)

    planning_problem_set = copy.deepcopy(planning_problem_set)
    # transform planning problems
    for planning_problem in planning_problem_set.planning_problem_dict.values():
        if planning_problem.initial_state:
            if isinstance(planning_problem.initial_state.position, ValidTypes.ARRAY):
                (
                    planning_problem.initial_state.position[0],
                    planning_problem.initial_state.position[1],
                ) = transformer.transform(
                    planning_problem.initial_state.position[0],
                    planning_problem.initial_state.position[1],
                )
            if isinstance(planning_problem.initial_state.position, Shape):
                planning_problem.initial_state.position = transform_shape(
                    planning_problem.initial_state.position, transformer
                )

        if planning_problem.goal:
            for state in planning_problem.goal.state_list:
                if state.position:
                    if isinstance(state.position, ValidTypes.ARRAY):
                        state.position[0], state.position[1] = transformer.transform(
                            state.position[0], state.position[1]
                        )
                    if isinstance(state.position, Shape):
                        state.position = transform_shape(state.position, transformer)

    return planning_problem_set


def project_lanelet_network(
    lanelet_network: LaneletNetwork, proj_string_from: str, proj_string_to: str
) -> LaneletNetwork:
    """
    Function that performs a projection onto the lanelet network.

    :param lanelet_network: LaneletNetwork that needs to be projected (if not None)
    :param proj_string_from: Source projection.
    :param proj_string_to: Target projection.
    :return: Projected lanelet network.
    """
    crs_from = CRS(proj_string_from)
    crs_to = CRS(proj_string_to)
    transformer = Transformer.from_proj(crs_from, crs_to)

    for lanelet in lanelet_network.lanelets:
        project_lanelet(lanelet, transformer)

    # transform traffic light coordinates
    for tl in lanelet_network.traffic_lights:
        tl.position[0], tl.position[1] = transformer.transform(tl.position[0], tl.position[1])

    # transform traffic sign coordinates
    for ts in lanelet_network.traffic_signs:
        ts.position[0], ts.position[1] = transformer.transform(ts.position[0], ts.position[1])

    # transform area coordinates
    for area in lanelet_network.areas:
        for border in area.border:
            for vertex in border.border_vertices:
                vertex[0], vertex[1] = transformer.transform(vertex[0], vertex[1])

    return lanelet_network


def project_lanelet(lanelet: Lanelet, transformer: Transformer):
    """
    Function that performs a projection onto the lanelet.

    :param lanelet: Lanelet that needs to be projected.
    :param transformer: Transformer which should be applied.
    """
    for left_vertex in lanelet.left_vertices:
        left_vertex[0], left_vertex[1] = transformer.transform(left_vertex[0], left_vertex[1])
    for right_vertex in lanelet.right_vertices:
        right_vertex[0], right_vertex[1] = transformer.transform(right_vertex[0], right_vertex[1])
    for center_vertex in lanelet.center_vertices:
        center_vertex[0], center_vertex[1] = transformer.transform(
            center_vertex[0], center_vertex[1]
        )
    # transform stop line coordinates
    if lanelet.stop_line is not None:
        lanelet.stop_line.start[0], lanelet.stop_line.start[1] = transformer.transform(
            lanelet.stop_line.start[0], lanelet.stop_line.start[1]
        )
        lanelet.stop_line.end[0], lanelet.stop_line.end[1] = transformer.transform(
            lanelet.stop_line.end[0], lanelet.stop_line.end[1]
        )


def project_obstacles(scenario: Scenario, proj_string_from: str, proj_string_to: str) -> Scenario:
    """
    Function that performs a projection onto the obstacles of a scenario.

    :param scenario: Scenario where obstacles need to be projected (if not None)
    :param proj_string_from: Source projection.
    :param proj_string_to: Target projection.
    :return: Scenario with the projected obstacles.
    """
    crs_from = CRS(proj_string_from)
    crs_to = CRS(proj_string_to)
    transformer = Transformer.from_proj(crs_from, crs_to)

    for obstacle in scenario.obstacles:
        if obstacle.obstacle_shape:
            obstacle.obstacle_shape = transform_shape(obstacle.obstacle_shape, transformer)

        if obstacle.initial_state:
            if obstacle.initial_state.position:
                if isinstance(obstacle.initial_state.position, ValidTypes.ARRAY):
                    obstacle.initial_state.position[0], obstacle.initial_state.position[1] = (
                        transformer.transform(
                            obstacle.initial_state.position[0], obstacle.initial_state.position[1]
                        )
                    )
                if isinstance(obstacle.initial_state.position, Shape):
                    obstacle.initial_state.position = transform_shape(
                        obstacle.initial_state.position, transformer
                    )

        if obstacle.prediction:
            if obstacle.prediction.occupancy_set:
                for occupancy in obstacle.prediction.occupancy_set:
                    occupancy.shape = transform_shape(occupancy.shape, transformer)

            if obstacle.prediction.shape:
                obstacle.prediction.shape = transform_shape(obstacle.prediction.shape, transformer)

            if obstacle.prediction.trajectory:
                for state in obstacle.prediction.trajectory.state_list:
                    if state.position:
                        if isinstance(state.position, ValidTypes.ARRAY):
                            state.position[0], state.position[1] = transformer.transform(
                                state.position[0], state.position[1]
                            )
                        if isinstance(state.position, Shape):
                            state.position = transform_shape(state.position, transformer)

    return scenario


def project_scenario_and_pps(
    scenario: Scenario,
    planning_problem_set: PlanningProblemSet,
    proj_string_from: str,
    proj_string_to: str,
) -> [Scenario, PlanningProblemSet]:
    """
    Function that performs a projection onto the entire scenario and a planning problem set.

    :param scenario: Scenario that needs to be projected.
    :param planning_problem_set: PlanningProblemSet that needs to be projected (if not None)
    :param proj_string_from: Source projection.
    :param proj_string_to: Target projection.
    :return: Projected scenario and a planning problem set.
    """

    # create a deep copy of the scenario
    scenario_copy = copy.deepcopy(scenario)

    # project the lanelet network
    project_lanelet_network(scenario_copy.lanelet_network, proj_string_from, proj_string_to)

    # project the obstacles
    project_obstacles(scenario_copy, proj_string_from, proj_string_to)

    # project the planning problem set
    planning_problem_set = project_planning_problem_set(
        planning_problem_set, proj_string_from, proj_string_to
    )

    return scenario_copy, planning_problem_set
