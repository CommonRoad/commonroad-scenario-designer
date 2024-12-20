"""
This module removes converting errors before exporting the scenario to XML
"""

import copy
import logging
from typing import Dict, Set

import networkx as nx
import numpy as np
from commonroad.scenario.scenario import Lanelet, LaneletNetwork, Scenario
from commonroad.scenario.traffic_sign import (
    LEFT_HAND_TRAFFIC,
    TRAFFIC_SIGN_VALIDITY_START,
)
from ordered_set import OrderedSet
from scipy import interpolate

from crdesigner.common.config.osm_config import osm_config as config


def sanitize(scenario: Scenario) -> None:
    """
    Sanitize resulting scenarios before export

    :param1 scenario: Scenario where operations will be performed on
    :return: None
    """
    # remove unconnected lanelets
    if config.REMOVE_UNCONNECTED_LANELETS:
        remove_unconnected_lanes(scenario)
    # remove non referenced traffic signs
    remove_empty_traffic_signs(scenario)
    remove_duplicate_traffic_signs(scenario)
    remove_non_referenced_signs(scenario)
    # merge too short and faulty lanes
    # TODO Deal with intersections
    # merge_short_lanes(scenario)
    # interpolate waypoints to smoothen lanes
    smoothen_scenario(scenario)
    # add positions to virtual traffic signs
    add_traffic_sign_position(scenario)
    # convert to left hand driving scenario if necessary
    convert_to_lht(scenario)


def _find_first_traffic_sign_occurrence(lanelet_network: LaneletNetwork) -> Dict[int, Set[int]]:
    """
    Evaluates all lanelets if a traffic sign occurs first within it

    :param lanelet_network: CommonRoad lanelet network
    :return: list of tuples with traffic sign ID and corresponding lanelet ID
    """
    occurrences = {}
    for lanelet in lanelet_network.lanelets:
        for traffic_sign in lanelet.traffic_signs:
            # create set object if none exist
            if occurrences.get(traffic_sign) is None:
                occurrences[traffic_sign] = set()
            # if there exists no predecessor, current lanelet is first occurrence
            if len(lanelet.predecessor) == 0:
                occurrences[traffic_sign].add(lanelet.lanelet_id)
            # if no predecessor references the traffic sign, this is the first occurrence
            elif all(
                traffic_sign not in lanelet_network.find_lanelet_by_id(pre).traffic_signs
                for pre in lanelet.predecessor
            ):
                occurrences[traffic_sign].add(lanelet.lanelet_id)

    return occurrences


def add_traffic_sign_position(scenario: Scenario):
    first_traffic_sign_occurrence = _find_first_traffic_sign_occurrence(scenario.lanelet_network)
    for sign in scenario.lanelet_network.traffic_signs:
        if sign.position is not None:
            continue
        for lanelet_id in first_traffic_sign_occurrence.get(sign.traffic_sign_id):
            if scenario.scenario_id.country_id in LEFT_HAND_TRAFFIC:
                if (
                    scenario.lanelet_network.find_lanelet_by_id(lanelet_id).adj_left_same_direction
                    is None
                    or scenario.lanelet_network.find_lanelet_by_id(
                        lanelet_id
                    ).adj_left_same_direction
                    is False
                ):
                    if any(
                        element.traffic_sign_element_id.name in TRAFFIC_SIGN_VALIDITY_START
                        for element in sign.traffic_sign_elements
                    ):
                        sign.position = scenario.lanelet_network.find_lanelet_by_id(
                            lanelet_id
                        ).left_vertices[0]
                    else:
                        sign.position = scenario.lanelet_network.find_lanelet_by_id(
                            lanelet_id
                        ).left_vertices[-1]
            else:
                if (
                    scenario.lanelet_network.find_lanelet_by_id(lanelet_id).adj_right_same_direction
                    is None
                    or scenario.lanelet_network.find_lanelet_by_id(
                        lanelet_id
                    ).adj_right_same_direction
                    is False
                ):
                    if any(
                        element.traffic_sign_element_id.name in TRAFFIC_SIGN_VALIDITY_START
                        for element in sign.traffic_sign_elements
                    ):
                        sign.position = scenario.lanelet_network.find_lanelet_by_id(
                            lanelet_id
                        ).right_vertices[0]
                    else:
                        sign.position = scenario.lanelet_network.find_lanelet_by_id(
                            lanelet_id
                        ).right_vertices[-1]
        if sign.position is None:
            current_lanelet = scenario.lanelet_network.find_lanelet_by_id(
                list(first_traffic_sign_occurrence.get(sign.traffic_sign_id))[0]
            )
            if scenario.scenario_id.country_id.value in LEFT_HAND_TRAFFIC:
                while (
                    current_lanelet.adj_left_same_direction is not None
                    and current_lanelet.adj_left_same_direction is not False
                ):
                    current_lanelet = scenario.lanelet_network.find_lanelet_by_id(
                        current_lanelet.adj_left
                    )
                if any(
                    element.traffic_sign_element_id.name in TRAFFIC_SIGN_VALIDITY_START
                    for element in sign.traffic_sign_elements
                ):
                    sign.position = current_lanelet.left_vertices[0]
                else:
                    sign.position = current_lanelet.left_vertices[-1]
            else:
                while (
                    current_lanelet.adj_right_same_direction is not None
                    and current_lanelet.adj_right_same_direction is not False
                ):
                    current_lanelet = scenario.lanelet_network.find_lanelet_by_id(
                        current_lanelet.adj_right
                    )
                if any(
                    element.traffic_sign_element_id.name in TRAFFIC_SIGN_VALIDITY_START
                    for element in sign.traffic_sign_elements
                ):
                    sign.position = current_lanelet.right_vertices[0]
                else:
                    sign.position = current_lanelet.right_vertices[-1]


