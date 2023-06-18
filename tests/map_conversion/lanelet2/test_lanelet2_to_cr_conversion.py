import time
import os
import unittest
from lxml import etree  # type: ignore

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile  # type: ignore
from commonroad.planning.planning_problem import PlanningProblemSet  # type: ignore
from commonroad.scenario.scenario import Tag, Scenario  # type: ignore

from crdesigner.map_conversion.common.utils import generate_unique_id
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.config.config import Lanelet2ConversionParams
from tests.map_conversion.utils import elements_equal


class TestLanelet2ToCommonRoadConversion(unittest.TestCase):
    """Tests the conversion from an osm file to a CommonRoad xml file."""

    @staticmethod
    def load_and_convert(osm_file_name: str, translate: bool = False) -> Scenario:
        """Loads and converts osm file to a scenario

        :param osm_file_name: name of the osm file
        :param translate: Boolean indicating whether the map should be moved to the origin
        :return: Scenario that corresponds to that osm file
        """
        cwd_path = os.path.dirname(os.path.abspath(__file__))
        out_path = cwd_path + "/.pytest_cache"
        if not os.path.isdir(out_path):
            os.makedirs(out_path)
        else:
            for (dir_path, _, filenames) in os.walk(out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dir_path, file))

        with open(os.path.dirname(os.path.realpath(__file__))
                  + f"/../test_maps/lanelet2/{osm_file_name}.osm", "r", ) as fh:
            osm = Lanelet2Parser(etree.parse(fh).getroot()).parse()

        config = Lanelet2ConversionParams()
        config.translate = translate
        osm2l = Lanelet2CRConverter(lanelet2_config=config)
        return osm2l(osm)

    def compare_maps(self, file_name: str, translate: bool = False) -> bool:
        """
        Test if the scenario is equal to the loaded xml file.
        Disregard the different dates.
        """
        xml_output_name = file_name
        translated = "" if not translate else "_translated"

        with open(os.path.dirname(os.path.realpath(__file__))
                  + f"/../test_maps/lanelet2/{xml_output_name}{translated}.xml", "r", ) as fh:
            parser = etree.XMLParser(remove_blank_text=True)
            tree_import = etree.parse(fh, parser=parser).getroot()
            writer = CommonRoadFileWriter(scenario=self.load_and_convert(file_name, translate=translate),
                                          planning_problem_set=PlanningProblemSet(), author="", affiliation="",
                                          source="CommonRoad Scenario Designer", tags={Tag.URBAN, Tag.HIGHWAY}, )
            writer.write_to_file(
                    os.path.dirname(os.path.abspath(__file__)) + "/.pytest_cache" + "/" + xml_output_name
                    + translated + ".xml", OverwriteExistingFile.ALWAYS)

            # set same date so this won't change the comparison
            date = time.strftime("%Y-%m-%d", time.localtime())
            tree_import.set("date", date)
            writer._file_writer.root_node.set("date", date)

            generate_unique_id(0)  # reset ID counter for next test case

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