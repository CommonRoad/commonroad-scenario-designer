import os
import subprocess
import warnings

import sumolib

from copy import deepcopy
from typing import Dict, List
from xml.dom import minidom
from xml.etree import ElementTree as et
import numpy as np

from commonroad.geometry.shape import Polygon
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad_cc.collision_detection.pycrcc_collision_dispatch import create_collision_object

# try:
#     import pycrcc
#     use_pycrcc = True
# except ModuleNotFoundError:
#     warnings.warn('Commonroad Collision Checker not installed, use shapely instead (slower).')
#     import shapely as shl
#    use_pycrcc = False
use_pycrcc = False


from ..config import SumoConfig, EGO_ID_START



def find_ego_ids_by_departure_time(rou_file: str, n_ego_vehicles: int,
                                   departure_time_ego: int,
                                   ego_ids: list) -> list:
    """
    Returns ids of vehicles from route file which match desired departure time as close as possible.

    :param rou_file: path of route file
    :param n_ego_vehicles:  number of ego vehicles
    :param departure_time_ego: desired departure time ego vehicle
    :param ego_ids: if desired ids of ego_vehicle known, specify here

    """
    vehicles = sumolib.output.parse_fast(rou_file, 'vehicle', ['id', 'depart'])
    dep_times = []
    veh_ids = []
    for veh in vehicles:
        veh_ids.append(veh[0])
        dep_times.append(int(float(veh[1])))

    if n_ego_vehicles > len(veh_ids):
        warnings.warn('only {} vehicles in route file instead of {}'.format(
            len(veh_ids), n_ego_vehicles),
                      stacklevel=1)
        n_ego_vehicles = len(veh_ids)

    # check if specified ids exist
    for i in ego_ids:
        if i not in veh_ids:
            warnings.warn(
                '<generate_rou_file> id {} not in route file!'.format_map(i))
            del i

    # assign vehicles as ego by finding closest departure time
    dep_times = np.array(dep_times)
    veh_ids = np.array(veh_ids)
    greater_start_time = np.where(dep_times >= departure_time_ego)[0]
    for index in greater_start_time:
        if len(ego_ids) == n_ego_vehicles:
            break
        else:
            ego_ids.append(veh_ids[index])

    if len(ego_ids) < n_ego_vehicles:
        n_ids_missing = n_ego_vehicles - len(ego_ids)
        ego_ids.extend((veh_ids[greater_start_time[0] -
                                n_ids_missing:greater_start_time[0]]).tolist())

    return ego_ids


def get_scenario_name_from_crfile(filepath: str) -> str:
    """
    Returns the scenario name specified in the cr file.

    :param filepath: the path of the cr file

    """
    scenario_name: str = (os.path.splitext(
        os.path.basename(filepath))[0]).split('.')[0]
    return scenario_name


def get_scenario_name_from_netfile(filepath: str) -> str:
    """
    Returns the scenario name specified in the net file.

    :param filepath: the path of the net file

    """
    scenario_name: str = (os.path.splitext(
        os.path.basename(filepath))[0]).split('.')[0]
    return scenario_name


def get_boundary_from_netfile(filepath: str) -> list:
    """
    Get the boundary of the netfile.
    :param filepath:
    :return: boundary as a list containing min_x, max_x, min_y, max_y coordinates
    """
    tree = et.parse(filepath)
    root = tree.getroot()
    location = root.find("location")
    boundary_list = location.attrib['origBoundary']  # origBoundary
    min_x, min_y, max_x, max_y = boundary_list.split(',')
    boundary = [float(min_x), float(max_x), float(min_y), float(max_y)]
    return boundary


def get_total_lane_length_from_netfile(filepath: str) -> float:
    """
    Compute the total length of all lanes in the net file.
    :param filepath:
    :return: float value of the total lane length
    """
    tree = et.parse(filepath)
    root = tree.getroot()
    total_lane_length = 0
    for lane in root.iter('lane'):
        total_lane_length += float(lane.get('length'))
    return total_lane_length


