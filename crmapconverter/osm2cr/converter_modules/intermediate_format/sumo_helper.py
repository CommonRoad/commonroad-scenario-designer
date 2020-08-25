"""
This module holds the classes and methods to convert to and from sumo
"""
__author__ = "Behtarin Ferdousi"

import os
import subprocess
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from typing import Set

from commonroad.scenario.traffic_sign import TrafficLightState
from commonroad.scenario.traffic_sign import TrafficSignIDGermany

# SUMO SAVE Files
SUMO_SAVE_FILE = 'files/sumo/'


def complement_traffic_light(light: TrafficLightState) -> TrafficLightState:
    """
    Return the complement of the traffic light state

    :param light: TrafficLightState
    :return: complement TrafficLightState
    """
    light = light.value
    if light == TrafficLightState.RED.value:
        return TrafficLightState.GREEN
    if light == TrafficLightState.GREEN.value:
        return TrafficLightState.RED
    if light == TrafficLightState.RED_YELLOW.value:
        return TrafficLightState.YELLOW
    if light == TrafficLightState.YELLOW.value:
        return TrafficLightState.RED_YELLOW


def map_traffic_light(light):
    """
    Map TrafficLightState to Sumo Traffic Light

    :param light: TrafficLightState
    :return: r,g, u or y
    """
    light = light.value
    if light == TrafficLightState.RED.value:
        return 'r'
    if light == TrafficLightState.GREEN.value:
        return 'g'
    if light == TrafficLightState.RED_YELLOW.value:
        return 'u'
    if light == TrafficLightState.YELLOW.value:
        return 'y'


def generate_state(light):
    """
    Generate traffic light phases on an intersection with 4 incomings

    :param light: TrafficLightState
    :return: str
    """
    state = ""
    for i in range(4):
        if i%2 == 0:
            state = state + map_traffic_light(light)
        else:
            state = state + map_traffic_light(complement_traffic_light(light))
    return state


