import matplotlib
matplotlib.use('TkAgg')
import os
import unittest

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter


class TestCR2SUMOScenarioBaseClass(unittest.TestCase):
    """Test the conversion from an CommonRoad map to a SUMO .net.xml file
    """
    __test__ = False
    cr_file_name = None
    proj_string = ""
    xml_output_name = None
    cwd_path = None
    out_path = None

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        if not self.xml_output_name:
            self.xml_output_name = self.cr_file_name

        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        self.out_path = self.cwd_path + "/.pytest_cache"

        if not os.path.isdir(self.out_path):
            os.makedirs(self.out_path)
        else:
            for (dirpath, dirnames, filenames) in os.walk(self.out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dirpath, file))

        self.path = os.path.dirname(os.path.realpath(
            __file__)) + f"/sumo_xml_test_files/{self.cr_file_name}.xml"


class TestComplexIntersection(TestCR2SUMOScenarioBaseClass):
    __test__ = True
    cr_file_name = 'USA_Peach-3_3_T-1'

    def test_complex_intersection(self):
        converter = CR2SumoMapConverter.from_file(self.path)
        conversion_succesful = converter.convert_to_net_file(os.path.join(self.out_path, 'complex_intersection.net.xml'))
        assert conversion_succesful

