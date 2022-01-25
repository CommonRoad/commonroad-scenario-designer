from typing import List, Dict

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.traffic_sign import TrafficLight


class Light(Signal):
    """
    This traffic light class inherits from Signal class
    which is used to convert the CommonRoad lights into the OpenDRIVE lights
    """
    def __init__(self, road_key: int, unique_id: int, data: List[TrafficLight], lane_list: LaneletNetwork) -> None:
        super().__init__(road_key, unique_id, data, lane_list)
        self.name = "Light_" + str(self.id)
        self.dynamic = "yes" if self.od_object.active else "no"
        self.country = "OpenDRIVE"
        self.type = "1000001"
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
        countryRevision={self.country_revision}
        value={self.value}
        unit={self.unit}
        width={self.width}
        height={self.height}
        hOffset={self.hOffset}
        """