class Sumo:
    """Class that offers functionality to convert Intermediate Format to SUMO
    and Vice-Versa. """

    def __init__(self, map,
                 path= SUMO_SAVE_FILE,
                 scenario_name="generated"):
        """
        Convert the data in map to format for Sumo
        :param map: map in the form of Intermediate Format
        :param path: Path to save the files
        :param scenario_name: Scenario Name for the file names
        """
        self.map = map
        self.path = path
        self.scenario_name = scenario_name

        self.node_file = ""
        self.edge_file = ""
        self.type_file = ""
        self.config_file = ""
        self.net_file = ""
        self.trip_file = ""
        self.route_file = ""

        # Default red and yellow light for traffic light
        self.red_light_duration = 60
        self.yellow_light_duration = 10

        # Generate network file for the map
        self._convert_net()

    def find_speedlimit(self, edge) -> float:
        """
        Find the speedlimit on the edge by traffic signs

        :param edge: Edge in Intermediate Format
        :return:
        """
        default_speedlimit = -1
        if edge.traffic_signs is None or len(edge.traffic_signs) == 0:
            return default_speedlimit

        for sign in edge.traffic_signs:
            sign_obj = self.map.find_traffic_sign_by_id(sign)

            # check if maxspeed sign
            for element in sign_obj.traffic_sign_elements:
                if element.traffic_sign_element_id == TrafficSignIDGermany.MAXSPEED.value: # TODO MAX_SPEED
                    return element.additional_values[0]

        return default_speedlimit

    def group_edges(self, edge) -> Set[int]:
        """
        Group multiple lanes into one edge for Sumo

        :param edge: Edge in Intermediate Format
        :return: edge ids of the grouped edges
        """
        edge_ids = set()
        edge_ids.add(edge.id)
        left_edge = edge
        right_edge = edge
        while left_edge.adjacent_left is not None and \
                left_edge.adjacent_left_direction_equal:
            left_edge = self.map.find_edge_by_id(left_edge.adjacent_left)
            edge_ids.add(left_edge.id)

        while right_edge.adjacent_right is not None and \
                left_edge.adjacent_right_direction_equal:
            right_edge = self.map.find_edge_by_id(right_edge.adjacent_right)
            edge_ids.add(right_edge.id)

        return edge_ids

    def add_node(self, node, is_traffic_light):
        """
        Add Intermediate Format Node to the sumo nodes

        :param node:
        :param is_traffic_light:
        """
        # Default type
        node_type = 'priority'

        if is_traffic_light:
            node_type = 'traffic_light'
        node = {
            'id': node.id,
            'x': node.point.x,
            'y': node.point.y,
            'type': node_type
        }
        self.nodes.append(node)

    def _convert_net(self):
        """
        Extract nodes, edges and types for SUMO Format
        """
        explored_edges = set()
        explored_nodes = set()
        traffic_light_nodes = set()

        self.edges = []
        self.nodes = []
        self.traffic_lights = []
        self.types = []

        # Find Nodes with Traffic Light
        for traffic_light in self.map.traffic_lights:
            #find node id
            for node in self.map.nodes:
                if node.point.x == traffic_light.position[0] and \
                        node.point.y == traffic_light.position[1]:
                    # TODO Generate traffic lights from States
                    traffic_light_nodes.add(node.id)

        for edge in self.map.edges:
            if edge.id in explored_edges:
                continue

            edge_ids = self.group_edges(edge)
            explored_edges = explored_edges.union(edge_ids)
            from_node = edge.node1
            to_node = edge.node2

            # find speedlimit
            speedlimit = self.find_speedlimit(edge)

            # add type
            new_type = {
                'id': f'{len(edge_ids)}L{int(speedlimit)}',
                'numLanes': len(edge_ids),
            }

            if speedlimit >= 0:
                new_type['speed'] = speedlimit

            self.types.append(new_type)

            self.edges.append({
                'id': edge.id,
                'from': from_node.id,
                'to': to_node.id,
                'type': new_type['id']
            })

            if from_node.id not in explored_nodes:
                self.add_node(from_node, from_node.id in traffic_light_nodes)
                explored_nodes.add(from_node.id)

            if to_node.id not in explored_nodes:
                self.add_node(to_node, to_node.id in traffic_light_nodes)
                explored_nodes.add(from_node.id)

    def _write_nodes_file(self) -> str:
        """
        Write the nodes in xml file

        :return: node xml file path
        """
        output = self.path+self.scenario_name+'_nodes.nod.xml'
        with open(output, 'w+') as output_file:
            root = ET.Element('root')
            nodes = ET.SubElement(root, 'nodes')
            for node in self.nodes:
                ET.SubElement(nodes, 'node', id=str(node['id']), x=str(node['x']),
                              y=str(node['y']), type=node['type'])
            output_str = ET.tostring(nodes, encoding='utf8', method='xml').decode("utf-8")

            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return output

    def _write_edges_file(self) -> str:
        """
        Write edges in  xml file for Sumo

        :return: path to the edges file
        """
        output = self.path+self.scenario_name+'_edges.edg.xml'
        with open(output, 'w+') as output_file:
            root = ET.Element('root')
            edges = ET.SubElement(root, 'edges')
            for edge in self.edges:
                edge_et = ET.SubElement(edges, 'edge')
                edge_et.set('from', str(edge['from']))
                edge_et.set('id', str(edge['id']))
                edge_et.set('to', str(edge['to']))
                edge_et.set('type', str(edge['type']))
            output_str = ET.tostring(edges, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return output

    def _write_types_file(self) -> str:
        """
        Write Type File

        :return: path to the types file
        """
        output = self.path+self.scenario_name+'_types.type.xml'
        with open(output, 'w+') as output_file:
            root = ET.Element('root')
            types = ET.SubElement(root, 'types')
            priority = 3 # TODO Set priority
            for type in self.types:
                type_et = ET.SubElement(types, 'type')
                type_et.set('id', str(type['id']))
                type_et.set('numLanes', str(type['numLanes']))
                if 'speed' in type:
                    type_et.set('speed', str(type['speed']))
                type_et.set('priority', str(priority))
            output_str = ET.tostring(types, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return output

    def _write_trafficlight_file(self) -> str:
        """
        Write Traffic Light File

        :return: path to the traffic file
        """
        output = self.path+self.scenario_name+'_traffic.xml'
        with open(output, 'w+') as output_file:
            root = ET.Element('root')
            additional = ET.SubElement(root, 'additional')
            for traffic_light in self.traffic_lights:
                traffic_light_et = ET.SubElement(additional, 'tlLogic')
                traffic_light_et.set('id', str(traffic_light['id']))
                traffic_light_et.set('programID', traffic_light['programID'])
                traffic_light_et.set('offset', str(traffic_light['offset']))
                traffic_light_et.set('type', traffic_light['type'])
                for phase in traffic_light['phases']:
                    phase_et = ET.SubElement(traffic_light_et, 'phase')
                    phase_et.set('duration', str(phase['duration']))
                    phase_et.set('state', str(phase['state']))
            output_str = ET.tostring(additional, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return output

    def _merge_files(self) -> str:
        """
        Function that merges the edges and nodes files into one using netconvert

        :return: path to the net file
        """
        output = self.path+self.scenario_name+'_net.net.xml'

        # Calling of Netconvert
        bashCommand = "netconvert " + \
                      "--node-files=" + str(self.node_file) + \
                      " --edge-files=" + str(self.edge_file) + \
                      " -t=" + str(self.type_file) + \
                      " --tls.red.time=" + str(self.red_light_duration) + \
                      " --tls.yellow.time=" + str(self.yellow_light_duration) +\
                      " --output-file=" + str(output)

        process = subprocess.call(bashCommand.split(), stdout=subprocess.PIPE)
        return output

    def write_net(self) -> str:
        """
        Function for writing the edges and nodes files in xml format

        :return: path to the net file
        """
        self.edge_file = self._write_edges_file()
        self.node_file = self._write_nodes_file()
        self.type_file = self._write_types_file()
        self.net_file = self._merge_files()
        return self.net_file

    def write_config_file(self, begin_time, end_time) -> str:
        """
        Write the Config file for Sumo
        :param begin_time: begin time for the simulation
        :param end_time: end time for the simulation
        :return: path to the config file
        """
        self.config_file = self.path+self.scenario_name+"_config.sumocfg"
        with open(self.config_file, 'w+') as output_file:
            root = ET.Element('root')
            configuration = ET.SubElement(root, 'configuration')
            input_et = ET.SubElement(configuration, 'input')
            # Add net file and trip file
            net_file_et = ET.SubElement(input_et, 'net-file')
            net_file_et.set('value', self.scenario_name+'_net.net.xml')

            trip_file_et = ET.SubElement(input_et, 'route-files')
            trip_file_et.set("value", self.scenario_name+'_trip.trips.xml')

            # Add Time
            time_et = ET.SubElement(configuration, 'time')
            begin_time_et = ET.SubElement(time_et, 'begin')
            begin_time_et.set('value', str(begin_time))

            end_time_et = ET.SubElement(time_et, 'end')
            end_time_et.set('value', str(end_time))
            output_str = ET.tostring(configuration, encoding='utf8', method='xml').decode("utf-8")
            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return self.config_file

    def generate_trip_file(self, begin_time, end_time) -> str:
        """
        Create Trip File using RandomTrips in Sumo
        :param begin_time: begin time of trips
        :param end_time: end Time of the trips
        :return: path to the trip file
        """
        if self.net_file == "":
            print("You need to write net file first")
            return ""

        trip_file = self.path + self.scenario_name + '_trip.trips.xml'
        try:
            subprocess.check_output(
                ['python',
                 os.path.join(os.environ['SUMO_HOME'], 'tools/randomTrips.py'),
                 '-n', self.net_file,
                 '-b', str(begin_time),
                 '-e', str(end_time),
                 '-o', trip_file
                 ])
            self.trip_file = trip_file
            return trip_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "Command '{}' return with error (code {}): {}".format(e.cmd,
                                                                      e.returncode,
                                                                      e.output))

    def generate_route_file(self) -> str:
        """
        Create Route File using DuaRouter
        :return: path to the generated route file
        """
        # filenames
        rou_file = os.path.join(self.path+self.scenario_name + '_routes.rou.xml')

        try:
            subprocess.check_output(
                ['duarouter', '-c', self.config_file,
                 '-o', rou_file
                 ])
            self.route_file = rou_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Command '{}' return with error (code {}): {}".
                               format(e.cmd, e.returncode, e.output))

        return rou_file
