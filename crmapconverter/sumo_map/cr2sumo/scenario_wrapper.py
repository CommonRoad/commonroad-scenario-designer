import logging
import os, sys, warnings
import matplotlib.pyplot as plt
from commonroad.visualization.draw_dispatch_cr import draw_object
from typing import List, Type
import pathlib
import xml.etree.ElementTree as et

from xml.dom import minidom
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.common.util import Interval
from commonroad.common.file_reader import CommonRoadFileReader
import numpy as np

from .errors import NetError
from .util import get_scenario_name_from_crfile, get_scenario_name_from_netfile, generate_rou_file, add_params_in_rou_file
from ..config import SumoConfig

DEFAULT_CFG_FILE = "./default.sumo.cfg"


class ScenarioWrapper:
    def __init__(self):
        self.scenario_name: str = ''
        self.net_file: str = ''
        self.cr_map_file: str = ''
        self.sumo_cfg_file = None
        self.ego_start_time: int = 0
        self.sumo_net = None
        self.lanelet_network: LaneletNetwork = None
        self._route_planner = None

    def initialize(self,
                   scenario_name: str,
                   sumo_cfg_file: str,
                   cr_map_file: str,
                   ego_start_time: int = None) -> None:
        """
        Initializes the ScenarioWrapper.

        :param scenario_name: the name of the scenario
        :param sumo_cfg_file: the .sumocfg file
        :param cr_map_file: the commonroad map file
        :param ego_start_time: the start time of the ego vehicle

        """
        self.scenario_name = scenario_name
        self.sumo_cfg_file = sumo_cfg_file
        self.net_file = self._get_net_file(self.sumo_cfg_file)
        self.cr_map_file = cr_map_file
        self.ego_start_time = ego_start_time
        self.lanelet_network = CommonRoadFileReader(
            self.cr_map_file).open_lanelet_network()

    @classmethod
    def init_from_scenario(cls,
                           config: SumoConfig,
                           ego_start_time: int = None,
                           cr_map_file=None) -> 'ScenarioWrapper':
        """
        Initializes the ScenarioWrapper according to the given scenario_name/ego_start_time and returns the ScenarioWrapper.
        :param config: config file for the initialization, contain scenario_name.
        :param ego_start_time: the start time of the ego vehicle.
        :param cr_map_file: path to commonroad map, if not in scenario folder

        """
        assert isinstance(
            config,
            SumoConfig), f'Expected type SumoConfig, got {type(config)}'

        obj = cls()
        sumo_cfg_file = os.path.join(config.scenarios_path,
                                     config.scenario_name,
                                     config.scenario_name + '.sumo.cfg')
        if cr_map_file is None:
            cr_map_file = os.path.join(os.path.dirname(__file__),
                                       '../../scenarios/',
                                       config.scenario_name,
                                       config.scenario_name + '.cr.xml')

        obj.initialize(config.scenario_name, sumo_cfg_file, cr_map_file,
                       ego_start_time)
        return obj

    @classmethod
    def recreate_route_file(
            cls,
            sumo_cfg_file,
            conf: SumoConfig = SumoConfig) -> 'ScenarioWrapper':
        """
        Creates new .rou.xml file and returns ScenarioWrapper. Assumes .cr.xml, .net.xml and .sumo.cfg file have already been created in scenario folder.

        :param sumo_cfg_file:
        :param conf:

        """
        sumo_scenario = cls()
        out_folder = os.path.dirname(sumo_cfg_file)
        net_file = sumo_scenario._get_net_file(sumo_cfg_file)
        scenario_name = get_scenario_name_from_netfile(net_file)
        generate_rou_file(net_file, out_folder, conf)

        cr_map_file = os.path.join(os.path.dirname(__file__),
                                   '../../scenarios/', scenario_name,
                                   scenario_name + '.cr.xml')

        sumo_scenario.initialize(scenario_name, sumo_cfg_file, cr_map_file,
                                 conf.ego_start_time)
        return sumo_scenario

    @classmethod
    def init_from_cr_file(
        cls, cr_file, conf: SumoConfig = SumoConfig()) -> 'ScenarioWrapper':
        """
        Convert CommonRoad xml to sumo net file and return Scenario Wrapper.
        :param cr_file: path to the cr map file
        :param conf: configuration file
        :return:total length of all lanes, conversion_possible
        """
        scenario_name = get_scenario_name_from_crfile(cr_file)
        out_folder = os.path.join(conf.scenarios_path, scenario_name)
        pathlib.Path(out_folder).mkdir(parents=False, exist_ok=True)
        net_file = os.path.join(out_folder, scenario_name + '.net.xml')

        # convert from cr to net
        cr2sumo_converter = SumoConfig.from_file(
            cr_file, SumoConfig.from_dict(conf.__dict__))
        # Write final net file
        logging.info('write map to path', net_file)
        conversion_possible = cr2sumo_converter.convert_to_net_file(net_file)
        assert conversion_possible, "Conversion from cr file to net file failed!"

        return ScenarioWrapper.init_from_net_file(net_file,conf=conf)
        # # generate add file + rou file + cfg file in sumo
        # assert len(conf.ego_ids) <= conf.n_ego_vehicles,\
        #     "total number of given ego_vehicles must be <= n_ego_vehicles, but {}not<={}"\
        #     .format(len(conf.ego_ids),conf.n_ego_vehicles)
        # assert conf.n_ego_vehicles <= conf.n_vehicles_max

        # sumo_scenario = cls()

        # # create files
        # add_file = sumo_scenario.generate_add_file(scenario_name, out_folder,
        #                                            conf.veh_distribution,
        #                                            conf.veh_params,
        #                                            conf.driving_params)
        # rou_file = generate_rou_file(net_file, out_folder, conf)
        # sumo_cfg_file = sumo_scenario.generate_cfg_file(
        #     scenario_name, out_folder)

        # sumo_scenario.initialize(scenario_name, sumo_cfg_file, cr_file,
        #                          conf.ego_start_time)
        # return sumo_scenario

    @classmethod
    def init_from_net_file(
        cls,
        net_file: str,
        cr_map_path: str = None,
        conf: SumoConfig = SumoConfig()
    ) -> 'ScenarioWrapper':
        """
        Convert net file to CommonRoad xml and generate specific ego vehicle either by using generated vehicles and/or by initial states.

        :param net_file: path of .net.xml file
        :param cr_map_path: optionally specify commonroad map
        :param conf: configuration file for additional parameters
     
        """
        assert len(conf.ego_ids) <= conf.n_ego_vehicles, "total number of given ego_vehicles must be <= n_ego_vehicles, but {}not<={}"\
            .format(len(conf.ego_ids),conf.n_ego_vehicles)
        assert conf.n_ego_vehicles <= conf.n_vehicles_max

        sumo_scenario = cls()
        scenario_name = get_scenario_name_from_netfile(net_file)
        out_folder = os.path.join(conf.scenarios_path, scenario_name)
        pathlib.Path(out_folder).mkdir(parents=False, exist_ok=True)

        # create files
        if cr_map_path is None:
            cr_map_path = convert_net_to_cr(net_file, out_folder)

        add_file = sumo_scenario.generate_add_file(scenario_name, out_folder,
                                                   conf.veh_distribution,
                                                   conf.veh_params,
                                                   conf.driving_params)
        rou_file = generate_rou_file(net_file, out_folder, conf)
        sumo_cfg_file = sumo_scenario.generate_cfg_file(
            scenario_name, out_folder)

        sumo_scenario.initialize(scenario_name, sumo_cfg_file, cr_map_path,
                                 conf.ego_start_time)
        return sumo_scenario

    @staticmethod
    def generate_add_file(scenario_name: str, output_folder: str,
                          veh_distribution: dict, veh_params: dict,
                          driving_params: dict) -> str:
        """
        Generate additional file for sumo scenario to define attributes of different vehicle types.
        :param scenario_name: name of the scenario used for the cfg file generation.
        :param output_folder: the generated add file will be saved here
        :param veh_distribution: probability distribution of different vehicle types
        :param veh_params: parameters to define vehicle attributes when generating sumo traffic
        :param driving_params: parameters to influence driving behavior when generating sumo traffic
        :return: additional file
        """
        add_file = os.path.join(output_folder, scenario_name + '.add.xml')

        # create file
        domTree = minidom.Document()
        additional_node = domTree.createElement("additional")
        domTree.appendChild(additional_node)
        vType_dist_node = domTree.createElement("vTypeDistribution")
        vType_dist_node.setAttribute("id", "DEFAULT_VEHTYPE")
        additional_node.appendChild(vType_dist_node)

        for veh_type, probability in veh_distribution.items():
            if probability != 0:
                vType_node = domTree.createElement("vType")
                vType_node.setAttribute("id", veh_type)
                vType_node.setAttribute("guiShape", veh_type)
                vType_node.setAttribute("vClass", veh_type)
                vType_node.setAttribute("probability", str(probability))
                for att_name, setting in veh_params.items():
                    att_value = setting[veh_type]
                    if type(att_value) is Interval:
                        att_value = np.random.uniform(att_value.start,
                                                      att_value.end, 1)[0]
                        att_value = str("{0:.2f}".format(att_value))
                    else:
                        att_value = str(att_value)
                    vType_node.setAttribute(att_name, att_value)
                for att_name, value_interval in driving_params.items():
                    att_value = np.random.uniform(value_interval.start,
                                                  value_interval.end, 1)[0]
                    vType_node.setAttribute(att_name,
                                            str("{0:.2f}".format(att_value)))
                vType_dist_node.appendChild(vType_node)
            #     print("The probability of the vehicle type %s is %s." % (veh_type, probability))
            # else:
            #     print("The probability of the vehicle type %s is 0." % veh_type)
        fileHandle = open(add_file, "w")
        domTree.documentElement.writexml(fileHandle,
                                         addindent="    ",
                                         newl="\n")
        fileHandle.close()
        print("Additional file written to %s" % add_file)

        return add_file

    @staticmethod
    def generate_cfg_file(scenario_name: str, output_folder: str) -> str:
        """
        Generates the configuration file according to the scenario name to the specified output folder.

        :param scenario_name: name of the scenario used for the cfg file generation.
        :param output_folder: the generated cfg file will be saved here

        :return: the path of the generated cfg file.
        """

        sumo_cfg_file = os.path.join(output_folder,
                                     scenario_name + '.sumo.cfg')
        tree = et.parse(
            os.path.join(os.path.dirname(__file__), '../../',
                         DEFAULT_CFG_FILE), )
        tree.findall(
            '*/net-file')[0].attrib['value'] = scenario_name + '.net.xml'
        tree.findall(
            '*/route-files')[0].attrib['value'] = scenario_name + '.rou.xml'
        add_file = os.path.join(output_folder, scenario_name + '.add.xml')
        if os.path.exists(add_file):
            tree.findall('*/additional-files'
                         )[0].attrib['value'] = scenario_name + '.add.xml'
        for elem in tree.iter():
            if (elem.text):
                elem.text = elem.text.strip()
            if (elem.tail):
                elem.tail = elem.tail.strip()
        rough_string = et.tostring(tree.getroot(), encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        text = reparsed.toprettyxml(indent="\t", newl="\n")
        file = open(sumo_cfg_file, "w")
        file.write(text)

        return sumo_cfg_file

    def _get_net_file(self, sumo_cfg_file: str) -> str:
        """
        Gets the net file configured in the cfg file.

        :param sumo_cfg_file: SUMO config file (.sumocfg)

        :return: net-file specified in the config file
        """
        if not os.path.isfile(sumo_cfg_file):
            raise ValueError(
                "File not found: {}. Maybe scenario name is incorrect.".format(
                    sumo_cfg_file))
        tree = et.parse(sumo_cfg_file)
        file_directory = os.path.dirname(sumo_cfg_file)
        # find net-file
        all_net_files = tree.findall('*/net-file')
        if len(all_net_files) != 1:
            raise NetError(len(all_net_files))
        return os.path.join(file_directory, all_net_files[0].attrib['value'])

    def print_lanelet_net(self,
                          with_lane_id=True,
                          with_succ_pred=False,
                          with_adj=False,
                          with_speed=False) -> None:
        """
        Prints the lanelet net.

        :param with_lane_id: if true, shows the lane id.
        :param with_succ_pred: if true, shows the successors and precessors.
        :param with_adj: if true, show the adjacent lanelets.
        :param with_speed: if true, shows the speed limit of the lanelt.

        """
        plt.figure(figsize=(25, 25))
        plt.gca().set_aspect('equal')
        draw_object(self.lanelet_network)
        k = len(self.lanelet_network.lanelets)
        # add annotations
        for l in self.lanelet_network.lanelets:
            # assure that text for two different lanelets starting on same position is placed differently
            print(l.lanelet_id)
            k = k - 1
            info = ''
            if with_lane_id:
                id = 'id: ' + str(l.lanelet_id)
                plt.text(l.center_vertices[0, 0],
                         l.center_vertices[0, 1],
                         id,
                         zorder=100,
                         size=8,
                         color='r',
                         verticalalignment='top')
            if with_succ_pred:
                info = info + '\nsucc: ' + str(l.successor) + ' pred: ' + str(
                    l.predecessor)
            if with_adj:
                info = info + ' \nadj_l: ' + str(
                    l.adj_left) + '; adj_l_same_dir: ' + str(
                        l.adj_left_same_direction)
                info = info + ' \nadj_r: ' + str(
                    l.adj_right) + '; adj_r_same_dir: ' + str(
                        l.adj_right_same_direction)
            if with_speed:
                info = info + '\nspeed limit: ' + str(l.speed_limit)
            plt.plot(l.center_vertices[0, 0], l.center_vertices[0, 1], 'x')
            plt.text(l.center_vertices[0, 0],
                     l.center_vertices[0, 1],
                     info,
                     zorder=100,
                     size=8,
                     verticalalignment='top')
        plt.show()