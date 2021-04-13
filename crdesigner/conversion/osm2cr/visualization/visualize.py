"""
This module holds all interaction between this application and the ***CommonRoad python tools**.
It allows to export a scenario to CR or plot a CR scenario.
"""

import matplotlib.pyplot as plt
# CommonRoad python tools are imported
from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.common.file_reader import CommonRoadFileReader
from crdesigner.conversion.osm2cr.converter_modules import find_bounds

def view_xml(filename= str, ax=None):
    """
    shows the plot of a CR scenario on a axes object
    if no axes are provided, a new window is opened with pyplot

    :param filename: file of scenario
    :param ax: axes to plot on
    :return: None
    """
    print("loading scenario from XML")
    scenario, problem = CommonRoadFileReader(filename).open()
    print("drawing scenario")
    if len(scenario.lanelet_network.lanelets) == 0:
        print("empty scenario")
        return
    limits = find_bounds(scenario)

    # draw params to modify
    draw_params = { 'lanelet_network': {'draw_intersections': True, 'draw_traffic_signs_in_lanelet': True,
                                        'draw_traffic_signs': True, 'draw_traffic_lights': True,
                                        'intersection': {'draw_intersections': True},
                                        'traffic_sign':{'draw_traffic_signs': True,
                                                        'show_label':False,
                                                        'show_traffic_signs':'all',

                                                        'scale_factor': 0.15}},
                    'lanelet': {'show_label': False}}
    if ax is None:
        draw_object(scenario, plot_limits=limits, draw_params=draw_params)
        plt.gca().set_aspect("equal")
        plt.show()
        return
    else:
        draw_object(scenario, plot_limits=limits, ax=ax, draw_params=draw_params)
        ax.set_aspect("equal")

if __name__ == "__main__":

    # TODO Add file location here
    filename = " "

    view_xml(filename)