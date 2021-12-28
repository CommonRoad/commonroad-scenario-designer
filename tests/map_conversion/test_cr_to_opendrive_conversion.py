import os
import unittest
import re
from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter

# to run the tests: pytest -v --cov=crdesigner.map_conversion.opendrive.cr_to_opendrive.converter --cov-report html
# This also generates a coverage report, see rootdir/htmlcov -> index.html


class TestConverterConvert(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestConverterConvert, self).__init__(*args, **kwargs)
        self.map_names = [
            "zero_width_lanes_map",
            "ARG_Carcarana-1_1_T-1",
            "DEU_Guetersloh-11_2_T-1",
            "USA_Lanker-1_17_T-1",
            "DEU_Test-1_1_T-1",
            "DEU_Muehlhausen-2_2_T-1",
            "lanelet_no_succ_or_pred",
        ]

    def prepareConversion(self, map_name):
        self.map_name = map_name
        # relative path for input
        self.file_path_in = f"commonroad_to_opendrive_test_files/{self.map_name}.xml"  
        
        # relative path for output
        self.file_path_out = f"commonroad_to_opendrive_test_files/converted_xodr_files/{self.map_name}.xodr"

        # load the xml file and preprocess it
        self.data = DataLoader(self.file_path_in)
        print(self.data)

        scenario, successors, ids = self.data.initialize()
        self.converter = Converter(self.file_path_in, scenario, successors, ids)

    # cuts out the date timestamp of both maps
    # (as they wont be equal) and compares them
    def checkWithGroundTruth(self, reference_file):
        with open(self.file_path_out, "r") as converted_file:
            converted_file_content = re.sub(r"date=\"[^ ]*", "", converted_file.read())

        with open(reference_file, "r") as reference_file:
            reference_file_content = re.sub(r"date=\"[^ ]*", "", reference_file.read())
        assert converted_file_content == reference_file_content

    def test_convert_USA_Lanker(self):
        self.prepareConversion("USA_Lanker-1_17_T-1")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_DEU_Guetersloh(self):
        self.prepareConversion("DEU_Guetersloh-11_2_T-1")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_ARG_Carcarana(self):
        self.prepareConversion("ARG_Carcarana-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_zero_width_lanes_map(self):
        self.prepareConversion("zero_width_lanes_map")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_DEU_Test(self):
        self.prepareConversion("DEU_Test-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_DEU_Muehlhausen(self):
        self.prepareConversion("DEU_Muehlhausen-2_2_T-1")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_convert_lanelet_no_succ_or_pred(self):
        self.prepareConversion("lanelet_no_succ_or_pred")
        self.converter.convert(self.file_path_out)
        self.checkWithGroundTruth(f"commonroad_to_opendrive_test_files/reference_xodr_files/{self.map_name}.xodr")

    def test_function_checkAllVisited(self):
        self.prepareConversion("DEU_Test-1_1_T-1")
        self.converter.id_dict.popitem()
        self.assertRaises(KeyError, lambda: self.converter.checkAllVisited())



if __name__ == "__main__":
    unittest.main()
