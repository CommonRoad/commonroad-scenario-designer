from typing import Tuple

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_light import (
    TrafficLightCycleElement,
    TrafficLightState,
)

from crdesigner.verification_repairing.repairing.repairing import ElementRepairing


class TrafficLightRepairing(ElementRepairing):
    """
    The class includes all repairing methods for each supported formula concerning the traffic light element.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: ScenarioID.
        """
        super(TrafficLightRepairing, self).__init__(network, scenario_id)

    def repair_at_least_one_cycle_element(self, location: Tuple[int]):
        """
        Repairs at_least_one_cycle_element.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._network.remove_traffic_light(traffic_light_id)

    def repair_traffic_light_per_incoming(self, location: Tuple[int, int, int]):
        """
        Repairs traffic_light_per_incoming.

        :param location: Location of invalid state.
        """
        traffic_light_id, lanelet_id, _ = location

        lanelet = self._network.find_lanelet_by_id(lanelet_id)
        lanelet.traffic_lights.discard(traffic_light_id)

    def repair_referenced_traffic_light(self, location: Tuple[int]):
        """
        Repairs referenced_traffic_light.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        self._network.remove_traffic_light(traffic_light_id)

    def repair_non_zero_duration(self, location: Tuple[int]):
        """
        Repairs non_zero_duration.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)

        for cycle_element in traffic_light.traffic_light_cycle.cycle_elements:
            if cycle_element.duration <= 0:
                cycle_element.duration = 30

    def repair_unique_state_in_cycle(self, location: Tuple[int, int]):
        """
        Repairs unique_state_in_cycle.

        :param location: Location of invalid state.
        """
        traffic_light_id, hashed_state = location

        state = None
        for s in TrafficLightState:
            if hashed_state == hash(s):
                state = s

        traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)

        cycle_element = None
        for c_element in traffic_light.traffic_light_cycle.cycle_elements:
            if c_element.state == state:
                cycle_element = c_element

        traffic_light.traffic_light_cycle.cycle_elements.remove(cycle_element)

    def repair_cycle_state_combinations(self, location: Tuple[int]):
        """
        Repairs cycle_state_combinations.

        :param location: Location of invalid state.
        """
        (traffic_light_id,) = location

        TLS = TrafficLightState
        default_combis = {
            "DEU": [(TLS.RED, 30), (TLS.RED_YELLOW, 3), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "CHN": [(TLS.GREEN, 30), (TLS.RED, 30), (TLS.YELLOW, 3)],
            "ESP": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "RUS": [
                (TLS.RED, 30),
                (TLS.YELLOW, 3),
                (TLS.GREEN, 30),
                (TLS.INACTIVE, 2),
                (TLS.GREEN, 2),
                (TLS.INACTIVE, 2),
                (TLS.GREEN, 2),
                (TLS.INACTIVE, 2),
                (TLS.GREEN, 2),
                (TLS.YELLOW, 3),
            ],
            "BEL": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "FRA": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "GRC": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "HRV": [(TLS.RED, 30), (TLS.RED_YELLOW, 3), (TLS.RED, 30), (TLS.YELLOW, 3)],
            "USA": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "ITA": [(TLS.RED, 30), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
            "ZAM": [(TLS.RED, 30), (TLS.RED_YELLOW, 3), (TLS.GREEN, 30), (TLS.YELLOW, 3)],
        }

        traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)

        default_combi = default_combis.get(self._complete_map_name.split("_")[0])

        cycle_elements = []
        for state, duration in default_combi:
            cycle_element = TrafficLightCycleElement(state, duration)
            cycle_elements.append(cycle_element)

        traffic_light.traffic_light_cycle.cycle_elements = cycle_elements