def remove_empty_traffic_signs(scenario: Scenario) -> None:
    """
    Removes traffic signs without TrafficSignElement.

    :param scenario: scenario from which empty traffic signs are removed
    :return: None
    """
    for sign in scenario.lanelet_network.traffic_signs:
        if sign.traffic_sign_elements is None or len(sign.traffic_sign_elements) == 0:
            scenario.remove_traffic_sign(sign)


def remove_duplicate_traffic_signs(scenario: Scenario) -> None:
    """
    Removes duplicate traffic signs at same lanelet.

    :param1 scenario: Scenario used to find duplicate traffic sings
    :return: None
    """
    net = scenario.lanelet_network
    filtered_signs = OrderedSet()

    for la in net.lanelets:
        sign_elements = set()
        for lanelet_sign in la.traffic_signs:
            already_added = False
            for element in net.find_traffic_sign_by_id(lanelet_sign).traffic_sign_elements:
                if element not in sign_elements:
                    sign_elements.add(element)
                else:
                    already_added = True
            if not already_added:
                sign = net.find_traffic_sign_by_id(lanelet_sign)
                #  Adding a default position to the sign
                if sign.position is None:
                    sign.position = la.right_vertices[0]
                filtered_signs.add(sign)
    for sign in filtered_signs:
        scenario.remove_traffic_sign(sign)


def remove_non_referenced_signs(scenario: Scenario) -> None:
    """
    Removes non referenced traffic signs from scenario.

    :param scenario: Scenario used to find non referenced traffic sings
    :return: None
    """
    net = scenario.lanelet_network
    filtered_signs = OrderedSet()
    for sign in net.traffic_signs:
        referenced = False
        for lanelet in net.lanelets:
            if sign.traffic_sign_id in lanelet.traffic_signs:
                referenced = True
                break
        if referenced:
            continue
        else:
            #  Adding a default position to the sign
            if sign.position is None:
                sign.position = np.ndarray([0, 0])
            filtered_signs.add(sign)

    for sign in filtered_signs:
        scenario.remove_traffic_sign(sign)


