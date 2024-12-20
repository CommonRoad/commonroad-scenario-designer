from typing import Tuple

import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_sign import (
    TrafficSignIDBelgium,
    TrafficSignIDChina,
    TrafficSignIDCroatia,
    TrafficSignIDFrance,
    TrafficSignIDGermany,
    TrafficSignIDGreece,
    TrafficSignIDItaly,
    TrafficSignIDPuertoRico,
    TrafficSignIDRussia,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points

from crdesigner.verification_repairing.repairing.repairing import ElementRepairing

TSGer = TrafficSignIDGermany
TSZam = TrafficSignIDZamunda
TSUsa = TrafficSignIDUsa
TSChn = TrafficSignIDChina
TSRus = TrafficSignIDRussia
TSBel = TrafficSignIDBelgium
TSFra = TrafficSignIDFrance
TSGrc = TrafficSignIDGreece
TSHrv = TrafficSignIDCroatia
TSIta = TrafficSignIDItaly
TSPri = TrafficSignIDPuertoRico


class TrafficSignRepairing(ElementRepairing):
    """
    The class includes all repairing methods for each supported formula concerning the traffic sign element.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: ScenarioID.
        """
        super().__init__(network, scenario_id)

    def repair_at_least_one_traffic_sign_element(self, location: Tuple[int]):
        """
        Repairs at_least_one_traffic_sign_element.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location

        self._network.remove_traffic_sign(traffic_sign_id)

    def repair_referenced_traffic_sign(self, location: Tuple[int]):
        """
        Repairs referenced_traffic_sign.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location

        self._network.remove_traffic_sign(traffic_sign_id)

    def repair_given_additional_value(self, location: Tuple[int, int]):
        """
        Repairs given_additional_value.

        :param location: Location of invalid state.
        """
        traffic_sign_id, hashed_sign_id = location

        traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)

        sign = None
        for traffic_sign_element in traffic_sign.traffic_sign_elements:
            if hashed_sign_id == hash(traffic_sign_element.traffic_sign_element_id.name.lower()):
                sign = traffic_sign_element

        default_values = {
            TSGer.TOWN_SIGN: "Munich",
            TSGer.MAX_SPEED: "120",
            TSGer.MAX_SPEED_ZONE_START: "70",
            TSGer.MAX_SPEED_ZONE_END: "70",
            TSGer.MIN_SPEED: "60",
            TSGer.MAX_SPEED_END: "70",
            TSZam.TOWN_SIGN: "Zamunda City",
            TSZam.MAX_SPEED: "120",
            TSZam.MAX_SPEED_ZONE_START: "70",
            TSZam.MAX_SPEED_ZONE_END: "70",
            TSZam.MIN_SPEED: "60",
            TSZam.MAX_SPEED_END: "70",
            TSUsa.MAX_SPEED: "120",
            TSChn.MAX_SPEED: "120",
            TSRus.MAX_SPEED: "120",
            TSBel.MAX_SPEED: "120",
            TSFra.MAX_SPEED: "120",
            TSGrc.MAX_SPEED: "120",
            TSHrv.MAX_SPEED: "120",
            TSIta.MAX_SPEED: "120",
            TSPri.MAX_SPEED: "120",
        }

        value = None
        for sign_id, default_value in default_values.items():
            if hashed_sign_id == hash(sign_id.name.lower()):
                value = default_value

        sign.additional_values.append(value)

    def repair_valid_additional_value_speed_sign(self, location: Tuple[int, int]):
        """
        Repairs valid_additional_value_speed_sign.

        :param location: Location of invalid state.
        """
        traffic_sign_id, hashed_sign_id = location

        traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)

        sign = None
        for traffic_sign_element in traffic_sign.traffic_sign_elements:
            if hashed_sign_id == hash(traffic_sign_element.traffic_sign_element_id.name.lower()):
                sign = traffic_sign_element

        for additional_value in sign.additional_values:
            if not additional_value.isnumeric() or (
                additional_value.isnumeric() and int(additional_value) < 0
            ):
                sign.additional_values.remove(additional_value)

    def repair_maximal_distance_from_lanelet(self, location: Tuple[int]):
        """
        Repairs maximal_distance_from_lanelet.

        :param location: Location of invalid state.
        """
        (traffic_sign_id,) = location
        traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)

        if traffic_sign is None:
            return

        lanelet = None
        if len(traffic_sign.first_occurrence) == 0:
            for la in self._network.lanelets:
                if traffic_sign.traffic_sign_id not in la.traffic_signs:
                    continue
                lanelet = la
                if la.adj_right is None:
                    break
        else:
            for lanelet_id in traffic_sign.first_occurrence:
                lanelet = self._network.find_lanelet_by_id(lanelet_id)
                if lanelet.adj_right is None:
                    break
        line = LineString(lanelet.right_vertices)
        point = Point(traffic_sign.position)
        n_point, _ = nearest_points(line, point)

        vector_line = LineString([[n_point.x, n_point.y], [point.x, point.y]])
        shifted_point = vector_line.interpolate(0.5)
        traffic_sign.position = np.array([shifted_point.x, shifted_point.y])
