from typing import List, Dict

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.traffic_sign import TrafficSign


class Sign(Signal):
    """
    This traffic sign class inherits from Signal class
    which is used to convert CommonRoad sign to OpenDRIVE sign.
    """
    def __init__(self, road_key: int, unique_id: int, data: List[TrafficSign], lane_list: LaneletNetwork) -> None:
        super().__init__(road_key, unique_id, data, lane_list)
        self.name = "Sign_" + str(self.id)
        self.dynamic = "no"
        self.country = self.get_country()
        self.type = str(
            self.od_object.traffic_sign_elements[0].traffic_sign_element_id.value
        )
        # self.value = str(self.od_object.traffic_sign_elements[0].additional_values[0])
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

    def get_country(self):
        base = str(self.od_object.traffic_sign_elements[0].traffic_sign_element_id)
        return base.split("TrafficSignID")[1].split(".")[0].upper()
