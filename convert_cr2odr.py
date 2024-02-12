import argparse
import logging
import traceback
import warnings
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.writer.file_writer_interface import OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.mp_renderer import MPRenderer

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from crdesigner.map_conversion.opendrive.cr2odr.converter import Converter
from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.map_verification_repairing import (
    verify_and_repair_map,
)
from crdesigner.verification_repairing.verification.formula_ids import LaneletFormulaID

warnings.filterwarnings("ignore")
date_strftime_format = "%d-%b-%y %H:%M:%S"
message_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(
    filename="exceptions.log", encoding="utf-8", level=logging.INFO, format=message_format, datefmt=date_strftime_format
)


def render_maps(network_id: str, scenario: Scenario, scenario_path: Path):
    """
    Creates figure for evaluating intersection conversion

    :param network_id: Map ID.
    :param scenario: CommonRoad scenario.
    :param scenario_path: Path where images should be stored.
    """
    rnd = MPRenderer()
    rnd.draw_params.lanelet_network.intersection.draw_intersections = True
    rnd.draw_params.lanelet_network.intersection.draw_crossings = False
    rnd.draw_params.lanelet_network.traffic_light.draw_traffic_lights = False
    rnd.draw_params.lanelet_network.traffic_sign.draw_traffic_signs = False
    rnd.draw_params.axis_visible = False

    # only incoming lanelets
    rnd.draw_params.lanelet_network.intersection.draw_outgoings = False
    rnd.draw_params.lanelet_network.intersection.draw_outgoing_group_lanelets = False
    scenario.lanelet_network.draw(rnd)
    rnd.render(filename=str(scenario_path / Path(f"{network_id}_incomings.svg")))

    # only traffic signs
    rnd.draw_params.lanelet_network.intersection.draw_incoming_lanelets = False
    # rnd.draw_params.lanelet_network.traffic_sign.draw_traffic_signs = True
    # scenario.lanelet_network.draw(rnd)
    # rnd.render(filename=scenario_path + "/" + network_id + "_signs")

    # only lanelet IDs
    # rnd.draw_params.lanelet_network.lanelet.show_label = True
    rnd.draw_params.lanelet_network.traffic_sign.draw_traffic_signs = False
    # scenario.lanelet_network.draw(rnd)
    # rnd.render(filename=scenario_path + "/" + network_id + "_lanelets")

    # only traffic lights
    rnd.draw_params.lanelet_network.lanelet.show_label = False
    # rnd.draw_params.lanelet_network.traffic_light.draw_traffic_lights = True
    # scenario.lanelet_network.draw(rnd)
    # rnd.render(filename=scenario_path + "/" + network_id + "_lights")

    # only outgoing lanelets
    rnd.draw_params.lanelet_network.intersection.draw_outgoing_group_lanelets = True
    rnd.draw_params.lanelet_network.traffic_light.draw_traffic_lights = False
    scenario.lanelet_network.draw(rnd)
    rnd.render(filename=str(scenario_path / Path(f"{network_id}_outgoing_groups.svg")))

    # only outgoing dir lanelets
    rnd.draw_params.lanelet_network.intersection.draw_outgoings = True
    rnd.draw_params.lanelet_network.intersection.draw_outgoing_group_lanelets = False
    scenario.lanelet_network.draw(rnd)
    rnd.render(filename=str(scenario_path / Path(f"{network_id}_outgoing_dir_lanelets.svg")))

    # all
    rnd.draw_params.lanelet_network.intersection.draw_incoming_lanelets = True
    rnd.draw_params.lanelet_network.intersection.draw_outgoing_group_lanelets = True
    scenario.lanelet_network.draw(rnd)
    rnd.render(filename=str(scenario_path / Path(f"{network_id}.svg")))

    # all with labels
    # rnd.draw_params.lanelet_network.intersection.show_label = True
    # scenario.lanelet_network.draw(rnd)
    # rnd.render(filename=scenario_path + "/" + network_id + "_labeled")


def map_conversion_scenario(file_path: Path) -> bool:
    """
    Evaluates whether map of scenario should be converted (only one same map will be converted).

    :param file_path:
    :return: Boolean indicating whether map should be converted.
    """
    file_name = file_path.name
    map_name = file_name.split("_")[0] + "_" + file_name.split("_")[1]
    if map_name in map_conversion_scenario.map_ids:
        return False
    else:
        map_conversion_scenario.map_ids.add(map_name)
        return True


map_conversion_scenario.map_ids = set()  # static variable of corresponding function to store maps
# which should be converted


