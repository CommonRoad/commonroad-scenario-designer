"""
Based on the x and y render specific things.
"""


def update_draw_params_based_on_scenario(lanelet_count: int, traffic_sign_count: int) -> {}:
    if lanelet_count > 200 or traffic_sign_count > 200:
        return PARAMS_DRAW_UNDETAILED
    else:
        return PARAMS_DRAW_DETAILED


def update_draw_params_dynamic_based_on_scenario(lanelet_count: int, traffic_sign_count: int) -> {}:
    if lanelet_count > 200 or traffic_sign_count > 200:
        return PARAMS_DRAW_DYNAMIC_UNDETAILED
    else:
        return PARAMS_DRAW_DYNAMIC_DETAILED


def update_draw_params_based_on_zoom(x: float, y: float) -> {}:
    print("Called update_draw_params_based_on_zoom with x: " + str(x) + " and y: " + str(y))
    # Here render the details
    if x <= 500.0 or y <= 500.0:
        return PARAMS_DRAW_DETAILED
    # else only render the lanelets -> big big performance gain
    else:
        return PARAMS_DRAW_UNDETAILED


def update_draw_params_dynamic_only_based_on_zoom(x: float, y: float) -> {}:
    print("Called update_draw_params_dynamic_only_based_on_zoom with x: " + str(x) + " and y: " + str(y))
    # Here render the details
    if x <= 500.0 or y <= 500.0:
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



PARAMS_DRAW_UNDETAILED = {'scenario': {
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


PARAMS_DRAW_DYNAMIC_UNDETAILED = {'scenario':
    {
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