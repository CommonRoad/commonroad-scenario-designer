from typing import Optional, Tuple

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import FileFormat, Path_T
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario

from crdesigner.common.common_file_reader_writer import project_scenario_and_pps
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_map,
    verify_and_repair_scenario,
)


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
        # map verification parameters
        self._mapver_params = MapVerParams()

    @property
    def mapver_params(self) -> MapVerParams:
        """
        Get the map verification parameters of the file reader.

        :return: map verification parameter
        """
        return self._mapver_params

    @mapver_params.setter
    def mapver_params(self, mapver_params_value: MapVerParams):
        self._mapver_params = mapver_params_value

    def open(
        self,
        verify_repair_scenario: bool = False,
        target_projection: str = None,
        lanelet_assignment: bool = False,
    ) -> Tuple[Scenario, PlanningProblemSet]:
        """
        Opens and loads CommonRoad scenario and planning problem set from file.
        If the boolean is set to True, the function verifies and repairs the scenario.

        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :param target_projection: Target projection that the user provides.
        :param lanelet_assignment: Activates calculation of lanelets occupied by obstacles.
        :return: Scenario and planning problem set.
        """
        scenario, planning_problem_set = super().open(lanelet_assignment)

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            proj_string_from = scenario.location.geo_transformation.geo_reference
            # If no source projection is defined in the scenario location element, we should skip the projection
            if proj_string_from is not None:
                scenario, planning_problem_set = project_scenario_and_pps(
                    scenario, planning_problem_set, proj_string_from, target_projection
                )

        # check for verifying and repairing the scenario
        if verify_repair_scenario is True:
            scenario = verify_and_repair_scenario(scenario, config=self.mapver_params)[0]

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
            lanelet_network = verify_and_repair_map(lanelet_network, config=self.mapver_params)[0]
        return lanelet_network