def merge_short_lanes(scenario: Scenario, min_distance=1) -> None:
    """
    Merges faulty short lanes with their longer successors

    :param1 scenario: Scenario whose short lanelets will be removed
    :param2 min_distance: Minimum distance a single lanelet has to have to not be merged
    :return: None
    """
    logging.info("merging short lanes")

    lanelets = scenario.lanelet_network.lanelets

    # collect all faulty lanelets
    too_small = []
    for la in lanelets:
        if la.distance[-1] < min_distance:
            too_small.append(la.lanelet_id)

    # iterate over all too small lanelets
    while len(too_small) > 0:
        lanelets = scenario.lanelet_network.lanelets.copy()
        net = scenario.lanelet_network

        l_id = too_small.pop()
        la = net.find_lanelet_by_id(l_id)

        if la not in lanelets:
            continue

        if len(la.successor) == 0 and len(la.predecessor) == 1:
            pre = net.find_lanelet_by_id(la.predecessor[0])
            new_pre = create_lanelet(
                pre, pre.left_vertices, pre.right_vertices, pre.center_vertices, successor=[]
            )
            lanelets.remove(la)
            lanelets.append(new_pre)
            continue

        if len(la.successor) == 1 and len(la.predecessor) == 0:
            suc = net.find_lanelet_by_id(la.successor[0])
            new_suc = create_lanelet(
                suc, suc.left_vertices, suc.right_vertices, suc.center_vertices, predecessor=[]
            )
            lanelets.remove(la)
            lanelets.append(new_suc)
            continue

        successors = la.successor
        predecessors = la.predecessor

        for suc in successors:
            suc_l = net.find_lanelet_by_id(suc)
            merged_lanelet = merge_lanelets(la, suc_l)
            lanelets.remove(suc_l)
            lanelets.append(merged_lanelet)

        lanelets.remove(la)

        # merge lanelets does not modify the predecessor's successor
        for pre in predecessors:
            pre_lanelet = net.find_lanelet_by_id(pre)
            sucs_of_pre = list(filter(lambda s: s != l_id, pre_lanelet.successor))
            sucs_of_pre.extend(successors)
            new_pre = create_lanelet(
                pre_lanelet,
                pre_lanelet.left_vertices,
                pre_lanelet.right_vertices,
                pre_lanelet.center_vertices,
                predecessor=pre_lanelet.predecessor,
                successor=sucs_of_pre,
            )
            lanelets.remove(pre_lanelet)
            lanelets.append(new_pre)

        # update scenario's road network

        scenario.replace_lanelet_network(
            create_laneletnetwork(
                lanelets,
                scenario.lanelet_network.traffic_signs,
                scenario.lanelet_network.traffic_lights,
                scenario.lanelet_network.intersections,
            )
        )


def merge_lanelets(lanelet1: Lanelet, lanelet2: Lanelet) -> Lanelet:
    """
    Merges two lanelets which are in predecessor-successor relation. Modified version from commonroad-io which does
    not remove adj lanelets (and speedlimits)

    :param lanelet1: The first lanelet
    :param lanelet2: The second lanelet
    :return: Merged lanelet (predecessor => successor)
    """
    assert isinstance(
        lanelet1, Lanelet
    ), "<Lanelet/merge_lanelets>: lanelet1 is not a valid lanelet object!"
    assert isinstance(
        lanelet2, Lanelet
    ), "<Lanelet/merge_lanelets>: lanelet1 is not a valid lanelet object!"
    # check connection via successor / predecessor
    assert lanelet1.lanelet_id in lanelet2.successor or lanelet2.lanelet_id in lanelet1.successor, (
        "<Lanelet/merge_lanelets>: cannot merge two not connected lanelets! successors of l1 = {}, "
        "successors of l2 = {}".format(lanelet1.successor, lanelet2.successor)
    )

    # check pred and successor
    if lanelet1.lanelet_id in lanelet2.successor:
        pred = lanelet2
        suc = lanelet1
    else:
        pred = lanelet1
        suc = lanelet2

    # build new merged lanelet (remove first node of successor if both lanes are connected)
    # check connectedness
    if np.isclose(pred.left_vertices[-1], suc.left_vertices[0]).all():
        idx = 1
    else:
        idx = 0

    # create new lanelet
    left_vertices = np.concatenate((pred.left_vertices, suc.left_vertices[idx:]))
    right_vertices = np.concatenate((pred.right_vertices, suc.right_vertices[idx:]))
    center_vertices = np.concatenate((pred.center_vertices, suc.center_vertices[idx:]))
    predecessor = pred.predecessor
    successor = suc.successor

    # Merge also traffic signs
    traffic_signs = set()
    traffic_lights = set()
    traffic_signs.update(lanelet1.traffic_signs)
    traffic_signs.update(lanelet2.traffic_signs)
    traffic_lights.update(lanelet1.traffic_lights)
    traffic_lights.update(lanelet2.traffic_lights)

    return create_lanelet(
        suc,
        left_vertices,
        right_vertices,
        center_vertices,
        predecessor=predecessor,
        successor=successor,
        traffic_signs=traffic_signs,
        traffic_lights=traffic_lights,
    )


