"""
This module removes converting errors which occurred during the previous steps of the osm2cr converter
"""
import numpy as np
from commonroad.scenario.scenario import Scenario, Lanelet, LaneletNetwork, Tag, Location

def sanitize(scenario: Scenario) -> Scenario:
    """
    Sanitize resulting scenarios before export

    :param1 scenario: Scenario where operations will be performed on
    :return: Sanitized scenario
    """
    return merge_short_lanes(scenario)


def merge_short_lanes(scenario: Scenario, min_distance=1) -> Scenario:
    """
    Merges faulty short lanes with their longer successors

    :param1 scenario: Scenario whose short lanelets will be removed
    :param2 min_distance: Minimum distance a single lanelet has to have to not be merged
    :return: Sanitized scenario
    """
    lanelets = scenario.lanelet_network.lanelets
    net = scenario.lanelet_network

    # collect all faulty lanelets
    too_small = []
    for l in lanelets:
        if l.distance[-1] < min_distance:
            too_small.append(l.lanelet_id)

    # iterate over all too small lanelets
    while len(too_small) > 0:
        lanelets = scenario.lanelet_network.lanelets.copy()
        net = scenario.lanelet_network

        l_id = too_small.pop()
        l = net.find_lanelet_by_id(l_id)

        if l not in lanelets:
            continue

        if len(l.successor) == 0 and len(l.predecessor) == 1:
            pre = net.find_lanelet_by_id(l.predecessor[0])
            new_pre = create_lanelet(pre, pre.left_vertices, pre.right_vertices, pre.center_vertices, successor=[])
            lanelets.remove(l)
            lanelets.append(new_pre)
            continue

        if len(l.successor) == 1 and len(l.predecessor) == 0:
            suc = net.find_lanelet_by_id(l.successor[0])
            new_suc = create_lanelet(suc, suc.left_vertices, suc.right_vertices, suc.center_vertices, predecessor=[])
            lanelets.remove(l)
            lanelets.append(new_suc)
            continue

        successors = l.successor
        predecessors = l.predecessor

        for suc in successors:
            suc_l = net.find_lanelet_by_id(suc)
            merged_lanelet = merge_lanelets(l, suc_l)
            lanelets.remove(suc_l)
            lanelets.append(merged_lanelet)

        lanelets.remove(l)

        # merge lanelets does not modify the predecessors's successor
        for pre in predecessors:
            pre_lanelet = net.find_lanelet_by_id(pre)
            sucs_of_pre = list(filter(lambda s: s != l_id, pre_lanelet.successor))
            sucs_of_pre.extend(successors)
            new_pre = create_lanelet(pre_lanelet, pre_lanelet.left_vertices, pre_lanelet.right_vertices, pre_lanelet.center_vertices, predecessor=pre_lanelet.predecessor, successor=sucs_of_pre)
            lanelets.remove(pre_lanelet)
            lanelets.append(new_pre)

        # update scenario's road network
        scenario.lanelet_network = scenario.lanelet_network.create_from_lanelet_list(lanelets)

    return scenario


def merge_lanelets(lanelet1: Lanelet, lanelet2: Lanelet) -> Lanelet:
    """
    Merges two lanelets which are in predecessor-successor relation. Modified version from commonroad-io which does not remove adj lanelets (and speedlimits)

    :param lanelet1: The first lanelet
    :param lanelet2: The second lanelet
    :return: Merged lanelet (predecessor => successor)
    """
    assert isinstance(lanelet1, Lanelet), '<Lanelet/merge_lanelets>: lanelet1 is not a valid lanelet object!'
    assert isinstance(lanelet2, Lanelet), '<Lanelet/merge_lanelets>: lanelet1 is not a valid lanelet object!'
    # check connection via successor / predecessor
    assert lanelet1.lanelet_id in lanelet2.successor or lanelet2.lanelet_id in lanelet1.successor,\
        '<Lanelet/merge_lanelets>: cannot merge two not connected lanelets! successors of l1 = {}, successors of l2 = {}'.format(
        lanelet1.successor, lanelet2.successor)

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

    return create_lanelet(suc, left_vertices, right_vertices, center_vertices, predecessor=predecessor, successor=successor)


def create_lanelet(l, left_vertices, right_vertices, center_vertices, predecessor=None, successor=None):
    """
    Create a new lanelet given an old one. Vertices, successors and predecessors can be modified
    :param1 l: The old lanelet
    :param2 left_vertices: New left vertices
    :param3 right_vertices: New right vertices
    :param4 center_vertices: New center vertices
    :param5 predecessor: optional new predecessor
    :param6 successor: Optional new successors
    :return: New Lanelet
    """
    if predecessor is None:
        predecessor = l.predecessor
    if successor is None:
        successor = l.successor

    # create new lanelet in CommomRoad2020 format
    new_lanelet = Lanelet(
        left_vertices=left_vertices,
        center_vertices=center_vertices,
        right_vertices=right_vertices,
        lanelet_id=l.lanelet_id,
        predecessor=predecessor,
        successor=successor,
        adjacent_left=l.adj_left,
        adjacent_left_same_direction=l.adj_left_same_direction,
        adjacent_right=l.adj_right,
        adjacent_right_same_direction=l.adj_right_same_direction,
        line_marking_left_vertices=l.line_marking_left_vertices,
        line_marking_right_vertices=l.line_marking_right_vertices,
        stop_line=l.stop_line,
        lanelet_type=l.lanelet_type,
        user_one_way=l.user_one_way,
        user_bidirectional=l.user_bidirectional,
        traffic_signs=l.traffic_signs,
        traffic_lights=l.traffic_lights
    )
    return new_lanelet
