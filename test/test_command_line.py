import unittest
import subprocess
from pathlib import Path
import time
import os


def test_gui():
    process = subprocess.Popen(['crdesigner'])
    process.terminate()
    process = subprocess.Popen(['crdesigner', 'gui'])
    process.terminate()


class MyTestCase(unittest.TestCase):
    def test_opendrive(self):
        subprocess.Popen(['crdesigner', 'opendrive',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/opendrive_test_files/poly3_and_border_record.xodr',
                          '-o', os.path.dirname(os.path.realpath(__file__)) + '/opendrive_command_line.xml',
                          '-t', 'urban', 'highway'])
        time.sleep(5)
        exists = Path(os.path.dirname(os.path.realpath(__file__)) + '/opendrive_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_osm(self):
        subprocess.Popen(['crdesigner', 'osm',
                          '-i', os.path.dirname(os.path.realpath(__file__)) + '/osm_test_files/munich.osm',
                          '-o', os.path.dirname(os.path.realpath(__file__)) + '/osm_command_line.xml'])
        time.sleep(15)
        exists = Path(os.path.dirname(os.path.realpath(__file__)) + '/osm_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_lanelet2_to_cr(self):
        subprocess.Popen(['crdesigner', 'lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/lanelet_lanelet2_test_files/traffic_priority_lanelets_utm.osm',
                          '-o', os.path.dirname(os.path.realpath(__file__)) + '/lanelet_lanelet2_command_line.xml'])
        time.sleep(5)
        exists = Path(os.path.dirname(os.path.realpath(__file__)) + '/lanelet_lanelet2_command_line.xml')
        self.assertTrue(exists.is_file())

    def test_cr_to_lanelet(self):
        subprocess.Popen(['crdesigner', 'lanelet',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/lanelet_lanelet2_test_files/merging_lanelets_utm.xml',
                          '-o', os.path.dirname(os.path.realpath(__file__)) + '/cr_lanelet_command_line.osm',
                          '--source_commonroad'])
        time.sleep(5)
        exists = Path(os.path.dirname(os.path.realpath(__file__)) + '/cr_lanelet_command_line.osm')
        self.assertTrue(exists.is_file())

    def test_cr_to_sumo(self):
        os.mkdir(os.path.dirname(os.path.realpath(__file__)) + '/cr_sumo_command_line')
        subprocess.Popen(['crdesigner', 'sumo',
                          '-i', os.path.dirname(os.path.realpath(__file__))
                          + '/sumo_test_files/ARG_Carcarana-10_2_T-1.xml',
                          '-o', os.path.dirname(os.path.realpath(__file__))
                          + '/cr_sumo_command_line/cr_sumo_command_line.net',
                          '--source_commonroad'])
        time.sleep(10)
        exists = Path(os.path.dirname(os.path.realpath(__file__))
                      + '/cr_sumo_command_line/cr_sumo_command_line.net.xml')
        self.assertTrue(exists.is_file())


if __name__ == '__main__':
    unittest.main()
