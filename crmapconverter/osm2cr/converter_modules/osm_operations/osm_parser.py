"""
This module provides all methods to parse an OSM file and convert it to a graph.
It also provides a method to project OSM nodes to cartesian coordinates.
"""
import xml.etree.ElementTree as ElTree
from typing import List, Dict, Tuple, Set, Optional

import numpy as np

from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.graph_operations import road_graph as rg
from crmapconverter.osm2cr.converter_modules.graph_operations.restrictions import (
    Restriction,
)
from crmapconverter.osm2cr.converter_modules.osm_operations import info_deduction as i_d
from crmapconverter.osm2cr.converter_modules.utility import idgenerator
from crmapconverter.osm2cr.converter_modules.utility.custom_types import Road_info
from crmapconverter.osm2cr.converter_modules.utility.geometry import (
    Point,
    is_corner,
    Area,
    lon_lat_to_cartesian,
)


def read_custom_bounds(root) -> Optional[Tuple[float, float, float, float]]:
    bounds = None
    for bound in root.findall("custom_bounds"):
        bounds = (
            bound.attrib["lat2"],
            bound.attrib["lon1"],
            bound.attrib["lat1"],
            bound.attrib["lon2"],
        )
        bounds = tuple(float(value) for value in bounds)
    return bounds


def get_points(
    nodes: Dict[int, ElTree.Element], custom_bounds=None
) -> Tuple[Dict[int, Point], Tuple[float, float], Tuple[float, float, float, float]]:
    """
    projects a set of osm nodes on a plane and returns their positions on that plane als Points

    :param custom_bounds:
    :param nodes: dict of osm nodes
    :type nodes: Dict[int, ElTree.Element]
    :return: dict of points
    :rtype: Dict[int, Point]
    """
    if len(nodes) < 1:
        raise ValueError("Map is empty")
    ids = []
    lons = []
    lats = []
    for id, node in nodes.items():
        ids.append(id)
        lons.append(float(node.attrib["lon"]))
        lats.append(float(node.attrib["lat"]))
    if custom_bounds is not None:
        bounds = custom_bounds
    else:
        bounds = max(lats), min(lons), min(lats), max(lons)
    assert bounds[0] >= bounds[2]
    assert bounds[3] >= bounds[1]
    lon_center = (bounds[1] + bounds[3]) / 2
    lat_center = (bounds[0] + bounds[2]) / 2
    # print(bounds)
    # lon_center = (min(lons) + max(lons)) / 2
    # lat_center = (min(lats) + max(lats)) / 2
    lons = np.array(lons)
    lats = np.array(lats)
    lons_d = lons - lon_center
    lats_d = lats - lat_center
    points = {}
    lon_constants = np.pi / 180 * config.EARTH_RADIUS * np.cos(np.radians(lats))
    x = lon_constants * lons_d
    lat_constant = np.pi / 180 * config.EARTH_RADIUS
    y = lat_constant * lats_d
    for index, id in enumerate(ids):
        points[id] = Point(id, x[index], y[index])
    print("{} required nodes found".format(len(points)))
    center_point = lat_center, lon_center
    return points, center_point, bounds


def get_nodes(roads: Set[ElTree.Element], root) -> Dict[int, ElTree.Element]:
    node_ids = set()
    for road in roads:
        nodes = road.findall("nd")
        for node in nodes:
            current_id = node.attrib["ref"]
            node_ids.add(current_id)
    nodes = root.findall("node")
    road_nodes = {}
    for node in nodes:
        if node.attrib["id"] in node_ids:
            road_nodes[node.attrib["id"]] = node
    assert len(road_nodes) == len(node_ids)
    return road_nodes


