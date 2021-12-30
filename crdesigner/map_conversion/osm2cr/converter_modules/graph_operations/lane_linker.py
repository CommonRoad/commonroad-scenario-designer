"""
This module provides all methods necessary to interconnect lanes.
"""
from typing import List, Tuple, Optional, Union, Dict

import numpy as np

from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import road_graph as rg


class CombinedEdge:
    """
    A wrapper class to encapsulate two one way edges to one object for the linking process

    """

    def __init__(self, edge1: rg.GraphEdge, edge2: rg.GraphEdge, node: rg.GraphNode):
        assert node == edge1.node1
        assert node == edge2.node2
        self.node1 = edge1.node1
        self.node2 = edge1.node2
        # self.lanes = edge2.lanes[::-1] + edge1.lanes
        self.edge1 = edge1
        self.edge2 = edge2

    def get_orientation(self, node) -> float:
        return self.edge1.get_orientation(node)

    def angle_to(
        self, other_edge: Union[rg.GraphEdge, "CombinedEdge"], node: rg.GraphNode
    ) -> float:
        if isinstance(other_edge, rg.GraphEdge):
            return self.edge1.angle_to(other_edge, node)
        elif isinstance(other_edge, CombinedEdge):
            return self.edge1.angle_to(other_edge.edge1, node)
        else:
            raise ValueError("other edge must be of type GraphEdge or CombinedEdge")

    def soft_angle(
        self, edge: Union[rg.GraphEdge, "CombinedEdge"], node: rg.GraphNode
    ) -> bool:
        if isinstance(edge, rg.GraphEdge):
            return self.edge1.soft_angle(edge, node)
        elif isinstance(edge, CombinedEdge):
            return self.edge1.soft_angle(edge.edge1, node)
        else:
            raise ValueError("edge must be of type GraphEdge or CombinedEdge")


def find_edges_to_combine(
    edges: List[rg.GraphEdge], node: rg.GraphNode
) -> List[Union[rg.GraphEdge, CombinedEdge]]:
    """
    finds edges which can be combined and returns updated list of edges

    :param edges: List of edges sorted counterclockwise
    :param node: The node at which the combination is applied
    :return:
    """
    # TODO move threshold to config.py?
    combine_angle_threshold = np.pi / 360.0 * 10.0
    result = []
    combine_with_next = [False] * len(edges)
    for index, edge in enumerate(edges):
        next_edge = edges[(index + 1) % len(edges)]
        if (
            edge.oneway
            and next_edge.oneway
            and edge.node1 == node
            and next_edge.node2 == node
            and edge.angle_to(next_edge, node) < combine_angle_threshold
            and edge.roadtype == next_edge.roadtype
        ):
            combine_with_next[index] = True
    for index in range(len(edges)):
        prev_edge = edges[(index - 1) % len(edges)]
        this_edge = edges[index]
        next_edge = edges[(index + 1) % len(edges)]
        if combine_with_next[(index - 1) % len(edges)]:
            pass
        elif combine_with_next[index]:
            result.append(CombinedEdge(this_edge, next_edge, node))
        else:
            result.append(this_edge)
    return result


def get_incomings_outgoings(
    edge: Union[rg.GraphEdge, CombinedEdge], node: rg.GraphNode
) -> Tuple[List[rg.Lane], List[rg.Lane]]:
    """
    returns the incoming and outgoing lanes of an edge at a node

    :param edge: edge
    :type edge: GraphEdge
    :param node: node
    :type node: GraphNode
    :return: incoming, outgoing: lists of lanes
    :rtype: Tuple[List[Lane], List[Lane]]
    """
    if isinstance(edge, CombinedEdge):
        if edge.node1 == node:
            incoming = edge.edge2.lanes
            outgoing = edge.edge1.lanes
        elif edge.node2 == node:
            incoming = edge.edge1.lanes
            outgoing = edge.edge2.lanes
        else:
            raise ValueError("malformed graph")
        return incoming, outgoing
    incoming = []
    outgoing = []
    for lane in edge.lanes:
        # lanes are sorted from left to right according to the direction of its edge
        # incoming and outgoing lanes are sorted from left to right according to their driving direction
        if edge.node1 == node:
            # forward_lanes begin here
            if lane.forward:
                outgoing.append(lane)
            else:
                incoming.insert(0, lane)
        elif edge.node2 == node:
            # forward_lanes end here
            if lane.forward:
                incoming.append(lane)
            else:
                outgoing.insert(0, lane)
        else:
            raise ValueError("malformed Graph, lanes are assigned to wrong nodes")
    return incoming, outgoing


