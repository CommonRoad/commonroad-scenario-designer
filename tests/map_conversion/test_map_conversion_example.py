import unittest
import os
from pathlib import Path


class MapConversionExampleTests(unittest.TestCase):
    # change the directory to match example scripts due to contained paths
    os.chdir(Path(__file__).parent.parent.parent/"tutorials/conversion_examples")

    def test_example_lanelet2_to_commonroad(self):
        # remove the file if it has already been created
        if Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.xml")):
            Path.unlink(Path("./example_files/lanelet2/merging_lanelets_utm.xml"))

        # check if there is no file
        self.assertFalse(Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.xml")))

        # call the execution of the example script
        exec(open(Path(__file__).parent.parent.parent/"tutorials/conversion_examples/example_lanelet2_to_commonroad.py").read())

        # check if the file has been created
        self.assertTrue(Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.xml")))

    def test_example_commonroad_to_lanelet2(self):
        # remove the file if it has already been created
        if Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.osm")):
            Path.unlink(Path("./example_files/lanelet2/merging_lanelets_utm.osm"))

        # check if there is no file
        self.assertFalse(Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.osm")))

        # call the execution of the example script
        exec(open("example_commonroad_to_lanelet2.py").read())

        # check if the file has been created
        self.assertTrue(Path.exists(Path("./example_files/lanelet2/merging_lanelets_utm.osm")))

    def test_example_opendrive_to_commonroad(self):
        # remove the file if it has already been created
        if Path.exists(Path("./example_files/opendrive/opendrive-1.xml")):
            Path.unlink(Path("./example_files/opendrive/opendrive-1.xml"))

        # check if there is no file
        self.assertFalse(Path.exists(Path("./example_files/opendrive/opendrive-1.xml")))

        # call the execution of the example script
        exec(open("example_opendrive_to_commonroad.py").read())

        # check if the file has been created
        self.assertTrue(Path.exists(Path("./example_files/opendrive/opendrive-1.xml")))

    def test_example_osm_to_commonroad(self):
        # remove the file if it has already been created
        if Path.exists(Path("./example_files/osm/munich.xml")):
            Path.unlink(Path("./example_files/osm/munich.xml"))

        # check if there is no file
        self.assertFalse(Path.exists(Path("./example_files/osm/munich.xml")))

        # call the execution of the example script
        exec(open("example_osm_to_commonroad.py").read())

        # check if the file has been created
        self.assertTrue(Path.exists(Path("./example_files/osm/munich.xml")))

    def test_example_osm_to_commonroad_using_sumo_parser(self):
        # remove the file if it has already been created
        if Path.exists(Path("./example_files/osm/test_ped_crossing.xml")):
            Path.unlink(Path("./example_files/osm/test_ped_crossing.xml"))

        # check if there is no file
        self.assertFalse(Path.exists(Path("./example_files/osm/test_ped_crossing.xml")))

        # call the execution of the example script
        exec(open("example_osm_to_commonroad_using_sumo_parser.py").read())

        # check if the file has been created
        self.assertTrue(Path.exists(Path("./example_files/osm/test_ped_crossing.xml")))
