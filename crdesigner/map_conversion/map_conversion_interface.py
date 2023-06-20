import subprocess
from pathlib import Path
from typing import Optional
from lxml import etree
import uuid
import os

from commonroad.scenario.scenario import Scenario
from commonroad.common.file_reader import CommonRoadFileReader

from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network

from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import (
    SUMO_AVAILABLE,
)

if SUMO_AVAILABLE:
    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
    from crdesigner.map_conversion.sumo_map.sumo2cr import convert_net_to_cr

from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export import (
    convert_to_scenario,
)
from crdesigner.map_conversion.osm2cr.converter_modules.converter import GraphScenario
from crdesigner.config.config import Lanelet2ConversionParams, OpenDRIVEConversionParams, GeneralParams


def lanelet_to_commonroad(
        input_file: str,
        general_config: GeneralParams = GeneralParams(),
        lanelet2_config: Lanelet2ConversionParams = Lanelet2ConversionParams()
) -> Scenario:
    """
    Converts lanelet/lanelet2 file to CommonRoad

    :param input_file: Path to lanelet/lanelet2 file
    :param general_config: General config parameters.
    :param lanelet2_config: Lanelet2 config parameters.
    :return: CommonRoad scenario
    """
    parser = Lanelet2Parser(etree.parse(input_file).getroot())
    lanelet2_content = parser.parse()

    lanelet2_converter = Lanelet2CRConverter(lanelet2_config=lanelet2_config, cr_config=general_config)
    scenario = lanelet2_converter(lanelet2_content)

    return scenario


def commonroad_to_lanelet(input_file: str, output_name: str, 
                          config: Lanelet2ConversionParams = Lanelet2ConversionParams()):
    """
    Converts CommonRoad map to lanelet format

    :param input_file: Path to CommonRoad map
    :param output_name: Name and path of lanelet file.
    :param config: Lanelet2 config parameters.
    """
    try:
        commonroad_reader = CommonRoadFileReader(input_file)
        scenario, _ = commonroad_reader.open()

    except etree.XMLSyntaxError as xml_error:
        print(f"SyntaxError: {xml_error}")
        print(
            "There was an error during the loading of the selected CommonRoad file.\n"
        )
        return

    l2osm = CR2LaneletConverter(config)
    osm = l2osm(scenario)
    with open(f"{output_name}", "wb") as file_out:
        file_out.write(
            etree.tostring(
                osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
            )
        )


def opendrive_to_commonroad(input_file: str,
                            general_config: GeneralParams = GeneralParams(),
                            odr_config: OpenDRIVEConversionParams = OpenDRIVEConversionParams()) -> Scenario:
    """
    Converts OpenDRIVE file to CommonRoad

    :param input_file: Path to OpenDRIVE file
    :param general_config: General config parameters.
    :param odr_config: OpenDRIVE config parameters.
    :return: CommonRoad scenario
    """
    opendrive = parse_opendrive(input_file)
    road_network = Network(odr_config)
    road_network.load_opendrive(opendrive)
    for index in range(len(road_network._traffic_lights)):
        road_network._traffic_lights[index]._traffic_light_id = \
            abs(road_network._traffic_lights[index].traffic_light_id)
    return road_network.export_commonroad_scenario(general_config, odr_config)


def sumo_to_commonroad(input_file: str) -> Scenario:
    """
    Converts SUMO net file to CommonRoad

    :param input_file: Path to SUMO net file
    :return: CommonRoad scenario
    """
    return convert_net_to_cr(input_file)


def commonroad_to_sumo(input_file: str, output_file: str):
    """
    Converts CommonRoad file to SUMO net file and stores it

    :param input_file: Path to CommonRoad file
    :param output_file: Path where files should be stored
    :return: CommonRoad scenario
    """
    try:
        commonroad_reader = CommonRoadFileReader(input_file)
        scenario, _ = commonroad_reader.open()
    except etree.XMLSyntaxError as xml_error:
        print(f"SyntaxError: {xml_error}")
        print(
            "There was an error during the loading of the selected CommonRoad file.\n"
        )
        return

    if SUMO_AVAILABLE:
        config = SumoConfig.from_scenario_name(str(uuid.uuid4()))
        path, file_name = os.path.split(output_file)
        config.scenario_name = file_name.partition(".")[0]
        converter = CR2SumoMapConverter(scenario, config)
        converter.create_sumo_files(path)


def osm_to_commonroad(input_file: str) -> Scenario:
    """
    Converts OpenStreetMap file to CommonRoad scenario

    :param input_file: Path to OpenStreetMap file
    :return: CommonRoad scenario
    """
    osm_graph = GraphScenario(input_file).graph
    return convert_to_scenario(osm_graph)


def osm_to_commonroad_using_sumo(input_file: str) -> Optional[Scenario]:
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
        print("__Warning__: {}.".format(e))
        return None
    return opendrive_to_commonroad(opendrive_file)
