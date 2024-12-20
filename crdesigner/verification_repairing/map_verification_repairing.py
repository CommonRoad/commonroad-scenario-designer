import copy
import logging
import time
from copy import deepcopy
from os.path import join
from pathlib import Path
from typing import List, Optional, Tuple

from commonroad.common.file_reader import CommonRoadFileReader, FileFormat
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import Scenario, ScenarioID

from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.drawing.invalid_states.invalid_states_drawer import (
    InvalidStatesDrawer,
)
from crdesigner.verification_repairing.repairing.map_repairer import MapRepairer
from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    GeneralFormulaID,
    extract_formula_ids,
)
from crdesigner.verification_repairing.verification.groups_handler import GroupsHandler
from crdesigner.verification_repairing.verification.map_verifier import MapVerifier
from crdesigner.verification_repairing.verification.sub_map import SubMap
from crdesigner.verification_repairing.verification.verification_result import (
    VerificationResult,
    initial_map_verification,
    update_map_verification,
)


def collect_scenario_paths(
    scenario_dir: Path, subdir: bool = True, file_format: Optional[FileFormat] = None
) -> List[Path]:
    """
    Collects scenarios from a directory and subdirectory and returns only paths to selected maps.

    :param scenario_dir: Scenario directory.
    :param subdir: Boolean indicating whether subdirectories should be considered.
    :param file_format: Selection of CommonRoad file format.
    :return: List of paths to maps.
    """
    scenario_names_complete = []
    if not subdir:
        if file_format is not None:
            scenario_names_complete += list(Path(scenario_dir).glob(f"*{file_format.value}"))
        else:
            scenario_names_complete += list(Path(scenario_dir).glob(f"*{FileFormat.XML.value}"))
            scenario_names_complete += list(
                Path(scenario_dir).glob(f"*{FileFormat.PROTOBUF.value}")
            )
    else:
        if file_format is not None:
            scenario_names_complete += list(Path(scenario_dir).rglob(f"*{file_format.value}"))
        else:
            scenario_names_complete += list(Path(scenario_dir).rglob(f"*{FileFormat.XML.value}"))
            scenario_names_complete += list(
                Path(scenario_dir).rglob(f"*{FileFormat.PROTOBUF.value}")
            )

    return scenario_names_complete


def verify_and_repair_scenario(
    scenario: Scenario, config: MapVerParams = MapVerParams()
) -> Tuple[Scenario, bool]:
    """
    Verifies and repairs single scenario.

    :param scenario: CommonRoad scenario.
    :param config: Config parameters.
    :return: Boolean indicating whether there were errors and updated scenario
    """
    network, result = verify_and_repair_map(
        copy.deepcopy(scenario.lanelet_network), config, scenario.scenario_id
    )
    new_scenario = copy.deepcopy(scenario)
    new_scenario.replace_lanelet_network(network)
    return new_scenario, len(
        result.map_verifications[0].map_verification_result.invalid_states
    ) == 0


