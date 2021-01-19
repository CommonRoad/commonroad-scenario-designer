from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement, TrafficSignIDGermany, TrafficSignIDUsa
from commonroad.scenario.lanelet import Lanelet
from crmapconverter.sumo_map.sumolib_net import Edge, EdgeType, EdgeTypes
import logging
from typing import Optional


class TrafficSignEncoder:
    def __init__(self, edge_types: EdgeTypes):
        self.edge_types = edge_types
        self.traffic_sign: Optional[TrafficSign] = None
        self.lanelet: Optional[Lanelet] = None
        self.edge: Optional[Edge] = None

    def encode(self, traffic_sign: TrafficSign, lanelet: Lanelet, edge: Edge):
        for element in traffic_sign.traffic_sign_elements:
            id = element.traffic_sign_element_id
            # TODO: Add all supported Traffic Sign Countries
            if isinstance(id, TrafficSignIDGermany):
                self._encode_german_traffic_sign_element(element, lanelet, edge)
            elif isinstance(id, TrafficSignIDUsa):
                self._encode_usa_traffic_sign_element(element, lanelet, edge)
            else:
                self._encode_zamunda_traffic_sign_element(element, lanelet, edge)

    def _encode_german_traffic_sign_element(self, element: TrafficSignElement, lanelet: Lanelet, edge: Edge):
        id = element.traffic_sign_element_id
        if id == TrafficSignIDGermany.MAX_SPEED:
            self._set_max_speed(element, edge)
        else:
            logging.warning(f"TrafficSignIDGermany: {element.traffic_sign_element_id} cannot be converted.")

    def _encode_usa_traffic_sign_element(self, traffic_sign_element: TrafficSignElement):
        pass

    def _encode_zamunda_traffic_sign_element(self, traffic_sign_element: TrafficSignElement):
        pass

    def _set_max_speed(self, traffic_sign_element: TrafficSignElement, edge: Edge):
        assert len(traffic_sign_element.additional_values) == 1, \
            f"MAX_SPEED, can only have one additional attribute, has: {traffic_sign_element.additional_values}"
        max_speed = float(traffic_sign_element.additional_values[0])  # in m/s
        new_type = self.edge_types.create_from_update_speed(edge.getType(), max_speed)
        # According to https://gitlab.lrz.de/tum-cps/commonroad-scenarios/-/blob/master/documentation/XML_commonRoad_2020a.pdf
        # MAX_SPEED is valid from the start of the specified lanelet, as well the succeeding one.
        for e in [edge] + list(edge.getOutgoing()):
            e.setType(new_type.id)
            for lane in e.getLanes():
                lane.speed = 0.
