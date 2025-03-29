from commonroad.scenario.lanelet import LaneletNetwork

from crdesigner.verification_repairing.repairing.intersection_repairing import (
    IntersectionRepairing,
)
from crdesigner.verification_repairing.repairing.lanelet_repairing import (
    LaneletRepairing,
)
from crdesigner.verification_repairing.repairing.traffic_light_repairing import (
    TrafficLightRepairing,
)
from crdesigner.verification_repairing.repairing.traffic_sign_repairing import (
    TrafficSignRepairing,
)
from crdesigner.verification_repairing.verification.satisfaction import InvalidStates


class MapRepairer:
    """
    The class repairs the invalid states. For each type of invalid state the corresponding repairing method
    is executed.
    """

    def __init__(self, network: LaneletNetwork):
        """
        Constructor.

        :param network: Lanelet network.
        """
        self._network = network
        self._repairings = []
        for repairing in [
            LaneletRepairing,
            TrafficSignRepairing,
            TrafficLightRepairing,
            IntersectionRepairing,
        ]:
            self._repairings.append(repairing(network))

    def repair_map(self, invalid_states: InvalidStates):
        """
        Repairs the invalid states in a map in a determined order.

        :param invalid_states: Invalid states.
        """
        for repairing in self._repairings:
            func_names = [func for func in dir(repairing) if callable(getattr(repairing, func))]

            for invalid_state_id, locations in invalid_states.items():
                repairing_name = "repair_" + str(invalid_state_id.value)
                if repairing_name in func_names:
                    for location in locations:
                        func = getattr(repairing, repairing_name)
                        func(location)