def link_two_lanes(lane1: rg.Lane, lane2: rg.Lane):
    """
    links two lanes

    :param lane1: lane object, predecessor
    :type lane1: Lane
    :param lane2: lane object, successor
    :type lane2: Lane
    :return: None
    """
    lane1.successors.add(lane2)
    lane2.predecessors.add(lane1)
    return


def link_interval(
    incoming: List[rg.Lane],
    outgoing: List[rg.Lane],
    start_incoming: int,
    start_outgoing: int,
    length: int,
):
    """
    links incoming and outgoing lanes in given interval

    :param incoming: list of incoming lanes
    :type incoming: List[Lane]
    :param outgoing: list of outgoing lanes
    :type outgoing: List[Lane]
    :param start_incoming: index of first incoming lane to link
    :type start_incoming: int
    :param start_outgoing: index of first outgoing lane to ling
    :type start_outgoing: int
    :param length: nr of links to create
    :type: length: int
    :return: None
    """
    if length > min(len(incoming) - start_incoming, len(outgoing) - start_outgoing):
        raise ValueError("interval is larger than set of lanes")
    if start_incoming < 0 or start_outgoing < 0:
        print("Info: length of outgoing lanes: {}".format(len(outgoing)))
        raise ValueError("index is lower than zero")
    for index in range(length):
        link_two_lanes(
            incoming[index + start_incoming], outgoing[index + start_outgoing]
        )
    return


def link_incoming_outgoing(
    incoming: List[rg.Lane], outgoing: List[rg.Lane], start_left: bool
):
    """
    links incoming and outgoing lanes, if one list is larger the additional lanes are not linked

    :param incoming: list of incoming lanes
    :type incoming: List[Lane]
    :param outgoing: list of outgoing lanes
    :type outgoing: List[Lane]
    :param start_left: if true linking is started from the beginning of the list, else from the end
    :type start_left: bool
    :return: None
    """
    nr_of_links = min(len(incoming), len(outgoing))
    for index in range(nr_of_links):
        if start_left:
            link_two_lanes(incoming[index], outgoing[index])
        else:
            link_two_lanes(incoming[-1 - index], outgoing[-1 - index])
    return


def link_full_incoming_outgoing(
    incoming: List[rg.Lane], outgoing: List[rg.Lane], merge_at_left: bool
):
    """
    links incoming and outgoing lanes,
    if one list is larger the additional lanes are linked to the first or last lane of the other list

    :param incoming: list of incoming lanes
    :type incoming: List[Lane]
    :param outgoing: list of outgoing lanes
    :type: outgoing: List[Lane]
    :param merge_at_left: if true additional lanes are linked to the first lane of the other list, else to the last
    :type merge_at_left: bool
    :return: None
    """
    link_incoming_outgoing(incoming, outgoing, not merge_at_left)
    if len(incoming) < len(outgoing):
        # new lanes are created
        difference = len(outgoing) - len(incoming)
        link_incoming_outgoing(incoming, outgoing, not merge_at_left)
        if merge_at_left:
            # new lanes are created at the left
            for index in range(difference):
                if not len(incoming) == 0:
                    link_two_lanes(incoming[0], outgoing[index])
        else:
            # new lanes are created at the right
            for index in range(difference):
                if not len(incoming) == 0:
                    link_two_lanes(incoming[-1], outgoing[-1 - index])
    elif len(incoming) > len(outgoing):
        # lanes are removed
        difference = len(incoming) - len(outgoing)
        if merge_at_left:
            # lanes are removed at the left
            for index in range(difference):
                if not len(outgoing) == 0:
                    link_two_lanes(incoming[index], outgoing[0])
        else:
            # lanes are removed at the right
            for index in range(difference):
                if not len(outgoing) == 0:
                    link_two_lanes(incoming[-1 - index], outgoing[-1])
    return


