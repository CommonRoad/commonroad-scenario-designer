from typing import List, Dict

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal
from commonroad.scenario.lanelet import LaneletNetwork


class StopLine(Signal):
    """
    This StopLine class inherits from Signal class
    which is used to convert CommonRoad stoplines to OpenDRIVE stoplines.
    """
    def __init__(self, road_key: int, unique_id: int, data, lane_list: LaneletNetwork) -> None:
        super().__init__(road_key, unique_id, data, lane_list)
        self.name = "StopLine_" + str(self.id)
        self.dynamic = "no"
        self.country = "OPENDRIVE"
        self.type = "294"
        self.value = "-1"

        self.road.print_signal(self)

    def __str__(self) -> str:
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