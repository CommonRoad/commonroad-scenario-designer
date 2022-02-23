import os
import unittest
import re
import time
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter


class TestSignConversion(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestSignConversion, self).__init__(*args, **kwargs)

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
            
        with open("{}".format(reference_file), "r") as reference_file:
            reference_tree = etree.parse(reference_file).getroot()

            for road1, road2 in zip(converted_tree.iter('road'), reference_tree.iter('road')):
                for signals1, signals2 in zip(road1.iter("signals"), road2.iter("signals")):
                    for signal1, signal2 in zip(signals1.iter("signal"), signals2.iter("signal")):
                        # comparing attributes of traffic_sign id: 4107 
                        if int(signal1.attrib["id"]) == 4107:
                            self.assertEqual(int(signal1.attrib['id']), int(signal2.attrib['id']), "Error: id mismatch")
                            self.assertEqual(float(signal1.attrib['s']), float(signal2.attrib['s']), "Error: s mismatch")
                            self.assertEqual(float(signal1.attrib['t']), float(signal2.attrib['t']), "Error: t mismatch")
                            self.assertEqual((signal1.attrib['orientation']), (signal2.attrib['orientation']),
                                            "Error: orientation mismatch")

    # def test_convert_USA_Lanker(self):
    #     self.prepare_conversion("USA_Lanker-1_17_T-1")
    #     self.converter.convert(self.file_path_out)
    #     self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    # def test_convert_DEU_Guetersloh(self):
    #     self.prepare_conversion("DEU_Guetersloh-11_2_T-1")
    #     self.converter.convert(self.file_path_out)
    #     self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ARG_Carcarana(self):
        self.prepare_conversion("ARG_Carcarana-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))


if __name__ == "__main__":
    unittest.main()
