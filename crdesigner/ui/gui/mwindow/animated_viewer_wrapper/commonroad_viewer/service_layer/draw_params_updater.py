from dataclasses import dataclass, field

from .general_services import detailed_drawing_params_threshold_zoom_met
from .general_services import is_big_map

# from commonroad.visualization.draw_params import MPDrawParams, LaneletNetworkParams, TrajectoryParams, \
#     IntersectionParams, TrafficSignParams, TrafficLightParams, OccupancyParams, DynamicObstacleParams, LaneletParams
modified_draw_params = False
PARAMS_OBSTACLE_CUSTOM = None


COLORSCHEME = {
    'axis': 'All',
    'background': '#f0f0f0',
    'color': '#0a0a0a',
    'font-size': '11pt',
    'highlight': '#202020',
    'highlighttext':'#202020',
    'secondbackground': '#ffffff'}


@dataclass
class ColorSchema:
    axis: str = 'all'
    background: str = '#f0f0f0'
    color: str = '#0a0a0a'
    font_size: str = '11pt'
    highlight: str = '#202020'
    highlight_text: str = '#202020'
    second_background: str = '#ffffff'


# @dataclass
# class DrawParamsCustom(MPDrawParams):
#     color_schema: ColorSchema = field(default_factory=ColorSchema)


def update_draw_params_based_on_scenario(lanelet_count: int, traffic_sign_count: int) -> {}:
    """
    Return the parameter for drawing a lanelet network in the Dynamic Canvas based on complexity of the lanelet network.
    Currently, there are 2 Options: Either the detailed parameter or the undetailed. Undetailed are used on large maps
    when zoomed out to improve performance.
    (lanelet_count and traffic_sign_count act as approximation for complexity)

    :param lanelet_count: how many lanelets are in the lanelet network.
    :param traffic_sign_count: how many traffic signs are in the network.
    :return: detailed, or not detailed draw_params depending on size of scenario
    if custom draw_params are used, they are returned
    """
    if modified_draw_params:
        return PARAMS_DRAW_CUSTOM

    if is_big_map(lanelet_count=lanelet_count, traffic_sign_count=traffic_sign_count):
        return PARAMS_DRAW_UNDETAILED
    else:
        return PARAMS_DRAW_DETAILED


def update_draw_params_dynamic_based_on_scenario(lanelet_count: int, traffic_sign_count: int) -> {}:
    """
    Same as update_draw_params_based_on_scenario, but returns parameters for dynamic visualizations.
    Also based on complexity of lanelet network.

    :param lanelet_count: how many lanelets are in the lanelet network.
    :param traffic_sign_count: how many traffic signs are in the network.
    :return: detailed, or not detailed draw_params depending on size of scenario
    if custom draw_params are used, they are returned
    """
    if modified_draw_params:
        return PARAMS_DRAW_CUSTOM

    if is_big_map(lanelet_count=lanelet_count, traffic_sign_count=traffic_sign_count):
        return PARAMS_DRAW_DYNAMIC_UNDETAILED
    else:
        return PARAMS_DRAW_DYNAMIC_DETAILED


def update_draw_params_based_on_zoom(x: float, y: float) -> {}:
    """
    Return the parameter for drawing a lanelet network in the Dynamic Canvas based on zoom into the canvas.
    When zoomed in enough display the details.

    :param x: Absolut value of x axis in Dynamic Canvas
    :param y: Absolut value of y axis in Dynamic Canvas
    :return: detailed, or not detailed draw_params depending on size of scenario
    if custom draw_params are used, they are returned
    """
    if modified_draw_params:
        return PARAMS_DRAW_CUSTOM
    # Here render the details
    if detailed_drawing_params_threshold_zoom_met(x=x, y=y):
        return PARAMS_DRAW_DETAILED
    # else only render the lanelets -> big big performance gain
    else:
        return PARAMS_DRAW_UNDETAILED


def update_draw_params_dynamic_only_based_on_zoom(x: float, y: float):
    """
    Same as update_draw_params_based_on_zoom but returns parameter for Dynamic Visualization.

    :param x: Absolut value of x-axis in Dynamic Canvas
    :param y: Absolut value of y-axis in Dynamic Canvas
    :return: detailed, or not detailed draw_params depending on size of scenario
    if custom draw_params are used, they are returned
    """
    if modified_draw_params:
        return PARAMS_DRAW_DYNAMIC_CUSTOM
    # Here render the details
    if detailed_drawing_params_threshold_zoom_met(x=x, y=y):
        return PARAMS_DRAW_DYNAMIC_DETAILED
    # else render only the lanelets
    else:
        return PARAMS_DRAW_DYNAMIC_UNDETAILED


