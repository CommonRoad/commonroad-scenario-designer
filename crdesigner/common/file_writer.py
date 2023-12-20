import copy
from typing import Set, Union

from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.util import FileFormat
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario, Tag, Location

from crdesigner.verification_repairing.map_verification_repairing import verify_and_repair_scenario


class CRDesignerFileWriter(CommonRoadFileWriter):

    def __init__(self, scenario: Scenario, planning_problem_set: PlanningProblemSet, author: str = None,
                 affiliation: str = None, source: str = None, tags: Set[Tag] = None, location: Location = None,
                 decimal_precision: int = 4, file_format: FileFormat = FileFormat.XML):
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
        super().__init__(scenario, planning_problem_set, author, affiliation, source, tags, location,
                         decimal_precision, file_format)

    def write_to_file(self, filename: Union[str, None] = None,
                      overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
                      check_validity: bool = False, verify_repair_scenario=False):
        """
        Writes CommonRoad scenario and planning problems to file.
        If the boolean is set to True, the function verifies and repairs the scenario.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :param check_validity: Validity check or not
        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :return: Scenario and planning problems
        """
        if verify_repair_scenario is True:
            self._file_writer.scenario = verify_and_repair_scenario(self._file_writer.scenario)[0]

        super().write_to_file(filename, overwrite_existing_file, check_validity)

    def write_scenario_to_file(self, filename: Union[str, None] = None,
                               overwrite_existing_file: OverwriteExistingFile = OverwriteExistingFile.ASK_USER_INPUT,
                               verify_repair_scenario: bool = False):
        """
        Writes CommonRoad scenario to file.
        If the boolean is set to True, the function verifies and repairs the scenario.

        :param filename: Name of file
        :param overwrite_existing_file: Overwriting mode
        :param verify_repair_scenario: Boolean that indicates if the function will verify and repair the scenario.
        :return: Scenario
        """
        if verify_repair_scenario is True:
            self._file_writer.scenario = verify_and_repair_scenario(self._file_writer.scenario)[0]

        super().write_scenario_to_file(filename, overwrite_existing_file)

    def check_validity_of_commonroad_file(self, commonroad_str: Union[str, bytes],
                                          file_format: FileFormat = FileFormat.XML) -> bool:
        """
        Checks validity of CommonRoad scenario and planning problem stored in XML or protobuf format.

        :param commonroad_str: Commonroad instance stored as string
        :param file_format: Format of file
        :return: Valid or not
        """
        return super().check_validity_of_commonroad_file(commonroad_str, file_format)