def generate_rou_file(net_file: str,
                      out_folder: str = None,
                      conf: SumoConfig = SumoConfig()) -> str:
    """
    Creates route & trips files using randomTrips generator.

    :param net_file: path of .net.xml file
    :param total_lane_length: total lane length of the network
    :param out_folder: output folder of route file (same as net_file if None)
    :param conf: configuration file for additional parameters
    :return: path of route file
    """
    if out_folder is None:
        out_folder = os.path.dirname(net_file)

    total_lane_length = get_total_lane_length_from_netfile(net_file)
    if total_lane_length is not None:
        # calculate period based on traffic frequency depending on map size
        period = 1 / (conf.max_veh_per_km *
                      (total_lane_length / 1000) * conf.dt)
        print(
            'SUMO traffic generation: traffic frequency is defined based on the total lane length of the road network.'
        )
    elif conf.veh_per_second is not None:
        # vehicles per second
        period = 1 / (conf.veh_per_second * conf.dt)
        print(
            'SUMO traffic generation: the total_lane_length of the road network is not available. '
            'Traffic frequency is defined based on equidistant depature time.')
    else:
        period = 0.5
        print(
            'SUMO traffic generation: neither total_lane_length nor veh_per_second is defined. '
            'For each second there are two vehicles generated.')
    #step_per_departure = ((conf.departure_interval_vehicles.end - conf.departure_interval_vehicles.start) / n_vehicles_max)

    # filenames
    scenario_name = get_scenario_name_from_netfile(net_file)
    rou_file = os.path.join(out_folder, scenario_name + '.rou.xml')
    trip_file = os.path.join(out_folder, scenario_name + '.trips.xml')
    add_file = os.path.join(out_folder, scenario_name + '.add.xml')

    # create route file
    cmd = [
        'python',
        os.path.join(os.environ['SUMO_HOME'], 'tools/randomTrips.py'), '-n',
        net_file, '-o', trip_file, '-r', rou_file, '-b',
        str(conf.departure_interval_vehicles.start), '-e',
        str(conf.departure_interval_vehicles.end), '-p',
        str(period), '--allow-fringe', '--fringe-factor',
        str(conf.fringe_factor),
        '--trip-attributes=departLane=\"best\" departSpeed=\"max\" departPos=\"base\" '
    ]
    # if os.path.isfile(add_file):
    #     cmd.extend(['--additional-files', add_file])

    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Command '{}' return with error (code {}): {}".format(
                e.cmd, e.returncode, e.output))

    if conf.n_ego_vehicles != 0:
        #get ego ids and add EGO_ID_START prefix
        ego_ids = find_ego_ids_by_departure_time(rou_file, conf.n_ego_vehicles,
                                                 conf.departure_time_ego,
                                                 conf.ego_ids)
        write_ego_ids_to_rou_file(rou_file, ego_ids)

    return rou_file


def add_params_in_rou_file(
        rou_file: str,
        driving_params: dict = SumoConfig.driving_params) -> None:
    """
    Add parameters for the vType setting in the route file generated by SUMO. Parameters are sampled from uniform distribution.
    :param rou_file: the route file to be modified
    :param driving_params: dictionary with driving parameter as keys and interval of sampling as values
    :return:
    """
    tree = et.parse(rou_file)
    root = tree.getroot()
    vType = root.find("vType")
    if vType is not None:
        for key, value_interval in driving_params.items():
            random_value = np.random.uniform(value_interval.start,
                                             value_interval.end, 1)[0]
            vType.set(key, str("{0:.2f}".format(random_value)))
    tree.write(rou_file)


