import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional, Union

from commonroad.scenario.scenario import Scenario
from lxml import etree

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.lanelet2_config import lanelet2_config
from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.common.file_reader import CRDesignerFileReader
from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.opendrive.cr2odr.converter import Converter
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.network import (
    Network,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.parser import (
    parse_opendrive,
)

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from crdesigner.map_conversion.sumo_map.sumo2cr import convert_net_to_cr

from crdesigner.map_conversion.osm2cr.converter_modules.converter import GraphScenario
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export import (
    convert_to_scenario,
)

Path_T = Union[str, Path]


def lanelet_to_commonroad(
    input_file: Path_T,
    general_conf: general_config = general_config,
    lanelet2_conf: lanelet2_config = lanelet2_config,
) -> Scenario:
    """
    Converts lanelet/lanelet2 file to CommonRoad

    :param input_file: Path to lanelet/lanelet2 file
    :param general_conf: General config parameters.
    :param lanelet2_conf: Lanelet2 config parameters.
    :return: CommonRoad scenario
    """
    parser = Lanelet2Parser(etree.parse(str(input_file)).getroot(), lanelet2_conf)
    lanelet2_content = parser.parse()

    lanelet2_converter = Lanelet2CRConverter(lanelet2_conf, general_conf)
    scenario = lanelet2_converter(lanelet2_content)

    return scenario


def commonroad_to_lanelet(
    input_file: Path_T, output_name: str, config: lanelet2_config = lanelet2_config
):
    """
    Converts CommonRoad map to lanelet format

    :param input_file: Path to CommonRoad map
    :param output_name: Name and path of lanelet file.
    :param config: Lanelet2 config parameters.
    """
    try:
        crdesigner_reader = CRDesignerFileReader(input_file)
        scenario, _ = crdesigner_reader.open()

    except etree.XMLSyntaxError as xml_error:
        logging.error(
            f"SyntaxError: {xml_error}.\n"
            f"There was an error during the loading of the selected CommonRoad file."
        )
        return

    l2osm = CR2LaneletConverter(config=config)
    osm = l2osm(scenario)
    with open(f"{output_name}", "wb") as file_out:
        file_out.write(
            etree.tostring(osm, xml_declaration=True, encoding="UTF-8", pretty_print=True)
        )


def opendrive_to_commonroad(
    input_file: Path_T,
    general_conf: general_config = general_config,
    odr_conf: open_drive_config = open_drive_config,
) -> Scenario:
    """
    Converts OpenDRIVE file to CommonRoad

    :param input_file: Path to OpenDRIVE file
    :param general_conf: General config parameters.
    :param odr_conf: OpenDRIVE config parameters.
    :return: CommonRoad scenario
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    opendrive = parse_opendrive(input_file)
    road_network = Network()
    road_network.load_opendrive(opendrive)
    return road_network.export_commonroad_scenario(general_conf, odr_conf)


def sumo_to_commonroad(input_file: Path_T) -> Scenario:
    """
    Converts SUMO net file to CommonRoad

    :param input_file: Path to SUMO net file
    :return: CommonRoad scenario
    """
    if SUMO_AVAILABLE:
        return convert_net_to_cr(str(input_file))
    else:
        logging.error("Cannot import SUMO. SUMO simulation cannot be offered.")


def commonroad_to_sumo(input_file: Path_T, output_file: Path_T):
    """
    Converts CommonRoad file to SUMO net file and stores it

    :param input_file: Path to CommonRoad file
    :param output_file: Path where files should be stored
    :return: CommonRoad scenario
    """
    try:
        crdesigner_reader = CRDesignerFileReader(input_file)
        scenario, _ = crdesigner_reader.open()
    except etree.XMLSyntaxError as xml_error:
        logging.error(
            f"SyntaxError: {xml_error}.\n"
            f"There was an error during the loading of the selected CommonRoad file."
        )
        return

    if SUMO_AVAILABLE:
        config = SumoConfig.from_scenario_name(str(uuid.uuid4()))
        path, file_name = os.path.split(output_file)
        config.scenario_name = file_name.partition(".")[0]
        converter = CR2SumoMapConverter(scenario, config)
        converter.create_sumo_files(path)
    else:
        logging.error("Cannot import SUMO. SUMO simulation cannot be offered.")


def osm_to_commonroad(input_file: Path_T) -> Scenario:
    """
    Converts OpenStreetMap file to CommonRoad scenario

    :param input_file: Path to OpenStreetMap file
    :return: CommonRoad scenario
    """
    osm_graph = GraphScenario(str(input_file)).graph
    return convert_to_scenario(osm_graph)


def osm_to_commonroad_using_sumo(input_file: Path_T) -> Optional[Scenario]:
    """
    Converts OpenStreetMap file to CommonRoad scenario using SUMO: SUMO offers the tool netconvert
    (https://sumo.dlr.de/docs/netconvert.html), which can be used to convert an OSM-file to OpenDrive (.xodr).
    This OpenDrive-file is then transformed to CommonRoad using the implementation here.
    Compared to the OSM-to-CommonRoad-conversion implemented here (see method :osm_to_commonroad), the
    road-interpolation is different. Furthermore, motorway services ("Raststätten") are currently not parsed
    when using :osm_to_commonroad.

    :param input_file: Path to OpenStreetMap file
    :return: CommonRoad scenario
    """
    if isinstance(input_file, str):
        input_file_pth = Path(input_file)
    scenario_name = str(input_file_pth.name)
    opendrive_file = str(input_file_pth.parent / f"{scenario_name}.xodr")
    # convert to OpenDRIVE file using netconvert
    try:
        subprocess.check_output(
            [
                "netconvert",
                "--osm-files",
                input_file,
                "--opendrive-output",
                opendrive_file,
                "--junctions.scurve-stretch",
                "1.0",
            ]
        )
    except Exception as e:
        logging.error(format(e))
        return None
    return opendrive_to_commonroad(Path(opendrive_file))


def opendrive_to_lanelet(
    input_file: Path_T,
    output_file: Path_T,
    odr_config: open_drive_config = open_drive_config,
    general_config=general_config,
    lanelet2_config: lanelet2_config = lanelet2_config,
):
    """
    Converts OpenDRIVE file to Lanelet2 file and stores it

    :param input_file: Path to the OpenDRIVE file
    :param output_file: Name and path of the Lanelet2 file
    :param odr_config: OpenDRIVE config parameters
    :param general_config: General config parameters
    :param lanelet2_config: Lanelet2 config parameters
    :return:
    """
    if isinstance(input_file, str):
        input_file = Path(input_file)
    if isinstance(output_file, str):
        output_file = Path(output_file)
    # convert a file from opendrive to commonroad
    scenario = opendrive_to_commonroad(input_file, general_conf=general_config, odr_conf=odr_config)

    # convert a file from commonroad to lanelet2
    l2osm = CR2LaneletConverter(config=lanelet2_config)
    osm = l2osm(scenario)
    with open(f"{output_file}", "wb") as file_out:
        file_out.write(
            etree.tostring(osm, xml_declaration=True, encoding="UTF-8", pretty_print=True)
        )


def commonroad_to_opendrive(input_file: Path, output_file: Path):
    """
    Converts CommonRoad file to OpenDRIVE file and stores it
    @param input_file: Path to CommonRoad file
    @param output_file: Path where OpenDRIVE file to be stored
    """
    converter = Converter(str(input_file))
    converter.convert(str(output_file))