def get_traffic_rules(nodes: Dict[int, ElTree.Element], roads: Dict[int, ElTree.Element],
                      accepted_traffic_sign_by_keys: List[str],
                      accepted_traffic_sign_by_values: List[str]) -> Dict:
    traffic_rules = {}
    for node_id in nodes:
        node = nodes[node_id]
        tags = node.findall('tag')
        for tag in tags:
            if tag.attrib['k'] in accepted_traffic_sign_by_keys or tag.attrib['v'] in accepted_traffic_sign_by_values:
                key = tag.attrib['k']
                value = tag.attrib['v']
                virtual = None
                if key == 'maxspeed':
                    value, virtual = extract_speedlimit(value)
                sign = {key: value, 'virtual': virtual}
                if node_id in traffic_rules:
                    traffic_rules[node_id].update(sign)
                else:
                    traffic_rules.update({node_id: sign})

    for road in roads:
        road_id = road.attrib['id']
        tags = road.findall('tag')
        for tag in tags:
            if tag.attrib['k'] in accepted_traffic_sign_by_keys or tag.attrib['v'] in accepted_traffic_sign_by_values:
                key = tag.attrib['k']
                value = tag.attrib['v']
                virtual= None
                if key == 'maxspeed':
                    value, virtual = extract_speedlimit(value)
                sign = {key: value, 'virtual': virtual}
                # check if traffic rule exists
                nodes = road.findall("nd")
                added = False
                for node in nodes:
                    if not added:
                        node_id = node.attrib['ref']
                        if node_id in traffic_rules  \
                                and key in traffic_rules[node_id].keys() and traffic_rules[node_id][key] == value:
                            # if already other roads exist
                            if 'road_id' in traffic_rules[node_id].keys():
                                traffic_rules[node_id]['road_id'].append(road_id)
                            else:
                                traffic_rules[node_id].update({'road_id': [road_id]})
                            added = True
                if not added:
                    sign['road_id'] = road_id
                    sign['virtual'] = True
                    traffic_rules.update({'road'+road_id: sign})


    return traffic_rules


def get_traffic_signs_and_lights(traffic_rules: Dict) -> (List, List):
    traffic_lights = []
    traffic_signs = []
    for node_id in traffic_rules:
        rule = traffic_rules[node_id]
        if 'traffic_sign' in rule.keys() or 'maxspeed' in rule.keys() or 'overtaking' in rule.keys():
            traffic_signs.append({node_id: rule})
        else:
            traffic_lights.append({node_id: rule})
    return traffic_signs, traffic_lights


def parse_restrictions(
    restrictions: Set[ElTree.Element]
) -> Dict[int, Set[Restriction]]:
    """
    parses a set of restrictions in tree form to restriction objects

    :param restrictions:
    :return:
    """
    result = {}
    for restriction_element in restrictions:
        from_edge_id, to_edge_id, via_element_id, via_element_type = (
            None,
            None,
            None,
            None,
        )
        restriction = restriction_element.attrib["restriction"]
        for member in restriction_element.findall("member"):
            if member.attrib["role"] == "from":
                from_edge_id = member.attrib["ref"]
            if member.attrib["role"] == "to":
                to_edge_id = member.attrib["ref"]
            if member.attrib["role"] == "via":
                via_element_id = member.attrib["ref"]
                via_element_type = member.attrib["type"]

        if None not in [from_edge_id, to_edge_id, via_element_id, via_element_type]:
            restriction_object = Restriction(
                from_edge_id, via_element_id, via_element_type, to_edge_id, restriction
            )
            if from_edge_id in result:
                result[from_edge_id].add(restriction_object)
            else:
                result[from_edge_id] = {restriction_object}
    return result


def get_restrictions(root) -> Dict[int, Set[Restriction]]:
    """
    finds restrictions in osm file and returns it as dict mapping from from_edge to restriction object

    :param root:
    :return:
    """
    restrictions = set()
    relations = root.findall("relation")
    for relation in relations:
        tags = relation.findall("tag")
        for tag in tags:
            if tag.attrib["k"] == "type" and tag.attrib["v"] == "restriction":
                restrictions.add(relation)
            if tag.attrib["k"] == "restriction":
                relation.set("restriction", tag.attrib["v"])
    restrictions = parse_restrictions(restrictions)
    return restrictions


def get_roads(accepted_highways: List[str], root) -> Set[ElTree.Element]:
    """
    finds roads of desired types in osm file

    :param accepted_highways:
    :param root:
    :return:
    """
    roads = set()
    ways = root.findall("way")
    for way in ways:
        is_road = False
        is_tunnel = False
        tags = way.findall("tag")
        has_maxspeed = False
        roadtype = None
        for tag in tags:
            if tag.attrib["k"] == "highway" and tag.attrib["v"] in accepted_highways:
                way.set("roadtype", tag.attrib["v"])
                roadtype = tag.attrib["v"]
                nodes = way.findall("nd")
                if len(nodes) > 0:
                    way.set("from", nodes[0].attrib["ref"])
                    way.set("to", nodes[-1].attrib["ref"])
                    is_road = True
            if tag.attrib["k"] == "tunnel" and tag.attrib["v"] == "yes":
                is_tunnel = True
            if tag.attrib["k"] == "maxspeed":
                has_maxspeed = True
        if is_road and (config.LOAD_TUNNELS or not is_tunnel):
            if not has_maxspeed:
                way.set('maxspeed', roadtype)
            roads.add(way)
    print("{} roads found".format(len(roads)))
    return roads


