from commonroad.scenario.scenario import Scenario
from commonroad.geometry.shape import Rectangle
from commonroad.scenario.lanelet import LaneletNetwork
import numpy as np


def resize_scenario_based_on_position(scenario: Scenario) -> Scenario:
    # TODO
    return scenario


def resize_scenario_based_on_zoom(scenario: Scenario, center_x: float, center_y: float, dim_x: float, dim_y: float) -> Scenario:
    # TODO
    # create a shape object big enough to fit all relevant shapes on the right positions
    # for this create the x any y positions of the polygon, for reference of naming:
    # A B
    # C D
    a_x = center_x - dim_x / 2
    a_y = center_y + dim_y / 2
    b_x = center_x + dim_x / 2
    b_y = center_y + dim_y / 2
    c_x = center_x - dim_x / 2
    c_y = center_y - dim_y / 2
    d_x = center_x + dim_x / 2
    d_y = center_y - dim_y / 2
    current_viewable_shape = Rectangle(length=dim_y, width=dim_x, center=np.array([center_x, center_y]))
    # now create the new lanelet network and assign it to the scenario
    new_lanelet_network = LaneletNetwork.create_from_lanelet_network(lanelet_network=scenario.lanelet_network,
                                                                     shape_input=current_viewable_shape)
    scenario.lanelet_network = new_lanelet_network
    return scenario
