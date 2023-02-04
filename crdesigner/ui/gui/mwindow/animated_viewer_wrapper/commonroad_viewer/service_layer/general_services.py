def detailed_drawing_params_threshold_zoom_met(x: float, y: float, x_threshold: int = 50, y_threshold: int = 50):
    """
    If x or y are smaller than the predefined (but editable) threshold.
    Used to determine wheter or not the details like traffic_sign etc.. are drawn.
    """
    return x <= x_threshold or y <= y_threshold


def is_big_map(lanelet_count: int, traffic_sign_count: int) -> bool:
    """
    If the criteria for a "big map" is meet.
    Used to determine when to resize etc..
    """
    return lanelet_count > 100 or traffic_sign_count > 50