def parse_file(
    filename: str, accepted_highways: List[str]
) -> Tuple[
    Set[ElTree.Element],
    Dict[int, Point],
    type(None),
    Tuple[float, float],
    Tuple[float, float, float, float],
    List,
    List
]:
    """
    extracts all ways with streets and all the nodes in these streets of a given osm file

    :param filename: the location of the osm file
    :type filename: str
    :param accepted_highways: a list of all highways that shall be extracted
    :type accepted_highways: List[str]
    :return: roads, road_points: set of all way objects, dict of required nodes and list of traffic signs
    :rtype: Tuple[Set[ElTree.Element], Dict[int, Point]]
    """
    tree = ElTree.parse(filename)
    root = tree.getroot()
    # get all roads
    roads = get_roads(accepted_highways, root)
    # get all required nodes
    road_nodes = get_nodes(roads, root)
    custom_bounds = read_custom_bounds(root)
    road_points, center_point, bounds = get_points(road_nodes, custom_bounds)
    traffic_rules = get_traffic_rules(road_nodes, roads, config.TRAFFIC_SIGN_KEYS, config.TRAFFIC_SIGN_VALUES)
    traffic_signs, traffic_lights = get_traffic_signs_and_lights(traffic_rules)
    restrictions = get_restrictions(root)
    # print("bounds", bounds, "custom_bounds", read_custom_bounds(root))
    if custom_bounds is not None:
        bounds = custom_bounds

    return roads, road_points, restrictions, center_point, bounds, traffic_signs, traffic_lights


def parse_turnlane(turnlane: str) -> str:
    """
    parses a turnlane to a simple and defined format
    all possible turnlanes are found in config.py

    :param turnlane: string, a turnlane
    :type turnlane: str
    :return: turnlane
    :rtype: str
    """
    if turnlane == "":
        return "none"
    if turnlane in config.RECOGNIZED_TURNLANES:
        return turnlane
    included = []
    if "left" in turnlane:
        included.append("left")
    if "through" in turnlane:
        included.append("through")
    if "right" in turnlane:
        included.append("right")
    result = ";".join(included)
    if result is "":
        return "none"
    return result

def extract_speedlimit(value):
    virtual = False
    try:
        speedlimit = float(value)
    except ValueError:
        if value == "walk":
            speedlimit = 7
            virtual = True
        elif value == "none":
            speedlimit = 250
            virtual = True
        elif value == "signals":
            pass
        elif value.endswith("mph"):
            try:
                speedlimit = int(float(value[:-3]) / 1.60934)
            except ValueError:
                print("unreadable speedlimit: '{}'".format(value))
        elif value in config.SPEED_LIMITS:
            speedlimit = config.SPEED_LIMITS[value]
            virtual = True
        else:
            print("unreadable speedlimit: '{}'".format(value))
    # convert from km/h to m/s
    if speedlimit is not None:
        speedlimit /= 3.6
        virtual = True

    return speedlimit, virtual


