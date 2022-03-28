from typing import List

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.signal import Signal

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.traffic_sign import TrafficSign


class Sign(Signal):
    """
    This traffic sign class inherits from Signal class
    which is used to convert CommonRoad sign to OpenDRIVE sign.
    """
    def __init__(self, road_key: int, unique_id: int, data: List[TrafficSign], lane_list: LaneletNetwork) -> None:
        """
        This function let class Sign to initialize the object with road_key, unique_id, data, lane_list and
        converts the CommonRoad traffic signs in to OpenDRIVE traffic signs.

        :param road_key: road id in OpenDRIVE format
        :param unique_id: signal(traffic sign) id
        :param data: list of traffic sign in scenario object
        :param lane_list: collection of LaneletNetwork
        """
        super().__init__(road_key, unique_id, data, lane_list)
        self.name = "Sign_" + str(self.id)
        self.dynamic = "no"
        self.country = self.get_country()
        self.type = str(
            self.od_object.traffic_sign_elements[0].traffic_sign_element_id.value
        )
        # Since sign element with id TrafficSignIDZamunda.PRIORITY or TrafficSignIDZamunda.YIELD and values [],
        # using try catch to avoid empty values
        try:
            self.value = str(self.od_object.traffic_sign_elements[0].additional_values[0])
        except:
            self.value = "-1"

        self.road.print_signal(self)

    def __str__(self) -> str:
        """
        This function returns attributes of sign signal in OpenDRIVE format as string.

        :return: attributes of sign signal in OpenDRIVE format as string.
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

    def get_country(self) -> str:
        """
        This function returns country code of the road.

        :return string: country code of the road.
        """
        base = str(self.od_object.traffic_sign_elements[0].traffic_sign_element_id)
        return base.split("TrafficSignID")[1].split(".")[0].upper()
