from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from commonroad.visualization.mp_renderer import MPRenderer

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.network import (
    Network,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.parser import (
    parse_opendrive,
)

input_path = Path("/home/sebastian/Downloads/CrossingComplex8Course.xodr")


opendrive = parse_opendrive(input_path)
road_network = Network()
road_network.load_opendrive(opendrive)
scenario = road_network.export_commonroad_scenario()

road = opendrive.roads[0]

plt.figure(figsize=(25, 10))


rnd = MPRenderer()
# rnd.draw_params.lanelet_network.lanelet.fill_lanelet = False
rnd.draw_params.lanelet_network.lanelet.draw_line_markings = False


scenario.translate_rotate(-scenario.lanelet_network.lanelets[0].left_vertices[0], np.pi / 2)
scenario.draw(rnd)
rnd.render()
la = scenario.lanelet_network.lanelets[0]
for lane_section in road.planView._geo_lengths:
    if lane_section > 11 or lane_section < 0.1:
        continue
    line = la.interpolate_position(lane_section)
    plt.plot(
        [la.left_vertices[line[-1]][0], la.right_vertices[line[-1]][0]],
        [la.left_vertices[line[-1]][1], la.right_vertices[line[-1]][1]],
        "b-",
        zorder=10,
    )
plt.plot([pos[0] for pos in la.left_vertices], [pos[1] for pos in la.left_vertices], "r->", zorder=10)

plt.show()