def set_draw_params(trajectory: bool, intersection: bool, obstacle_label: bool,
                    obstacle_icon: bool, obstacle_direction: bool,
                    obstacle_signal: bool, occupancy: bool, traffic_signs: bool,
                    traffic_lights: bool, incoming_lanelets: bool, successors: bool,
                    intersection_labels: bool, colorscheme: dict):
    """
    sets draw params
    :param trajectory: toggle draw_trajectory
    :param intersection: toggle draw_intersection
    :param obstacle_label: toggle draw_obstacle_label
    :param obstacle_icon: toggle draw_obstacle_icon
    :param obstacle_signal: toggle draw_signals
    :param occupancy: toggle draw_occupancy
    :param traffic_signs: toggle draw_traffic_signs
    :param traffic_lights: toggle draw_traffic_lights
    :param incoming_lanelets: toggle draw_incoming_lanelets
    :param successors: toggle draw_successors
    :param intersection_labels: toggle show_label
    :param obstacle_directon: toggle obstacle_direction
    """

    global modified_draw_params
    modified_draw_params = True

    global PARAMS_DRAW_CUSTOM
    PARAMS_DRAW_CUSTOM = {'colorscheme': colorscheme,
        'lanelet_network': {'traffic_sign': {'draw_traffic_signs': traffic_signs, 'show_traffic_signs': 'all', },
            'intersection': {'draw_intersections': intersection, 'draw_incoming_lanelets': incoming_lanelets,
                'incoming_lanelets_color': '#3ecbcf', 'draw_crossings': True, 'crossings_color': '#b62a55',
                'draw_successors': successors, 'successors_left_color': '#ff00ff', 'successors_straight_color': 'blue',
                'successors_right_color': '#ccff00', 'show_label': intersection_labels, },
            "traffic_light": {"draw_traffic_lights": traffic_lights, }, },
        'trajectory': {'draw_trajectory': trajectory}, "occupancy": {'draw_occupancies': occupancy, }, }

    global PARAMS_DRAW_DYNAMIC_CUSTOM
    PARAMS_DRAW_DYNAMIC_CUSTOM = {'colorscheme': colorscheme,
        'dynamic_obstacle': {'trajectory': {# 'show_label': obstacle_label,
            'draw_trajectory': trajectory, 'draw_icon': obstacle_icon, 'draw_direction': obstacle_direction,
            'draw_signals': obstacle_signal, }}, 'lanelet_network': {'intersection': {'draw_intersections': False},
            'lanelet': {'draw_border_vertices': False, 'draw_start_and_direction': False, 'draw_stop_line': False,
                'draw_center_bound': False, 'draw_right_bound': False, 'draw_left_bound': False},
            'traffic_sign': {'draw_traffic_signs': True, 'show_traffic_signs': 'all', # 'scale_factor': 0.2
            }, }}


PARAMS_DRAW_DETAILED = {'colorscheme': COLORSCHEME,
    'dynamic_obstacle': {'trajectory': {'show_label': True, 'draw_trajectory': False}},
    'lanelet_network': {'traffic_sign': {'draw_traffic_signs': True, 'show_traffic_signs': 'all', },
        'intersection': {'draw_intersections': False, 'draw_incoming_lanelets': True,
            'incoming_lanelets_color': '#3ecbcf', 'draw_crossings': True, 'crossings_color': '#b62a55',
            'draw_successors': True, 'successors_left_color': '#ff00ff', 'successors_straight_color': 'blue',
            'successors_right_color': '#ccff00', 'show_label': True, }, }}

PARAMS_DRAW_UNDETAILED = {'colorscheme': COLORSCHEME,
    'dynamic_obstacle': {'trajectory': {'show_label': False, 'draw_trajectory': False}},
    'lanelet_network': {'traffic_sign': {'draw_traffic_signs': False},
        'lanelet': {'draw_border_vertices': False, 'draw_start_and_direction': False, 'draw_stop_line': False,
            'draw_center_bound': False, 'draw_right_bound': False, 'draw_left_bound': False, "fill_lanelet": True,
            "draw_line_markings": False}, 'intersection': {'draw_intersections': False, 'draw_incoming_lanelets': True,
            'incoming_lanelets_color': '#3ecbcf', 'draw_crossings': True, 'crossings_color': '#b62a55',
            'draw_successors': True, 'successors_left_color': '#ff00ff', 'successors_straight_color': 'blue',
            'successors_right_color': '#ccff00', 'show_label': True, },
        "traffic_light": {"draw_traffic_lights": False, "draw_stop_line": False, "draw_start_and_direction": False}}}

PARAMS_DRAW_DYNAMIC_DETAILED = {'colorscheme': COLORSCHEME,
    'dynamic_obstacle': {'trajectory': {'show_label': True, 'draw_trajectory': False}},
    'lanelet_network': {'intersection': {'draw_intersections': False},
        'lanelet': {'draw_border_vertices': False, 'draw_start_and_direction': False, 'draw_stop_line': False,
            'draw_center_bound': False, 'draw_right_bound': False, 'draw_left_bound': False},
        'traffic_sign': {'draw_traffic_signs': True, 'show_traffic_signs': 'all', }, }}

