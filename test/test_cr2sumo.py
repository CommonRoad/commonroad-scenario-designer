# -*- coding: utf-8 -*-
"""Test case file for SUMO to CR conversion and simulation"""

import os
import unittest
import numpy as np

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from crmapconverter.sumo_map.config import SumoConfig

from sumocr.interface.sumo_simulation import SumoSimulation


# force test execution to be in specified order
# unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)


class TestCR2SUMOScenarioBaseClass(unittest.TestCase):
    """Test the conversion from an CommonRoad map to a SUMO .net.xml file
    """
    __test__ = False
    cr_file_name = None
    proj_string = ""
    scenario_name = None
    cwd_path = None
    out_path = None
    scenario = None
    config = None

    tls_lanelet_ids = []

    def setUp(self):
        """Load the osm file and convert it to a scenario."""
        if not self.scenario_name:
            self.scenario_name = self.cr_file_name

        self.cwd_path = os.path.dirname(os.path.abspath(__file__))
        self.out_path = os.path.join(self.cwd_path, ".pytest_cache")

        if not os.path.isdir(self.out_path):
            os.makedirs(self.out_path)
        else:
            for (dirpath, _, filenames) in os.walk(self.out_path):
                for file in filenames:
                    if file.endswith('.xml'):
                        os.remove(os.path.join(dirpath, file))

        self.path = os.path.join(self.cwd_path, "sumo_xml_test_files",
                                 self.cr_file_name + ".xml")

        self.scenario, planning_problem = CommonRoadFileReader(
            self.path).open()

        # translate scenario to center
        centroid = np.mean(np.concatenate([
            l.center_vertices for l in self.scenario.lanelet_network.lanelets
        ]),
            axis=0)
        self.scenario.translate_rotate(-centroid, 0)
        planning_problem.translate_rotate(-centroid, 0)
        self.config = SumoConfig.from_scenario_name(self.scenario_name)
        # convert to SUMO
        self.wrapper = CR2SumoMapConverter(self.scenario.lanelet_network,
                                           self.config)

    def test_sumo_run(self):
        # was the conversion successful?
        conversion_successfull = self.wrapper.convert_to_net_file(
            os.path.dirname(self.path))
        self.assertTrue(conversion_successfull)

        # can we generate traffic light systems?
        self.assertTrue(
            all([
                self.wrapper.auto_generate_traffic_light_system(lanelet_id)
                for lanelet_id in self.tls_lanelet_ids
            ]))

        simulation = SumoSimulation()
        simulation.initialize(self.config, self.wrapper)

        for _ in range(self.config.simulation_steps):
            simulation.simulate_step()
        simulation.stop()

        simulated_scenario = simulation.commonroad_scenarios_all_time_steps()
        self.assertIsNotNone(simulated_scenario)

        # write simulated scenario to disk
        CommonRoadFileWriter(
            simulated_scenario,
            None,
            author=self.scenario.author,
            affiliation=self.scenario.affiliation,
            source=self.scenario.source,
            tags=self.scenario.tags,
            location=self.scenario.location).write_scenario_to_file(
            os.path.join(os.path.dirname(self.path),
                         self.scenario_name + ".simulated.xml"),
            overwrite_existing_file=True)
        # check validity of written file


class TestConversionComplexIntersection(TestCR2SUMOScenarioBaseClass):
    """Test conversion of a CR scenario to SUMO for a complex intersection"""
    __test__ = True
    cr_file_name = 'USA_Peach-3_3_T-1'
    # tls_lanelet_ids = [43513]


class TestConversionGarching(TestCR2SUMOScenarioBaseClass):
    """Test conversion of a CR scenario to SUMO for an intersection in garching with pedestrian path ways"""
    __test__ = True
    cr_file_name = "garching"
    tls_lanelet_ids = [270]


class TestConversionIntersectAndCrossing(TestCR2SUMOScenarioBaseClass):
    """Test conversion of a CR scenario to SUMO for a simple intersection crossing a pedestrian path way"""
    __test__ = True
    cr_file_name = "intersect_and_crossing"
    tls_lanelet_ids = [56]


class TestConversionMergingLanelets(TestCR2SUMOScenarioBaseClass):
    """Test conversion of a CR scenario to SUMO for merging lanelets"""
    __test__ = True
    cr_file_name = "merging_lanelets_utm"
    tls_lanelet_ids = [107]


class TestConversionUrban1(TestCR2SUMOScenarioBaseClass):
    """Test conversion of a CR scenario to SUMO for a simple crossing"""
    __test__ = True
    cr_file_name = "urban-1_lanelets_utm"
    tls_lanelet_ids = [105]


class TestSimulationAAH1(TestCR2SUMOScenarioBaseClass):
    __test__ = False
    cr_file_name = "DEU_AAH-1_8007_T-1"
    tls_lanelet_ids = [154]


class TestSimulationAAH2(TestCR2SUMOScenarioBaseClass):
    """Test conversion & simulation of a CR scenario to SUMO for a complex crossing"""
    __test__ = True
    cr_file_name = "DEU_AAH-2_19000_T-1"
    tls_lanelet_ids = [118]


class TestDEU_Guetersloh(TestCR2SUMOScenarioBaseClass):
    __test__ = True
    cr_file_name = "DEU_Guetersloh-20_4_T-1"


class TestDEU_Muc(TestCR2SUMOScenarioBaseClass):
    __test__ = True
    cr_file_name = "DEU_Muc-13_1_T-1"



if __name__ == "__main__":
    unittest.main()
