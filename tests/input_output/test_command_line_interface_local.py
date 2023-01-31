import unittest
import subprocess
from pathlib import Path
import time
import os


class TestCommandLineInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.output_path = os.path.dirname(os.path.realpath(__file__)) + "/.pytest_cache"
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

    def test_opendrive(self):
        subprocess.Popen(['crdesigner', 'map-convert-opendrive',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/test_maps/opendrive/poly3_and_border_record.xodr',
                          '-o', self.output_path + "/opendrive_command_line.xml", '-t', 'urban', 'highway'])
        time.sleep(10)
        exists = Path(self.output_path + "/opendrive_command_line.xml")
        self.assertTrue(exists.is_file())

    def test_osm(self):
        subprocess.Popen(['crdesigner', 'map-convert-osm',
                          '-i', os.path.dirname(os.path.realpath(__file__)) +
                          '/../map_conversion/test_maps/osm/munich.osm',
                          '-o', self.output_path + "/osm_command_line.xml"])
        time.sleep(30)
        exists = Path(self.output_path + '/osm_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_lanelet2_to_cr(self):
        subprocess.Popen(['crdesigner', 'map-convert-lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/test_maps/lanelet2/traffic_priority_lanelets_utm.osm',
                          '-o', self.output_path + "/lanelet2_command_line.xml"])
        time.sleep(5)
        exists = Path(self.output_path + "/lanelet2_command_line.xml")
        self.assertTrue(exists.is_file())

    def test_cr_to_lanelet(self):
        subprocess.Popen(['crdesigner', 'map-convert-lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/../map_conversion/test_maps/lanelet2/merging_lanelets_utm.xml',
                          '-o', self.output_path + "/cr_lanelet_command_line.osm", '--source_commonroad'])
        time.sleep(5)
        exists = Path(self.output_path + "/cr_lanelet_command_line.osm")
        self.assertTrue(exists.is_file())

    # def test_cr_to_sumo(self):
    #     if not os.path.isdir(self.output_path + '/cr_sumo_command_line'):
    #         os.makedirs(self.output_path + '/cr_sumo_command_line')
    #     subprocess.Popen(['crdesigner', 'map-convert-sumo',
    #                       '-i', os.path.dirname(os.path.realpath(__file__))
    #                       + '/../map_conversion/test_maps/sumo/ARG_Carcarana-10_2_T-1.xml',
    #                       '-o', self.output_path + "/cr_sumo_command_line" +
    #                       "/cr_sumo_command_line.net.xml", '--source_commonroad'])
    #     time.sleep(10)
    #     exists = Path(self.output_path + "/cr_sumo_command_line" + "/cr_sumo_command_line.net.xml")
    #     self.assertTrue(exists.is_file())

    def test_gui(self):
        process = subprocess.Popen(['crdesigner'])
        time.sleep(5)
        process.terminate()
        process = subprocess.Popen(['crdesigner', 'gui'])
        time.sleep(5)
        process.terminate()
