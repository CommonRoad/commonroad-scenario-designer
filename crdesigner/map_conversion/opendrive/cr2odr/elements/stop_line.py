from typing import Tuple

import numpy as np
from commonroad.geometry.polyline_util import (
    compute_polyline_initial_orientation,  # type: ignore
)
from commonroad.scenario.lanelet import LaneletNetwork  # type: ignore

from crdesigner.map_conversion.opendrive.cr2odr.elements.signal import Signal
from crdesigner.map_conversion.opendrive.cr2odr.utils import config


class StopLine(Signal):
    """
    This StopLine class inherits from Signal class
    which is used to convert CommonRoad stop lines to OpenDRIVE stop lines.
    """

    def __init__(self, road_key: int, unique_id: int, data, lane_list: LaneletNetwork) -> None:
        """
        This function let class StopLine to initialize the object with road_key, unique_id, data, lane_list and
        converts the CommonRoad stop lines into OpenDRIVE stop lines.

        :param road_key: road id in OpenDRIVE format
        :param unique_id: lanelet id
        :param data: list of stop lines in scenario object
        :param lane_list: collection of LaneletNetwork
        """
        Signal.__init__(self, road_key, unique_id, data, lane_list)

        self.name = config.STOPLINE_PREFIX + str(self.id)
        self.dynamic = config.NO
        self.country = config.OPENDRIVE
        self.type = config.STOPLINE_TYPE
        self.value = "-1"

        self.road.print_signal(self)

    def __str__(self) -> str:
        """
        This function returns attributes of stop line in OpenDRIVE format as string.

        :return: attributes of stop line in OpenDRIVE format as string.
        """
        return f"""
        s={self.s}
        t={self.t}
        id={self.id}
        name={self.name}
        dynamic={self.dynamic}
        orientation={self.orientation}
        zOffset={self.zOffset}
        country={self.country}
        type={self.type}
        subtype={self.subtype}
        country_revision={self.country_revision}
        value={self.value}
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
        coords = self.road.center[0] - self.od_object.start
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
        left_dist = np.linalg.norm(mean_left - self.od_object.start)
        right_dist = np.linalg.norm(mean_right - self.od_object.start)
        return config.MINUS_SIGN if (left_dist - right_dist < 0) else config.PLUS_SIGN
