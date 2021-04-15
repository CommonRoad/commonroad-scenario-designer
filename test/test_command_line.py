import unittest
import subprocess
from pathlib import Path
import time


def test_gui():
    process = subprocess.Popen(['crdesigner'])
    process.terminate()
    process = subprocess.Popen(['crdesigner', 'gui'])
    process.terminate()


class MyTestCase(unittest.TestCase):
    def test_opendrive(self):
        subprocess.Popen(['crdesigner', 'opendrive',
                          '-i', './opendrive_test_files/poly3_and_border_record.xodr',
                          '-o', './opendrive_command_line.xml'])
        time.sleep(5)
        exists = Path('./opendrive_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_osm(self):
        subprocess.Popen(['crdesigner', 'osm',
                          '-i', './osm_test_files/munich.osm',
                          '-o', './osm_command_line.xml'])
        time.sleep(15)
        exists = Path('./osm_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_lanelet2_to_cr(self):
        subprocess.Popen(['crdesigner', 'lanelet',
                          '-i', './lanelet_lanelet2_test_files/traffic_priority_lanelets_utm.osm',
                          '-o', './lanelet_lanelet2_command_line.xml'])
        time.sleep(5)
        exists = Path('./lanelet_lanelet2_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_cr_to_lanelet(self):
        subprocess.Popen(['crdesigner', 'lanelet',
                          '-i', './lanelet_lanelet2_test_files/merging_lanelets_utm.xml',
                          '-o', './cr_lanelet_command_line.osm',
                          '--source_commonroad'])
        time.sleep(5)
        exists = Path('./cr_lanelet_command_line.osm')
        self.assertTrue(exists.is_file())


if __name__ == '__main__':
    unittest.main()
