import copy
from typing import Set, Union

from commonroad.common.common_scenario import Location
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.util import FileFormat
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario, Tag

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


class CRDesignerFileWriter(CommonRoadFileWriter):
    def __init__(
        self,
        scenario: Scenario,
        planning_problem_set: PlanningProblemSet,
        author: str = None,
        affiliation: str = None,
        source: str = None,
        tags: Set[Tag] = None,
        location: Location = None,
        decimal_precision: int = 4,
        file_format: FileFormat = FileFormat.XML,
    ):
        """
        Initializes the CR Designer FileWriter for CommonRoad files.
        Standard commonroad-io FileWriter is used, with an addition that the writer optionally verifies and repairs
        the road network using the new map verification.

        :param scenario: Scenario
        :param planning_problem_set: Planning problems
        :param author: Name of author
        :param affiliation: Affiliation of author
        :param source: Source of dataset, e.g., database, handcrafted, etc.
        :param tags: Keywords describing the scenario
        :param decimal_precision: Number of decimal places used when writing float values
        :param file_format: Format of file
        :return:
        """
        super().__init__(
            scenario,
            planning_problem_set,
            author,
            affiliation,
            source,
            tags,
            location,
            decimal_precision,
            file_format,
        )
        # map verification parameters
        self._mapver_params = MapVerParams()

    @property
    def mapver_params(self) -> MapVerParams:
        """
        Get the map verification parameters of the file writer.

        :return: map verification parameter
        """
        return self._mapver_params

    @mapver_params.setter
    def mapver_params(self, mapver_params_value: MapVerParams):
        self._mapver_params = mapver_params_value

    def write_to_file(
        self,
        filename: Union[str, None] = None,
        overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
        check_validity: bool = False,
        verify_repair_scenario=False,
        target_projection: str = None,
    ):
        """
        Writes (old format) CommonRoad scenario and planning problems to file.
        If the boolean is set to True, the function verifies and repairs the scenario.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :param check_validity: Validity check or not
        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :param target_projection: Target projection that the user provides.
        :return: Scenario and planning problems
        """

        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            proj_string_from = (
                self._file_writer.scenario.lanelet_network.location.geo_transformation.geo_reference
            )
            # If no source projection is defined in the scenario location element, we should skip the projection
            if proj_string_from is not None:
                self._file_writer.scenario, self._file_writer.planning_problem_set = (
                    project_scenario_and_pps(
                        self._file_writer.scenario,
                        self._file_writer.planning_problem_set,
                        proj_string_from,
                        target_projection,
                    )
                )

        # check for verifying and repairing the scenario
        if verify_repair_scenario is True:
            self._file_writer.scenario = verify_and_repair_scenario(self._file_writer.scenario)[0]

        super().write_to_file(filename, overwrite_existing_file, check_validity)

    def write_map_to_file(
        self,
        filename: Union[str, None] = None,
        overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
        check_validity: bool = False,
        verify_repair_map: bool = False,
        target_projection: str = None,
    ):
        """
        Writes 2024 CommonRoad Map to the file.
        If the verify_repair_map boolean is set to True, the function verifies and repairs the map.
        If the target_projection string is given, and the source projection in the lanelet network location is defined,
        the function projects the lanelet network and env obstacles according to those parameters.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :param check_validity: Validity check or not
        :param verify_repair_map: Boolean that indicates if the function will verify and repair the map.
        :param target_projection: Target projection that the user provides.
        :return: Map (Lanelet Network)
        """
        # check for a projection
        # If target projection is not provided, no projection should be applied
        if target_projection is not None:
            # check for geo transformation and geo reference
            if getattr(
                self._file_writer.scenario.lanelet_network.location.geo_transformation,
                "geo_reference",
                None,
            ):
                proj_string_from = self._file_writer.scenario.lanelet_network.location.geo_transformation.geo_reference
                # If no source projection is defined in the lanelet network location, we should skip the projection
                if proj_string_from is not None:
                    # if both target & source projection are given, we project the lanelet network and env obstacles and
                    # update the scenario accordingly
                    projected_ll = project_lanelet_network(
                        copy.deepcopy(self._file_writer.scenario.lanelet_network),
                        proj_string_from,
                        target_projection,
                    )

                    self._file_writer.scenario.replace_lanelet_network(projected_ll)

                    self._file_writer.scenario.add_objects(
                        project_obstacles(
                            self._file_writer.scenario.environment_obstacle,
                            proj_string_from,
                            target_projection,
                        )
                    )

        # check for verifying and repairing the lanelet network
        if verify_repair_map is True:
            self._file_writer.scenario.replace_lanelet_network(
                verify_and_repair_map(self._file_writer.scenario.lanelet_network)[0]
            )

        super().write_map_to_file(filename, overwrite_existing_file, check_validity)

    def write_dynamic_to_file(
        self,
        filename: Union[str, None] = None,
        overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
    ):
        """
        Writes 2024 CommonRoad Dynamic to file.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :return: Dynamic
        """
        super().write_dynamic_to_file(filename, overwrite_existing_file)

    def write_scenario_to_file(
        self,
        filename: Union[str, None] = None,
        overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
    ):
        """
        Writes 2024 CommonRoad Scenario to file.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :return: Scenario
        """
        super().write_scenario_to_file(filename, overwrite_existing_file)

    def check_validity_of_commonroad_file(
        self, commonroad_str: Union[str, bytes], file_format: FileFormat = FileFormat.XML
    ) -> bool:
        """
        Checks validity of CommonRoad scenario and planning problem stored in XML or protobuf format.

        :param commonroad_str: Commonroad instance stored as string
        :param file_format: Format of file
        :return: Valid or not
        """
        return super().check_validity_of_commonroad_file(commonroad_str, file_format)
