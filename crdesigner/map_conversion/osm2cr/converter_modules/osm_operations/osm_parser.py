"""
This module provides all methods to parse an OSM file and convert it to a graph.
It also provides a method to project OSM nodes to cartesian coordinates.
"""

import dataclasses
import logging
import xml.etree.ElementTree as ElTree
from collections import OrderedDict
from typing import Any, Dict, List, Set, Tuple
from typing import OrderedDict as typingOD
from xml.etree.ElementTree import Element

import numpy as np
from ordered_set import OrderedSet
from pyproj import CRS, Transformer

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.osm_config import osm_config
from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.common.geometry import (
    Area,
    Point,
    is_corner,
    lon_lat_to_cartesian,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.restrictions import (
    Restriction,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_edge import (
    GraphEdge,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_node import (
    GraphNode,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_traffic_light import (
    GraphTrafficLight,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph_traffic_sign import (
    GraphTrafficSign,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._sublayered_graph import (
    SublayeredGraph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations import (
    info_deduction as i_d,
)
from crdesigner.map_conversion.osm2cr.converter_modules.utility import idgenerator
from crdesigner.map_conversion.osm2cr.converter_modules.utility.custom_types import (
    Road_info,
)

# type def
RestrictionDict = Dict[int, Set[Restriction]]


@dataclasses.dataclass
class Bounds:
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


def extract_lat_lon(nodes: Dict[int, ElTree.Element]) -> Tuple[List[int], List[float], List[float]]:
    if len(nodes) < 1:
        raise ValueError("Map is empty")

    ids = []
    lons = []
    lats = []
    for node_id, node in nodes.items():
        ids.append(node_id)
        lons.append(float(node.attrib["lon"]))
        lats.append(float(node.attrib["lat"]))

    return ids, lats, lons


def transform_lat_lon(
    ids: List[int], lats: List[float], lons: List[float], transformer: Transformer
) -> typingOD[int, Point]:
    x, y = transformer.transform(lats, lons)
    points = OrderedDict()
    for index, point_id in enumerate(ids):
        points[int(point_id)] = Point(int(point_id), x[index], y[index])
    logging.info("{} required nodes found".format(len(points)))
    return points


def get_nodes(
    roads: Set[ElTree.Element], root
) -> Tuple[Dict[int, ElTree.Element], Dict[int, ElTree.Element]]:
    """
    returns all nodes that are part of the specified roads and a subset
    of nodes that are crossings
    """
    node_ids = OrderedSet()
    for road in roads:
        nodes = road.findall("nd")
        for node in nodes:
            current_id = int(node.attrib["ref"])
            node_ids.add(current_id)
    nodes = root.findall("node")
    road_nodes = OrderedDict()
    crossing_nodes = OrderedDict()
    for node in nodes:
        node_id = int(node.attrib["id"])
        if node_id in node_ids:
            road_nodes[node_id] = node
            tags = node.findall("tag")
            for tag in tags:
                if (
                    tag.attrib["k"] == "highway"
                    and tag.attrib["v"] == "crossing"
                    or tag.attrib["k"] == "crossing"
                ):
                    crossing_nodes[node_id] = node
    assert len(road_nodes) == len(node_ids)
    return road_nodes, crossing_nodes


def get_traffic_rules(
    nodes: Dict[int, ElTree.Element],
    roads: Dict[int, ElTree.Element],
    accepted_traffic_sign_by_keys: List[str],
    accepted_traffic_sign_by_values: List[str],
) -> Dict[str, Dict[str, str]]:
    """
    Extract traffic rules from nodes and roads.

    :return: a Dict with type and value of the rules
    """
    traffic_rules = OrderedDict()
    for node_id in nodes:
        node = nodes[node_id]
        tags = node.findall("tag")
        for tag in tags:
            if (
                tag.attrib["k"] in accepted_traffic_sign_by_keys
                or tag.attrib["v"] in accepted_traffic_sign_by_values
            ):
                key = tag.attrib["k"]
                value = tag.attrib["v"]
                virtual = None
                if key == "maxspeed":
                    value, virtual = extract_speedlimit(value)
                sign = {key: value, "virtual": virtual}
                if node_id in traffic_rules:
                    traffic_rules[str(node_id)].update(sign)
                else:
                    traffic_rules.update({str(node_id): sign})

    for road in roads:
        road_id = int(road.attrib["id"])
        tags = road.findall("tag")
        for tag in tags:
            if (
                tag.attrib["k"] in accepted_traffic_sign_by_keys
                or tag.attrib["v"] in accepted_traffic_sign_by_values
                or tag.attrib["k"] == "highway"
            ):
                key = tag.attrib["k"]
                value = tag.attrib["v"]
                virtual = None
                if key == "maxspeed":
                    value, virtual = extract_speedlimit(value)
                elif key == "highway":
                    # fallback if no speedlimit was found
                    value, virtual = extract_speedlimit(value)
                    key = "maxspeed"
                sign = {key: value, "virtual": virtual}
                # check if traffic rule exists
                nodes = road.findall("nd")
                added = False
                for node in nodes:
                    if not added:
                        node_id = int(node.attrib["ref"])
                        if (
                            node_id in traffic_rules
                            and key in traffic_rules[node_id].keys()
                            and traffic_rules[node_id][key] == value
                        ):
                            # if already other roads exist
                            if "road_id" in traffic_rules[node_id].keys():
                                traffic_rules[node_id]["road_id"].append(road_id)
                            else:
                                traffic_rules[node_id].update({"road_id": [road_id]})
                            added = True
                if not added:
                    sign["road_id"] = road_id
                    sign["virtual"] = True
                    traffic_rules.update({"road" + str(road_id): sign})

    return traffic_rules


def get_traffic_signs_and_lights(traffic_rules: Dict) -> (List, List):
    traffic_lights = []
    traffic_signs = []
    for rule_id, rule in traffic_rules.items():
        if (
            "traffic_sign" in rule.keys()
            or "maxspeed" in rule.keys()
            or "overtaking" in rule.keys()
        ):
            traffic_signs.append({rule_id: rule})
        else:
            traffic_lights.append({rule_id: rule})
    return traffic_signs, traffic_lights


def parse_restrictions(restrictions: Set[ElTree.Element]) -> RestrictionDict:
    """
    parses a set of restrictions in tree form to restriction objects

    :param restrictions:
    :return:
    """
    result = OrderedDict()
    for restriction_element in restrictions:
        from_edge_id, to_edge_id, via_element_id, via_element_type = (
            None,
            None,
            None,
            None,
        )
        if "restriction" in restriction_element.attrib:
            restriction = restriction_element.attrib["restriction"]
        # connectivity can be used as restriction.
        # In order to distinguish from known restrictions, a connectivity prefix is added
        elif "connectivity" in restriction_element.attrib:
            restriction = "connectivity=" + str(restriction_element.attrib["connectivity"])
        else:
            continue
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


def get_restrictions(root) -> RestrictionDict:
    """
    finds restrictions in osm file and returns it as dict mapping from from_edge to restriction object

    :param root:
    :return:
    """
    restrictions = OrderedSet()
    relations = root.findall("relation")
    for relation in relations:
        tags = relation.findall("tag")
        for tag in tags:
            if tag.attrib["k"] == "type" and tag.attrib["v"] == "restriction":
                restrictions.add(relation)
            if tag.attrib["k"] == "restriction":
                relation.set("restriction", tag.attrib["v"])
            # TODO Handle vehicle specific restrictions, e.g. restriction:hgv
            # also add connectivity relations, since it can be used as a restriction for lane linking
            if tag.attrib["k"] == "type" and tag.attrib["v"] == "connectivity":
                restrictions.add(relation)
            if tag.attrib["k"] == "connectivity":
                relation.set("connectivity", tag.attrib["v"])
    restrictions = parse_restrictions(restrictions)
    return restrictions


def get_ways(
    accepted_highways: List[str], rejected_tags: Dict[str, str], root
) -> OrderedSet[ElTree.Element]:
    """
    finds ways of desired types in osm file.

    :param accepted_highways: only ways with those highway tag will be considered
    :param rejected_tags: reject ways with at least one of those tags
    :param root:
    :return:
    """
    roads = OrderedSet()
    ways = root.findall("way")
    for way in ways:
        tags = way.findall("tag")

        # discard ways with a rejected tag
        reject_way = False
        for tag in tags:
            tag_key = tag.attrib["k"]
            if tag_key in rejected_tags:
                if tag.attrib["v"] == rejected_tags[tag.attrib["k"]]:
                    reject_way = True
                    break
        if reject_way:
            continue

        is_road = False
        is_tunnel = False
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
                way.set("maxspeed", roadtype)
            roads.add(way)
    logging.info("{} roads found".format(len(roads)))
    return roads


def parse_file(
    filename: str,
    accepted_highways: List[str],
    rejected_tags: Dict[str, str],
    custom_bounds: Bounds = None,
) -> Tuple[
    OrderedSet[Element],
    Dict[int, Point],
    Tuple[float, float],
    Bounds,
    Dict[int, Set[Restriction]],
    List[Dict[Any, Any]],
    List[Dict[Any, Any]],
    Dict[int, Point],
    Transformer,
]:
    """
    extracts all ways with streets and all the nodes in these streets of a given osm file

    :param filename: the location of the osm file
    :param accepted_highways: a list of all highways that shall be extracted
    :return: roads, road_points: set of all way objects, dict of required nodes and list of traffic signs and more
    """
    tree = ElTree.parse(filename)
    root = tree.getroot()
    ways = get_ways(accepted_highways, rejected_tags, root)
    road_nodes, crossing_nodes = get_nodes(ways, root)

    # custom bounds were originally used this way.
    # Now they are used for sublayer extraction
    # custom_bounds = read_custom_bounds(root)
    road_ids, road_lats, road_lons = extract_lat_lon(road_nodes)
    crossing_ids, crossing_lats, crossing_lons = (
        extract_lat_lon(crossing_nodes) if len(crossing_nodes) > 0 else ([], [], [])
    )

    if custom_bounds is not None:
        bounds = custom_bounds
    else:
        # we define the bounds based on the road network
        bounds = Bounds(min(road_lats), max(road_lats), min(road_lons), max(road_lons))
    assert bounds.lat_max >= bounds.lat_min
    assert bounds.lon_max >= bounds.lon_min
    lon_center = (bounds.lon_min + bounds.lon_max) / 2
    lat_center = (bounds.lat_max + bounds.lat_min) / 2
    center_point = lat_center, lon_center

    # create transformer for projecting lat/lon
    crs_from = CRS(osm_config.PROJ_STRING_FROM)
    crs_to = CRS(general_config.proj_string_cr)
    transformer = Transformer.from_proj(crs_from, crs_to)

    road_points = transform_lat_lon(road_ids, road_lats, road_lons, transformer)
    crossing_points = transform_lat_lon(crossing_ids, crossing_lats, crossing_lons, transformer)
    traffic_rules = get_traffic_rules(
        road_nodes, ways, config.TRAFFIC_SIGN_KEYS, config.TRAFFIC_SIGN_VALUES
    )
    traffic_signs, traffic_lights = get_traffic_signs_and_lights(traffic_rules)
    restrictions = get_restrictions(root)

    return (
        ways,
        road_points,
        center_point,
        bounds,
        restrictions,
        traffic_signs,
        traffic_lights,
        crossing_points,
        transformer,
    )


def parse_turnlane(turnlane: str) -> str:
    """
    parses a turnlane to a simple and defined format
    all possible turnlanes are found in osm_config.py

    :param turnlane: string, a turnlane
    :return: turnlane
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
    if result == "":
        return "none"
    return result


def extract_speedlimit(value) -> Tuple[float, bool]:
    """
    Returns a speedlimit and flag if it is virtual.
    """
    virtual = False
    speedlimit = None
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
                logging.error("unreadable speedlimit: '{}'".format(value))
        elif value in config.SPEED_LIMITS:
            speedlimit = config.SPEED_LIMITS[value]
            virtual = True
        else:
            logging.warning("unreadable speedlimit: '{}'".format(value))

    # convert from km/h to m/s
    if speedlimit is not None:
        speedlimit /= 3.6
        virtual = True

    return speedlimit, virtual


def extract_tag_info(road: ElTree.Element) -> Tuple[Road_info, int]:
    """
    extracts the information of roads given in tags

    :param road: osm road object
    :return: (nr_of_lanes, forward_lanes, backward_lanes, oneway, turnlanes,
        turnlanes_forward, turnlanes_backward), speedlimit
    """
    nr_of_lanes, forward_lanes, backward_lanes = None, None, None
    speedlimit, oneway = None, None
    turnlanes, turnlanes_forward, turnlanes_backward = None, None, None
    for tag in road.findall("tag"):
        if tag.attrib["k"] == "lanes":
            try:
                nr_of_lanes = int(tag.attrib["v"])
            except ValueError:
                logging.error("unreadable nr_of_lanes: {}".format(tag.attrib["v"]))
        if tag.attrib["k"] == "lanes:forward":
            forward_lanes = int(tag.attrib["v"])
        if tag.attrib["k"] == "lanes:backward":
            backward_lanes = int(tag.attrib["v"])
        if tag.attrib["k"] == "maxspeed":
            speedlimit, virtual = extract_speedlimit(tag.attrib["v"])
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


def get_graph_traffic_signs(
    nodes: Dict[int, GraphNode], roads: Dict[int, GraphEdge], traffic_signs: List[Dict]
) -> List[GraphTrafficSign]:
    """
    Create the extracted traffic signs.
    """
    graph_traffic_signs = []
    for traffic_sign in traffic_signs:
        node_id = next(iter(traffic_sign))
        if node_id.startswith("road"):
            road_id = int(node_id[4:])
            graph_traffic_sign = GraphTrafficSign(
                traffic_sign[node_id], node=None, edges=[roads[road_id]]
            )
        else:
            graph_traffic_sign = GraphTrafficSign(traffic_sign[node_id], nodes[int(node_id)])
        # extract road_ids to edges in sign
        if "road_id" in traffic_sign.keys():
            roads = traffic_sign["road_id"]
            for road_id in roads:
                graph_traffic_sign.edges.append(roads[road_id])

        graph_traffic_signs.append(graph_traffic_sign)

    return graph_traffic_signs


def get_graph_traffic_lights(
    nodes: Dict[int, GraphNode], traffic_lights: List[Dict]
) -> List[GraphTrafficLight]:
    """
    Create the extracted traffic lights.
    """
    graph_traffic_lights = []
    for traffic_light in traffic_lights:
        node_id = next(iter(traffic_light))
        graph_traffic_light = GraphTrafficLight(traffic_light[node_id], nodes[int(node_id)])
        graph_traffic_lights.append(graph_traffic_light)
    return graph_traffic_lights


def get_graph_nodes(
    roads: Set[ElTree.Element], points: Dict[int, Point], traffic_signs: List, traffic_lights: List
) -> Dict[int, GraphNode]:
    """
    gets graph nodes from set of osm ways
    all points that are referenced by traffic signs, by traffic lights or by
    two or more ways or are at the end of a way are returned

    :param roads: set of osm ways
    :param points: dict of points of each osm node
    :return: nodes, set of graph node objects
    """
    nodes = OrderedDict()
    point_degree = OrderedDict()  # number of roads sharing a point
    for road in roads:
        for waypoint in road.findall("nd"):
            point_id = int(waypoint.attrib["ref"])
            if point_id in point_degree:
                point_degree[point_id] += 1
            else:
                point_degree[point_id] = 1
        # get nodes from endpoints of ways
        for point_id in (int(road.attrib["from"]), int(road.attrib["to"])):
            current_point = points[point_id]
            if point_id not in nodes:
                nodes[point_id] = GraphNode(
                    point_id, current_point.x, current_point.y, OrderedSet()
                )

    for traffic_sign in traffic_signs:
        point_id = next(iter(traffic_sign))
        if point_id.startswith("road"):
            continue
        if int(point_id) not in nodes:
            current_point = points[int(point_id)]
            nodes[int(point_id)] = GraphNode(
                int(point_id), current_point.x, current_point.y, OrderedSet()
            )

    for traffic_light in traffic_lights:
        point_id = int(next(iter(traffic_light)))
        if point_id not in nodes:
            current_point = points[point_id]
            nodes[point_id] = GraphNode(point_id, current_point.x, current_point.y, OrderedSet())

    # get nodes from intersection points of roads
    for point_id in point_degree:
        current_point = points[point_id]
        if point_id not in nodes and point_degree[point_id] > 1:
            nodes[point_id] = GraphNode(point_id, current_point.x, current_point.y, OrderedSet())
    return nodes


def get_area_from_bounds(bounds: Bounds) -> Area:
    """
    returns a rectangular area in cartesian coordinates from given
    bounds and origin in longitude and latitude
    """
    max_point = lon_lat_to_cartesian(np.array([bounds.lat_max, bounds.lon_max]), np.array([0, 0]))
    min_point = lon_lat_to_cartesian(np.array([bounds.lat_min, bounds.lon_min]), np.array([0, 0]))
    return Area(min_point[0], max_point[0], min_point[1], max_point[1])


def get_graph_edges_from_road(
    roads: Set[ElTree.Element],
    nodes: Dict[int, GraphNode],
    points: Dict[int, Point],
    bounds: Bounds,
    transformer: Transformer,
) -> Dict[int, Set[GraphEdge]]:
    """
    gets graph edges from set of roads

    :param bounds:
    :param roads: set of osm way objects
    :param nodes: set of graph nodes
    :param points: dict of points of each osm node
    :return: edges: set of graph edge objects
    """

    def neighbor_in_area(index: int, point_in_area_list: List[bool]) -> bool:
        result = False
        if index >= 1:
            result = result or point_in_area_list[index - 1]
        if index + 1 < len(point_in_area_list):
            result = result or point_in_area_list[index + 1]
        return result

    left, bottom, right, top = transformer.transform_bounds(
        bounds.lat_min, bounds.lon_min, bounds.lat_max, bounds.lon_max
    )
    area = Area(left, right, bottom, top)
    edges = OrderedDict()
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
        (
            nr_of_lanes,
            forward_lanes,
            backward_lanes,
            oneway,
            turnlanes,
            turnlanes_forward,
            turnlanes_backward,
        ) = lane_info
        if forward_lanes is not None and backward_lanes is not None:
            assert forward_lanes + backward_lanes == nr_of_lanes
        lane_info, assumptions = i_d.assume_missing_info(lane_info, roadtype)
        (
            nr_of_lanes,
            forward_lanes,
            backward_lanes,
            oneway,
            turnlanes,
            turnlanes_forward,
            turnlanes_backward,
        ) = lane_info
        assert forward_lanes + backward_lanes == nr_of_lanes

        # get waypoints
        waypoints = []
        outside_waypoints = OrderedSet()
        point_list = [points[int(nd.attrib["ref"])] for nd in road.findall("nd")]
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
                nodes[point.id] = GraphNode(point.id, point.x, point.y, OrderedSet())
            else:
                # point is not added
                pass

        if flip:
            waypoints.reverse()

        osm_id = int(road.attrib["id"])
        edges[osm_id] = OrderedSet()

        # road is split at nodes and edges are created for each segment
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
                        nodes[waypoint_id] = GraphNode(id_int, waypoint.x, waypoint.y, OrderedSet())
                    edge_nodes.append((nodes[waypoint_id], index))
                except ValueError:
                    logging.error("edge could not be splitted at corner")

        new_edges = []
        for index, node in enumerate(edge_nodes[:-1]):
            node1, index1 = edge_nodes[index]
            node2, index2 = edge_nodes[index + 1]
            current_waypoints = waypoints[index1 : index2 + 1]
            # only edges with sufficient nr of waypoint are added
            if len(current_waypoints) >= 2:
                # create edge
                edge_id = idgenerator.get_id()
                new_edge = GraphEdge(
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
                logging.warning("a small edge occurred in the map, it is omitted")

        # add successors to edges
        for index, edge in enumerate(new_edges[:-1]):
            edge.forward_successor = new_edges[index + 1]

    return edges


def map_restrictions(
    edges: Dict[int, Set[GraphEdge]],
    restrictions: Dict[int, Set[Restriction]],
    nodes: Dict[int, GraphNode],
):
    """
    assigns restriction string to corresponding edges

    :param edges: dict mapping from edge ids to edges
    :param restrictions: dict mapping from from_edge ids to restrictions
    :param nodes: dict mapping from node_id to node
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
                        ] in (
                            from_edge.node1,
                            from_edge.node2,
                        ):
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
                logging.warning(
                    "several edges have the same id, we cannot apply restrictions to it"
                )
                # TODO implement restrictions for multiple edges with same id
                pass
        else:
            logging.warning(
                "unknown id '{}' for restriction element. skipping restriction".format(from_id)
            )


def get_node_set(edges: Set[GraphEdge]) -> Set[GraphNode]:
    """
    gets all nodes referenced by a set of edges

    :param edges:
    :return:
    """
    nodes = OrderedSet()
    for edge in edges:
        nodes.add(edge.node1)
        nodes.add(edge.node2)
    return nodes


def roads_to_graph(
    roads: Set[ElTree.Element],
    road_points: Dict[int, Point],
    restrictions: RestrictionDict,
    center_point: Tuple[float, float],
    bounds: Bounds,
    traffic_signs: List,
    traffic_lights: List,
    transformer: Transformer,
    additional_nodes: List[GraphNode] = None,
) -> Graph:
    """
    converts a set of roads and points to a road graph

    :param bounds:
    :param roads: set of roads
    :param road_points: corresponding points
    :param restrictions: restrictions which will be applied to edges
    :param traffic_signs: traffic signs to apply
    :param traffic_lights: traffic lights to apply
    :param additional_nodes: nodes that should be considered additionally
    """
    nodes = get_graph_nodes(roads, road_points, traffic_signs, traffic_lights)
    if additional_nodes is not None:
        for node in additional_nodes:
            nodes[node.id] = node
    #            logging.info("added crossing point", node)
    edges = get_graph_edges_from_road(roads, nodes, road_points, bounds, transformer)
    graph_traffic_signs = get_graph_traffic_signs(nodes, edges, traffic_signs)
    graph_traffic_lights = get_graph_traffic_lights(nodes, traffic_lights)
    map_restrictions(edges, restrictions, nodes)
    edges = OrderedSet([elem for edge_set in edges.values() for elem in edge_set])
    # node_set = set()
    # for node in nodes:
    #     node_set.add(nodes[node])
    node_set = get_node_set(edges)
    graph = Graph(
        node_set,
        edges,
        center_point,
        bounds,
        transformer,
        graph_traffic_signs,
        graph_traffic_lights,
    )
    return graph


def get_crossing_points(
    comb_graph, main_graph, main_cross_points, sub_cross_points
) -> Tuple[Set[GraphNode], Set[GraphNode]]:
    """
    Get the nodes where the sub network is crossing the main network.

    :param comb_graph: parsed with accepted highways both of main and sub
    :param main_graph: parsed with accepted highways of main
    :param main_cross_points: points of the main layer tagged as crossing
    :param sub_cross_points: points of the main layer tagged as crossing
    :return: a set of new nodes and a set of contained nodes
        where both networks cross
    """

    def close_to_intersection(node_id, combined_graph, road_g):
        intersection_range = config.INTERSECTION_DISTANCE / 2.0
        node = [nd for nd in combined_graph.nodes if nd.id == node_id][0]
        road_node_ids = [nd.id for nd in road_g.nodes]
        for edge in node.edges:
            if node == edge.node1:
                neighbor = edge.node2
            else:
                neighbor = edge.node1
            if (
                neighbor.id in road_node_ids
                and neighbor.get_degree() > 2
                and neighbor.get_distance(node) < intersection_range
            ):
                return True
        return False

    new_crossing_nodes = OrderedSet()
    already_contained = OrderedSet()
    main_node_dict = OrderedDict((node.id, node) for node in main_graph.nodes)
    for point_id, point in main_cross_points.items():
        if point_id in sub_cross_points and not close_to_intersection(
            point_id, comb_graph, main_graph
        ):
            if point_id in main_node_dict:
                already_contained.add(point_id)
            else:
                crossing_node = GraphNode(int(point_id), point.x, point.y, OrderedSet())
                crossing_node.is_crossing = True
                new_crossing_nodes.add(crossing_node)
    return new_crossing_nodes, already_contained


def _value_set(layer: Dict[str, bool]) -> Set[str]:
    """
    Extracts the street layer from the given layer dict.
    """
    street_layer = set()
    for key, value in layer.items():
        if value:
            street_layer.add(key)
    return street_layer


def _value_list(layer: Dict[str, bool]) -> List[str]:
    """
    Extracts the street layer from the given layer dict.
    """
    street_layer = []
    for key, value in layer.items():
        if value:
            street_layer.append(key)
    return street_layer


def create_graph(file_path: str) -> Graph:
    """
    Create a graph from the given osm file.
    If a sublayer should be extracted the graph will be a SublayeredGraph.
    """

    def _create_graph(file, accepted_ways, custom_bounds=None, additional_nodes=None):
        (
            roads,
            points,
            center_point,
            bounds,
            restrictions,
            traffic_signs,
            traffic_lights,
            crossing_points,
            transformer,
        ) = parse_file(file, accepted_ways, config.REJECTED_TAGS, custom_bounds)
        graph = roads_to_graph(
            roads,
            points,
            restrictions,
            center_point,
            bounds,
            traffic_signs,
            traffic_lights,
            transformer,
            additional_nodes,
        )
        return graph, crossing_points

    #  reset id generator for new graph
    idgenerator.reset()

    if config.EXTRACT_SUBLAYER:
        if _value_set(config.ACCEPTED_HIGHWAYS_MAINLAYER) & _value_set(
            config.ACCEPTED_HIGHWAYS_SUBLAYER
        ):
            raise RuntimeError("main layer types and sublayer types have equal elements")

        #  get combined graph
        logging.info("extract combined layer")
        all_accepted_ways = _value_list(config.ACCEPTED_HIGHWAYS_MAINLAYER)
        all_accepted_ways.extend(_value_list(config.ACCEPTED_HIGHWAYS_SUBLAYER))
        combined_g, _ = _create_graph(file_path, all_accepted_ways)

        # get crossing nodes
        main_g, main_crossing_points = _create_graph(
            file_path, _value_list(config.ACCEPTED_HIGHWAYS_MAINLAYER), combined_g.bounds
        )
        logging.info("extract sub layer")
        sub_g, sub_crossing_points = _create_graph(
            file_path, _value_list(config.ACCEPTED_HIGHWAYS_SUBLAYER), combined_g.bounds
        )
        new_crossing_nodes, already_contained = get_crossing_points(
            combined_g, main_g, main_crossing_points, sub_crossing_points
        )

        # create the main graph with additional crossing nodes
        extended_main_graph, _ = _create_graph(
            file_path,
            _value_list(config.ACCEPTED_HIGHWAYS_MAINLAYER),
            combined_g.bounds,
            new_crossing_nodes,
        )
        for node in extended_main_graph.nodes:
            if node.id in already_contained:
                node.is_crossing = True

        logging.info("extract main layer")
        main_g = SublayeredGraph(
            extended_main_graph.nodes,
            extended_main_graph.edges,
            extended_main_graph.center_point,
            extended_main_graph.bounds,
            extended_main_graph.transformer,
            extended_main_graph.traffic_signs,
            extended_main_graph.traffic_lights,
            sub_g,
        )

    else:
        logging.info("extract main layer")
        main_g, _ = _create_graph(file_path, _value_list(config.ACCEPTED_HIGHWAYS_MAINLAYER))

    return main_g
