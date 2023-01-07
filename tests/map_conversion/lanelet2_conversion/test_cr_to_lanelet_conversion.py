import os
import unittest
from lxml import etree # type: ignore 

from commonroad.common.file_reader import CommonRoadFileReader # type: ignore

from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from tests.map_conversion.utils import elements_equal


class TestCommonRoadToLaneletConversion(unittest.TestCase):
    """
    Test the conversion of a specific osm file.

    This converted scenario should describe the same map as the osm file,
    by reading it, parsing it and then converting it to a CommonRoad file including a scenario.
    """
    
    def setUp(self) -> None:
        self.proj_string = "+proj=utm +zone=32 +ellps=WGS84"

    def load_and_convert(self, xml_file_name: str) -> etree.Element:
        """Load the osm file and convert it to a scenario."""
        try:
            commonroad_reader = CommonRoadFileReader(
                f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/{xml_file_name}.xml"
            )
            scenario, _ = commonroad_reader.open()
            l2osm = CR2LaneletConverter(self.proj_string)
            osm = l2osm(scenario)
            return osm
        except etree.XMLSyntaxError as xml_error:
            print(f"SyntaxERror: {xml_error}")
            print(
                "There was an error during the loading of the selected CommonRoad file.\n"
            )
            return None

    def compare_maps(self, xml_file_name: str) -> bool:
        """Test if converted scenario is equal to the loaded xml file.    
        Disregard the different dates.
        """
        fh = f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/{xml_file_name}_from_cr.osm"
        parser = etree.XMLParser(remove_blank_text=True)
        tree_import = etree.parse(fh, parser=parser).getroot()

        # set same date so this won't change the comparison
        tree_import.set("generator", "42")
        osm = self.load_and_convert(xml_file_name)
        osm.set("generator", "42")

        # compare both element trees
        return elements_equal(tree_import, osm)

    def test_urban_lanelets(self):
        """Simple test case file which includes succesors and predecessors and adjacencies."""
        self.assertTrue(self.compare_maps("urban-1_lanelets_utm"))

    def test_merging_lanelets(self):
        """Basic test file including some splits and joins."""
        self.assertTrue(self.compare_maps("merging_lanelets_utm"))
