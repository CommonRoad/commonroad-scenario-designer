import copy
import os.path
import time
from copy import deepcopy
from os import listdir
from os.path import isfile, join, isdir
from typing import List, Tuple, Optional
import logging
from glob import glob

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import OverwriteExistingFile, CommonRoadFileWriter
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID, Scenario

from crdesigner.crmapver.verification.verification_result import VerificationResult, initial_map_verification, \
    update_map_verification
from crdesigner.crmapver.verification.formula_ids import extract_formula_ids
from crdesigner.crmapver.verification.groups_handler import GroupsHandler
from crdesigner.crmapver.config import MapVerParams
from crdesigner.crmapver.repairing.map_repairer import MapRepairer
from crdesigner.crmapver.verification.map_verifier import MapVerifier
from crdesigner.crmapver.verification.sub_map import SubMap


def collect_scenario_paths(scenario_dir: str, map_names_selected: Optional[List[str]],
                           excluded_maps: Optional[List[str]]) -> List[str]:
    """
    Collects scenarios from a directory and subdirectory and returns only paths to selected maps.

    :param scenario_dir: Scenario directory.
    :param map_names_selected: Selected map names.
    :param excluded_maps: Excluded map names.
    :return: List of paths to maps.
    """
    relevant_scenario_paths = []
    map_names = set()
    scenario_names_complete = [y for x in os.walk(scenario_dir) for y in glob(os.path.join(x[0], '*.pb'))]
    for scenario_path in scenario_names_complete:
        name_split = scenario_path.split("/")[-1].split("_", 2)
        map_name = name_split[0] + "_" + name_split[1].split(".")[0]
        if map_name in map_names or map_name[0] == "C" or map_name in excluded_maps or (
                map_names_selected is not None and map_name not in map_names_selected):
            continue
        else:
            map_names.add(map_name)
            relevant_scenario_paths.append(scenario_path)
    return relevant_scenario_paths


def verify_and_repair_map(network: LaneletNetwork, config: MapVerParams = MapVerParams(),
                          scenario_id: ScenarioID = ScenarioID()) -> Tuple[LaneletNetwork, VerificationResult]:
    """
    Verifies and repairs a CommonRoad map. In the verification process the desired formulas are checked to be
    satisfiable. If a formula cannot be satisfied, an invalid state is inferred. These formulas can be executed
    in parallel. After verification the repairing process starts and removes the invalid states. Subsequent
    invalid states can occur and therefore a further iteration is needed. As a measure the maps in the
    repository commonroad-scenarios require maximum 2 to 4 iterations. If the number of iterations is equal to
    zero, then the map is only verified and not repaired.

    Whether a map is valid or was successfully repaired can be summarized in a file. The mentioned iterations and the
    respective occurred invalid states are listed. To make it more apparent, the invalid states can be also
    visualized with symbols for an invalid map.

    If a large map with more than 200 lanelets should be verified and repaired, the supported partitioning
    is strongly recommended. The map is divided into blocks and for each block the verification is applied separately.
    The verification of the blocks can be parallelized and visualized.

    The HOL solver is used for validating the map.

    Statistics are maintained for the verification as well as repairing process and are returned as result.

    :param network: LaneletNetwork.
    :param config: Config parameters.
    :param scenario_id: ScenarioID used for complete map name.
    :return: Verified as well as repaired scenario and verification result.
    """
    assert network is not None, 'LaneletNetwork is not provided!'

    if not config.evaluation.overwrite_scenario:
        network = deepcopy(network)

    if config.verification.formulas is None or config.verification.formulas == []:
        config.verification.formulas = extract_formula_ids()

    complete_map_name = str(scenario_id.country_id)+'_'+str(scenario_id.map_name)+'-'+str(scenario_id.map_id)
    verification_result = VerificationResult()
    map_verification = initial_map_verification(verification_result, str(complete_map_name),
                                                config)

    verification_time, repairing_time = 0.0, 0.0
    logging.info(f'Validating map {complete_map_name} with hol solver')

    groups_handler = GroupsHandler()

    initial_invalid_states = {}
    final_errors = set()
    repairing_possible = True

    org_config = copy.deepcopy(config)

    group_i = 0
    while groups_handler.is_next_group():
        group = groups_handler.next_group()

        final_formulas = list(set(org_config.verification.formulas).intersection(set(group)))
        if not final_formulas:
            continue
        else:
            config.verification.formulas = final_formulas

        start = time.time()
        map_verifier = MapVerifier(network, config)
        invalid_states = map_verifier.verify()
        end = time.time()
        verification_time += end - start

        for formula_id, locations in invalid_states.items():
            pre_locations = initial_invalid_states[formula_id] if formula_id in initial_invalid_states.keys() else []
            initial_invalid_states[formula_id] = pre_locations + locations

        for formula_id, locations in invalid_states.items():
            for location in locations:
                iter_i = 0
                errors = {(formula_id, location)}
                while errors and iter_i < config.verification.max_iterations:
                    f_id, loc = errors.pop()

                    element_id = loc[0]

                    sub_map = SubMap(network)
                    sub_map.extract_from_element(element_id)
                    sub_network = sub_map.create_subnetwork()

                    start = time.time()
                    map_repairer = MapRepairer(sub_network)
                    map_repairer.repair_map({f_id: [loc]})
                    end = time.time()
                    repairing_time += end - start

                    start = time.time()
                    map_verifier = MapVerifier(sub_network, config)
                    invalid_states = map_verifier.verify()
                    end = time.time()
                    verification_time += end - start

                    for f_id, locs in invalid_states.items():
                        for loc in locs:
                            errors.add((f_id, loc))

                    iter_i += 1
                else:
                    if errors and iter_i >= config.verification.max_iterations:
                        repairing_possible = False

                final_errors = final_errors.union(errors)

        group_i += 1

    invalid_states = {}
    for formula_id, location in final_errors:
        if formula_id in invalid_states.keys():
            invalid_states[formula_id].append(location)
        else:
            invalid_states[formula_id] = [location]

    update_map_verification(map_verification, verification_time, repairing_time, initial_invalid_states)

    logging.info(f'Validating map {complete_map_name} finished with hol solver')
    if not repairing_possible:
        logging.error(f"Repairing was not successful with map {complete_map_name}.")
    return network, verification_result