def get_turnlane_usefull(
    turnlanes: List[str],
    incoming: List[rg.Lane],
    outgoing_left: List[rg.Lane],
    outgoing_through: Optional[List[rg.Lane]],
    outgoing_right: List[rg.Lane],
    fourway: bool,
    edge: rg.GraphEdge,
    edge_left: Optional[rg.GraphEdge],
    edge_right: Optional[rg.GraphEdge],
    node: rg.GraphNode,
) -> Tuple[bool, str]:
    """
    checks if the given turnlanes make sense an can be used for linking
    gives back rotation of turnlanes for 3way intersections

    :param turnlanes: list of turnlanes
    :type turnlanes: List[str]
    :param incoming: list of incoming lanes
    :type incoming: List[Lane]
    :param outgoing_left: list of outgoing lanes at the left
    :type outgoing_left: List[Lane]
    :param outgoing_through: list of outgoing lanes at the opposite side
    :type outgoing_through: List[Lane]
    :param outgoing_right: list of outgoing lanes at the right
    :type outgoing_right: List[Lane]
    :param fourway: if true the intersection is a 4way intersection, else 3way
    :type fourway: bool
    :param edge: the edge the incoming lanes belong to
    :type edge: GraphEdge
    :param edge_left: the edge the outgoing lanes at the left belong to
    :type edge_left: GraphEdge
    :param edge_right: the edge the outgoing lanes at the right belong to
    :type edge_right: GraphEdge
    :param node: the node of the intersection
    :type node: GraphNode
    :return: turnlane_useful: true if the turnlanes can be used for linking,
             threeway_rotate: states if 'through' tags should be switched with 'left' or 'right'
    :rtype: Tuple[bool, str]
    """
    turnlane_useful = True
    left_turnlanes = 0
    through_turnlanes = 0
    right_turnlanes = 0
    none_turnlanes = 0
    threeway_rotate = None
    through = False
    right = False
    for turnlane in turnlanes:
        if turnlane == "merge_to_right" or turnlane == "merge_to_left":
            turnlane_useful = False
        if turnlane == "none":
            none_turnlanes += 1
        else:
            if (
                turnlane == "left"
                or turnlane == "left;through"
                or turnlane == "left;right"
                or turnlane == "left;through;right"
            ):
                if through or right:
                    turnlane_useful = False
                left_turnlanes += 1
            if (
                turnlane == "through"
                or turnlane == "left;through"
                or turnlane == "through;right"
                or turnlane == "left;through;right"
            ):
                through_turnlanes += 1
                through = True
                if right:
                    turnlane_useful = False
            if (
                turnlane == "right"
                or turnlane == "through;right"
                or turnlane == "left;right"
                or turnlane == "left;through;right"
            ):
                right_turnlanes += 1
                right = True
    if fourway:
        # check for a 4way intersection
        if (
            none_turnlanes == len(incoming)
            or left_turnlanes > len(outgoing_left)
            or right_turnlanes > len(outgoing_right)
            or through_turnlanes > len(outgoing_through)
        ):
            turnlane_useful = False
    else:
        # check for 3way intersection
        if left_turnlanes > 0 and through_turnlanes > 0 and right_turnlanes > 0:
            turnlane_useful = False
        if none_turnlanes == len(incoming):
            turnlane_useful = False
        if left_turnlanes > 0 and through_turnlanes > 0 and right_turnlanes == 0:
            # rotate through to right
            if left_turnlanes > len(outgoing_left) or through_turnlanes > len(
                outgoing_right
            ):
                turnlane_useful = False
            threeway_rotate = "through_to_right"
        elif left_turnlanes > 0 and through_turnlanes == 0 and right_turnlanes > 0:
            # nothing to rotate here
            if left_turnlanes > len(outgoing_left) or right_turnlanes > len(
                outgoing_right
            ):
                turnlane_useful = False
        elif left_turnlanes == 0 and through_turnlanes > 0 and right_turnlanes > 0:
            # rotate through to left
            if through_turnlanes > len(outgoing_left) or right_turnlanes > len(
                outgoing_right
            ):
                turnlane_useful = False
            threeway_rotate = "through_to_left"
        else:
            if left_turnlanes > 0 and through_turnlanes == 0 and right_turnlanes == 0:
                if left_turnlanes > len(outgoing_left):
                    turnlane_useful = False
            elif left_turnlanes == 0 and through_turnlanes > 0 and right_turnlanes == 0:
                # check which direction via geometry
                left_angle = edge.angle_to(edge_left, node)
                right_angle = edge.angle_to(edge_right, node)
                if left_angle > right_angle:
                    # rotate through to left
                    if through_turnlanes > len(outgoing_left):
                        turnlane_useful = False
                    threeway_rotate = "through_to_left"
                else:
                    # rotate through to right
                    if through_turnlanes > len(outgoing_right):
                        turnlane_useful = False
                    threeway_rotate = "through_to_right"
            elif left_turnlanes == 0 and through_turnlanes == 0 and right_turnlanes > 0:
                if right_turnlanes > len(outgoing_right):
                    turnlane_useful = False
    return turnlane_useful, threeway_rotate


