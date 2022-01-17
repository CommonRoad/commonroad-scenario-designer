import unittest
import subprocess
from pathlib import Path
import time
import os

__author__ = "Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["BMW Car@TUM"]
__version__ = "0.4"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class TestCommandLineInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.output_path = os.path.dirname(os.path.realpath(__file__)) + "/.pytest_cache"
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

    def test_opendrive(self):
        subprocess.Popen(['crdesigner', 'map-convert-opendrive',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/opendrive_test_files/poly3_and_border_record.xodr',
                          '-o', self.output_path + "/opendrive_command_line.xml", '-t', 'urban', 'highway'])
        time.sleep(5)
        exists = Path(self.output_path + "/opendrive_command_line.xml")
        self.assertTrue(exists.is_file())

    def test_osm(self):
        subprocess.Popen(['crdesigner', 'map-convert-osm',
                          '-i', os.path.dirname(os.path.realpath(__file__)) +
                          '/../map_conversion/osm_test_files/munich.osm',
                          '-o', self.output_path + "/osm_command_line.xml"])
        time.sleep(30)
        exists = Path(self.output_path + '/osm_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_lanelet2_to_cr(self):
        subprocess.Popen(['crdesigner', 'map-convert-lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/lanelet_lanelet2_test_files/traffic_priority_lanelets_utm.osm',
                          '-o', self.output_path + "/lanelet_lanelet2_command_line.xml"])
        time.sleep(5)
        exists = Path(self.output_path + "/lanelet_lanelet2_command_line.xml")
        self.assertTrue(exists.is_file())

    def test_cr_to_lanelet(self):
        subprocess.Popen(['crdesigner', 'map-convert-lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/lanelet_lanelet2_test_files/merging_lanelets_utm.xml',
                          '-o', self.output_path + "/cr_lanelet_command_line.osm", '--source_commonroad'])
        time.sleep(5)
        exists = Path(self.output_path + "/cr_lanelet_command_line.osm")
        self.assertTrue(exists.is_file())

    def test_cr_to_sumo(self):
        if not os.path.isdir(self.output_path + '/cr_sumo_command_line'):
            os.makedirs(self.output_path + '/cr_sumo_command_line')
        subprocess.Popen(['crdesigner', 'map-convert-sumo',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/sumo_test_files/ARG_Carcarana-10_2_T-1.xml',
                          '-o', self.output_path + "/cr_sumo_command_line" +
                          "/cr_sumo_command_line.net.xml", '--source_commonroad'])
        time.sleep(10)
        exists = Path(self.output_path + "/cr_sumo_command_line" + "/cr_sumo_command_line.net.xml")
        self.assertTrue(exists.is_file())

    def test_gui(self):
        process = subprocess.Popen(['crdesigner'])
        time.sleep(5)
        process.terminate()
        process = subprocess.Popen(['crdesigner', 'gui'])
        time.sleep(5)
        process.terminate()
