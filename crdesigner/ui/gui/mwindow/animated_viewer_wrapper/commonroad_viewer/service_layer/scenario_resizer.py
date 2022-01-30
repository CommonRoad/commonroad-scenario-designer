from commonroad.geometry.shape import Rectangle
from commonroad.scenario.lanelet import LaneletNetwork
import numpy as np

from .general_services import detailed_drawing_params_threshold_zoom_met
from .general_services import is_big_map


def resize_lanelet_network(
        original_lanelet_network: LaneletNetwork,
        center_x: float,
        center_y: float,
        dim_x: float,
        dim_y: float)\
        -> (LaneletNetwork, bool):
    """
    Resize the lanelet_network when handling a large map AND beeing zoomed in. Otherwise there is no performance gain.
    """
    # check if the map is big AND we shall zoom in
    if detailed_drawing_params_threshold_zoom_met(x=dim_x, y=dim_y) and is_big_map(
            lanelet_count=len(original_lanelet_network.lanelets),
            traffic_sign_count=len(original_lanelet_network.traffic_signs)):
        # create a shape object big enough to fit all relevant shapes on the right positions
        current_viewable_shape = Rectangle(length=dim_x * 2, width=dim_y * 2, center=np.array([center_x, center_y]))
        # now create the new lanelet network and return it, also return a boolean to indicate if it was resized or not
        new_lanelet_network = LaneletNetwork.create_from_lanelet_network(lanelet_network=original_lanelet_network,
                                                                         shape_input=current_viewable_shape)
        return new_lanelet_network, True
    else:
        return original_lanelet_network, False