def set_turnlane_borders(
    turnlanes: List[str],
    incoming: List[rg.Lane],
    outgoing_left: List[rg.Lane],
    outgoing_through: List[rg.Lane],
    outgoing_right: List[rg.Lane],
    turnlane_useful: bool,
    edge: rg.GraphEdge,
    edge_through: Optional[rg.GraphEdge],
    edge_left: rg.GraphEdge,
    edge_right: rg.GraphEdge,
    node: rg.GraphNode,
) -> Tuple[int, int, int, int]:
    """
    sets the borders of the three sections of turnlanes: left, through and right
    these sections can intersect at at most one lane

    :param turnlanes: list of turnlanes
    :type turnlanes: List[str]
    :param incoming: list of incoming lanes
    :type incoming: List[Lane]
    :param outgoing_left: list of outgoing lanes at the left
    :type outgoing_left: List[Lane]
    :param outgoing_through: list of outgoing lanes at the opposite side
    :type outgoing_through: List[Lane]
    :param outgoing_right: list of outgoing lanes at the right
    :type outgoing_right: List[Lane]
    :param turnlane_useful: if true turnlanes can be used
    :type turnlane_useful: bool
    :param edge: the edge the incoming lanes belong to
    :type edge: GraphEdge
    :param edge_through: the edge the outgoing lanes in the middle belong to
    :type edge_through: GraphEdge
    :param edge_left: the edge the outgoing lanes at the left belong to
    :type edge_left: GraphEdge
    :param edge_right: the edge the outgoing lanes at the right belong to
    :type edge_right: GraphEdge
    :param node: the node of the intersection
    :type node: GraphNode
    :return: borders of groups: last_left, first_through, last_through, first_right
    :rtype: Tuple[int, int, int, int]
    """
    last_left, first_through, last_through, first_right = None, None, None, None
    upper_bound_left = min(len(incoming) - 1, len(outgoing_left) - 1)
    lower_bound_through = 0
    upper_bound_through = len(incoming) - 1
    lower_bound_right = max(0, len(incoming) - len(outgoing_right))
    if turnlane_useful:
        for index, turnlane in enumerate(turnlanes):
            if turnlane == "left":
                lower_bound_through = max(lower_bound_through, index + 1)
                lower_bound_right = max(lower_bound_right, index + 1)
            elif turnlane == "through":
                upper_bound_left = min(upper_bound_left, index - 1)
                lower_bound_right = max(lower_bound_right, index + 1)
            elif turnlane == "right":
                upper_bound_left = min(upper_bound_left, index - 1)
                upper_bound_through = min(upper_bound_through, index - 1)
            elif turnlane == "left;through":
                last_left = index
                first_through = index
                lower_bound_right = max(lower_bound_right, index + 1)
            elif turnlane == "through;right":
                last_through = index
                first_right = index
                upper_bound_left = min(upper_bound_left, index - 1)
            elif turnlane == "left;through;right":
                last_left = index
                first_through = index
                last_through = index
                first_right = index
            elif turnlane == "left;right":
                last_left = index
                first_through = index
                last_through = index - 1
                first_right = index
            elif turnlane == "none":
                pass

        # update bounds
        if last_left is not None:
            upper_bound_left = min(upper_bound_left, last_left)
        if first_through is not None:
            lower_bound_through = max(lower_bound_through, first_through)
        if last_through is not None:
            upper_bound_through = min(upper_bound_through, last_through)
        if first_right is not None:
            lower_bound_right = max(lower_bound_right, first_right)

        # create missing borders
        if first_through is None:
            nr = min(len(incoming), len(outgoing_through))
            if last_through is not None:
                first_through = max(last_through - nr + 1, lower_bound_through)
            else:
                if nr <= 0:
                    first_through = lower_bound_through
                else:
                    first_through = max(
                        lower_bound_through, upper_bound_through - nr + 1
                    )
        if last_through is None:
            nr = min(len(incoming), len(outgoing_through))
            last_through = min(upper_bound_through, first_through + nr - 1)
        if last_left is None:
            nr = min(len(incoming), len(outgoing_left))
            last_left = min(upper_bound_left, nr - 1)
        if first_right is None:
            nr = min(len(incoming) - last_through, len(outgoing_right))
            first_right = max(lower_bound_right, len(incoming) - nr)

        # check if borders are valid
        if (
            last_left in range(-1, len(incoming))
            and first_through in range(0, len(incoming) + 1)
            and last_through in range(-1, len(incoming))
            and first_right in range(0, len(incoming) + 1)
            and last_left + 1 <= len(outgoing_left)
            and len(incoming) - first_right <= len(outgoing_right)
            and last_through - first_through + 1 <= len(outgoing_through)
        ):
            # turnlanes useful
            pass
        else:
            # turnlane info is erroneous, turnlanes are not used
            last_left, first_through, last_through, first_right = None, None, None, None
            turnlane_useful = False
            print("Warning: turnlanes are inconsistent and are therefore ignored")

    if not turnlane_useful:
        # Fallback if turnlanes of successor are the same, set all to through
        if edge_through is not None and isinstance(edge_through, rg.GraphEdge):
            if edge_through.node1 == node:
                next_turnlanes = edge_through.turnlanes_forward
            elif edge_through.node2 == node:
                next_turnlanes = edge_through.turnlanes_backward
            else:
                raise ValueError("malformed Graph, lanes are assigned to wrong nodes")
            if next_turnlanes == turnlanes:
                last_left = -1
                first_through = 0
                last_through = len(incoming) - 1
                first_right = len(incoming)
                turnlane_useful = True

        if not turnlane_useful:
            # assume all borders
            through_nr = min(len(incoming), len(outgoing_through))
            if edge.soft_angle(edge_left, node):
                left_nr = min(len(incoming), len(outgoing_left))
            else:
                left_nr = 0
            if edge.soft_angle(edge_right, node):
                right_nr = min(len(incoming), len(outgoing_right))
            else:
                right_nr = 0
            first_through = max(0, min(left_nr, len(incoming) - through_nr - right_nr))
            last_through = min(
                len(incoming) - 1,
                max(-1, len(incoming) - right_nr + 1),
                first_through + through_nr - 1,
            )
            last_left = max(-1, min(first_through, left_nr - 1))
            first_right = max(0, last_through, len(incoming) - right_nr)

    # assert that borders are valid
    for index, border in enumerate(
        (last_left, first_through, last_through, first_right)
    ):
        assert border is not None
    assert last_left in range(-1, len(incoming))
    assert first_through in range(0, len(incoming) + 1)
    assert last_through in range(-1, len(incoming))
    assert first_right in range(0, len(incoming) + 1)
    assert last_left + 1 <= len(outgoing_left)
    assert len(incoming) - first_right <= len(outgoing_right)
    assert last_through - first_through + 1 <= len(outgoing_through)

    return last_left, first_through, last_through, first_right


