from abc import ABC

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID


class ElementRepairing(ABC):
    """
    The class includes all repairing methods for each supported formula.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: ScenarioID.
        """

        self._complete_map_name = (
            str(scenario_id.country_id)
            + "_"
            + str(scenario_id.map_name)
            + "-"
            + str(scenario_id.map_id)
        )
        self._network = network