def extract_tag_info(road: ElTree.Element) -> Tuple[Road_info, int]:
    """
    extracts the information of roads given in tags

    :param road: osm road object
    :type road: ElTree.Element
    :return: (nr_of_lanes, forward_lanes, backward_lanes, oneway, turnlanes, turnlanes_forward, turnlanes_backward),
        speedlimit
    :rtype: Tuple[Road_info, int]
    """
    nr_of_lanes, forward_lanes, backward_lanes = None, None, None
    speedlimit, oneway = None, None
    turnlanes, turnlanes_forward, turnlanes_backward = None, None, None
    for tag in road.findall("tag"):
        if tag.attrib["k"] == "lanes":
            try:
                nr_of_lanes = int(tag.attrib["v"])
            except ValueError:
                print("unreadable nr_of_lanes: {}".format(tag.attrib["v"]))
        if tag.attrib["k"] == "lanes:forward":
            forward_lanes = int(tag.attrib["v"])
        if tag.attrib["k"] == "lanes:backward":
            backward_lanes = int(tag.attrib["v"])
        if tag.attrib["k"] == "maxspeed":
            speedlimit, virtual = extract_speedlimit(tag.attrib['v'])
        if tag.attrib["k"] == "oneway":
            oneway = tag.attrib["v"] == "yes"
        if tag.attrib["k"] == "junction":
            if oneway is None:
                if tag.attrib["v"] == "roundabout":
                    oneway = True
        if tag.attrib["k"] == "turn:lanes":
            turnlanes = tag.attrib["v"].split("|")
        if tag.attrib["k"] == "turn:lanes:forward":
            turnlanes_forward = tag.attrib["v"].split("|")
        if tag.attrib["k"] == "turn:lanes:backward":
            turnlanes_backward = tag.attrib["v"].split("|")
        for current_list in [turnlanes, turnlanes_forward, turnlanes_backward]:
            if current_list is not None:
                for index, turnlane in enumerate(current_list):
                    current_list[index] = parse_turnlane(turnlane)
        # turnlanelength should match lanelength
    return (
        (
            nr_of_lanes,
            forward_lanes,
            backward_lanes,
            oneway,
            turnlanes,
            turnlanes_forward,
            turnlanes_backward,
        ),
        speedlimit,
    )


def get_graph_traffic_signs(nodes: Dict, roads: Dict, traffic_signs: List):
    graph_traffic_signs = []
    for traffic_sign in traffic_signs:
        node_id = next(iter(traffic_sign))
        if node_id.startswith('road'):
            road_id = node_id[4:]
            graph_traffic_sign = rg.GraphTrafficSign(traffic_sign[node_id], node=None, edges=[roads[road_id]])
        else:
            graph_traffic_sign = rg.GraphTrafficSign( traffic_sign[node_id], nodes[node_id])
        # extract road_ids to edges in sign
        if 'road_id' in traffic_sign.keys():
            roads = traffic_sign['road_id']
            for road_id in roads:
                graph_traffic_sign.edges.append(roads[road_id])
                
        graph_traffic_signs.append(graph_traffic_sign)

    return graph_traffic_signs


def get_graph_traffic_lights(nodes: Dict, traffic_lights: List):
    graph_traffic_lights = []
    for traffic_light in traffic_lights:
        node_id = next(iter(traffic_light))
        graph_traffic_light = rg.GraphTrafficLight( traffic_light[node_id], nodes[node_id])
        graph_traffic_lights.append(graph_traffic_light)
    return graph_traffic_lights


def get_graph_nodes(
        roads: Set[ElTree.Element], points: Dict[int, Point], traffic_signs: List,
        traffic_lights: List
) -> Dict[int, rg.GraphNode]:
    """
    gets graph nodes from set of osm ways
    all points that are referenced by two or more ways or are at the end of a way are returned as nodes

    :param roads: set of osm ways
    :type roads: Set[ElTree.Element]
    :param points: dict of points of each osm node
    :type points: Dict[int, Point]
    :return: nodes, set of graph node objects
    :rtype: Dict[int, GraphNode]
    """
    nodes = {}
    node_degree = {}
    for road in roads:
        for waypoint in road.findall("nd"):
            id = waypoint.attrib["ref"]
            if id in node_degree:
                node_degree[id] += 1
            else:
                node_degree[id] = 1
        for id in (road.attrib["from"], road.attrib["to"]):
            current_point = points[id]
            if id not in nodes:
                nodes[id] = rg.GraphNode(
                    int(id), current_point.x, current_point.y, set()
                )

    for traffic_sign in traffic_signs:
        id = next(iter(traffic_sign))
        if id.startswith('road'):
            continue
        if id not in nodes:
            current_point = points[id]
            nodes[id] = rg.GraphNode(int(id), current_point.x, current_point.y, set())

    for traffic_light in traffic_lights:
        id = next(iter(traffic_light))
        if id not in nodes:
            current_point = points[id]
            nodes[id] = rg.GraphNode(int(id), current_point.x, current_point.y, set())

    for id in node_degree:
        current_point = points[id]
        if id not in nodes and node_degree[id] > 1:
            nodes[id] = rg.GraphNode(int(id), current_point.x, current_point.y, set())
    return nodes