def find_next_linked_lane(lanes: List[rg.Lane], index: int, predecessor: bool) -> int:
    """
    finds the nearest lane in a list which has a predecessor or successer

    :param lanes: list of lanes
    :type lanes: List[Lane]
    :param index: index of the lane
    :type index: int
    :param predecessor: if true a neighbor with a predecessor is searched, otherwise a neighbor with a successor
    :type predecessor: bool
    :return: index of the nearest linked neighbor
    :rtype: int
    """
    assert len(lanes) > 0
    assert index in range(0, len(lanes))
    distance = 0
    while distance <= len(lanes):
        distance += 1
        if predecessor:
            if index - distance >= 0 and lanes[index - distance].predecessors:
                return index - distance
            if len(lanes) > index + distance and lanes[index + distance].predecessors:
                return index + distance
        else:
            if index - distance >= 0 and lanes[index - distance].successors:
                return index - distance
            if len(lanes) > index + distance and lanes[index + distance].successors:
                return index + distance
    return -1


def link_skipped_lanes(node: rg.GraphNode):
    """
    links lanes that do not have predecessors or successors

    :param node: respective node
    :type node: GraphNode
    :return: None
    """
    for index, edge in enumerate(node.edges):
        incoming, outgoing = get_incomings_outgoings(edge, node)
        for lane_index, lane in enumerate(outgoing):
            if not lane.predecessors:
                linked_lane_index = find_next_linked_lane(outgoing, lane_index, True)
                if linked_lane_index > -1:
                    lane_to_link = next(iter(outgoing[linked_lane_index].predecessors))
                    lane_to_link.successors.add(lane)
                    lane.predecessors.add(lane_to_link)
        for lane_index, lane in enumerate(incoming):
            if not lane.successors:
                linked_lane_index = find_next_linked_lane(incoming, lane_index, False)
                if linked_lane_index > -1:
                    lane_to_link = next(iter(incoming[linked_lane_index].successors))
                    lane_to_link.predecessors.add(lane)
                    lane.successors.add(lane_to_link)
    return


