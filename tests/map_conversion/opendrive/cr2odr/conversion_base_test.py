import os
import time
import unittest

from commonroad.common.util import Path_T
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter
from tests.map_conversion.utils import elements_equal


class ConversionBaseTestCases:
    class ConversionBaseTest(unittest.TestCase):
        def prepare_conversion(self, map_name: str):
            self.cwd_path = os.path.dirname(os.path.abspath(__file__))
            out_path = self.cwd_path + "/.pytest_cache/converted_xodr_files"

            if not os.path.isdir(out_path):
                os.makedirs(out_path)
            else:
                for dir_path, _, filenames in os.walk(out_path):
                    for file in filenames:
                        if file.endswith(".xodr"):
                            os.remove(os.path.join(dir_path, file))

            self.map_name = map_name
            self.path_reference_xodr_file = f"../../test_maps/cr2odr/reference_xodr_files/{self.map_name}.xodr"
            # absolute path for input
            self.file_path_in = os.path.join(self.cwd_path, f"../../test_maps/cr2odr/{self.map_name}.xml")
            # absolute path for output
            self.file_path_out = os.path.join(self.cwd_path, f".pytest_cache/converted_xodr_files/{self.map_name}.xodr")

            self.converter = Converter(self.file_path_in)

        # cuts out the date timestamp of both maps
        # (as they wont be equal) and compares them
        def check_with_ground_truth(self, reference_file: Path_T):
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