def convert_scenarios(cr_scenarios_path: Path, odr_path: Path, num_threads: int = 1) -> None:
    """Converts 2020a maps to OpenDRIVE maps."""

    convert_single_scenario = ""
    duplicated_dirs = ["environment-model", "commonroad-monitor"]
    num_cores = num_threads if convert_single_scenario == "" else 1

    #  Path to the folder from which the script collects the old xml files
    scenarios_paths = list(Path.rglob(cr_scenarios_path, "*.xml"))

    scenarios_paths_reduced = list(
        filter(
            lambda sc_path: "cooperative" not in str(sc_path)
            and not any([dir_dupl in str(sc_path) for dir_dupl in duplicated_dirs])
            and convert_single_scenario in str(sc_path)
            or convert_single_scenario is None
            or convert_single_scenario == "",
            scenarios_paths,
        )
    )
    map_paths = list(filter(map_conversion_scenario, scenarios_paths_reduced))
    map_conversion_scenario.map_ids = set()
    scenarios_paths = list(
        filter(
            lambda sc_path: "cooperative" not in str(sc_path)
            and convert_single_scenario in str(sc_path)
            or convert_single_scenario is None
            or convert_single_scenario == "",
            scenarios_paths,
        )
    )
    map_paths += list(
        filter(lambda sc_path: any([dir_dupl in str(sc_path) for dir_dupl in duplicated_dirs]), scenarios_paths)
    )

    func = partial(convert_single_map, odr_path)
    with Pool(processes=num_cores) as pool:
        pool.map(func, scenarios_paths)


def convert_single_map(conversion_path_odr: Path, path_cr: Path):
    """
    Converts single CommonRoad map to new format.

    :param conversion_path_odr: Path where new scenario files without figures should be stored.
    :param path_cr: Path of old format scenario.
    """
    scenario, planning_problem_set = CommonRoadFileReader(path_cr).open()
    scenario_id = scenario.scenario_id
    network_id = str(scenario_id.country_id) + "_" + str(scenario_id.map_name) + "-" + str(scenario_id.map_id)

    try:
        formulas = [
            LaneletFormulaID.EXISTENCE_RIGHT_ADJ,
            LaneletFormulaID.EXISTENCE_LEFT_ADJ,
            LaneletFormulaID.EXISTENCE_PREDECESSOR,
            LaneletFormulaID.EXISTENCE_SUCCESSOR,
            LaneletFormulaID.NON_PREDECESSOR_AS_SUCCESSOR,
            LaneletFormulaID.NON_SUCCESSOR_AS_PREDECESSOR,
            LaneletFormulaID.POLYLINES_INTERSECTION,
            LaneletFormulaID.RIGHT_SELF_INTERSECTION,
            LaneletFormulaID.LEFT_SELF_INTERSECTION,
            LaneletFormulaID.POTENTIAL_SUCCESSOR,
            LaneletFormulaID.POTENTIAL_PREDECESSOR,
            LaneletFormulaID.POTENTIAL_RIGHT_MERGING_ADJ,
            LaneletFormulaID.POTENTIAL_LEFT_MERGING_ADJ,
            LaneletFormulaID.POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ,
            LaneletFormulaID.POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ,
            LaneletFormulaID.POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ,
            LaneletFormulaID.POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ,
            LaneletFormulaID.POTENTIAL_LEFT_FORKING_ADJ,
            LaneletFormulaID.POTENTIAL_RIGHT_FORKING_ADJ,
        ]
        config = MapVerParams()
        config.verification.formulas = formulas
        scenario.replace_lanelet_network(verify_and_repair_map(scenario.lanelet_network, config)[0])

        output_name = conversion_path_odr / f"{network_id}.odr"
        if not conversion_path_odr.exists():
            conversion_path_odr.mkdir(parents=True, exist_ok=True)
        converter = Converter(scenario)
        converter.convert(str(output_name))
        logging.info(f"Conversion of {path_cr} was successful.")

        scenario_new = opendrive_to_commonroad(output_name)
        for obs in scenario.obstacles:
            obs.obstacle_id = scenario_new.generate_object_id()
            scenario_new.add_objects(obs)
        scenario_new.scenario_id = scenario.scenario_id

    except Exception as e:
        logging.error(f"Conversion of {path_cr} was unsuccessful: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CommonRoad maps to OpenDRIVE.')
    parser.add_argument('--num_threads', type=int, help='Number of threads', default=1, required=False)
    parser.add_argument('--input_path', type=Path, help='Path to CommonRoad maps',
                        default=Path("/media/sebastian/TUM/06_code/scenarios/commonroad/scenarios_2020a"), required=False)
    parser.add_argument('--output_path', type=Path, help='Path where OpenDRIVE maps should be stored.',
                        default=Path("/home/sebastian/Downloads"), required=False)

    args = parser.parse_args()
    convert_scenarios(args.input_path, args.output_path, args.num_threads)