def merge_left(incoming: List[rg.Lane], outgoing: List[rg.Lane]) -> bool:
    """
    estimates if a intersection should merge lanes at the left or at the right,
    chooses always left, except two cases:
    - new turn lane turning right follows at the right
    - left lane has tag merge_to_left

    :param incoming: incoming lanes
    :type incoming: List[Lane]
    :param outgoing: outgoing lanes
    :type outgoing: List[Lane]
    :return: True if merge at left, False else
    :rtype: bool
    """
    merge_at_left = True
    if (
        len(incoming) > len(outgoing)
        and len(incoming) >= 1
        and ("left" in incoming[-1].turnlane
             or any([p.turnlane in ("merge_to_left", "slight_left") for p in incoming[-1].predecessors]))
    ):
        merge_at_left = False
    elif len(incoming) < len(outgoing) and "right" in outgoing[-1].turnlane:
        merge_at_left = False
    return merge_at_left


def linkleft_interval(
    last_left: int, incoming: List[rg.Lane], outgoing_left: List[rg.Lane]
):
    """
    links all incoming lanes at an intersection to the lanes outgoing left

    :param last_left: index of the last lane turning to the left
    :type last_left: int
    :param incoming: lanes coming to the intersection
    :type incoming: List[Lane]
    :param outgoing_left: lanes leaving the intersection at the left
    :type outgoing_left: List[Lane]
    :return: None
    """
    if last_left + 1 > 0:
        start_at = 0
        if (
            len(outgoing_left) > last_left + 1
            and outgoing_left[0].turnlane == "left"
            and outgoing_left[1].turnlane != "left"
        ):
            start_at += 1
        link_interval(incoming, outgoing_left, 0, start_at, last_left + 1)
    return


def link_right_interval(
    first_right: int, incoming: List[rg.Lane], outgoing_right: List[rg.Lane]
):
    """
    links all incoming lanes at an intersection to the lanes outgoing right

    :param first_right: index of the first lane turning right
    :type first_right: int
    :param incoming: lanes coming to the intersection
    :type incoming: List[Lane]
    :param outgoing_right: lanes leaving the intersection at the left
    :type outgoing_right: List[Lane]
    :return: None
    """
    outgoing_right_nr = len(incoming) - first_right
    if outgoing_right_nr > 0:
        start_outgoing = len(outgoing_right) - outgoing_right_nr
        link_interval(
            incoming, outgoing_right, first_right, start_outgoing, outgoing_right_nr
        )


