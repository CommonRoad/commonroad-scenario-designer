import contextlib
import io
import os

import unittest
import warnings
from typing import List

import numpy as np
import pytest
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.obstacle import ObstacleType
from crdesigner.map_conversion.sumo_map.config import SumoConfig
from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
from parameterized import parameterized
from sumocr.interface.sumo_simulation import SumoSimulation


class TestCommonRoadToSUMOConversion(unittest.TestCase):
    """Tests the conversion from a CommonRoad map to a SUMO .net.xml file
    """
    proj_string = ""
    scenario_name = None
    cwd_path = None
    scenario = None
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pytest_cache/sumo_map")
    _outfile_extensions = ('.xml', 'sumo.cfg', '.mp4')
    avg_velocities = []
    colliding_ids = 0

    @property
    def out_path_test(self):
        return os.path.join(self.out_path, str(self.id()).split(".")[2])

    def setUp(self) -> None:
        if not os.path.isdir(self.out_path_test):
            os.makedirs(self.out_path_test)

    def read_cr_file(self, cr_file_name: str, folder="test_maps/sumo"):
        """Load the osm file and convert it to a scenario."""
        if not self.scenario_name:
            self.scenario_name = cr_file_name

        self.cwd_path = os.path.dirname(os.path.abspath(__file__))

        self.path = os.path.join(self.cwd_path, folder, cr_file_name + ".xml")

        self.scenario, planning_problem = CommonRoadFileReader(self.path).open()

        # translate scenario to center
        centroid = np.mean(np.concatenate([la.center_vertices for la in self.scenario.lanelet_network.lanelets]),
                           axis=0)
        self.scenario.translate_rotate(-centroid, 0)
        planning_problem.translate_rotate(-centroid, 0)
        config = SumoConfig.from_scenario(self.scenario)
        config.veh_distribution[ObstacleType.PEDESTRIAN] = 0.0
        # convert to SUMO
        wrapper = CR2SumoMapConverter(self.scenario, config)
        return config, wrapper

    def sumo_run(self, config: SumoConfig, converter: CR2SumoMapConverter, tls_lanelet_ids: List[int]) -> str:
        # was the conversion successful?
        conversion_successful = converter.create_sumo_files(self.out_path_test)
        import glob
        print(glob.glob(self.out_path_test + "/*"))
        self.assertTrue(conversion_successful)

        # can we generate traffic light systems?
        if tls_lanelet_ids:
            self.assertTrue(
                    all(converter.auto_generate_traffic_light_system(lanelet_id) for lanelet_id in tls_lanelet_ids))

        simulation = SumoSimulation()
        f = io.StringIO()
        with contextlib.redirect_stderr(f):
            simulation.initialize(config, converter)

            for _ in range(config.simulation_steps):
                simulation.simulate_step()
            simulation.stop()

        simulated_scenario = simulation.commonroad_scenarios_all_time_steps()
        self.assertIsNotNone(simulated_scenario)

        # write simulated scenario to disk
        CommonRoadFileWriter(simulated_scenario, None, author=self.scenario.author,
                affiliation=self.scenario.affiliation, source=self.scenario.source, tags=self.scenario.tags,
                location=self.scenario.location).write_scenario_to_file(
                os.path.join(os.path.dirname(self.path), self.scenario_name + ".simulated.xml"),
                overwrite_existing_file=OverwriteExistingFile.ALWAYS)
        return f.getvalue()

    @staticmethod
    def validate_output(captured):
        lines = captured.split("\n")
        keywords = ["teleporting", "collision"]
        for keyword in keywords:
            matches = [line for line in lines if keyword in line]
            err_str = "\n".join(matches)
            if len(matches) > 0:
                warnings.warn(f"Simulation Error, {keyword} found {len(matches)} times in stderr:" + "\n" + err_str)

  #  @parameterized.expand([
       # ["USA_Peach-3_3_T-1", []],
        # ["DEU_garching-1_1", [270]],
        # ["DEU_garching-1_2", []],
        # ["ZAM_intersectandcrossing-1_0", [56]],
       # ["ZAM_merging-1_1", [107]],
        # ["USA_urban_1", [105]],
        # ["DEU_AAH-1_8007_T-1", [154]],
        # ["DEU_AAH-2_19000_T-1", [118]],
        # ["DEU_Guetersloh-20_4_T-1", []],
        # ["DEU_Muc-13_1_T-1", [257,253]],
        # ["USA_Lanker-2_13_T-1", [3670]],
        # ["ARG_Carcarana-10_5_T-1", [6758, 6712, 6917, 8325]],
        # ["ARG_Carcarana-10_2_T-1", [6917, 6988, 8325]],
        # ["BEL_Putte-10_1_T-1", []],
        # ["BEL_Putte-1_3_T-1", [6077]],
        # ["BEL_Zaventem-4_1_T-1", []],
        # ["DEU_BadEssen-1_6_T-1", [23452]],
        # ["DEU_Guetersloh-11_2_T-1", [80457]],
        # ["DEU_Guetersloh-5_2_T-1", []],
        # ["DEU_Hennigsdorf-1_2_T-1", []],
        # ["DEU_Hennigsdorf-16_3_T-1", []],
        # ["DEU_Hennigsdorf-18_2_T-1", []],
        # ["DEU_Hennigsdorf-9_3_T-1", []],
        # ["DEU_Meckenheim-2_4_T-1", []],
        # ["DEU_Moabit-6_1_T-1", []],
        # ["DEU_Moelln-12_1_T-1", []],
        # ["DEU_Moelln-2_1_T-1", []],
        # ["DEU_Moelln-9_1_T-1", []],
        # ["DEU_Muehlhausen-12_4_T-1", []],
        # ["DEU_Muehlhausen-13_6_T-1", []],
        # ["DEU_Rheinbach-2_5_T-1", []],
        # ["DEU_Speyer-4_3_T-1", []],
        # ["ESP_Almansa-1_1_T-1", []],
        # ["ESP_Berga-4_1_T-1", []],
        # ["ESP_Cambre-3_3_T-1", []],
        # ["ESP_Ceuta-1_2_T-1", []],
        # ["ESP_Ceuta-1_3_T-1", []],
        # ["ESP_Inca-3_2_T-1", []],
        # ["ESP_Inca-7_1_T-1", []],
        # ["ESP_SantBoideLlobregat-11_3_T-1", []],
        # ["ESP_Toledo-8_3_T-1", []],
        # ["FRA_Miramas-4_6_T-1", []],
        # ["GRC_Perama-2_2_T-1", []],
        # ["HRV_Pula-12_2_T-1", []],
        # ["HRV_Pula-4_1_T-1", []],
        # ["HRV_Pula-4_5_T-1", []],
        # ["ITA_Siderno-1_2_T-1", []],
        # ["ITA_Siderno-8_2_T-1", []],
        # ["USA_US101-3_1_T-1", []],
        # ["ZAM_Tjunction-1_56_T-1", []],
        # ["ZAM_Zip-1_54_T-1", []],
        # ["ZAM_MergingTrafficSign-1_1_T-1", []],
        # ["ZAM_MergingTrafficSign-1_2_T-1", []],
        # ["ZAM_TrafficLightTest-1_1-T-1", []],
        # ["ZAM_TrafficLightTest-1_2-T-1", []],
        # ["ZAM_TrafficLightLanes-1_1_T-1", []],
   # ])
   #  @pytest.mark.parallel
   #  def test_parameterized_sumo_run(self, cr_file_name: str, tls: List[int]):
   #      config, converter = self.read_cr_file(cr_file_name)
   #      out = self.sumo_run(config, converter, tls)
   #      self.validate_output(out)

    # @parameterized.expand([  #     # ["ESP_Ceuta-1_2_T-1", []],  #     # ["USA_Peach-3_3_T-1", []],
    #     ["USA_Lanker-2_13_T-1", []],  # ])  # def test_ngsim_conversion(self, cr_file_name: str, tls: List[int]):
    #     config, wrapper = self.read_cr_file(cr_file_name)  #     out = self.sumo_run(config, wrapper, tls)  #     #
    #     print(err.getvalue())  #     self.validate_output(out)

    # @parameterized.expand([  #     # ["ESP_Ceuta-1_2_T-1", []],  #     # ["USA_Peach-3_3_T-1", []],
    #     ["KA-Suedtangente-atlatec", []],  # ])  # def test_opendrive_source(self, cr_file_name: str,
    #     tls: List[int]):  #     """Test with maps that have been converted from openDRIVE"""  #     config,
    #     wrapper = self.read_cr_file(cr_file_name, folder="opendrive")  #     out = self.sumo_run(config, wrapper,
    #     tls)  #     # print(err.getvalue())  #     self.validate_output(out)  #     self.tearDown()

    # @parameterized.expand([  #     ["USA_Peach-3_3_T-1", []],  # ])  # def convert_scenario_to_net_file(self,
    # cr_file_name: str, tls: List[int]):  #     # load CR scenario and translate to origo  #     scenario,
    # planning_problem_set = CommonRoadFileReader(scenario_file).open()  #     conf.country_id =
    # scenario.scenario_id.country_id  #     scenario.scenario_id.obstacle_behavior = "I"  #     conf.scenario_name =
    # str(scenario.scenario_id)  #     conf.presimulation_steps = 0  #     output_folder = os.path.join(
    # output_folder_path, conf.scenario_name)  #     os.makedirs(output_folder, exist_ok=True)  #  #     # convert
    # scenario to SUMO files  #     converter_config = SumoConfig()  #     converter_config.scenario_name = str(
    # scenario.scenario_id)  #     converter_config.country_id = scenario.scenario_id.country_id  #     converter =
    # CR2SumoMapConverter(scenario, converter_config)
