import numpy as np
from typing import List, Dict

import crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road as road
import crdesigner.map_conversion.opendrive.cr_to_opendrive.utils.commonroad_ccosy_geometry_util as util

from commonroad.scenario.lanelet import LaneletNetwork


class Signal:
    """
    This class converts CommonRoad traffic signal to OpenDRIVE traffic signal
    """
    def __init__(self, road_key: int, unique_id: int, data: List, lane_list: LaneletNetwork) -> None:
        self.road = road.Road.roads[road_key]
        self.id = str(unique_id)
        self.lane_list = lane_list
        self.od_object = data[0]
        self.lanelet_id = data[1]
        self.zOffset = "3.3885"
        self.subtype = "-1"
        self.country_revision = "2021"
        self.unit = "km/h"
        self.width = "0.77"
        self.height = "0.77"
        self.hOffset = "0.0"

        self.s, self.t = self.compute_coordinate()
        self.orientation = self.get_orientation()

    def __str__(self) -> str:
        return f"""
        s={self.s}
        t={self.t}
        id={self.id}
        orientation={self.orientation}
        zOffset={self.zOffset}
        subtype={self.subtype}
        country_revision={self.country_revision}
        unit={self.unit}
        width={self.width}
        height={self.height}
        hOffset={self.hOffset}
        """

    def compute_coordinate(self) -> np.ndarray:
        """
        This function compute reference line coordinates s,t.

        :return: Coordinate along reference line as s
                 and lateral position, positive to the left within the inertial x/y plane as t.
        """
        coords = self.road.center[0] - self.od_object.position

        hdg = util.compute_orientation_from_polyline(self.road.center)[0]

        s = coords[0] * np.cos(hdg) + coords[1] * np.sin(hdg)
        t = coords[1] * np.cos(hdg) - coords[0] * np.sin(hdg)

        if s < 0:
            s = -s
            t = -t
        return s, t

    def get_orientation(self) -> str:
        """
        This function compute orientation of lanelet.

        :return: Either positive sign or negative sign as string.
        """
        lanelet = self.lane_list.find_lanelet_by_id(self.lanelet_id)
        mean_left = np.mean(lanelet.left_vertices)
        mean_right = np.mean(lanelet.right_vertices)
        left_dist = np.linalg.norm(mean_left - self.od_object.position)
        right_dist = np.linalg.norm(mean_right - self.od_object.position)
        if left_dist - right_dist < 0:
            return "-"
        else:
            return "+"