def verify_and_repair_maps(scenarios: List[Scenario], config: MapVerParams) \
        -> Tuple[List[LaneletNetwork], VerificationResult]:
    """
    List of scenarios are verified and repaired successively.

    Statistics are maintained for the verification as well as repairing process and are returned as result.

    :param scenarios: List of scenarios
    :param config: Configuration parameters.
    :return: List of verified as well as repaired scenarios and verification result.
    """
    assert scenarios is not None and len(scenarios) > 0, 'Scenarios are not provided!'

    verification_result = VerificationResult()

    repaired_networks = []
    for scenario in scenarios:
        repaired_network, scenario_verification_result = \
            verify_and_repair_map(scenario.lanelet_network, config, scenario.scenario_id)
        repaired_networks.append(repaired_network)
        verification_result.map_verifications += scenario_verification_result.map_verifications

    return repaired_networks, verification_result


def verify_and_repair_dir_maps(scenarios_dir_path: str, config: MapVerParams = MapVerParams()) \
        -> Tuple[List[LaneletNetwork], VerificationResult]:
    """
    List of scenarios in directory and included subdirectories are verified and repaired successively.
    The loaded scenarios can be overwritten or a new scenario can be stored with file ending '-repaired.xml'.

    Statistics are maintained for the verification as well as repairing process and are returned as result.

    :param scenarios_dir_path: Path to scenarios in directory.
    :param config: Configuration parameters.
    :return: List of verified as well as repaired scenarios and verification result.
    """
    assert os.path.exists(scenarios_dir_path), 'The path to configuration file is not existent!'

    file_names = []
    dir_names = []
    for name in listdir(scenarios_dir_path):
        if isfile(join(scenarios_dir_path, name)) and (name.endswith('.xml') or name.endswith('.pb')):
            file_names.append(name)
        elif isdir(join(scenarios_dir_path, name)):
            dir_names.append(name)

    scenarios = []
    for name in file_names:
        scenario, pp = CommonRoadFileReader(join(scenarios_dir_path, name)).open()
        scenarios.append(scenario)

    repaired_networks, verification_result = \
        verify_and_repair_maps(scenarios, config)

    for repaired_network, name in zip(repaired_networks, file_names):
        for scenario in scenarios:
            if scenario.lanelet_network == repaired_network:
                pp = PlanningProblemSet()
                writer = CommonRoadFileWriter(scenario=scenario, planning_problem_set=pp)
                file_path = join(scenarios_dir_path, name)
                if not config.evaluation.overwrite_scenario:
                    file_path = file_path.replace('.xml', '') + '-repaired.xml'
                writer.write_to_file(file_path, OverwriteExistingFile.ALWAYS)

    for name in dir_names:
        sub_dir_path = join(scenarios_dir_path, name)
        verify_and_repair_dir_maps(sub_dir_path, config)

    return repaired_networks, verification_result
