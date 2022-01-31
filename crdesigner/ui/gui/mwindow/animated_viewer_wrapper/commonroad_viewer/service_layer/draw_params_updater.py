from .general_services import detailed_drawing_params_threshold_zoom_met
from .general_services import is_big_map


def update_draw_params_based_on_scenario(lanelet_count: int, traffic_sign_count: int) -> {}:
    """
    Return the parameter for drawing a lanelet network in the Dynamic Canvas based on complexity of the lanelet network.
    Currently there are 2 Options: Either the detailed parameter or the undetailed. Undetailed are used on large maps
    when zoomed out to improve performance.
    (lanelet_count and traffic_sign_count act as approximation for complexity)
    :param lanelet_count: how many lanelets are in the lanelet network.
    :param traffic_sign_count: how many traffic signs are in the network.
    """
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
    """
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
    """
    # Here render the details
    if detailed_drawing_params_threshold_zoom_met(x=x, y=y):
        return PARAMS_DRAW_DETAILED
    # else only render the lanelets -> big big performance gain
    else:
        return PARAMS_DRAW_UNDETAILED


def update_draw_params_dynamic_only_based_on_zoom(x: float, y: float) -> {}:
    """
    Same as update_draw_params_based_on_zoom but returns parameter for Dynamic Visualization.
    :param x: Absolut value of x axis in Dynamic Canvas
    :param y: Absolut value of y axis in Dynamic Canvas
    """
    # Here render the details
    if detailed_drawing_params_threshold_zoom_met(x=x, y=y):
        return PARAMS_DRAW_DYNAMIC_DETAILED
    # else render only the lanelets
    else:
        return PARAMS_DRAW_DYNAMIC_UNDETAILED


PARAMS_DRAW_DETAILED = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                },
                'lanelet_network': {
                    'traffic_sign': {
                        'draw_traffic_signs': True,
                        'show_traffic_signs': 'all',
                    },
                    'intersection': {
                        'draw_intersections': False,
                        'draw_incoming_lanelets': True,
                        'incoming_lanelets_color': '#3ecbcf',
                        'draw_crossings': True,
                        'crossings_color': '#b62a55',
                        'draw_successors': True,
                        'successors_left_color': '#ff00ff',
                        'successors_straight_color': 'blue',
                        'successors_right_color': '#ccff00',
                        'show_label': True,
                    },
                }
            }
        }


PARAMS_DRAW_UNDETAILED = {
    'scenario': {
        'dynamic_obstacle': {
            'trajectory': {
                'show_label': False,
                'draw_trajectory': False
            }
        },
        'lanelet_network':
            {'traffic_sign': {
                'draw_traffic_signs': False
            },
            'lanelet': {
                'draw_border_vertices': False,
                'draw_start_and_direction': False,
                'draw_stop_line': False,
                'draw_center_bound': False,
                'draw_right_bound': False,
                'draw_left_bound': False,
                "fill_lanelet": True,
                "draw_line_markings": False
            },
            'intersection': {
                'draw_intersections': False,
                'draw_incoming_lanelets': True,
                'incoming_lanelets_color': '#3ecbcf',
                'draw_crossings': True,
                'crossings_color': '#b62a55',
                'draw_successors': True,
                'successors_left_color': '#ff00ff',
                'successors_straight_color': 'blue',
                'successors_right_color': '#ccff00',
                'show_label': True, },
            "traffic_light": {
                "draw_traffic_lights": False,
                "draw_stop_line": False,
                "draw_start_and_direction": False
            }
            }
        }
    }


PARAMS_DRAW_DYNAMIC_DETAILED = {
            'scenario': {
                'dynamic_obstacle': {
                    'trajectory': {
                        'show_label': True,
                        'draw_trajectory': False
                    }
                },
                'lanelet_network': {
                    'intersection': {'draw_intersections': False},
                    'lanelet': {
                        'draw_border_vertices': False,
                        'draw_start_and_direction': False,
                        'draw_stop_line': False,
                        'draw_center_bound': False,
                        'draw_right_bound': False,
                        'draw_left_bound': False
                    },
                    'traffic_sign': {
                        'draw_traffic_signs': True,
                        'show_traffic_signs': 'all',
                        # 'scale_factor': 0.2
                    },
                }
            }
        }


PARAMS_DRAW_DYNAMIC_UNDETAILED = {
    'scenario': {
        'dynamic_obstacle': {
            'trajectory': {
                'show_label': False,
                'draw_trajectory': False
            }
        },
        'lanelet_network': {
            'intersection': {
                'draw_intersections': False
            },
            'lanelet': {
                'draw_border_vertices': False,
                'draw_start_and_direction': False,
                'draw_stop_line': False,
                'draw_center_bound': False,
                'draw_right_bound': False,
                'draw_left_bound': False,
                "fill_lanelet": True,
                "draw_line_markings": False
            }, 'traffic_sign': {
                'draw_traffic_signs': False,
            },
            "traffic_light": {
                "draw_traffic_lights": False,
                "draw_stop_line": False,
                "draw_start_and_direction": False
            }
        }
    }
}
