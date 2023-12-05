import copy
import logging
import os

import matplotlib.pyplot as plt
import numpy as np

# Commonroad
from commonroad.geometry.shape import Rectangle
from commonroad.visualization.mp_renderer import MPRenderer
from commonroad.visualization.draw_params import MPDrawParams

# Typing
from typing import List
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crdesigner.comparison_visualization.Lanelet2NodeVisualization import Lanelet2VisNode
    from commonroad.scenario.scenario import Scenario

def convert_scenario_params():
    """
    Converts scenario params from config to commonroad 2023
    """
    draw_params = MPDrawParams()
    draw_params.dynamic_obstacle.draw_icon = True
    draw_params.dynamic_obstacle.show_label = False
    draw_params.lanelet_network.lanelet.show_label = True
    draw_params.planning_problem.initial_state.state.draw_arrow = True
    draw_params.planning_problem.goal_region.draw_occupancies = True
    return draw_params


def convert_planning_to_new_crio_param_version():
    """
    Converts planning params from config to commonroad 2023
    """
    draw_params = MPDrawParams()
    draw_params.planning_problem.initial_state.state.draw_arrow = True
    draw_params.planning_problem.initial_state.state.radius = 0.
    return draw_params



def plot_comparison(
        lanelet2_nodes: List["Lanelet2VisNode"],
        cr_scenario: "Scenario",
        plot_limits_xminmax_yminmax: List[float]

):
    """
    Summary
    -------
    Plots scenario with computed reachable sets for cooperative vehicle.
    """

    # create figure
    figsize = (25, 15)
    plot_limits = None

    renderer = MPRenderer(plot_limits=plot_limits, figsize=figsize)

    draw_params = convert_scenario_params()

    try:
        # plot cr scenario
        cr_scenario.draw(renderer, draw_params=draw_params)
    except:
        pass

    try:
        # plot nodes
        for node in lanelet2_nodes:
            draw_lanelet2_node(node, renderer, draw_params)#
    except:
        pass



    # settings and adjustments
    plt.rc("axes", axisbelow=True)
    ax = plt.gca()
    ax.set_aspect("equal")
    ax.set_title(f"Map Comparison[s]", fontsize=28)
    ax.set_xlabel(f"$s$ [m]", fontsize=28)
    ax.set_ylabel("$d$ [m]", fontsize=28)
    plt.margins(0, 0)
    renderer.render()


    plt.show()




def draw_lanelet2_node(node: "Lanelet2VisNode", renderer, draw_params):
    """
    Draw target state as pink, opace polygon
    """

    dp = copy.copy(draw_params)
    dp.shape.edgecolor = "#ff0000"
    dp.shape.facecolor = "#ff0000"
    dp.shape.opacity = 0.5


    center = np.asarray([node.x, node.y])
    width = 0.00001
    length = 0.00001
    Rectangle(length, width, center).draw(renderer, draw_params=dp)




def save_fig(save_gif: bool, path_output: str, time_step: int):
    """
    Save figures. If save_fig: png for gifs, else format is svg.
    """
    if save_gif:
        # save as png
        print("\tSaving", os.path.join(path_output, f'{"png_reachset"}_{time_step:05d}.png'))
        plt.savefig(os.path.join(path_output, f'{"png_reachset"}_{time_step:05d}.png'), format="png",
                    bbox_inches="tight",
                    transparent=False)

    else:
        # save as svg
        print("\tSaving", os.path.join(path_output, f'{"svg_reachset"}_{time_step:05d}.svg'))
        plt.savefig(f'{path_output}{"svg_reachset"}_{time_step:05d}.svg', format="svg", bbox_inches="tight",
                    transparent=False)