def smoothen_scenario(scenario: Scenario) -> None:
    """
    Smoothens every lanelet in an scenario

    :param1 scenario: Scenario whose lanelets shall be smoothended
    :return: None
    """
    logging.info("smoothening all lanelets of the scenario")

    net = scenario.lanelet_network
    lanelets = net.lanelets

    # smoothen lanes
    lanelets = list(map(smoothen_lane, lanelets))

    # update scenario
    scenario.replace_lanelet_network(
        create_laneletnetwork(
            lanelets,
            scenario.lanelet_network.traffic_signs,
            scenario.lanelet_network.traffic_lights,
            scenario.lanelet_network.intersections,
        )
    )


def b_spline(ctr, max_nodes=10) -> np.array:
    """
    Performing b spline interpolation over a given point list.
    Based on https://github.com/kawache/Python-B-spline-examples from Kaoua Cherif

    :param1 ctr: The point list b spline interpolation will be performed on
    :param2 max_nodes: Number of nodes that should be created during interpolation process
    :return: Interpolated point list
    """

    x = ctr[:, 0]
    y = ctr[:, 1]

    # return straight line if we have less or equal 3 waypoints
    if len(x) <= 3:
        x = np.linspace(x[0], x[-1], num=max_nodes)
        y = np.linspace(y[0], y[-1], num=max_nodes)
        return np.column_stack((x, y))

    try:
        # b_spline
        tck, u = interpolate.splprep([x, y], k=3, s=0)
        u = np.linspace(0, 1, num=max_nodes)
        out = interpolate.splev(u, tck)
    except (RuntimeError, TypeError, ValueError):
        logging.error("error occurred in b spline interpolation")
        return ctr

    return np.column_stack((out[0], out[1]))


def smoothen_lane(lanelet: Lanelet, min_dis=0.7, number_nodes=50) -> Lanelet:
    """
    Smoothens the vertices of a single lanelet

    :param1 lanelet: The lanelet which is manipulated
    :param2 min_dis: Minimum distance waypoints are supposed to have between each other
    :param3 number_nodes: Minimum number of nodes that shall be used for the b spline interpolation process
    :return: Smoothed lanelet
    """
    assert len(lanelet.left_vertices) == len(lanelet.right_vertices) == len(lanelet.center_vertices)

    if not number_nodes:
        number_nodes = len(lanelet.left_vertices)

    rv = lanelet.right_vertices
    lv = lanelet.left_vertices
    cv = lanelet.center_vertices
    filtered_lv = [lv[0]]
    filtered_rv = [rv[0]]
    filtered_cv = [cv[0]]

    # compute euclidean distance between last accepted way point and new waypoint
    for i in range(0, len(lanelet.left_vertices)):
        if not np.linalg.norm(filtered_rv[-1] - rv[i]) < min_dis:
            filtered_rv.append(rv[i])
        if not np.linalg.norm(filtered_lv[-1] - lv[i]) < min_dis:
            filtered_lv.append(lv[i])
        if not np.linalg.norm(filtered_cv[-1] - cv[i]) < min_dis:
            filtered_cv.append(cv[i])

    # add end waypoints in case they were filtered out in earlier step
    if not (rv[-1] == filtered_rv[-1]).all():
        filtered_rv.append(rv[-1])
    if not (lv[-1] == filtered_lv[-1]).all():
        filtered_lv.append(lv[-1])
    if not (cv[-1] == filtered_cv[-1]).all():
        filtered_cv.append(cv[-1])

    # convert to np.array
    filtered_lv = np.array(filtered_lv)
    filtered_rv = np.array(filtered_rv)
    filtered_cv = np.array(filtered_cv)

    # minimum vertices of all way points
    mv = min(len(filtered_lv), len(filtered_cv), len(filtered_rv))
    # fallback, if errors have occurred
    if mv <= 1:
        return lanelet

    # create new waypoints using b_splines if old waypoints changed
    length = len(lv)
    if any(len(wp) != length for wp in [rv, cv, filtered_lv, filtered_rv, filtered_cv]):
        num_nodes = max(mv, number_nodes)
        filtered_lv = b_spline(filtered_lv, max_nodes=num_nodes)
        filtered_rv = b_spline(filtered_rv, max_nodes=num_nodes)
        filtered_cv = b_spline(filtered_cv, max_nodes=num_nodes)

    assert len(filtered_lv) == len(filtered_rv), "error during b spline interpolation"
    return create_lanelet(lanelet, filtered_lv, filtered_rv, filtered_cv)