def link_through_interval(
    last_through: int,
    first_through: int,
    incoming: List[rg.Lane],
    outgoing_through: List[rg.Lane],
):
    """
    links a incoming lanes at an intersection to through lanes

    :param last_through: index of the first incoming lane to link
    :type last_through: int
    :param first_through: index of the last incoming lane to link
    :type first_through: int
    :param incoming: coming to the intersection
    :type incoming: List[Lane]
    :param outgoing_through: lanes leaving the intersection across
    :type outgoing_through: List[Lane]
    :return: None
    """
    outgoing_through_nr = last_through - (first_through - 1)
    if outgoing_through_nr > 0:
        start_outgoing = int(np.ceil((len(outgoing_through) - outgoing_through_nr) / 2))
        link_interval(
            incoming,
            outgoing_through,
            first_through,
            start_outgoing,
            outgoing_through_nr,
        )


def link_second_degree(node: rg.GraphNode):
    """
    links two roads at a node with a 2way intersection

    :param node: the node of the intersection
    :type node: GraphNode
    :return: None
    """
    # assert node.get_degree() == 2
    edge1 = list(node.edges)[0]
    edge2 = list(node.edges)[1]
    incoming1, outgoing1 = get_incomings_outgoings(edge1, node)
    incoming2, outgoing2 = get_incomings_outgoings(edge2, node)
    # full link between streets
    for incoming, outgoing in [(incoming1, outgoing2), (incoming2, outgoing1)]:
        link_full_incoming_outgoing(incoming, outgoing, merge_left(incoming, outgoing))


def link_third_degree(
    node: rg.GraphNode, edges: List[Union[rg.GraphEdge, CombinedEdge]]
):
    """
    links three roads at a node with a 3way intersection

    :param node: the node of the intersection
    :type node: GraphNode
    :param edges: edges to link
    :return: None
    """
    assert node.get_degree() == 3
    for index, edge in enumerate(edges):
        incoming, outgoing = get_incomings_outgoings(edge, node)
        turnlanes = []
        for lane in incoming:
            turnlanes.append(lane.turnlane)
        edge_left, edge_right = edges[(index - 1) % 3], edges[(index + 1) % 3]
        incoming_left, outgoing_left = get_incomings_outgoings(edge_left, node)
        incoming_right, outgoing_right = get_incomings_outgoings(edge_right, node)

        turnlane_useful, rotate = get_turnlane_usefull(
            turnlanes,
            incoming,
            outgoing_left,
            None,
            outgoing_right,
            False,
            edge,
            edge_left,
            edge_right,
            node,
        )

        # Only left and right turns are used for 3way intersections. Through lanes are rotated
        if turnlane_useful and rotate is not None:
            if rotate == "through_to_left":
                for turnlane_index, turnlane in enumerate(turnlanes):
                    turnlanes[turnlane_index] = turnlane.replace("through", "left")
                rotate_restrictions(edge, node, "left")
            elif rotate == "through_to_right":
                for turnlane_index, turnlane in enumerate(turnlanes):
                    turnlanes[turnlane_index] = turnlane.replace("through", "right")
                rotate_restrictions(edge, node, "right")

        last_left, first_through, last_through, first_right = set_turnlane_borders(
            turnlanes,
            incoming,
            outgoing_left,
            [],
            outgoing_right,
            turnlane_useful,
            edge,
            None,
            edge_left,
            edge_right,
            node,
        )

        # connect lanes
        linkleft_interval(last_left, incoming, outgoing_left)
        link_right_interval(first_right, incoming, outgoing_right)
    link_skipped_lanes(node)


def link_fourth_degree(
    node: rg.GraphNode, edges: List[Union[rg.GraphEdge, CombinedEdge]]
):
    """
    links four roads at a node with a 4way intersection

    :param node: the node of the intersection
    :type node: GraphNode
    :param edges: the edges to link
    :return: None
    """
    assert len(edges) == 4
    for index, edge in enumerate(edges):
        incoming, outgoing = get_incomings_outgoings(edge, node)
        turnlanes = []
        for lane in incoming:
            turnlanes.append(lane.turnlane)

        edge_left = edges[(index - 1) % 4]
        edge_through = edges[(index - 2) % 4]
        edge_right = edges[(index - 3) % 4]
        incoming_left, outgoing_left = get_incomings_outgoings(edge_left, node)
        incoming_through, outgoing_through = get_incomings_outgoings(edge_through, node)
        incoming_right, outgoing_right = get_incomings_outgoings(edge_right, node)

        forbidden_turns = get_forbidden_turns(edge, node)
        if config.USE_RESTRICTIONS:
            if forbidden_turns["left"]:
                outgoing_left = []
            if forbidden_turns["right"]:
                outgoing_right = []
            if forbidden_turns["through"]:
                outgoing_through = []

        turnlane_useful, _ = get_turnlane_usefull(
            turnlanes,
            incoming,
            outgoing_left,
            outgoing_through,
            outgoing_right,
            True,
            edge,
            None,
            None,
            node,
        )

        last_left, first_through, last_through, first_right = set_turnlane_borders(
            turnlanes,
            incoming,
            outgoing_left,
            outgoing_through,
            outgoing_right,
            turnlane_useful,
            edge,
            edge_through,
            edge_left,
            edge_right,
            node,
        )

        # connect lanes
        linkleft_interval(last_left, incoming, outgoing_left)
        link_right_interval(first_right, incoming, outgoing_right)
        link_through_interval(last_through, first_through, incoming, outgoing_through)
    link_skipped_lanes(node)