PARAMS_DRAW_DYNAMIC_UNDETAILED = {'colorscheme': COLORSCHEME,
    'dynamic_obstacle': {'trajectory': {'show_label': False, 'draw_trajectory': False}},
    'lanelet_network': {'intersection': {'draw_intersections': False},
        'lanelet': {'draw_border_vertices': False, 'draw_start_and_direction': False, 'draw_stop_line': False,
            'draw_center_bound': False, 'draw_right_bound': False, 'draw_left_bound': False, "fill_lanelet": True,
            "draw_line_markings": False}, 'traffic_sign': {'draw_traffic_signs': False, },
        "traffic_light": {"draw_traffic_lights": False, "draw_stop_line": False, "draw_start_and_direction": False}}}

#
#     global PARAMS_DRAW_CUSTOM
#     PARAMS_DRAW_CUSTOM = DrawParamsCustom(color_schema=colorscheme, lanelet_network=LaneletNetworkParams(
#             traffic_sign=TrafficSignParams(draw_traffic_signs=traffic_signs),
#             intersection=IntersectionParams(draw_intersections=intersection, draw_incoming_lanelets=incoming_lanelets,
#                                             draw_successors=successors,
#                                             show_label=intersection_labels),
#             traffic_light=TrafficLightParams(draw_traffic_lights=traffic_lights)),
#                                           trajectory=TrajectoryParams(draw_trajectory=trajectory),
#                                           occupancy=OccupancyParams(draw_occupancies=occupancy))
#
#     global PARAMS_DRAW_DYNAMIC_CUSTOM
#     PARAMS_DRAW_DYNAMIC_CUSTOM = DrawParamsCustom(color_schema=colorscheme, dynamic_obstacle=DynamicObstacleParams(
#             trajectory=TrajectoryParams(draw_trajectory=trajectory), draw_icon=obstacle_icon,
#             draw_direction=obstacle_direction, draw_signals=obstacle_signal),
#                                                   lanelet_network=LaneletNetworkParams(
#             lanelet=LaneletParams(draw_start_and_direction=False, draw_stop_line=False, draw_center_bound=False,
#                                   draw_right_bound=False, draw_left_bound=False),
#             traffic_sign=TrafficSignParams(draw_traffic_signs=True),
#             intersection=IntersectionParams(draw_intersections=False)))
#
#
# PARAMS_DRAW_DETAILED = DrawParamsCustom(dynamic_obstacle=DynamicObstacleParams(
#         trajectory=TrajectoryParams(draw_trajectory=False), show_label=True),
#                                               lanelet_network=LaneletNetworkParams(
#         lanelet=LaneletParams(draw_start_and_direction=False, draw_stop_line=False, draw_center_bound=False,
#                               draw_right_bound=False, draw_left_bound=False),
#         traffic_sign=TrafficSignParams(draw_traffic_signs=True)))
#
# PARAMS_DRAW_UNDETAILED = DrawParamsCustom(lanelet_network=LaneletNetworkParams(
#         lanelet=LaneletParams(draw_start_and_direction=False, draw_stop_line=False, draw_center_bound=False,
#                               draw_right_bound=False, draw_left_bound=False, fill_lanelet=False,
#                               draw_line_markings=False)),
#         traffic_light=TrafficLightParams(draw_traffic_lights=False))
#
# PARAMS_DRAW_DYNAMIC_DETAILED = DrawParamsCustom(dynamic_obstacle=DynamicObstacleParams(
#         trajectory=TrajectoryParams(draw_trajectory=False), show_label=True),
#         lanelet_network=LaneletNetworkParams(
#         lanelet=LaneletParams(draw_start_and_direction=False, draw_stop_line=False, draw_center_bound=False,
#                               draw_right_bound=False, draw_left_bound=False, fill_lanelet=False,
#                               draw_line_markings=False)),
#         traffic_sign=TrafficSignParams(draw_traffic_signs=True))
#
# PARAMS_DRAW_DYNAMIC_UNDETAILED = DrawParamsCustom(dynamic_obstacle=DynamicObstacleParams(
#         trajectory=TrajectoryParams(draw_trajectory=False)),
#         lanelet_network=LaneletNetworkParams(
#         lanelet=LaneletParams(draw_start_and_direction=False, draw_stop_line=False, draw_center_bound=False,
#                               draw_right_bound=False, draw_left_bound=False, fill_lanelet=False,
#                               draw_line_markings=False)),
#         traffic_light=TrafficLightParams(draw_traffic_lights=False))
#
