from typing import List, Optional, Tuple

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.reader.dynamic_interface import DynamicInterface
from commonroad.common.reader.scenario_interface import ScenarioInterface
from commonroad.common.util import Path_T
from commonroad.planning.planning_problem import (
    CooperativePlanningProblem,
    PlanningProblemSet,
)
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.obstacle import EnvironmentObstacle
from commonroad.scenario.scenario import Scenario

from crdesigner.common.common_file_reader_writer import (
    project_lanelet_network,
    project_obstacles,
    project_scenario_and_pps,
)
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_map,
    verify_and_repair_scenario,
)


class CRDesignerFileReader(CommonRoadFileReader):
    def __init__(
        self,
        filename_2020a: Path_T = None,
        filename_map: Path_T = None,
        filename_scenario: Path_T = None,
        filename_dynamic: Path_T = None,
    ):
        """
        Initializes the CR Designer FileReader for CommonRoad files.
        Standard commonroad-io FileReader is used, with an addition that the reader optionally verifies and repairs
        the road network using the new map verification.

        :param filename_2020a: Path of the 2020a xml file
        :param filename_map: Path of the 2024 protobuf map file
        :param filename_scenario: Path of the 2024 protobuf scenario file
        :param filename_dynamic: Path of the 2024 protobuf dynamic file
        """
        super().__init__(filename_2020a, filename_map, filename_scenario, filename_dynamic)
        # map verification parameters
        self._mapver_params = MapVerParams()

    @property
    def filename_2020a(self) -> Optional[Path_T]:
        """
        Path of the 2020a xml file path.
        """
        return self._filename_2020a

    @filename_2020a.setter
    def filename_2020a(self, filename_2020a: Optional[Path_T]):
        self._filename_2020a = filename_2020a

    @property
    def filename_map(self) -> Optional[Path_T]:
        """
        Path of the 2024 map file.
        """
        return self._filename_map

    @filename_map.setter
    def filename_map(self, filename_map: Optional[Path_T]):
        self._filename_map = filename_map

    @property
    def filename_scenario(self) -> Optional[Path_T]:
        """
        Path of the 2024 scenario file.
        """
        return self._filename_scenario

    @filename_scenario.setter
    def filename_scenario(self, filename_scenario: Optional[Path_T]):
        self._filename_scenario = filename_scenario

    @property
    def mapver_params(self) -> MapVerParams:
        """
        Get the map verification parameters of the file reader.

        :return: map verification parameter
        """
        return self._mapver_params

    @property
    def filename_dynamic(self) -> Optional[Path_T]:
        """
        Path of the 2024 dynamic file.
        """
        return self._filename_dynamic

    @filename_dynamic.setter
    def filename_dynamic(self, filename_dynamic: Optional[Path_T]):
        self._filename_dynamic = filename_dynamic

    # 2020a reader
    def open(
        self,
        verify_repair_scenario: bool = False,
        target_projection: str = None,
        lanelet_assignment: bool = False,
    ) -> Tuple[Scenario, PlanningProblemSet]:
        """
        Opens and loads CommonRoad scenario and planning problem set from file.
        If the verify_repair_scenario boolean is set to True, the function verifies and repairs the scenario.
        If the target_projection string is given, and the source projection in the lanelet network location is defined,
        the function projects the scenario and the planning problem set according to those parameters.

        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :param target_projection: Target projection that the user provides.
        :param lanelet_assignment: Activates calculation of lanelets occupied by obstacles.
        :return: Scenario and planning problem set.
        """
        scenario, planning_problem_set = super().open(lanelet_assignment)

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference
            if getattr(scenario.lanelet_network.location.geo_transformation, "geo_reference", None):
                proj_string_from = (
                    scenario.lanelet_network.location.geo_transformation.geo_reference
                )
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target and source projection are given, we project the scenario and the pps
                    scenario, planning_problem_set = project_scenario_and_pps(
                        scenario, planning_problem_set, proj_string_from, target_projection
                    )

        # check for verifying and repairing the scenario
        if verify_repair_scenario is True:
            scenario = verify_and_repair_scenario(scenario)[0]

        return scenario, planning_problem_set

    # 2020a reader
    def open_lanelet_network(
        self, verify_repair_lanelet_network: bool = False, target_projection: str = None
    ) -> LaneletNetwork:
        """
        Opens and loads CommonRoad lanelet network from the file.
        If the verify_repair_scenario boolean is set to True, the function verifies and repairs the lanelet network.
        If the target_projection string is given, and the source projection in the lanelet network location is defined,
        the function projects the lanelet network according to those parameters.

        :param verify_repair_lanelet_network: Boolean that indicates if the function will verify and repair
        the lanelet network.
        :param target_projection: Target projection that the user provides.
        :return: Lanelet network.
        """
        lanelet_network = super().open_lanelet_network()

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference
            if getattr(lanelet_network.location.geo_transformation, "geo_reference", None):
                proj_string_from = lanelet_network.location.geo_transformation.geo_reference
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target and source projection are given, we project the lanelet network
                    lanelet_network = project_lanelet_network(
                        lanelet_network, proj_string_from, target_projection
                    )

        # check for verifying and repairing the lanelet network
        if verify_repair_lanelet_network is True:
            lanelet_network = verify_and_repair_map(lanelet_network)[0]

        return lanelet_network

    def open_map(
        self, verify_repair_lanelet_network: bool = False, target_projection: str = None
    ) -> Tuple[LaneletNetwork, List[EnvironmentObstacle]]:
        """
        Opens and loads CommonRoadMap from the file.
        If the verify_repair_lanelet_network boolean is True, the function verifies and repairs the lanelet network.
        If the target_projection is given, and the source projection in the lanelet network location is defined,
        the function projects the lanelet network and env obstacles according to those parameters.

        :param verify_repair_lanelet_network: Boolean that indicates if the function will verify and repair
        the lanelet network.
        :param target_projection: Target projection that the user provides.
        :return: Tuple consisted of Lanelet network and the list of Environment obstacles.
        """

        lanelet_network, env_obstacles = super().open_map()

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference
            if getattr(lanelet_network.location.geo_transformation, "geo_reference", None):
                proj_string_from = lanelet_network.location.geo_transformation.geo_reference
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target & source projection are given, we project the lanelet network and env obstacles
                    lanelet_network = project_lanelet_network(
                        lanelet_network, proj_string_from, target_projection
                    )
                    env_obstacles = project_obstacles(
                        env_obstacles, proj_string_from, target_projection
                    )

        # check for verifying and repairing the lanelet network
        if verify_repair_lanelet_network:
            lanelet_network = verify_and_repair_map(lanelet_network)[0]

        return lanelet_network, env_obstacles

    def open_map_dynamic(
        self, verify_repair_lanelet_network: bool = False, target_projection: str = None
    ) -> Scenario:
        """
        Opens and combines CommonRoadMap and CommonRoadDynamic files.
        The user has to provide both map and dynamic filenames in order to call this function.
        If the verify_repair_lanelet_network is set to True, the function verifies and repairs the lanelet network.
        If the target_projection is given, and the source projection in the lanelet network location is defined,
        the function projects the scenario according to those parameters.

        :param verify_repair_lanelet_network: Boolean that indicates if the function will verify and repair
        the lanelet network.
        :param target_projection: Target projection that the user provides.
        :return: Scenario.
        """
        scenario = super().open_map_dynamic()

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference:
            if getattr(scenario.lanelet_network.location.geo_transformation, "geo_reference", None):
                proj_string_from = (
                    scenario.lanelet_network.location.geo_transformation.geo_reference
                )
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target and source projection are given, we project the scenario
                    scenario, _ = project_scenario_and_pps(
                        scenario, PlanningProblemSet(), proj_string_from, target_projection
                    )

        # check for verifying and repairing the lanelet network
        if verify_repair_lanelet_network is True:
            scenario.replace_lanelet_network(verify_and_repair_map(scenario.lanelet_network)[0])

        return scenario

    def open_all(
        self, verify_repair_lanelet_network: bool = False, target_projection: str = None
    ) -> Tuple[Scenario, PlanningProblemSet, List[CooperativePlanningProblem]]:
        """
        Opens and combines CommonRoadMap, CommonRoadDynamic and CommonRoadScenario files.
        The user has to provide scenario, dynamic and map filenames in order to call this function.
        If the verify_repair_lanelet_network is set to True, the function verifies and repairs the lanelet network.
        If the target_projection is given, and the source projection in the lanelet network location is defined,
        the function projects the scenario and the planning problem set according to those parameters.

        :param verify_repair_lanelet_network: Boolean that indicates if the function will verify and repair
        the lanelet network.
        :param target_projection: Target projection that the user provides.
        :return: Tuple of a Scenario, PlanningProblemSet and a list of CooperativePlanningProblems
        """
        scenario, pps, cpp = super().open_all()

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference:
            if getattr(scenario.lanelet_network.location.geo_transformation, "geo_reference", None):
                proj_string_from = (
                    scenario.lanelet_network.location.geo_transformation.geo_reference
                )
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target and source projection are given, we project the scenario and the pps
                    scenario, pps = project_scenario_and_pps(
                        scenario, pps, proj_string_from, target_projection
                    )

        # check for verifying and repairing the lanelet network
        if verify_repair_lanelet_network is True:
            scenario.replace_lanelet_network(verify_and_repair_map(scenario.lanelet_network)[0])

        return scenario, pps, cpp

    def open_dynamic(self) -> DynamicInterface:
        """
        Opens and loads CommonRoadDynamic from the file.

        :return: DynamicInterface
        """
        return super().open_dynamic()

    def open_scenario(self) -> ScenarioInterface:
        """
        Opens and loads CommonRoadScenario from the file.

        :return: ScenarioInterface
        """
        return super().open_scenario()
