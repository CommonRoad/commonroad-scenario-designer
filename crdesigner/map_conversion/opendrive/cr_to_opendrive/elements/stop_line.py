import numpy as np
from typing import Tuple

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal
from commonroad.geometry.polyline_util import compute_polyline_initial_orientation
from commonroad.scenario.lanelet import LaneletNetwork


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

        self.name = "StopLine_" + str(self.id)
        self.dynamic = "no"
        self.country = "OPENDRIVE"
        self.type = "294"
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