def convert_to_lht(scenario: Scenario) -> None:
    """
    checks if scenario is from left hand traffic country and converts it if necessary

    :param1 scenario: The scenario to be checked
    :return: None
    """
    if scenario.scenario_id.country_id in LEFT_HAND_TRAFFIC:
        logging.info("converting scenario to lht")
        rht_to_lht(scenario)


def rht_to_lht(scenario: Scenario) -> None:
    """
    Converts scenario to left hand traffic.
    WARNING! Use with caution. See Globetrotter thesis for more information

    :return: None
    """

    net = scenario.lanelet_network
    lanelets = net.lanelets

    lht_lanes = []
    for la in lanelets:
        adj_r_same = False
        adj_l_same = False
        if la.adj_right and la.adj_right_same_direction:
            adj_r_same = True
        if la.adj_left and la.adj_left_same_direction:
            adj_l_same = True

        lht_l = create_lanelet(
            lanelet=la,
            left_vertices=la.right_vertices,
            right_vertices=la.left_vertices,
            center_vertices=la.center_vertices,
            predecessor=la.successor,
            successor=la.predecessor,
            adjacent_right=la.adj_left,
            adjacent_left=la.adj_right,
            adjacent_right_same_direction=adj_l_same,
            adjacent_left_same_direction=adj_r_same,
        )

        lht_lanes.append(lht_l)

    scenario.replace_lanelet_network(
        create_laneletnetwork(
            lht_lanes,
            scenario.lanelet_network.traffic_signs,
            scenario.lanelet_network.traffic_lights,
            scenario.lanelet_network.intersections,
        )
    )


def remove_unconnected_lanes(scenario: Scenario):
    """
    Remove unconnected lanes which are not part of the scenario

    :param1 scenario: Scenario where operations are performed on
    :return: None
    """
    graph = scenario_to_networkx_graph(scenario)
    net = scenario.lanelet_network
    lanelets = net.lanelets

    # create connections for adjacent lanelets
    tmp_edges = []
    for la in lanelets:
        if la.adj_right:
            graph.add_edge(la.lanelet_id, la.adj_right)
            tmp_edges.append((la.lanelet_id, la.adj_right))
        if la.adj_left:
            graph.add_edge(la.lanelet_id, la.adj_left)
            tmp_edges.append((la.lanelet_id, la.adj_left))

    # choose the subgraph with the most forking points as intersection
    # more information about subgraphs:
    # https://networkx.github.io/documentation/networkx-1.10/reference/generated/networkx.algorithms.components.
    # weakly_connected.weakly_connected_component_subgraphs.html#networkx.algorithms.components.weakly_connected.
    # weakly_connected_component_subgraphs
    components = [graph.subgraph(c).copy() for c in nx.weakly_connected_components(graph)]

    main_graph = components[0]
    for comp in components:
        if comp.number_of_nodes() > main_graph.number_of_nodes():
            main_graph = comp

    filtered_lanelets = list(
        filter(lambda lanelet: lanelet.lanelet_id not in main_graph.nodes, lanelets)
    )
    for let in filtered_lanelets:
        scenario.remove_lanelet(let)