def get_area_from_bounds(
    bounds: Tuple[float, float, float, float], origin: np.ndarray
) -> Area:
    max_point = lon_lat_to_cartesian(np.array([bounds[3], bounds[0]]), origin)
    min_point = lon_lat_to_cartesian(np.array([bounds[1], bounds[2]]), origin)
    # print("maxpoint", max_point, "minpoint", min_point)
    # print("bounds", bounds)
    # print("origin", origin)
    return Area(min_point[0], max_point[0], min_point[1], max_point[1])


def get_graph_edges_from_road(
    roads: Set[ElTree.Element],
    nodes: Dict[int, rg.GraphNode],
    points: Dict[int, Point],
    bounds: Tuple[float, float, float, float],
    origin: np.ndarray,
) -> Dict[int, Set[rg.GraphEdge]]:
    """
    gets graph edges from set of roads

    :param origin:
    :param bounds:
    :param roads: set of osm way objects
    :type roads: Set[ElTree.Element]
    :param nodes: set of graph nodes
    :type nodes: Dict[int, GraphNode]
    :param points: dict of points of each osm node
    :type points: Dict[int, Point]
    :return: edges: set of graph edge objects
    :rtype: Set[GraphEdge]
    """

    def neighbor_in_area(index: int, point_in_area_list: List[bool]) -> bool:
        result = False
        if index >= 1:
            result = result or point_in_area_list[index - 1]
        if index + 1 < len(point_in_area_list):
            result = result or point_in_area_list[index + 1]
        return result

    area = get_area_from_bounds(bounds, origin)
    edges = {}
    for road_index, road in enumerate(roads):
        # get basic information of road
        # edge_id = road.attrib['id']
        edge_node_ids = []
        edge_nodes = []
        roadtype = road.attrib["roadtype"]

        lane_info, speedlimit = extract_tag_info(road)
        # if speedlimit is None:
        #     speedlimit = config.SPEED_LIMITS[roadtype] / 3.6
        lane_info, flip = i_d.extract_missing_info(lane_info)
        nr_of_lanes, forward_lanes, backward_lanes, oneway, turnlanes, turnlanes_forward, turnlanes_backward = (
            lane_info
        )
        if forward_lanes is not None and backward_lanes is not None:
            assert forward_lanes + backward_lanes == nr_of_lanes
        lane_info, assumptions = i_d.assume_missing_info(lane_info, roadtype)
        nr_of_lanes, forward_lanes, backward_lanes, oneway, turnlanes, turnlanes_forward, turnlanes_backward = (
            lane_info
        )
        assert forward_lanes + backward_lanes == nr_of_lanes

        # get waypoints
        waypoints = []
        outside_waypoints = set()
        point_list = road.findall("nd")
        point_list = [points[point.attrib["ref"]] for point in point_list]
        point_in_area_list = [point in area for point in point_list]
        for index, point in enumerate(point_list):
            # loading only inside of bounds
            if point_in_area_list[index]:
                # point is added
                waypoints.append(point)
            elif neighbor_in_area(index, point_in_area_list):
                # point is added, but edge is split
                outside_waypoints.add(point.id)
                waypoints.append(point)
                nodes[point.id] = rg.GraphNode(point.id, point.x, point.y, set())
            else:
                # point is not added
                pass

        if flip:
            waypoints.reverse()

        osm_id = road.attrib["id"]
        edges[osm_id] = set()

        # road is split and edges are created for each segment
        for index, waypoint in enumerate(waypoints):
            waypoint_id: int = waypoint.id
            if waypoint_id in nodes or waypoint_id in outside_waypoints:
                edge_node_ids.append((waypoint_id, index))
                edge_nodes.append((nodes[waypoint_id], index))
            if config.SPLIT_AT_CORNER and is_corner(index, waypoints):
                try:
                    edge_node_ids.append((waypoint_id, index))
                    if waypoint_id not in nodes:
                        id_int = int(waypoint_id)
                        nodes[waypoint_id] = rg.GraphNode(
                            id_int, waypoint.x, waypoint.y, set()
                        )
                    edge_nodes.append((nodes[waypoint_id], index))
                except ValueError:
                    print("edge could not be splitted at corner")

        new_edges = []
        for index, node in enumerate(edge_nodes[:-1]):
            node1, index1 = edge_nodes[index]
            node2, index2 = edge_nodes[index + 1]
            current_waypoints = waypoints[index1 : index2 + 1]
            # only edges with sufficient nr of waypoint are added
            if len(current_waypoints) >= 2:
                # create edge
                edge_id = idgenerator.get_id()
                new_edge = rg.GraphEdge(
                    edge_id,
                    node1,
                    node2,
                    current_waypoints,
                    lane_info,
                    assumptions,
                    speedlimit,
                    roadtype,
                )
                new_edges.append(new_edge)
                edges[osm_id].add(new_edge)

                # assign edges to nodes
                node1.edges.add(new_edge)
                node2.edges.add(new_edge)

                new_edge.generate_lanes()
            else:
                print("a small edge occurred in the map, it is omitted")

        # add successors to edges
        for index, edge in enumerate(new_edges[:-1]):
            edge.forward_successor = new_edges[index + 1]
    return edges


