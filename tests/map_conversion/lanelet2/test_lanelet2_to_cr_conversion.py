import time
import os
import unittest
from lxml import etree  # type: ignore

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile  # type: ignore
from commonroad.planning.planning_problem import PlanningProblemSet  # type: ignore
from commonroad.scenario.scenario import Tag, Scenario  # type: ignore

from crdesigner.config.gui_config import utm_default, pseudo_mercator
from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from tests.map_conversion.utils import elements_equal


def get_tmp_dir():
    return os.path.dirname(os.path.abspath(__file__)) + "/.pytest_cache" + "/"


class TestLanelet2ToCommonRoadConversion(unittest.TestCase):
    """Tests the conversion from an osm file to a CommonRoad xml file."""

    @classmethod
    def setUpClass(cls):
        lanelet2_config.proj_string_l2 = pseudo_mercator

    @staticmethod
    def load_and_convert(osm_file_name: str, translate: bool = False, proj_string: str = None,
                         file_path: str = None) -> Scenario:
        """Loads and converts osm file to a scenario

        :param osm_file_name: name of the osm file
        :param translate: Boolean indicating whether the map should be moved to the origin
        :param proj_string: string defining projection method from geo-coordinates
        :return: Scenario that corresponds to that osm file
        """
        generate_unique_id(0)  # reset ID counter for next test case
        cwd_path = os.path.dirname(os.path.abspath(__file__))
        out_path = cwd_path + "/.pytest_cache"
        if not os.path.isdir(out_path):
            os.makedirs(out_path)
        else:
            for (dir_path, _, filenames) in os.walk(out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dir_path, file))

        if file_path is None:
            file_path = os.path.dirname(os.path.realpath(__file__)) + f"/../test_maps/lanelet2/{osm_file_name}.osm"

        with open(file_path, "r", ) as fh:
            osm = Lanelet2Parser(etree.parse(fh).getroot()).parse()

        if proj_string is not None:
            lanelet2_config.proj_string_l2 = proj_string
        if translate is not None:
            lanelet2_config.translate = translate
        osm2l = Lanelet2CRConverter()
        return osm2l(osm)

    def compare_maps(self, file_name: str, translate: bool = False, file_path: str = None) -> bool:
        """
        Test if the scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        xml_output_name = file_name
        translated = "" if not translate else "_translated"

        cr_file_path = os.path.dirname(os.path.realpath(__file__)) + f"/../test_maps/lanelet2/{xml_output_name}{translated}.xml"
        with open(cr_file_path, "r", ) as fh:
            parser = etree.XMLParser(remove_blank_text=True)
            tree_import = etree.parse(fh, parser=parser).getroot()
            writer = CommonRoadFileWriter(scenario=self.load_and_convert(file_name, translate=translate,
                                                                         file_path=file_path),
                                          planning_problem_set=PlanningProblemSet(), author="", affiliation="",
                                          source="CommonRoad Scenario Designer", tags={Tag.URBAN, Tag.HIGHWAY}, )
            writer.write_to_file(
                    get_tmp_dir() + xml_output_name
                    + translated + ".xml", OverwriteExistingFile.ALWAYS)

            # set same date so this won't change the comparison
            date = time.strftime("%Y-%m-%d", time.localtime())
            tree_import.set("date", date)
            writer._file_writer.root_node.set("date", date)

            # compare both element trees
            return elements_equal(tree_import, writer._file_writer.root_node)

    def test_simple_map(self):
        """Simple test case file which includes successors and predecessors and adjacencies."""
        self.assertTrue(self.compare_maps("urban-1_lanelets_utm"))

    def test_simple_map_translated(self):
        """Simple test case file which includes successors and predecessors and adjacencies."""
        self.assertTrue(self.compare_maps("urban-1_lanelets_utm", translate=True))

    def test_merging_lanelets(self):
        """Basic test file including some splits and joins."""
        self.assertTrue(self.compare_maps("merging_lanelets_utm"))

    def test_map_with_priorities(self):
        """Basic test file including priorities."""
        self.assertTrue(self.compare_maps("traffic_priority_lanelets_utm"))

    def test_map_with_speed_limits(self):
        """Basic test file including speed limits."""
        self.assertTrue(self.compare_maps("traffic_speed_limit_utm"))

    @unittest.skip("there are minor differences between the file at the end of the pipeline")
    def test_geodetic_transformation(self):
        """
        Convert lanelet2 to CR, then back to lanelet2 and again to CR in order to test
        whether the projection works correctly.
        More precisely: when converting from lanelet2 to CR, the method for projecting geodesic
        coordinates can be configured and is stored in the CR-scenario. When converting back
        to lanelet2, this stored projection method should be considered.
        """
        lanelet2_file_name = "urban-1_lanelets_utm"
        proj_string = utm_default

        cr_scenario = self.load_and_convert(lanelet2_file_name, proj_string=proj_string)
        l2osm = CR2LaneletConverter()
        lanelet2 = l2osm(cr_scenario)
        lanelet2_converted_file_name = f'{lanelet2_file_name}__converted'
        lanelet2_converted_file_path = f'{get_tmp_dir()}{lanelet2_converted_file_name}.osm'
        etree.ElementTree(lanelet2).write(lanelet2_converted_file_path, pretty_print=True)

        self.assertTrue(self.compare_maps(lanelet2_file_name, file_path=lanelet2_converted_file_path))