def write_ego_ids_to_rou_file(rou_file: str, ego_ids: List[int]) -> None:
    """
    Writes ids of ego vehicles to the route file.

    :param rou_file: the route file
    :param ego_ids: a list of ego vehicle ids

    """
    tree = et.parse(rou_file)
    vehicles = tree.findall('vehicle')
    ego_str = {}
    for ego_id in ego_ids:
        ego_str.update({str(ego_id): EGO_ID_START + str(ego_id)})

    for veh in vehicles:
        if veh.attrib['id'] in ego_str:
            veh.attrib['id'] = ego_str[veh.attrib['id']]

    for elem in tree.iter():
        if (elem.text):
            elem.text = elem.text.strip()
        if (elem.tail):
            elem.tail = elem.tail.strip()
    rough_string = et.tostring(tree.getroot(), encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    text = reparsed.toprettyxml(indent="\t", newl="\n")
    file = open(rou_file, "w")
    file.write(text)


def compute_max_curvature_from_polyline(polyline: np.ndarray) -> float:
    """
    Computes the curvature of a given polyline
    :param polyline: The polyline for the curvature computation
    :return: The pseudo maximum curvature of the polyline
    """
    assert isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(
        polyline[:, 0]
    ) >= 2, 'Polyline malformed for curvature computation p={}'.format(
        polyline)
    x_d = np.gradient(polyline[:, 0])
    x_dd = np.gradient(x_d)
    y_d = np.gradient(polyline[:, 1])
    y_dd = np.gradient(y_d)

    # compute curvature
    curvature = (x_d * y_dd - x_dd * y_d) / ((x_d**2 + y_d**2)**(3. / 2.))

    # compute maximum curvature
    abs_curvature = [abs(ele) for ele in curvature]  # absolute value
    max_curvature = max(abs_curvature)

    # compute pseudo maximum -- mean of the two largest curvatures --> relax the constraint
    abs_curvature.remove(max_curvature)
    second_max_curvature = max(abs_curvature)
    max_curvature = (max_curvature + second_max_curvature) / 2

    return max_curvature


def _erode_lanelets(lanelet_network: LaneletNetwork,
                    radius: float = 0.4) -> LaneletNetwork:
    """Erode shape of lanelet by given radius."""

    lanelets_ero = []
    crop_meters = 0.3
    min_factor = 0.1
    for lanelet in lanelet_network.lanelets:
        lanelet_ero = deepcopy(lanelet)

        # shorten lanelet by radius
        if len(lanelet_ero._center_vertices) > 4:
            i_max = int(
                (np.floor(len(lanelet_ero._center_vertices) - 1) / 2)) - 1

            i_crop_0 = np.argmax(lanelet_ero.distance >= crop_meters)
            i_crop_1 = len(lanelet_ero.distance) - np.argmax(
                lanelet_ero.distance >= lanelet_ero.distance[-1] - crop_meters)
            i_crop_0 = min(i_crop_0, i_max)
            i_crop_1 = min(i_crop_1, i_max)

            lanelet_ero._left_vertices = lanelet_ero._left_vertices[
                i_crop_0:-i_crop_1]
            lanelet_ero._center_vertices = lanelet_ero._center_vertices[
                i_crop_0:-i_crop_1]
            lanelet_ero._right_vertices = lanelet_ero._right_vertices[
                i_crop_0:-i_crop_1]
        else:
            factor_0 = min(1, crop_meters / lanelet_ero.distance[1])
            lanelet_ero._left_vertices[0] = factor_0 * lanelet_ero._left_vertices[0]\
                                            + (1-factor_0) * lanelet_ero._left_vertices[1]
            lanelet_ero._right_vertices[0] = factor_0 * lanelet_ero._right_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._right_vertices[1]
            lanelet_ero._center_vertices[0] = factor_0 * lanelet_ero._center_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._center_vertices[1]

            factor_0 = min(
                1, crop_meters /
                (lanelet_ero.distance[-1] - lanelet_ero.distance[-2]))
            lanelet_ero._left_vertices[-1] = factor_0 * lanelet_ero._left_vertices[-2] \
                                            + (1 - factor_0) * lanelet_ero._left_vertices[-1]
            lanelet_ero._right_vertices[-1] = factor_0 * lanelet_ero._right_vertices[-2] \
                                             + (1 - factor_0) * lanelet_ero._right_vertices[-1]
            lanelet_ero._center_vertices[-1] = factor_0 * lanelet_ero._center_vertices[-2] \
                                              + (1 - factor_0) * lanelet_ero._center_vertices[-1]

        # compute eroded vector from center
        perp_vecs = (lanelet_ero.left_vertices -
                     lanelet_ero.right_vertices) * 0.5
        length = np.linalg.norm(perp_vecs, axis=1)
        factors = np.divide(radius, length)  # 0.5 * np.ones_like(length))
        factors = np.reshape(factors, newshape=[-1, 1])
        factors = 1 - np.maximum(
            factors,
            np.ones_like(factors) *
            min_factor)  # ensure minimum width of eroded lanelet
        perp_vec_ero = np.multiply(perp_vecs, factors)

        # recompute vertices
        lanelet_ero._left_vertices = lanelet_ero.center_vertices + perp_vec_ero
        lanelet_ero._right_vertices = lanelet_ero.center_vertices - perp_vec_ero
        if lanelet_ero._polygon is not None:
            lanelet_ero._polygon = Polygon(
                np.concatenate((lanelet_ero.right_vertices,
                                np.flip(lanelet_ero.left_vertices, 0))))
        lanelets_ero.append(lanelet_ero)

    return LaneletNetwork.create_from_lanelet_list(lanelets_ero)


def _find_intersecting_edges(
        edges_dict: Dict[int, List[int]],
        lanelet_network: LaneletNetwork) -> List[List[int]]:
    """

    :param lanelet_network:
    :return:
    """
    eroded_lanelet_network = _erode_lanelets(lanelet_network)
    polygons_dict = {}
    edge_shapes_dict = {}
    for edge_id, lanelet_ids in edges_dict.items():
        edge_shape = []
        for lanelet_id in (lanelet_ids[0], lanelet_ids[-1]):
            if lanelet_id not in polygons_dict:
                polygon = eroded_lanelet_network.find_lanelet_by_id(
                    lanelet_id).convert_to_polygon()

                if use_pycrcc:
                    polygons_dict[lanelet_id] = create_collision_object(
                        polygon)
                else:
                    polygons_dict[lanelet_id] = polygon.shapely_object

                edge_shape.append(polygons_dict[lanelet_id])

        edge_shapes_dict[edge_id] = edge_shape

    intersecting_edges = []
    for edge_id, shape_list in edge_shapes_dict.items():
        for edge_id_other, shape_list_other in edge_shapes_dict.items():
            if edge_id == edge_id_other: continue
            edges_intersect = False
            for shape_0 in shape_list:
                if edges_intersect: break
                for shape_1 in shape_list_other:
                    if use_pycrcc:
                        if shape_0.collide(shape_1):
                            edges_intersect = True
                            intersecting_edges.append([edge_id, edge_id_other])
                            break
                    else:
                        # shapely
                        if shape_0.intersection(shape_1).area > 0.0:
                            edges_intersect = True
                            intersecting_edges.append([edge_id, edge_id_other])
                            break

    return intersecting_edges
