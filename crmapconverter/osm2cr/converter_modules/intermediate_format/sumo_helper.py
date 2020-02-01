"""
This module holds the classes and methods to convert to and from sumo
"""
import os
import subprocess
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

from typing import List

from commonroad.common.util import Interval
from commonroad.scenario.traffic_sign import TrafficLightState
from commonroad.scenario.traffic_sign import TrafficSignIDGermany


def complement_traffic_light(light):
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
    state = ""
    for i in range(4):
        if i%2 == 0:
            state = state + map_traffic_light(light)
        else:
            state = state + map_traffic_light(complement_traffic_light(light))
    return state

class Sumo:
    """Class that offers functionality to convert Intermediate format to SUMO and Vice-Versa. """

    def __init__(self, map):
        self.map = map
        self._convert_net()

    def find_speedlimit(self, edge):
        default_speedlimit = -1
        if edge.traffic_signs is None or len(edge.traffic_signs) == 0:
            return default_speedlimit

        for sign in edge.traffic_signs:
            sign_obj = self.map.find_traffic_sign_by_id(sign)
            #check if maxspeed
            for element in sign_obj.traffic_sign_elements:
                if element.traffic_sign_element_id == TrafficSignIDGermany.MAXSPEED.value:
                    return element.additional_values[0]
        return default_speedlimit


    def group_edges(self, edge):
        edge_ids = set()
        edge_ids.add(edge.id)
        left_edge = edge
        right_edge = edge
        while left_edge.adjacent_left is not None and left_edge.adjacent_left_direction_equal:
            left_edge = self.map.find_edge_by_id(left_edge.adjacent_left)
            edge_ids.add(left_edge.id)

        while right_edge.adjacent_right is not None and left_edge.adjacent_right_direction_equal:
            right_edge = self.map.find_edge_by_id(right_edge.adjacent_right)
            edge_ids.add(right_edge.id)

        return edge_ids


    def _convert_net(self):
        explored_edges = set()
        explored_nodes = set()
        traffic_light_nodes = set()
        self.edges = []
        self.nodes = []
        self.traffic_lights = []
        self.types = []

        for traffic_light in self.map.traffic_lights:
            #find node id
            for node in self.map.nodes:
                if node.point.x == traffic_light.position[0] and node.point.y == traffic_light.position[1]:
                    phases = []
                    for state in traffic_light.cycle:
                        phase_state = generate_state(state.state)
                        phase = {
                            'duration': state.duration,
                            'state': phase_state
                        }
                        phases.append(phase)
                    self.traffic_lights.append({
                        'id': node.id,
                        'programID': 'myprogram' + str(node.id),
                        'offset': traffic_light.time_offset,
                        'type': 'static',
                        'phases': phases
                    })
                    traffic_light_nodes.add(node.id)

        for edge in self.map.edges:
            if edge.id in explored_edges:
                continue

            edge_ids = self.group_edges(edge)
            explored_edges = explored_edges.union(edge_ids)
            from_node = edge.node1
            to_node = edge.node2

            #find speed
            speedlimit = self.find_speedlimit(edge)
            #add type
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
                node_type = 'priority'
                if from_node.id in traffic_light_nodes:
                    node_type = 'traffic_light'
                node = {
                    'id': from_node.id,
                    'x': from_node.point.x,
                    'y': from_node.point.y,
                    'type': node_type
                }
                if from_node.id in traffic_light_nodes:
                    node.update({'type': 'traffic_light'})
                self.nodes.append(node)
                explored_nodes.add(from_node.id)

            if to_node.id not in explored_nodes:
                node_type = 'priority'
                if to_node.id in traffic_light_nodes:
                    node_type = 'traffic_light'
                node = {
                    'id': to_node.id,
                    'x': to_node.point.x,
                    'y': to_node.point.y,
                    'type': node_type
                }
                self.nodes.append(node)
                explored_nodes.add(from_node.id)

        print(self.types)
        print(self.edges)
        print(self.nodes)
        print(self.traffic_lights)

    def _write_nodes_file(self, output_path):
        """
        Functio for writing the nodes file
        :param output_path: path for the file
        :return: nothing
        """
        with open(output_path+'_nodes.nod.xml', 'w+') as output_file:
            root = ET.Element('root')
            nodes = ET.SubElement(root, 'nodes')
            for node in self.nodes:
                ET.SubElement(nodes, 'node', id=str(node['id']), x=str(node['x']),
                              y=str(node['y']), type=node['type'])   # TODO Add traffic signals
            output_str = ET.tostring(nodes, encoding='utf8', method='xml').decode("utf-8")

            reparsed = minidom.parseString(output_str)
            output_file.write(reparsed.toprettyxml(indent="\t"))
            return output_file.name

    def _write_edges_file(self, output_path):

        with open(output_path+'_edges.edg.xml', 'w+') as output_file:
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


    def _write_types_file(self, output_path):
        with open(output_path+'_type.type.xml', 'w+') as output_file:
            root = ET.Element('root')
            types = ET.SubElement(root, 'types')
            priority = 3 #TODO Set priority
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

    def _write_trafficlight_file(self, output_path):
        with open(output_path+'_traffic.xml', 'w+') as output_file:
            root = ET.Element('root')
            additional  = ET.SubElement(root, 'additional')
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


    def merge_files(self, output_path:str, scenario_name:str):
        """
        Function that merges the edges and nodes files into one using netconvert
        :param output_path: the relative path of the output
        :return: nothing
        """
        # The header of the xml files must be removed
        toRemove = ["options", "xml"]
        os.chdir(os.path.dirname(output_path))

        nodesFile = scenario_name +'_nodes.nod.xml'
        edgesFile = scenario_name +'_edges.edg.xml'
        typesFile = scenario_name +'_type.type.xml'
        output = scenario_name+'.net.xml'

        # Calling of Netconvert
        bashCommand = "netconvert " + \
                      "--node-files=" + str(nodesFile) + \
                      " --edge-files=" + str(edgesFile) + \
                      " -t=" + str(typesFile) + \
                      " --output-file=" + str(output)

        process = subprocess.call(bashCommand.split(), stdout=subprocess.PIPE)

    def write_net(self, output_path):
        """
        Function for writing the edges and nodes files in xml format
        :param output_path: the relative path of the output
        :return: nothing
        """
        scenario_name = "test"
        self._write_edges_file(output_path+"test")
        self._write_nodes_file(output_path+scenario_name)
        self._write_types_file(output_path+scenario_name)
        self._write_trafficlight_file(output_path+scenario_name)
        self.merge_files(output_path, scenario_name)
        self.generate_rou_file(output_path+scenario_name+".net.xml", scenario_name, 1, 50, Interval(0, 2000), 1, 0)

        #self._write_connections_file(output_path)

    def generate_rou_file(self,net_file: str, scenario_name, dt: float, n_vehicles_max: int, departure_time: Interval,
                          n_ego_vehicles: int, departure_time_ego: int, ego_ids: List[int] = None,
                          veh_per_second: float = None, out_folder: str = None) -> str:
        """
        Creates route & trips files using randomTrips generator.

        :param net_file: path of .net.xml file
        :param dt: length of the time step
        :param n_vehicles_max: max. number of vehicles in route file
        :param departure_time: Interval of departure times for vehicles
        :param n_ego_vehicles: number of ego vehicles
        :param departure_time_ego: desired departure time ego vehicle
        :param ego_ids: if desired ids of ego_vehicle known, specify here
        :param veh_per_second: number of vehicle departures per second
        :param out_folder: output folder of route file (same as net_file if None)

        :return: path of route file
        """
        if out_folder is None:
            out_folder = os.path.dirname(net_file)

        # vehicles per second
        if veh_per_second is not None:
            period = 1 / (veh_per_second * dt)
        else:
            period = 1

        # filenames
        rou_file = os.path.join(out_folder, scenario_name + '.rou.xml')
        trip_file = os.path.join(out_folder, scenario_name + '.trips.xml')

        # create route file
        step_per_departure = ((departure_time.end - departure_time.start) / n_vehicles_max)
        try:
            subprocess.check_output(
                ['python', os.path.join(os.environ['SUMO_HOME'], 'tools/randomTrips.py'), '-n', net_file,
                 '-e', "50" #, '-p', str(step_per_departure), '--allow-fringe',
                 # '--vehicle-class', str('passenger'),
                 # '--trip-attributes=departLane=\"free\" departSpeed=\"random\" departPos=\"base\"',
                 # '--period', str(period) #'--fringe-factor', str(fringe_factor)
                 ])
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        config_file = os.path.join(out_folder,'config.sumocfg')  #TODO Dynamic
        try:
            subprocess.check_output(
                ['duarouter', '-c', config_file,
                 '-o', rou_file
                 ])
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        # get ego ids and add EGO_ID_START prefix
        # ego_ids = find_ego_ids_by_departure_time(rou_file, n_ego_vehicles, departure_time_ego, ego_ids)
        # write_ego_ids_to_rou_file(rou_file, ego_ids)

        return rou_file