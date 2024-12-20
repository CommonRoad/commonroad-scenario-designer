from typing import List, Tuple  # type: ignore

import numpy as np
from commonroad.geometry.polyline_util import (
    compute_polyline_initial_orientation,  # type: ignore
)
from commonroad.scenario.lanelet import LaneletNetwork  # type: ignore

import crdesigner.map_conversion.opendrive.cr2odr.elements.road as road  # type: ignore
from crdesigner.map_conversion.opendrive.cr2odr.utils import config


class Signal:
    """
    This class converts CommonRoad traffic signal to OpenDRIVE traffic signal.
    Class serves as base class for different signal types.
    """

    def __init__(
        self, road_key: int, unique_id: int, data: List, lane_list: LaneletNetwork
    ) -> None:
        """
        This function let class Signal to initialize the object with road_key, unique_id, data, lane_list and
        converts the CommonRoad traffic signals into OpenDRIVE traffic signals.

        :param road_key: road id in OpenDRIVE format
        :param unique_id: signal id
        :param data: list of traffic signal in scenario object
        :param lane_list: collection of LaneletNetwork
        """
        self.road = road.Road.roads[road_key]
        self.id = str(unique_id)
        self.lane_list = lane_list
        self.od_object = data[0]
        self.lanelet_id = data[1]
        self.zOffset = config.SIGNAL_ZOFFSET_VALUE
        self.subtype = config.SIGNAL_SUBTYPE
        self.country_revision = config.SIGNAL_COUNTRY_REVISION_VALUE
        self.unit = config.SIGNAL_UNIT_VALUE
        self.width = config.SIGNAL_WIDTH_VALUE
        self.height = config.SIGNAL_HEIGHT_VALUE
        self.hOffset = config.SIGNAL_HOFFSET_VALUE

        self.s, self.t = self.compute_coordinate()
        self.orientation = self.get_orientation()

    def __str__(self) -> str:
        """
        This function returns attributes of signal in OpenDRIVE format as string.

        :return: attributes of signal in OpenDRIVE format as string.
        """
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

    def compute_coordinate(self) -> Tuple[float, float]:
        """
        This function compute reference line coordinates s,t.

        :return: Coordinate along reference line as s
                 and lateral position, positive to the left within the inertial x/y plane as t.
        """
        coords = self.road.center[0] - self.od_object.position
        hdg = compute_polyline_initial_orientation(self.road.center)

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
        return config.MINUS_SIGN if (left_dist - right_dist < 0) else config.PLUS_SIGN