def scenario_to_networkx_graph(scenario) -> nx.DiGraph:
    """
    Convert scenario to NetworkX graph

    :return: networkX Graph
    """
    net = scenario.lanelet_network
    lanelets = net.lanelets
    lanelet_ids = [la.lanelet_id for la in lanelets]

    graph = nx.DiGraph(scenario=scenario)
    for la in lanelets:
        position = (
            np.mean([p[0] for p in la.center_vertices]),
            np.mean([p[1] for p in la.center_vertices]),
        )
        graph.add_node(la.lanelet_id, pos=position, lanelet=la)
        edges = [(la.lanelet_id, s) for s in la.successor if s in lanelet_ids]
        if edges:
            graph.add_edges_from(edges)

    return graph


def create_lanelet(
    lanelet,
    left_vertices,
    right_vertices,
    center_vertices,
    predecessor=None,
    successor=None,
    adjacent_right=None,
    adjacent_left=None,
    adjacent_right_same_direction=None,
    adjacent_left_same_direction=None,
    traffic_signs=None,
    traffic_lights=None,
) -> Lanelet:
    """
    Create a new lanelet given an old one. Vertices, successors and predecessors can be modified

    :param1 lanelet: The old lanelet
    :param2 left_vertices: New left vertices
    :param3 right_vertices: New right vertices
    :param4 center_vertices: New center vertices
    :param5 predecessor: optional new predecessor
    :param6 successor: Optional new successors
    :return: New Lanelet
    """
    if predecessor is None:
        predecessor = lanelet.predecessor
    if successor is None:
        successor = lanelet.successor
    if adjacent_left is None:
        adjacent_left = lanelet.adj_left
    if adjacent_right is None:
        adjacent_right = lanelet.adj_right
    if adjacent_left_same_direction is None:
        adjacent_left_same_direction = lanelet.adj_left_same_direction
    if adjacent_right_same_direction is None:
        adjacent_right_same_direction = lanelet.adj_right_same_direction
    if traffic_signs is None:
        traffic_signs = lanelet.traffic_signs
    if traffic_lights is None:
        traffic_lights = lanelet.traffic_lights

    # create new lanelet in CommomRoad2020 format
    new_lanelet = Lanelet(
        left_vertices=left_vertices,
        center_vertices=center_vertices,
        right_vertices=right_vertices,
        lanelet_id=lanelet.lanelet_id,
        predecessor=predecessor,
        successor=successor,
        adjacent_left=adjacent_left,
        adjacent_left_same_direction=adjacent_left_same_direction,
        adjacent_right=adjacent_right,
        adjacent_right_same_direction=adjacent_right_same_direction,
        line_marking_left_vertices=lanelet.line_marking_left_vertices,
        line_marking_right_vertices=lanelet.line_marking_right_vertices,
        stop_line=lanelet.stop_line,
        lanelet_type=lanelet.lanelet_type,
        user_one_way=lanelet.user_one_way,
        user_bidirectional=lanelet.user_bidirectional,
        traffic_signs=traffic_signs,
        traffic_lights=traffic_lights,
    )
    return new_lanelet


def create_laneletnetwork(lanelets, traffic_signs, traffic_lights, intersections) -> LaneletNetwork:
    """
    Create a new lanelet network

    :param1 lanelets: Lanelets used for the new network
    :param2 traffic_signs: Traffic signs used for the new network
    :param3 traffic_lights: Traffic lights used for the new network
    :param4 intersections: Intersections used for the new network
    :return: New lanelet network
    """
    net = LaneletNetwork()

    # Add lanelets
    for lanelet in lanelets:
        # In contrast to all other objects, the lanelets do not need to be copied,
        # because they are newly created by `create_lanelet` during the sanitization process.
        # Therefore, they should not be susceptible to the same problems as traffic signs/lights and intersections.
        net.add_lanelet(lanelet)

    # Traffic signs/lights and intersections all must be copied, so that modifications to the objects
    # in the original lanelet network do not spill over into the new lanelet network.

    # Add Traffic Signs
    for sign in traffic_signs:
        net.add_traffic_sign(copy.deepcopy(sign), set())

    # Add Traffic Lights
    for light in traffic_lights:
        net.add_traffic_light(copy.deepcopy(light), set())

    # Add Intersections
    for intersection in intersections:
        net.add_intersection(copy.deepcopy(intersection))

    return net
