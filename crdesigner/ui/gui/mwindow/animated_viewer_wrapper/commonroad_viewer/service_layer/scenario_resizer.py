from commonroad.geometry.shape import Rectangle
from commonroad.scenario.lanelet import LaneletNetwork
import numpy as np

from .general_services import detailed_drawing_params_threshold_zoom_met
from .general_services import is_big_map

# TODO rename this - its the general version
def resize_scenario_based_on_zoom(original_lanelet_network: LaneletNetwork, center_x: float, center_y: float, dim_x: float, dim_y: float) -> (LaneletNetwork, bool):
    # TODO only resize when the criteria for a detailed view is meet -> otherwise it takes too long (because resizing with a big shape_input takes much time) and also dont resize if it is a too small map -> then it is unecessary
    # TODO in a nutshell: Resize only big maps when details are displayed
    # only resize the map when details should be shown and the map is large
    # - otherwise the undetailed view is faster than resizing all the time
    print("resize_scenario_based_on_zoom with x y " + str(dim_x) + " " + str(dim_y))
    if detailed_drawing_params_threshold_zoom_met(x=dim_x, y=dim_y) and is_big_map(
            lanelet_count=len(original_lanelet_network.lanelets),
            traffic_sign_count=len(original_lanelet_network.traffic_signs)):
        # create a shape object big enough to fit all relevant shapes on the right positions
        # for this create the x any y positions of the polygon
        current_viewable_shape = Rectangle(length=dim_x * 2, width=dim_y * 2, center=np.array([center_x, center_y]))
        # now create the new lanelet network and assign it to the scenario
        new_lanelet_network = LaneletNetwork.create_from_lanelet_network(lanelet_network=original_lanelet_network,
                                                                         shape_input=current_viewable_shape)
        return new_lanelet_network, True
    else:
        return original_lanelet_network, False
