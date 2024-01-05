import copy
from typing import Optional, Tuple

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.util import Path_T, FileFormat
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario
from pyproj import Transformer, CRS

from crdesigner.verification_repairing.map_verification_repairing import (verify_and_repair_scenario,
                                                                          verify_and_repair_map)


def project_complete_scenario(scenario: Scenario, proj_string_from: str, proj_string_to: str) -> Scenario:
    """
    Function that performs a projection onto the entire scenario.

    :param scenario: Scenario that needs to be projected.
    :param proj_string_from: Source projection.
    :param proj_string_to: Target projection.
    :return: Projected scenario.
    """
    crs_from = CRS(proj_string_from)
    crs_to = CRS(proj_string_to)
    # why do we convert proj to crs and then use Transformer.from_proj? Shouldn't we use Transformer.from_crs in
    # that case - line 177 in cr2lanelet?
    transformer = Transformer.from_proj(crs_from, crs_to)

    # create a deep copy of the scenario
    scenario_copy = copy.deepcopy(scenario)

    # transform lanelet vertex coordinates
    for lanelet in scenario_copy.lanelet_network.lanelets:
        for left_vertex in lanelet.left_vertices:
            left_vertex[0], left_vertex[1] = transformer.transform(left_vertex[0], left_vertex[1])
        for right_vertex in lanelet.right_vertices:
            right_vertex[0], right_vertex[1] = transformer.transform(right_vertex[0], right_vertex[1])
        for center_vertex in lanelet.center_vertices:
            center_vertex[0], center_vertex[1] = transformer.transform(center_vertex[0], center_vertex[1])

    # transform traffic light coordinates
    for tl in scenario_copy.lanelet_network.traffic_lights:
        tl.position[0], tl.position[1] = transformer.transform(tl.position[0], tl.position[1])
        # z coordinate stays the same?

    # transform traffic sign coordinates
    for ts in scenario_copy.lanelet_network.traffic_lights:
        ts.position[0], ts.position[1] = transformer.transform(ts.position[0], ts.position[1])

    return scenario_copy


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

    def open(self, verify_repair_scenario: bool = False, target_projection: str = None,
             lanelet_assignment: bool = False) -> Tuple[Scenario, PlanningProblemSet]:
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
        # If target projection is provided, no projection should be applied
        if target_projection is not None:
            proj_string_from = scenario.location.geo_transformation.geo_reference
            # If no source projection is defined in the scenario location element, we should skip the projection
            if proj_string_from is not None:
                scenario = project_complete_scenario(scenario, proj_string_from, target_projection)

        # check for verifying and repairing the scenario
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