def link_high_degree(
    node: rg.GraphNode, edges: List[Union[rg.GraphEdge, CombinedEdge]]
):
    """
    links all roads at a node with a multi way intersection
    this method only provides a simple procedure

    :param node: the node of the intersection
    :type node: GraphNode
    :param edges: the edges to link
    :return: None
    """
    for index, edge in enumerate(edges):
        incoming, outgoing = get_incomings_outgoings(edge, node)
        turnlanes = []
        for lane in incoming:
            turnlanes.append(lane.turnlane)

        other_edges = edges[index + 1:] + edges[:index]
        for other_edge_index, other_edge in enumerate(other_edges):
            if edge.soft_angle(other_edge, node):
                incoming_other, outgoing_other = get_incomings_outgoings(
                    other_edge, node
                )
                rightturn = other_edge_index < len(other_edges) / 2
                link_interval_size = min(len(incoming), len(outgoing_other))
                if rightturn:
                    start_incoming = len(incoming) - link_interval_size
                    start_outgoing = len(outgoing_other) - link_interval_size
                else:
                    start_incoming = 0
                    start_outgoing = 0
                link_interval(
                    incoming,
                    outgoing_other,
                    start_incoming,
                    start_outgoing,
                    link_interval_size,
                )
    link_skipped_lanes(node)


def get_forbidden_turns(edge: rg.GraphEdge, node: rg.GraphNode) -> Dict[str, bool]:
    if edge.node1 == node:
        restrictions = edge.backward_restrictions
    elif edge.node2 == node:
        restrictions = edge.forward_restrictions
    else:
        raise ValueError("malformed graph")
    if restrictions is None:
        restrictions = set()
    result = {"left": False, "through": False, "right": False}
    if "no_left_turn" in restrictions:
        result["left"] = True
    if "no_right_turn" in restrictions:
        result["right"] = True
    if "no_straight_on" in restrictions:
        result["through"] = True
    return result


def rotate_restrictions(edge: rg.GraphEdge, node: rg.GraphNode, direction: str):
    """
    rotates through restrictions to left or right according to direction parameter

    :param edge:
    :param node:
    :param direction:
    :return:
    """
    assert direction in ("left", "right")
    if edge.node1 == node:
        restrictions = edge.backward_restrictions
    elif edge.node2 == node:
        restrictions = edge.forward_restrictions
    else:
        raise ValueError("malformed graph")
    if "no_straight_on" in restrictions:
        restrictions -= "no_straight_on"
        restrictions.add("no_{}_turn".format(direction))


def link_graph(graph: rg.Graph):
    """
    links all lanes in a graph

    :param graph: the graph to link
    :type graph: Graph
    :return: None
    """
    for node in graph.nodes:
        # edges are sorted counterclockwise
        edges = sorted(node.edges, key=lambda e: e.get_orientation(node))
        edges = find_edges_to_combine(edges, node)
        nr_of_edges = len(edges)
        if nr_of_edges == 1:
            # nothing to link here
            pass
        elif nr_of_edges == 2:
            link_second_degree(node)
        elif nr_of_edges == 3:
            link_third_degree(node, edges)
        elif nr_of_edges == 4:
            link_fourth_degree(node, edges)
        else:
            link_high_degree(node, edges)