def map_restrictions(
    edges: Dict[int, Set[rg.GraphEdge]],
    restrictions: Dict[int, Set[Restriction]],
    nodes: Dict[int, rg.GraphNode],
):
    """
    assigns restriction string to corresponding edges

    :param edges: dict mapping from edge ids to edges
    :param restrictions: dict mapping from from_edge ids to restrictions
    :param nodes: dict mapping from node_id to node
    :return:
    """
    for from_id, restrictions in restrictions.items():
        if from_id in edges:
            from_edges = edges[from_id]
            if len(from_edges) == 1:
                from_edge = next(iter(from_edges))
                for restriction in restrictions:
                    if restriction.restriction is None:
                        continue
                    if restriction.via_element_type == "node":
                        if restriction.via_element_id in nodes and nodes[
                            restriction.via_element_id
                        ] in (from_edge.node1, from_edge.node2):
                            restriction_node = nodes[restriction.via_element_id]
                        else:
                            continue
                    elif restriction.via_element_type == "way":
                        if restriction.via_element_id in edges:
                            via_edge = next(iter(edges[restriction.via_element_id]))
                            restriction_node = from_edge.common_node(via_edge)
                        else:
                            continue
                    else:
                        continue
                    if restriction_node is from_edge.node1:
                        from_edge.backward_restrictions |= restriction.restriction
                    elif restriction_node is from_edge.node2:
                        from_edge.forward_restrictions |= restriction.restriction
            else:
                print(
                    "several edges have the same id, we cannot apply restrictions to it"
                )
                # TODO implement restrictions for mutliple edges with same id
                pass
        else:
            print(
                "unknown id '{}' for restriction element. skipping restriction".format(
                    from_id
                )
            )


def get_node_set(edges: Set[rg.GraphEdge]) -> Set[rg.GraphNode]:
    """
    gets all nodes referenced by a set of edges

    :param edges:
    :return:
    """
    nodes = set()
    for edge in edges:
        nodes.add(edge.node1)
        nodes.add(edge.node2)
    return nodes


def roads_to_graph(
    roads: Set[ElTree.Element],
    road_points: Dict[int, Point],
    restrictions: Dict[int, Set[Restriction]],
    center_point: Tuple[float, float],
    bounds: Tuple[float, float, float, float],
    origin: tuple,
    traffic_signs: List,
    traffic_lights: List
) -> rg.Graph:
    """
    converts a set of roads and points to a road graph

    :param origin:
    :param bounds:
    :param roads: set of roads
    :type roads: Set[ElTree.Element]
    :param road_points: corresponding points
    :type road_points: Dict[int, Point]
    :param restrictions: restrictions which will be applied to edges
    :param center_point: gps coordinates of the origin
    :param traffic_signs: traffic signs to apply
    :param traffic_lights: traffic lights to apply
    :return:
    """
    origin = np.array(origin)[::-1]
    nodes = get_graph_nodes(roads, road_points, traffic_signs, traffic_lights)
    edges = get_graph_edges_from_road(roads, nodes, road_points, bounds, origin)
    graph_traffic_signs = get_graph_traffic_signs(nodes, edges, traffic_signs)
    graph_traffic_lights = get_graph_traffic_lights(nodes, traffic_lights)
    map_restrictions(edges, restrictions, nodes)
    edges = {elem for edge_set in edges.values() for elem in edge_set}
    # node_set = set()
    # for node in nodes:
    #     node_set.add(nodes[node])
    node_set = get_node_set(edges)
    graph = rg.Graph(node_set, edges, center_point, bounds, graph_traffic_signs, graph_traffic_lights)
    return graph