def verify_and_repair_map(
    network: LaneletNetwork,
    config: MapVerParams = MapVerParams(),
    scenario_id: ScenarioID = ScenarioID(),
) -> Tuple[LaneletNetwork, VerificationResult]:
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
    assert network is not None, "LaneletNetwork is not provided!"

    config = deepcopy(config)
    if not config.evaluation.overwrite_scenario:
        network = deepcopy(network)

    if config.verification.formulas is None or config.verification.formulas == []:
        config.verification.formulas = extract_formula_ids()

    drawer = (
        InvalidStatesDrawer(network, scenario_id)
        if config.evaluation.invalid_states_draw_dir
        else None
    )

    complete_map_name = (
        str(scenario_id.country_id)
        + "_"
        + str(scenario_id.map_name)
        + "-"
        + str(scenario_id.map_id)
    )
    verification_result = VerificationResult()
    map_verification = initial_map_verification(verification_result, str(complete_map_name), config)

    verification_time, repairing_time = 0.0, 0.0
    logging.info(f"Validating map {complete_map_name}.")

    groups_handler = GroupsHandler()

    initial_invalid_states = {}
    final_errors = set()

    map_repairer = MapRepairer(network)

    org_config = copy.deepcopy(config)

    group_i = 0
    while groups_handler.is_next_group():
        group = groups_handler.next_group()
        logging.debug(f"Verifying group number {group_i}")
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
            pre_locations = (
                initial_invalid_states[formula_id]
                if formula_id in initial_invalid_states.keys()
                else []
            )
            initial_invalid_states[formula_id] = pre_locations + locations

        if drawer is not None:
            drawer.save_invalid_states_drawing(
                invalid_states,
                config.evaluation.invalid_states_draw_dir,
                file_name=f"group_{group_i}_{complete_map_name}",
                file_format=config.evaluation.file_format,
            )

        f_id: FormulaID = GeneralFormulaID.UNIQUE_ID
        loc: Tuple[int, int] = (0, 0)
        for formula_id, locations in invalid_states.items():
            for location in locations:
                iter_i = 0
                errors = {(formula_id, location)}
                while errors and iter_i < config.verification.max_iterations:
                    if iter_i > 0:
                        logging.error(
                            f"Repairing was not successful at first attempt with map {complete_map_name} "
                            f"using specification {f_id} and error {loc}."
                        )
                    f_id, loc = errors.pop()
                    element_id = loc[0]

                    start = time.time()
                    map_repairer.repair_map({f_id: [loc]})
                    end = time.time()
                    repairing_time += end - start

                    sub_map = SubMap(network)
                    sub_map.extract_from_element(element_id)
                    sub_network = sub_map.create_subnetwork()
                    start = time.time()
                    config_tmp = copy.deepcopy(config)
                    config_tmp.verification.formulas = [f_id]
                    map_verifier = MapVerifier(sub_network, config_tmp)
                    invalid_states_tmp = map_verifier.verify()
                    end = time.time()
                    verification_time += end - start

                    if drawer is not None:
                        drawer.save_invalid_states_drawing(
                            invalid_states,
                            config.evaluation.invalid_states_draw_dir,
                            file_name=f"group_{group_i}_iteration_{iter_i}_" f"{complete_map_name}",
                            file_format=config.evaluation.file_format,
                        )

                    if invalid_states_tmp.get(f_id) is not None and loc in invalid_states_tmp.get(
                        f_id
                    ):
                        errors.add((f_id, loc))

                    iter_i += 1
                else:
                    if errors and iter_i >= config.verification.max_iterations:
                        raise RuntimeError(
                            f"Repairing was not successful with map {complete_map_name} with "
                            f"specification {f_id} and error {loc}."
                        )

                final_errors = final_errors.union(errors)

        group_i += 1

    invalid_states = {}
    for formula_id, location in final_errors:
        if formula_id in invalid_states.keys():
            invalid_states[formula_id].append(location)
        else:
            invalid_states[formula_id] = [location]

    update_map_verification(
        map_verification, verification_time, repairing_time, initial_invalid_states
    )

    if drawer is not None:
        drawer.save_invalid_states_drawing(
            initial_invalid_states,
            config.evaluation.invalid_states_draw_dir,
            file_name=f"initial_result_{complete_map_name}",
            file_format=config.evaluation.file_format,
        )
        drawer.save_invalid_states_drawing(
            invalid_states,
            config.evaluation.invalid_states_draw_dir,
            file_name=f"final_result_{complete_map_name}",
            file_format=config.evaluation.file_format,
        )

    logging.info(f"Validating map {complete_map_name} finished.")

    return network, verification_result


def verify_and_repair_maps(
    scenarios: List[Scenario], config: MapVerParams
) -> Tuple[List[LaneletNetwork], VerificationResult]:
    """
    List of scenarios are verified and repaired successively.

    Statistics are maintained for the verification as well as repairing process and are returned as result.

    :param scenarios: List of scenarios
    :param config: Configuration parameters.
    :return: List of verified as well as repaired scenarios and verification result.
    """
    assert scenarios is not None and len(scenarios) > 0, "Scenarios are not provided!"

    verification_result = VerificationResult()

    repaired_networks = []
    for scenario in scenarios:
        repaired_network, scenario_verification_result = verify_and_repair_map(
            scenario.lanelet_network, config, scenario.scenario_id
        )
        repaired_networks.append(repaired_network)
        verification_result.map_verifications += scenario_verification_result.map_verifications

    return repaired_networks, verification_result


def verify_and_repair_dir_maps(
    scenarios_dir_path: Path, config: MapVerParams = MapVerParams()
) -> Tuple[List[LaneletNetwork], VerificationResult]:
    """
    List of scenarios in directory and included subdirectories are verified and repaired successively.
    The loaded scenarios can be overwritten or a new scenario can be stored with file ending '-repaired.xml'.

    Statistics are maintained for the verification as well as repairing process and are returned as result.

    :param scenarios_dir_path: Path to scenarios in directory.
    :param config: Configuration parameters.
    :return: List of verified as well as repaired scenarios and verification result.
    """
    assert Path.exists(scenarios_dir_path), "The path to configuration file is not existent!"

    file_paths = collect_scenario_paths(scenarios_dir_path)
    scenarios_pp = [
        CommonRoadFileReader(join(scenarios_dir_path, name)).open() for name in file_paths
    ]

    repaired_networks, verification_result = verify_and_repair_maps(
        list(zip(*scenarios_pp))[0], config
    )

    for repaired_network, file_path in zip(repaired_networks, file_paths):
        for scenario, pp in scenarios_pp:
            if (
                repaired_network.information == scenario.lanelet_network.information
                and scenario.lanelet_network != repaired_network
            ):
                writer = CommonRoadFileWriter(scenario=scenario, planning_problem_set=pp)
                if not config.evaluation.overwrite_scenario:
                    file_path = str(file_path).replace(".xml", "") + "-repaired.xml"
                writer.write_to_file(file_path, OverwriteExistingFile.ALWAYS)
                break

    return repaired_networks, verification_result
