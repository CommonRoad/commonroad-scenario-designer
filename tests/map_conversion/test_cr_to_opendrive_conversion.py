import os
import unittest
import re
import time
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter
from crdesigner.map_conversion.opendrive.opendrive_parser.parser import parse_opendrive

from tests.map_conversion.utils import elements_equal

# to run the tests: pytest -v --cov=crdesigner.map_conversion.opendrive.cr_to_opendrive.converter --cov-report html
# This also generates a coverage report, see rootdir/htmlcov -> index.html


class TestConverterConvert(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestConverterConvert, self).__init__(*args, **kwargs)

    def prepare_conversion(self, map_name: str):
        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        out_path = self.cwd_path + "/.pytest_cache/converted_xodr_files"

        if not os.path.isdir(out_path):
            os.makedirs(out_path)
        else:
            for (dir_path, _, filenames) in os.walk(out_path):
                for file in filenames:
                    if file.endswith('.xodr'):
                        os.remove(os.path.join(dir_path, file))

        self.map_name = map_name
        self.path_reference_xodr_file = f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr"
        # absolute path for input
        self.file_path_in = os.path.join(self.cwd_path, f"commonroad_to_opendrive_test_files/{self.map_name}.xml")  
        # absolute path for output
        self.file_path_out = os.path.join(self.cwd_path, f".pytest_cache/converted_xodr_files/{self.map_name}.xodr")
        # load the xml file and preprocess it
        self.data = DataLoader(self.file_path_in)
        print(self.data)

        scenario, successors, ids = self.data.initialize()
        self.converter = Converter(self.file_path_in, scenario, successors, ids)

    # cuts out the date timestamp of both maps
    # (as they wont be equal) and compares them
    def check_with_ground_truth(self, reference_file: str):
        with open("{}".format(self.file_path_out), "r") as converted_file:
            converted_tree = etree.parse(converted_file).getroot()
            date = time.strftime("%Y-%m-%d", time.localtime())
            converted_tree.set("date", date)

        with open("{}".format(reference_file), "r") as reference_file:
            reference_tree = etree.parse(reference_file).getroot()
            date = time.strftime("%Y-%m-%d", time.localtime())
            reference_tree.set("date", date)

        # compare both element trees
        return elements_equal(converted_tree, reference_tree)

    def test_convert_USA_Lanker(self):
        self.prepare_conversion("USA_Lanker-1_17_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_DEU_Guetersloh(self):
        self.prepare_conversion("DEU_Guetersloh-11_2_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ARG_Carcarana(self):
        self.prepare_conversion("ARG_Carcarana-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_zero_width_lanes_map(self):
        self.prepare_conversion("zero_width_lanes_map")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_DEU_Test(self):
        self.prepare_conversion("DEU_Test-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_DEU_Muehlhausen(self):
        self.prepare_conversion("DEU_Muehlhausen-2_2_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_lanelet_no_succ_or_pred(self):
        self.prepare_conversion("lanelet_no_succ_or_pred")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_function_checkAllVisited(self):
        self.prepare_conversion("DEU_Test-1_1_T-1")
        self.converter.id_dict.popitem()
        self.assertRaises(KeyError, lambda: self.converter.check_all_visited())

    def test_convert_BEL_Wervik(self):
        self.prepare_conversion("BEL_Wervik-2_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_CulDeSac(self):
        self.prepare_conversion("CulDeSac")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_Over(self):
        self.prepare_conversion("ZAM_Over-1_1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_town03_right_width_coefficient(self):
        self.prepare_conversion("town03_right_width_coefficient")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))


if __name__ == "__main__":
    unittest.main()
