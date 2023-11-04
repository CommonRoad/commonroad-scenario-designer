import os
import unittest
from pathlib import Path
from lxml import etree  # type: ignore

from commonroad.common.file_reader import CommonRoadFileReader  # type: ignore

from crdesigner.config.gui_config import gui_config
from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.map_conversion.lanelet2.cr2lanelet import CR2LaneletConverter
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from tests.map_conversion.utils import elements_equal


def load_and_convert(xml_file_name: str) -> etree.Element:
    """Load the osm file and convert it to a scenario."""
    try:
        commonroad_reader = CommonRoadFileReader(
            f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/{xml_file_name}.xml"
        )
        scenario, _ = commonroad_reader.open()
        lanelet2_config.proj_string_l2 = gui_config.utm_default
        l2osm = CR2LaneletConverter()
        osm = l2osm(scenario)
        return osm
    except etree.XMLSyntaxError as xml_error:
        print(f"SyntaxError: {xml_error}")
        print(
            "There was an error during the loading of the selected CommonRoad file.\n"
        )
        return None


def compare_maps(xml_file_name: str) -> bool:
    """Test if converted scenario is equal to the loaded xml file.
    Disregard the different dates.
    """
    fh = f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/lanelet2/{xml_file_name}_from_cr.osm"
    parser = etree.XMLParser(remove_blank_text=True)
    tree_import = etree.parse(fh, parser=parser).getroot()

    # set same date so this won't change the comparison
    tree_import.set("generator", "42")
    osm = load_and_convert(xml_file_name)
    osm.set("generator", "42")

    # compare both element trees
    return elements_equal(tree_import, osm)


class TestCommonRoadToLaneletConversion(unittest.TestCase):
    """
    Test the conversion of a specific osm file.

    This converted scenario should describe the same map as the osm file,
    by reading it, parsing it and then converting it to a CommonRoad file including a scenario.
    """

    def test_urban_lanelets(self):
        """Simple test case file which includes succesors and predecessors and adjacencies."""
        self.assertTrue(compare_maps("urban-1_lanelets_utm"))

    def test_merging_lanelets(self):
        """Basic test file including some splits and joins."""
        self.assertTrue(compare_maps("merging_lanelets_utm"))


class TestOpenDRIVEToLaneletConversion(unittest.TestCase):
    """
    Test the conversion of a specific OpenDRIVE file.

    This converted lanelet2 map should describe the same map as the OpenDRIVE map,
    by reading it, parsing it, converting it to a CommonRoad, and finally to an OpenDRIVE map.
    """

    def test_crossing_complex8_course(self):
        input_path = f"{os.path.dirname(os.path.realpath(__file__))}/../test_maps/opendrive/CrossingComplex8Course.xodr"
        scenario = opendrive_to_commonroad(Path(input_path))
        l2osm = CR2LaneletConverter(lanelet2_config)
        self.assertIsNotNone(l2osm(scenario))  # TODO better evaluation
