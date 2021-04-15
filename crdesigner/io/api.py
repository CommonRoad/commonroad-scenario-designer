from lxml import etree

from commonroad.scenario.scenario import Scenario
from commonroad.common.file_reader import CommonRoadFileReader

from crdesigner.conversion.opendrive.opendriveparser.parser import parse_opendrive
from crdesigner.conversion.opendrive.opendriveconversion.network import Network

from crdesigner.conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter

from crdesigner.io.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.io.gui.toolboxes.gui_sumo_simulation import SUMOSimulation
    from crdesigner.conversion.sumo_map.sumo2cr import convert_net_to_cr

from crdesigner.conversion.osm2cr.converter_modules.converter import GraphScenario
from crdesigner.conversion.osm2cr.converter_modules.cr_operations.export import convert_to_scenario


__author__ = "Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["BMW Car@TUM"]
__version__ = "0.5.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


def lanelet_to_commonroad(input_file: str, proj: str, left_driving: bool, adjacencies: bool) -> Scenario:
    """
    Converts lanelet/lanelet2 file to CommonRoad

    @param input_file: Path to lanelet/lanelet2 file
    @param proj: proj-string
    @param left_driving: Map describes left driving system.
    @param adjacencies: Detect left and right adjacencies of lanelets if they do not share a common way
    @return: CommonRoad scenario
    """
    parser = Lanelet2Parser(etree.parse(input_file).getroot())
    osm = parser.parse()

    osm2l = Lanelet2CRConverter(proj_string=proj)
    scenario = osm2l(osm, detect_adjacencies=adjacencies, left_driving_system=left_driving)

    return scenario


def commonroad_to_lanelet(input_file: str, output_name: str, proj: str):
    """
    Converts CommonRoad map to lanelet format

    @param input_file: Path to CommonRoad map
    @param output_name: Name and path of lanelet file.
    @param proj: proj-string
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

    l2osm = CR2LaneletConverter(proj)
    osm = l2osm(scenario)
    with open(f"{output_name}", "wb") as file_out:
        file_out.write(
            etree.tostring(
                osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
            )
        )


def opendrive_to_commonroad(input_file: str) -> Scenario:
    """
    Converts OpenDRIVE file to CommonRoad

    @param input_file: Path to OpenDRIVE file
    @return: CommonRoad scenario
    """
    with open("{}".format(input_file), "r") as file_in:
        opendrive = parse_opendrive(etree.parse(file_in).getroot())

    road_network = Network()
    road_network.load_opendrive(opendrive)

    return road_network.export_commonroad_scenario()


def sumo_to_commonroad(input_file: str) -> Scenario:
    """
    Converts SUMO net file to CommonRoad

    @param input_file: Path to SUMO net file
    @return: CommonRoad scenario
    """
    return convert_net_to_cr(input_file)


def commonroad_to_sumo(input_file: str):
    """
    Converts CommonRoad file to SUMO net file and stores it

    @param input_file: Path to CommonRoad file
    @return: CommonRoad scenario
    """
    if SUMO_AVAILABLE:
        sumo_simulation = SUMOSimulation("./")
        sumo_simulation.convert(input_file)


def osm_to_commonroad(input_file: str) -> Scenario:
    """
    Converts OpenStreetMap file to CommonRoad scenario

    @param input_file: Path to OpenStreetMap file
    @return: CommonRoad scenario
    """
    osm_graph = GraphScenario(input_file).graph
    return convert_to_scenario(osm_graph)
