import matplotlib.pyplot as plt
from crdesigner.conversion.osm2cr.converter_modules.cr_operations.export import find_bounds
from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.common.file_reader import CommonRoadFileReader

from commonroad.visualization.video import create_scenario_video

import os

def view_xml(filename: str, ax=None, video_path=None, video=True, video_length=100) -> None:
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

    # draw limits
    limits = find_bounds(scenario)
 
    draw_params = { 'lanelet_network': {'draw_intersections': True, 'draw_traffic_signs_in_lanelet': True,
                                        'draw_traffic_signs': True, 'draw_traffic_lights': True,
                                        'intersection': {'draw_intersections': False},
                                        'traffic_sign':{'draw_traffic_signs': False,
                                                        'show_label':False,
                                                        'show_traffic_signs':'all',

                                                        'scale_factor': 0.15}},
                    'lanelet': {'show_label': False}}

    # create gif
    if video_path is None:
        video_path = os.path.splitext(filename)[0] + '.gif'

    if video:
        create_scenario_video(obj_lists=[scenario],
        plot_limits=limits, draw_params=draw_params,
        file_path=video_path, time_begin=0, time_end=video_length)
        return

    if ax is None:
        draw_object(scenario, plot_limits=limits, draw_params=draw_params)
        plt.gca().set_aspect("equal")
        plt.show()
        return
    else:
        draw_object(scenario, plot_limits=limits, ax=ax, draw_params=draw_params)
        ax.set_aspect("equal")

def create_video(file):

    view_xml(
        file,
        video_path=file.split('.')[-2] + '.gif')


if __name__ == "__main__": 
    
    # TODO add file location here 
    file = ""

    create_video(file)
