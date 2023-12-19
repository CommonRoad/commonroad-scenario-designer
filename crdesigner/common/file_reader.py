from typing import Optional, Tuple

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Path_T, FileFormat
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario

from crdesigner.verification_repairing.map_verification_repairing import (verify_and_repair_scenario,
                                                                          verify_and_repair_map)


class CRDesignerFileReader(CommonRoadFileReader):

    def __init__(self, filename: Path_T, file_format: Optional[FileFormat] = None):
        """
        Initializes the CR Designer FileReader for CommonRoad files.
        Standard commonroad-io FileReader is used, with an addition that the reader optionally verifies and repairs
        the road network using the new map verification.

        :param filename: Name of the file
        :param file_format: Format of the file. If None, inferred from file suffix.
        :return:
        """
        super().__init__(filename, file_format)

    def open(self, verify_repair_scenario: bool = False, lanelet_assignment: bool = False) -> Tuple[Scenario, PlanningProblemSet]:
        """
        Opens and loads CommonRoad scenario and planning problem set from file.
        If the boolean is set to True, the function verifies and repairs the scenario.

        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :param lanelet_assignment: Activates calculation of lanelets occupied by obstacles.
        :return: Scenario and planning problem set.
        """
        scenario, planning_problem_set = super().open(lanelet_assignment)
        if verify_repair_scenario is True:
            scenario = verify_and_repair_scenario(scenario)[0]
        return scenario, planning_problem_set

    def open_lanelet_network(self, verify_repair_lanelet_network: bool = False) -> LaneletNetwork:
        """
        Opens and loads CommonRoad lanelet network from the file.
        If the boolean is set to True, the function verifies and repairs the lanelet network.

        :param verify_repair_lanelet_network: Boolean that indicates if the function will verify and repair
        the lanelet network.
        :return: Lanelet network.
        """
        lanelet_network = super().open_lanelet_network()
        if verify_repair_lanelet_network is True:
            lanelet_network = verify_and_repair_map(lanelet_network)[0]
        return lanelet_network
