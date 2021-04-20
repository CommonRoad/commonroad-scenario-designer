# -*- coding: utf-8 -*-

"""Module to enhance LaneletNetwork class
so it can be used for conversion from the opendrive format."""
import itertools
import warnings
from typing import List, Optional
from queue import Queue
import numpy as np

from commonroad.scenario.lanelet import LaneletNetwork, StopLine
from commonroad.scenario.intersection import IntersectionIncomingElement, Intersection
from commonroad.scenario.traffic_sign import TrafficLightDirection, TrafficLight, TrafficSign

from crdesigner.conversion.osm2cr import config
from crdesigner.conversion.osm2cr.converter_modules.utility import geometry

from crdesigner.conversion.opendrive.opendriveconversion.conversion_lanelet import ConversionLanelet

__author__ = "Benjamin Orthen, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


def convert_to_new_lanelet_id(old_lanelet_id: str, ids_assigned: dict) -> int:
    """Convert the old lanelet ids (format 501.1.-1.-1) to newer,
    simpler ones (100, 101 etc.).

    Do this by consecutively assigning
    numbers, starting at 100, to the old_lanelet_id strings. Save the
    assignments in the dict which is passed to the function as ids_assigned.

    Args:
      old_lanelet_id: Old id with format "501.1.-1.-1".
      ids_assigned: Dict with all previous assignments

    Returns:
      The new lanelet id.

    """

    starting_lanelet_id = 100

    if old_lanelet_id in ids_assigned.keys():
        new_lanelet_id = ids_assigned[old_lanelet_id]
    else:
        try:
            new_lanelet_id = max(ids_assigned.values()) + 1
        except ValueError:
            new_lanelet_id = starting_lanelet_id
        ids_assigned[old_lanelet_id] = new_lanelet_id

    return new_lanelet_id


class ConversionLaneletNetwork(LaneletNetwork):
    """Add functions to LaneletNetwork which
    further enable it to modify its Lanelets."""

    def __init__(self):
        super().__init__()
        self._old_lanelet_ids = {}

    def old_lanelet_ids(self):
        return self._old_lanelet_ids

    def remove_lanelet(self, lanelet_id: str, remove_references: bool = False):
        """Remove a lanelets with the specific lanelet_id
        from the _lanelets dict.

        Args:
          lanelet_id: id of lanelet to be removed.
          remove_references: Also remove references which point to to be removed lanelet.

        Returns:
          None

        """
        del self._lanelets[lanelet_id]
        if remove_references:
            for lanelet in self.lanelets:
                lanelet.predecessor[:] = [
                    pred for pred in lanelet.predecessor if pred != lanelet_id
                ]

                lanelet.successor[:] = [
                    succ for succ in lanelet.successor if succ != lanelet_id
                ]
                if lanelet.adj_right == lanelet_id:
                    lanelet.adj_right = None
                if lanelet.adj_left == lanelet_id:
                    lanelet.adj_left = None

    def find_lanelet_by_id(self, lanelet_id) -> ConversionLanelet:
        """Find a lanelet for a given lanelet_id.
        Disable natural number check of parent class.

        Args:
          lanelet_id: The id of the lanelet to find

        Returns:
          The lanelet object if the id exists and None otherwise

        """
        return self._lanelets.get(lanelet_id)

    def find_traffic_light_by_id(self, traffic_light_id) -> TrafficLight:
        """Find a traffic light for a given traffic light id.

        Args:
          Traffic Light id: The id of the traffic light to find

        Returns:
          The traffic light object if the id exists and None otherwise

        """
        return self._traffic_lights.get(traffic_light_id)

    def find_traffic_sign_by_id(self, traffic_sign_id) -> TrafficSign:
        """Find a traffic sign for a given traffic sign id.

        Args:
          Traffic Sign id: The id of the traffic sign to find

        Returns:
          The traffic sign object if the id exists and None otherwise

        """
        return self._traffic_signs.get(traffic_sign_id)

    def find_stop_linee_by_id(self, stop_line_id) -> StopLine:
        """Find a stop line for a given stop line id.

        Args:
          Stop line id: The id of the stop line to find

        Returns:
          The stop line object if the id exists and None otherwise

        """
        return self._stop_linees.get(stop_line_id)


    def convert_all_lanelet_ids(self):
        """Convert lanelet ids to numbers which comply with the Commonroad specification.

        These numbers have to be positive integers.
        """
        old_ids = self._old_lanelet_ids.copy()

        for lanelet in self.lanelets:
            lanelet.description = lanelet.lanelet_id
            self.remove_lanelet(lanelet.lanelet_id)
            lanelet.lanelet_id = convert_to_new_lanelet_id(
                lanelet.lanelet_id, self._old_lanelet_ids
            )
            lanelet.predecessor = [
                convert_to_new_lanelet_id(x, self._old_lanelet_ids)
                for x in lanelet.predecessor
            ]
            lanelet.successor = [
                convert_to_new_lanelet_id(x, self._old_lanelet_ids)
                for x in lanelet.successor
            ]
            if lanelet.adj_left is not None:
                lanelet.adj_left = convert_to_new_lanelet_id(
                    lanelet.adj_left, self._old_lanelet_ids
                )
            if lanelet.adj_right is not None:
                lanelet.adj_right = convert_to_new_lanelet_id(
                    lanelet.adj_right, self._old_lanelet_ids
                )
            self.add_lanelet(lanelet)

        new_lanelet_ids_assigned = {}
        for key in self._old_lanelet_ids.keys():
            if old_ids.get(key, False) is False:
                new_lanelet_ids_assigned[key] = self._old_lanelet_ids[key]
        return new_lanelet_ids_assigned


    def prune_network(self):
        """Remove references in predecessor, successor etc. to
        non existing lanelets.

        Args:

        Returns:

        """
        self.delete_zero_width_parametric_lanes()

        lanelet_ids = [x.lanelet_id for x in self.lanelets]

        for lanelet in self.lanelets:
            lanelet.predecessor[:] = [
                pred for pred in lanelet.predecessor if pred in lanelet_ids
            ]
            lanelet.successor[:] = [
                succ for succ in lanelet.successor if succ in lanelet_ids
            ]
            if lanelet.adj_left not in lanelet_ids:
                lanelet.adj_left = None
            if lanelet.adj_right not in lanelet_ids:
                lanelet.adj_right = None

    def delete_zero_width_parametric_lanes(self):
        """Remove all ParametricLaneGroup which have zero width at every point from
        this network.
        """
        for lanelet in self.lanelets:
            if lanelet.has_zero_width_everywhere():
                if lanelet.adj_right:
                    adj_right = self.find_lanelet_by_id(lanelet.adj_right)
                    if adj_right:
                        if adj_right.adj_left == lanelet.lanelet_id:
                            adj_right.adj_left = lanelet.adj_left
                            adj_right.adj_left_same_direction = (
                                lanelet.adj_left_same_direction
                            )
                        else:
                            adj_right.adj_right = lanelet.adj_left
                            adj_right.adj_right_same_direction = (
                                not lanelet.adj_left_same_direction
                            )

                if lanelet.adj_left:
                    adj_left = self.find_lanelet_by_id(lanelet.adj_left)
                    if adj_left:
                        if adj_left.adj_right == lanelet.lanelet_id:
                            adj_left.adj_right = lanelet.adj_right
                            adj_left.adj_right_same_direction = (
                                lanelet.adj_right_same_direction
                            )
                        else:
                            adj_left.adj_left = lanelet.adj_right
                            adj_left.adj_left_same_direction = (
                                not lanelet.adj_right_same_direction
                            )

                self.remove_lanelet(lanelet.lanelet_id, remove_references=True)

    def update_lanelet_id_references(self, old_id: str, new_id: str):
        """Update all references to the old lanelet_id with the new_lanelet_id.

        Args:
          old_id: Old lanelet_id which has changed.
          new_id: New lanelet_id the old_id has changed into.

        """

        for lanelet in self.lanelets:
            lanelet.predecessor[:] = [
                new_id if pred == old_id else pred for pred in lanelet.predecessor
            ]

            lanelet.successor[:] = [
                new_id if succ == old_id else succ for succ in lanelet.successor
            ]

            if lanelet.adj_right == old_id:
                lanelet.adj_right = new_id

            if lanelet.adj_left == old_id:
                lanelet.adj_left = new_id

    def concatenate_possible_lanelets(self):
        """Iterate trough lanelets in network and concatenate possible lanelets together.

        Check for each lanelet if it can be concatenated with its successor and
        if its neighbors can be concatenated as well. If yes, do the concatenation.

        """
        concatenate_lanelets = []
        for lanelet in self.lanelets:

            possible_concat_lanes = None
            if lanelet.adj_right is None:
                possible_concat_lanes = self.check_concatenation_potential(
                    lanelet, "left"
                )
            elif lanelet.adj_left is None:
                possible_concat_lanes = self.check_concatenation_potential(
                    lanelet, "right"
                )
            if possible_concat_lanes:
                concatenate_lanelets.append(possible_concat_lanes)

        # this dict saves the lanelet_ids which point to another lanelet_id
        # because they were concatenated together and the resulting lanelet
        # can only have one lanelet_id.
        # key in dict has been renamed to value
        replacement_ids = dict()

        for possible_concat_lanes in concatenate_lanelets:
            # prevent chains of more than one lanelet being renamed
            replacement_ids = {
                k: replacement_ids.get(v, v) for k, v in replacement_ids.items()
            }

            possible_concat_lanes = [
                (
                    replacement_ids.get(pair[0], pair[0]),
                    replacement_ids.get(pair[1], pair[1]),
                )
                for pair in possible_concat_lanes
            ]

            replacement_ids.update(
                self._concatenate_lanelet_pairs_group(possible_concat_lanes)
            )

        return replacement_ids

    def _concatenate_lanelet_pairs_group(self, lanelet_pairs: list) -> dict:
        """Concatenate a group of lanelet_pairs, with setting correctly the new lanelet_ids
        at neighbors.

        Args:
          lanelet_pairs: List with tuples of lanelet_ids which should be concatenated.

        Returns:
          Dict with information which lanelet_id was converted to a new one.

        """

        new_lanelet_ids = dict()
        for pair in lanelet_pairs:
            if pair[0] == pair[1]:
                continue
            lanelet_1 = self.find_lanelet_by_id(pair[0])
            lanelet_2 = self.find_lanelet_by_id(pair[1])
            lanelet_1.concatenate(lanelet_2)

            self.remove_lanelet(pair[1])

            # each reference to lanelet_2 should point to lanelet_id
            # of new_lanelet instead
            self.update_lanelet_id_references(
                lanelet_2.lanelet_id, lanelet_1.lanelet_id
            )
            # update dict to show which lanelet_id changed to which
            new_lanelet_ids[pair[1]] = pair[0]

        return new_lanelet_ids

    def join_and_split_possible_lanes(self):
        """Move lanelet boundaries for lanelet splits or joins.

        This method provides the functionality to modify the lane boundaries if
        a lane merges into another lane or splits from another lane.
        """
        # Condition for lane merge:
        # left and right vertices at end or beginning are the same
        js_targets = []
        for lanelet in self.lanelets:

            lanelet_split, lanelet_join = False, False
            if not lanelet.predecessor and np.allclose(
                lanelet.left_vertices[0], lanelet.right_vertices[0]
            ):
                lanelet_split = True

            if not lanelet.successor and np.allclose(
                lanelet.left_vertices[-1], lanelet.right_vertices[-1]
            ):
                lanelet_join = True

            if lanelet_join or lanelet_split:
                js_targets.append(
                    _JoinSplitTarget(self, lanelet, lanelet_split, lanelet_join)
                )

        for js_target in js_targets:
            js_target.determine_apt_js_pairs()
            js_target.move_borders()
            js_target.add_adjacent_predecessor_or_successor()

    def predecessor_is_neighbor_of_neighbors_predecessor(
        self, lanelet: "ConversionLanelet"
    ) -> bool:
        """Checks if neighbors of predecessor are the successor of the adjacent neighbors
        of the lanelet.

        Args:
          lanelet: Lanelet to check neighbor requirement for.

        Returns:
          True if this neighbor requirement is fulfilled.

        """
        if not self.has_unique_pred_succ_relation(-1, lanelet):
            return False

        predecessor = self.find_lanelet_by_id(lanelet.predecessor[0])
        return self.successor_is_neighbor_of_neighbors_successor(predecessor)

    def add_successors_to_lanelet(
        self, lanelet: ConversionLanelet, successor_ids: List[str]
    ):
        """Add a successor to a lanelet, but add the lanelet also to the predecessor
        of the succesor.

        Args:
          lanelet: Lanelet to add successor to.
          successor_ids: Id of successor to add to lanelet.
        """
        for successor_id in successor_ids:
            lanelet.successor.append(successor_id)
            successor = self.find_lanelet_by_id(successor_id)
            successor.predecessor.append(lanelet.lanelet_id)

    def add_predecessors_to_lanelet(
        self, lanelet: ConversionLanelet, predecessor_ids: List[str]
    ):
        """Add a successor to a lanelet, but add the lanelet also to the predecessor
        of the succesor.

        Args:
          lanelet: Lanelet to add successor to.
          predecessor_id: Id of successor to add to lanelet.
        """
        for predecessor_id in predecessor_ids:
            lanelet.predecessor.append(predecessor_id)
            predecessor = self.find_lanelet_by_id(predecessor_id)
            predecessor.successor.append(lanelet.lanelet_id)

    def set_adjacent_left(
        self, lanelet: ConversionLanelet, adj_left_id: str, same_direction: bool = True
    ):
        """Set the adj_left of a lanelet to a new value.

        Update also the lanelet which is the new adjacent left to
        have new adjacent right.

        Args:
          lanelet: Lanelet which adjacent left should be updated.
          adj_left_id: New value for update.
          same_direction: New adjacent lanelet has same direction as lanelet.
        Returns:
          True if operation successful, else false.
        """
        new_adj = self.find_lanelet_by_id(adj_left_id)
        if not new_adj:
            return False
        lanelet.adj_left = adj_left_id
        lanelet.adj_left_same_direction = same_direction
        if same_direction:
            new_adj.adj_right = lanelet.lanelet_id
            new_adj.adj_right_same_direction = True
        else:
            new_adj.adj_left = lanelet.lanelet_id
            new_adj.adj_left_same_direction = False
        return True

    def set_adjacent_right(
        self, lanelet: ConversionLanelet, adj_right_id: str, same_direction: bool = True
    ):
        """Set the adj_right of a lanelet to a new value.

        Update also the lanelet which is the new adjacent right to
        have new adjacent left.

        Args:
          lanelet: Lanelet which adjacent right should be updated.
          adj_right_id: New value for update.
          same_direction: New adjacent lanelet has same direction as lanelet.
        Returns:
          True if operation successful, else false.
        """
        new_adj = self.find_lanelet_by_id(adj_right_id)
        if not new_adj:
            return False
        lanelet.adj_right = adj_right_id
        lanelet.adj_right_same_direction = same_direction
        if same_direction:
            new_adj.adj_left = lanelet.lanelet_id
            new_adj.adj_left_same_direction = True
        else:
            new_adj.adj_right = lanelet.lanelet_id
            new_adj.adj_right_same_direction = False
        return True

    def check_concatenation_potential(
        self, lanelet: ConversionLanelet, adjacent_direction: str
    ) -> list:
        """Check if lanelet could be concatenated with its successor.

        Args:
          lanelet: Lanelet to check concatenation potential with its successor
          adjacent_direction: "Left" or "Right", determinating which lanelet

        Returns:
          A list of pairs of lanelets which can be concatenated. None if it is not possible.

        """
        mergeable_lanelets = []
        neighbor_ok = self.successor_is_neighbor_of_neighbors_successor(lanelet)
        if not neighbor_ok:
            return None

        if adjacent_direction == "left":
            mergeable_lanelets.append((lanelet.lanelet_id, lanelet.successor[0]))
            if lanelet.adj_left is None:
                return mergeable_lanelets
            if lanelet.adj_left_same_direction:
                next_neighbor = self.find_lanelet_by_id(lanelet.adj_left)
                new_direction = "left"
            else:
                next_neighbor = self.find_lanelet_by_id(
                    self.find_lanelet_by_id(lanelet.adj_left).predecessor[0]
                )
                new_direction = "right"

        else:
            mergeable_lanelets.append((lanelet.lanelet_id, lanelet.successor[0]))
            if lanelet.adj_right is None:
                return mergeable_lanelets
            if lanelet.adj_right_same_direction:
                next_neighbor = self.find_lanelet_by_id(lanelet.adj_right)
                new_direction = "right"
            else:
                next_neighbor = self.find_lanelet_by_id(
                    self.find_lanelet_by_id(lanelet.adj_right).predecessor[0]
                )
                new_direction = "left"

        recursive_merge = self.check_concatenation_potential(
            next_neighbor, new_direction
        )
        if recursive_merge is None:
            return None

        mergeable_lanelets.extend(recursive_merge)
        return mergeable_lanelets

    def successor_is_neighbor_of_neighbors_successor(
        self, lanelet: ConversionLanelet
    ) -> bool:
        """Checks if neighbors of successor are the successor of the adjacent neighbors
        of the lanelet.

        Args:
          lanelet: Lanelet to check specified relation for.

        Returns:
          True if this neighbor requirement is fulfilled.

        """
        if not self.has_unique_pred_succ_relation(1, lanelet):
            return False

        return self.adj_left_consistent_nb(lanelet) and self.adj_right_consistent_nb(
            lanelet
        )

    def has_unique_pred_succ_relation(
        self, direction: int, lanelet: ConversionLanelet
    ) -> bool:
        """Checks if lanelet has only one successor/predecessor and the
        successor/predecessor has only one predecessor/successor, s.t.
        it is a one-to-one relation.

        Args:
          direction: 1 if the successor should be checked.
        -1 (or all other values) for the predecessor.
          lanelet_network: Network to search for lanelets by ids.
          direction: int:
          lanelet_network: "LaneletNetwork":

        Returns:
          True if the relation is unique, False otherwise.

        """
        if direction == 1:
            neighbors = lanelet.successor
        else:
            neighbors = lanelet.predecessor

        # check if neighbor is only one
        if neighbors is None or len(neighbors) != 1:
            return False

        # get lanelet object with id
        neighbor = self.find_lanelet_by_id(neighbors[0])

        # get the neighbor of the neighbor
        nb_neighbor = neighbor.predecessor if direction == 1 else neighbor.successor

        # check if nb_neighbor has one neighbor in proper direction
        if nb_neighbor is None or len(nb_neighbor) != 1:
            return False

        # return True if these ids are the same (they should be!)
        return lanelet.lanelet_id == nb_neighbor[0]

    def adj_right_consistent_nb(self, lanelet: ConversionLanelet) -> bool:
        """Checks if right neighbor of successor is the successor
        of the right adjacent neighbor of the lanelet.

        Args:
          lanelet: Lanelet to check specified relation for.

        Returns:
          True if this neighbor requirement is fulfilled.

        """
        successor = self.find_lanelet_by_id(lanelet.successor[0])
        adj_right = self.find_lanelet_by_id(lanelet.adj_right)
        if adj_right:
            if lanelet.adj_right_same_direction:
                if not self.has_unique_pred_succ_relation(1, adj_right):
                    return False
                if adj_right.successor[0] != successor.adj_right:
                    return False
            else:
                if not lanelet.has_unique_pred_succ_relation(-1, adj_right):
                    return False
                if adj_right.predecessor[0] != successor.adj_right:
                    return False
        else:
            return successor.adj_right is None
        return True

    def adj_left_consistent_nb(self, lanelet: ConversionLanelet) -> bool:
        """Checks if left neighbor of successor is the successor of the
        left adjacent neighbor of the lanelet.

        Args:
          lanelet: Lanelet to check specified relation for.

        Returns:
          True if this neighbor requirement is fulfilled.

        """
        successor = self.find_lanelet_by_id(lanelet.successor[0])
        adj_left = self.find_lanelet_by_id(lanelet.adj_left)
        if adj_left:
            if lanelet.adj_left_same_direction:
                if not self.has_unique_pred_succ_relation(1, adj_left):
                    return False
                if adj_left.successor[0] != successor.adj_left:
                    return False
            else:
                if not self.has_unique_pred_succ_relation(-1, adj_left):
                    return False
                if adj_left.predecessor[0] != successor.adj_left:
                    return False
        else:
            return successor.adj_left is None
        return True

    def create_intersection(self, intersection_map, intersection_id):
        """
        Creates an intersection inside the lanelet network object
        Args:
            intersection_map - information about the successors of a lanelet in a junction
            intersection_id - The unique id used to reference the intersection
        Return:
        """
        # TODO: Define criterion for intersection ID. Currently only iterative numbering
        incoming_id_counter = 0
        # If different incoming lanelets have same successors, combine into set
        incoming_lanelet_ids = self.combine_common_incoming_lanelets(intersection_map)
        intersection_incoming_lanes = list()

        for incoming_lanelet_set in incoming_lanelet_ids:
            # Since all the lanes have the same successors,
            # we simply use the first one to check for the successor directions
            # if more than one incoming lanes exist
            successor_right = set()
            successor_left = set()
            successor_straight = set()

            for incoming_lane in incoming_lanelet_set:
                self.set_intersection_lanelet_type(incoming_lane, intersection_map)
                successor_directions = self.get_successor_directions(self.find_lanelet_by_id(incoming_lane))
                for successor, direction in successor_directions.items():
                    if direction == "right":
                        successor_right.add(successor)
                    elif direction == "left":
                        successor_left.add(successor)
                    elif direction == "straight":
                        successor_straight.add(successor)
                    else:
                        print(direction)
                        warnings.warn("Incorrect direction assigned to successor of incoming lanelet in intersection")

            intersection_incoming_lane = IntersectionIncomingElement(incoming_id_counter, incoming_lanelet_set,
                                                                     successor_right, successor_straight,
                                                                     successor_left)

            intersection_incoming_lanes.append(intersection_incoming_lane)
            # TODO: Add crossings to intersections
            # Increment id counter to generate next unique intersection id. See To Do.
            incoming_id_counter += 1
        intersection = Intersection(intersection_id, intersection_incoming_lanes)
        self.find_left_of(intersection.incomings)
        self.add_intersection(intersection)

    def set_intersection_lanelet_type(self, incoming_lane, intersection_map):
        """
        Set the lanelet type of all the lanelets inside an intersection to Intersection from the enum class
        Args:
            incoming_lane: ID of incoming lanelet
            intersection_map: dictionary that contains all the incomings of a particular intersection
        """
        for successor_incoming in self.find_lanelet_by_id(incoming_lane).successor:
            successor_incoming_lanelet = self.find_lanelet_by_id(successor_incoming)
            successor_incoming_lanelet.lanelet_type = "intersection"
            # Also check if the successor of a incoming successor intersects with another successor of an incoming
            self.check_lanelet_type_for_successor_of_successor(successor_incoming_lanelet, intersection_map)

    def check_lanelet_type_for_successor_of_successor(self, successor_incoming_lanelet, intersection_map):
        """
        Check if the successor of an incoming successor in an intersection is also a part of the lanelet.
        This is done by checking if this lanelet intersects with successors of all the incomigns in the intersection
        If the test passes, then the successor of the incoming successor is also set as intersection lanelet type
        Args:
            successor_incoming_lanelet: lanelet for which we require to test if it is a part of a particular intersection
            intersection_map: dict of the particular intersection for which the test is being conducted.
        """
        for successor_successor_incoming in successor_incoming_lanelet.successor:
            successor_successor_incoming_lanelet = self.find_lanelet_by_id(successor_successor_incoming)
            if self.check_if_lanelet_in_intersection(successor_successor_incoming_lanelet, intersection_map):
                successor_successor_incoming_lanelet.lanelet_type = "intersection"

    def check_if_lanelet_in_intersection(self, lanelet, intersection_map):
        """
        Check if a particular lanelet intersects any of the lanelets that are part of a particular intersection
        using the shapely crosses method.
        Args:
            lanelet: lanelet which is being tested for being part of the intersection.
            intersection_map: dict of the particular intersection for which the test is being conducted.
        Returns:
            true if any intersection found otherwise return False.
        """
        for incoming_lane in intersection_map.keys():
            for successor in self.find_lanelet_by_id(incoming_lane).successor:
                if successor != lanelet.lanelet_id:
                    successor_lane_polygon = self.find_lanelet_by_id(successor).convert_to_polygon()
                    lanelet_polygon = lanelet.convert_to_polygon()
                    if successor_lane_polygon.shapely_object.crosses(lanelet_polygon.shapely_object):
                        return True
        return False

    def find_left_of(self, incomings):
        """
            Find and add isLeftOf property for the incomings using the right before left rule.

            :param incoming_data: incomings without isLeftOf
            :param incoming_data_id: List of the id of the incomings
            :return: incomings with the isLeftOf assigned
        """
        # Choose a reference incoming vector
        ref = self.find_lanelet_by_id(incomings[0].incoming_lanelets[0]).center_vertices[-1] - \
              self.find_lanelet_by_id(incomings[0].incoming_lanelets[0]).center_vertices[-2]
        angles = [(0, 0)]
        # calculate all incoming angle from the reference incoming vector
        for index in range(1, len(incomings)):
            new_v = self.find_lanelet_by_id(incomings[index].incoming_lanelets[0]).center_vertices[-1] - \
                    self.find_lanelet_by_id(incomings[index].incoming_lanelets[0]).center_vertices[-2]
            angle = geometry.get_angle(ref, new_v)
            if angle < 0:
                angle += 360
            angles.append((index, angle))
        prev = -1

        is_left_of_map = dict()
        # take the incomings which have less than 90 degrees in between
        index = 0
        min_angle = 360
        while index < len(incomings):
            angle = angles[index][1] - angles[prev][1]
            if angle < 0:
                angle += 360
            if angle > config.LANE_SEGMENT_ANGLE and angle <= 180 - config.LANE_SEGMENT_ANGLE and angle < min_angle:
                # is left of the previous incoming
                is_left_of = angles[prev][0]
                data_index = angles[index][0]
                incomings[data_index].left_of = incomings[is_left_of].incoming_id
                min_angle = angle
                if abs(prev) >= len(incomings):
                    max_angle = 360
                    prev = -1
                    index += 1
                else:
                    prev -= 1
            else:
                if abs(prev) >= len(incomings):
                    min_angle = 360
                    index += 1
                    prev = -1
                else:
                    prev -= 1

    def combine_common_incoming_lanelets(self, intersection_map):
        """
        Returns a list of tuples which are pairs of adj incoming lanelets and the union of their successors
        Args:
            intersection_map: dict containing the information regarding a particular intersection
        """
        incoming_lane_ids = intersection_map.keys()
        combined_incoming_lane_ids = []
        for incoming_lane_id, successors in intersection_map.items():
            intersection_incoming_set = list()
            incoming_lane = self.find_lanelet_by_id(incoming_lane_id)
            intersection_incoming_set.append(incoming_lane_id)
            adj_right = incoming_lane.adj_right
            adj_left = incoming_lane.adj_left
            while adj_right is not None:
                if adj_right in incoming_lane_ids:
                    adj_right_lane = self.find_lanelet_by_id(adj_right)
                    if adj_right_lane.adj_right_same_direction:
                        intersection_incoming_set.append(adj_right)
                        adj_right = adj_right_lane.adj_right
                    else:
                        adj_right = None
                else:
                    adj_right = None

            while adj_left is not None:
                if adj_left in incoming_lane_ids:
                    adj_left_lane = self.find_lanelet_by_id(adj_left)
                    if adj_left_lane.adj_left_same_direction:
                        intersection_incoming_set.append(adj_left)
                        adj_left = adj_left_lane.adj_left
                    else:
                        adj_left = None
                else:
                    adj_left = None
            intersection_incoming_set.sort()
            combined_incoming_lane_ids.append(intersection_incoming_set)
            combined_incoming_lane_ids.sort()
        combined_incoming_lane_ids = list(k for k, _ in itertools.groupby(combined_incoming_lane_ids))
        return combined_incoming_lane_ids

    def get_successor_directions(self, incoming_lane):
        """
        Find all directions of a incoming lane's successors

        :param incoming_lane: incoming lane from intersection
        :return: str: left or right or through
        """
        straight_threshold_angel = config.INTERSECTION_STRAIGHT_THRESHOLD
        assert 0 < straight_threshold_angel < 90

        angels = {}
        directions = {}

        for successor in incoming_lane.successor:
            # only use the last three waypoints of the incoming for angle calculation
            succeeding_lane = self.find_lanelet_by_id(successor)
            a_angle = geometry.curvature(incoming_lane.center_vertices[-3:])
            b_angle = geometry.curvature(succeeding_lane.center_vertices)
            angle = a_angle - b_angle
            angels[succeeding_lane.lanelet_id] = angle

            # determine direction of trajectory
            # right-turn

            if geometry.is_clockwise(list(succeeding_lane.center_vertices)) > 0:
                angels[succeeding_lane.lanelet_id] = abs(angels[succeeding_lane.lanelet_id])
            # left-turn
            if geometry.is_clockwise(list(succeeding_lane.center_vertices)) < 0:
                angels[succeeding_lane.lanelet_id] = -abs(angels[succeeding_lane.lanelet_id])

        # sort after size
        sorted_angels = {k: v for k, v in sorted(angels.items(), key=lambda item: item[1])}
        sorted_keys = list(sorted_angels.keys())
        sorted_values = list(sorted_angels.values())

        # if 3 successors we assume the directions
        if len(sorted_angels) == 3:
            directions = {sorted_keys[0]: 'left', sorted_keys[1]: 'straight', sorted_keys[2]: 'right'}

        # if 2 successors we assume that they both cannot have the same direction
        if len(sorted_angels) == 2:

            directions = dict.fromkeys(sorted_angels)

            if (abs(sorted_values[0]) > straight_threshold_angel) \
                    and (abs(sorted_values[1]) > straight_threshold_angel):
                directions[sorted_keys[0]] = 'left'
                directions[sorted_keys[1]] = 'right'
            elif abs(sorted_values[0]) < abs(sorted_values[1]):
                directions[sorted_keys[0]] = 'straight'
                directions[sorted_keys[1]] = 'right'
            elif abs(sorted_values[0]) > abs(sorted_values[1]):
                directions[sorted_keys[0]] = 'left'
                directions[sorted_keys[1]] = 'straight'
            else:
                directions[sorted_keys[0]] = 'straight'
                directions[sorted_keys[1]] = 'straight'

        # if we have 1 or more than 3 successors it's hard to make predictions,
        # therefore only straight_threshold_angel is used
        if len(sorted_angels) == 1 or len(sorted_angels) > 3:
            directions = dict.fromkeys(sorted_angels, 'straight')
            for key in sorted_angels:
                if sorted_angels[key] < -straight_threshold_angel:
                    directions[key] = 'left'
                if sorted_angels[key] > straight_threshold_angel:
                    directions[key] = 'right'

        return directions

    def add_traffic_lights_to_network(self, traffic_lights: List):
        """
        Adds all the traffic lights in the network object to the lanelet network
        Requires a list of all the traffic lights in the entire map
        Args:
            traffic_lights: list of all the traffic lights in the lanelet network
        """
        for traffic_light in traffic_lights:
            min_distance = float("inf")
            for intersection in self.intersections:
                for incoming in intersection.incomings:
                    for lanelet in incoming.incoming_lanelets:
                        lane = self.find_lanelet_by_id(lanelet)
                        # Lanelet cannot have more traffic lights than number of successors
                        if len(lane.successor) > len(lane.traffic_lights):
                            pos_1 = traffic_light.position
                            pos_2 = lane.center_vertices[-1]
                            dist = np.linalg.norm(pos_1 - pos_2)
                            if dist < min_distance:
                                min_distance = dist
                                id_for_adding = lanelet
            target_lanelet = self.find_lanelet_by_id(id_for_adding)
            self.add_traffic_light(traffic_light, {id_for_adding})

        # Traffic light directions are assigned once all traffic lights are assigned to lanelets so that it can be
        # determined how directions need to be divided (i.e. the decision between left to one light and straight to
        # one light instead of left-striaght)
        self.add_traffic_light_directions()

    def add_traffic_light_directions(self):
        """
        Assigns directions to the traffic lights based on the directions of the lanelet successors.
        Rule in case of no traffic lights < no of successor = left traffic light becomes left-straight and
        right traffic light remains right.
        """
        for intersection in self.intersections:
            for incoming in intersection.incomings:
                for lanelet in incoming.incoming_lanelets:
                    target_lanelet = self.find_lanelet_by_id(lanelet)
                    traffic_light_ids = target_lanelet.traffic_lights
                    no_of_traffic_lights = len(traffic_light_ids)
                    if no_of_traffic_lights == 1:
                        successor_directions = self.get_successor_directions(target_lanelet)
                        if len(successor_directions) == 1:
                            traffic_light = self.find_traffic_light_by_id(list(traffic_light_ids)[0])
                            if list(successor_directions.values())[0] == 'left':
                                traffic_light.direction = TrafficLightDirection.LEFT
                            elif list(successor_directions.values())[0] == 'right':
                                traffic_light.direction = TrafficLightDirection.RIGHT
                            elif list(successor_directions.values())[0] == 'straight':
                                traffic_light.direction = TrafficLightDirection.STRAIGHT
                        elif len(successor_directions) == 2:
                            if (list(successor_directions.values())[0] == 'left' and list(successor_directions.values())[1] == 'right') \
                                    or (list(successor_directions.values())[0] == 'right' and list(successor_directions.values())[1] == 'left'):
                                traffic_light.direction = TrafficLightDirection.LEFT_RIGHT
                            if (list(successor_directions.values())[0] == 'left' and list(successor_directions.values())[1] == 'straight') \
                                    or (list(successor_directions.values())[0] == 'straight' and list(successor_directions.values())[1] == 'left'):
                                traffic_light.direction = TrafficLightDirection.LEFT_STRAIGHT
                            if (list(successor_directions.values())[0] == 'right' and list(successor_directions.values())[1] == 'straight') \
                                    or (list(successor_directions.values())[0] == 'straight' and list(successor_directions.values())[1] == 'right'):
                                traffic_light.direction = TrafficLightDirection.STRAIGHT_RIGHT

                    if no_of_traffic_lights == 2:
                        successor_directions = self.get_successor_directions(target_lanelet)
                        if len(successor_directions) == 1:
                            warnings.warn("Number of traffic lights should never be more than the number of successors "
                                          "of a lanelet")
                        elif len(successor_directions) == 2:
                            # TODO: In case a lanelet has 2 successors and 2 traffic lights,
                            #  apply directions based on position. How to cater to straight case?
                            for index, traffic_light_id in enumerate(traffic_light_ids):
                                traffic_light = self.find_traffic_light_by_id(traffic_light_id)
                                traffic_light_position = traffic_light.position
                                lanelet_left_position = target_lanelet.left_vertices[-1]
                                lanelet_right_position = target_lanelet.right_vertices[-1]
                                distance_from_right = np.linalg.norm(lanelet_right_position - traffic_light_position)
                                distance_from_left = np.linalg.norm(lanelet_left_position - traffic_light_position)
                                if distance_from_left < distance_from_right and 'left' in list(successor_directions.values()):
                                    traffic_light.direction = TrafficLightDirection.LEFT
                                elif distance_from_left < distance_from_right and 'right' in list(successor_directions.values()):
                                    traffic_light.direction = TrafficLightDirection.RIGHT
                                elif 'straight' in list(successor_directions.values()) or distance_from_left - distance_from_right < 0.001:
                                    traffic_light.direction = TrafficLightDirection.STRAIGHT

                        elif len(successor_directions) == 3:
                            # TODO: In case a lanelet has 3 successors and 2 traffic lights, define
                            #  which light gets which direction
                            # Currently the left traffic light controls the left and straight successor while the right
                            # traffic light only controls the right successor.
                            for index, traffic_light_id in enumerate(traffic_light_ids):
                                traffic_light = self.find_traffic_light_by_id(traffic_light_id)
                                # Check if traffic light is to the left of the lanelet or to the right of the lanelet
                                traffic_light_position = traffic_light.position
                                lanelet_left_position = target_lanelet.left_vertices[-1]
                                lanelet_right_position = target_lanelet.right_vertices[-1]
                                distance_from_right = np.linalg.norm(lanelet_right_position - traffic_light_position)
                                distance_from_left = np.linalg.norm(lanelet_left_position - traffic_light_position)
                                if distance_from_left < distance_from_right:
                                    traffic_light.direction = TrafficLightDirection.LEFT_STRAIGHT
                                elif distance_from_left > distance_from_right:
                                    traffic_light.direction = TrafficLightDirection.RIGHT
                    if no_of_traffic_lights == 3:
                        successor_directions = self.get_successor_directions(target_lanelet)
                        if len(successor_directions) < 3:
                            warnings.warn("Number of traffic lights should never be more than the number of successors "
                                          "of a lanelet")
                        elif len(successor_directions) == 3:
                            # TODO: In case a lanelet has 3 successors and 3 traffic lights,
                            #  apply directions based on position
                            for index, traffic_light_id in enumerate(traffic_light_ids):
                                traffic_light = self.find_traffic_light_by_id(traffic_light_id)
                                # Check if traffic light is to the left of the lanelet or to the right of the lanelet
                                traffic_light_position = traffic_light.position
                                lanelet_left_position = target_lanelet.left_vertices[-1]
                                lanelet_right_position = target_lanelet.right_vertices[-1]
                                distance_from_right = np.linalg.norm(lanelet_right_position - traffic_light_position)
                                distance_from_left = np.linalg.norm(lanelet_left_position - traffic_light_position)
                                if distance_from_left < distance_from_right:
                                    traffic_light.direction = TrafficLightDirection.LEFT
                                elif distance_from_left > distance_from_right:
                                    traffic_light.direction = TrafficLightDirection.RIGHT
                                elif 'straight' in list(successor_directions.values()) or distance_from_left - distance_from_right < 0.001:
                                    traffic_light.direction = TrafficLightDirection.STRAIGHT

    def add_traffic_signs_to_network(self, traffic_signs):
        """
        Adds all the traffic signs in the network object to the lanelet network
        Requires a list of all the traffic signs in the entire map
        Args:
            traffic_signs: list of all the traffic signs
        """

        # Assign traffic signs to lanelets
        for traffic_sign in traffic_signs:
            min_distance = float("inf")
            for lanelet in self.lanelets:
                # Find closest lanelet to traffic signal
                pos_1 = traffic_sign.position
                pos_2 = lanelet.center_vertices[-1]
                dist = np.linalg.norm(pos_1 - pos_2)
                if dist < min_distance:
                    min_distance = dist
                    id_for_adding = lanelet.lanelet_id

            self.add_traffic_sign(traffic_sign, {id_for_adding})

    def add_stop_lines_to_network(self, stop_lines: List[StopLine]):
        """
        Adds all the stop lines in the network object to the lanelet network
        Requires a list of all the stop lines in the entire map
        Args:
            stop_lines: list of all the stop lines

        """
        # Assign stop lines to lanelets

        for stop_line in stop_lines:
            min_start = float("inf")
            min_end = float("inf")
            for intersection in self.intersections:
                for incoming in intersection.incomings:
                    for lanelet in incoming.incoming_lanelets:
                        lane = self.find_lanelet_by_id(lanelet)
                        lanelet_position_left = lane.left_vertices[-1]
                        lanelet_position_right = lane.right_vertices[-1]
                        stop_line_position_end = stop_line.start
                        stop_line_position_start = stop_line.end
                        if np.linalg.norm(lanelet_position_right - stop_line_position_start) < min_start and \
                                np.linalg.norm(lanelet_position_left - stop_line_position_end) < min_end:
                            lane_to_add_stop_line = lane
                            min_start = np.linalg.norm(lanelet_position_right - stop_line_position_start)
                            min_end = np.linalg.norm(lanelet_position_left - stop_line_position_end)
            if lane_to_add_stop_line is None:
                warnings.warn("No lanelet was matched with a stop line")
                continue
            if stop_line.traffic_light_ref is None:
                stop_line.traffic_light_ref = lane_to_add_stop_line.traffic_lights
            if stop_line.traffic_sign_ref is None:
                stop_line.traffic_sign_ref = lane_to_add_stop_line.traffic_signs
            lane_to_add_stop_line.stop_line = stop_line


class _JoinSplitTarget:
    """Class to integrate joining/splitting of lanelet borders.

    Provides methods to determine the lanelets with which the
    join and/or split can be performed. Additionally a method to
    change the borders of the determined lanelets.

    Attributes:
      main_lanelet (ConversionLanelet): Lanelet where split starts or join ends.
      lanelet_network (ConversionLaneletNetwork): LaneletNetwork where join/split occurs.
      _mode (int): Number denoting if join (0), split (1), or join and split (2) occurs.
      change_width (float): Width at start of split or end of join.
        Is list with two elements, [split_width, join_width] if _mode == 2
      linking_side (str): Side on which the split/join happens (either "left" or "right")
      _js_pairs (list): List of :class:`._JoinSplitPair` elements.
      _single_lanelet_operation (bool): Indicates whether only one lanelet and
        its adjacent lanelet can be used for the join/split.
    """

    def __init__(
        self,
        lanelet_network: ConversionLaneletNetwork,
        main_lanelet: ConversionLanelet,
        split: bool,
        join: bool,
    ):
        self.main_lanelet = main_lanelet
        self.lanelet_network = lanelet_network
        if split and join:
            self._mode = 2
        elif split:
            self._mode = 1
        else:
            self._mode = 0
        self.change_width = None
        self.linking_side = None
        self._js_pairs = []
        self._single_lanelet_operation = False

    @property
    def split(self):
        """Lanelet splits at start.

        Returns:
          True if lanelet splits from other lanelet at start.
        """
        return self._mode >= 1

    @property
    def join(self):
        """Lanelet joins at end.

        Returns:
          True if lanelet joins to other lanelet at end.
        """
        return self._mode != 1

    @property
    def split_and_join(self) -> bool:
        """Lanelet splits at start and joins at end.

        Returns:
          True if it has a join and a split.
        """
        return self.split and self.join

    def use_only_single_lanelet(self) -> bool:
        """Only single lanelet can be used for join/split.

        Returns:
          True if only one can be used.
        """
        return self._single_lanelet_operation and self.split_and_join

    def _find_lanelet_by_id(self, lanelet_id: str) -> ConversionLanelet:
        """Run :func:`.ConversionLaneletNetwork.find_lanelet_by_id` of self.lanelet_network.

        Returns:
          Lanelet matching the lanelet_id.
        """
        return self.lanelet_network.find_lanelet_by_id(lanelet_id)

    def complete_js_interval_length(self) -> float:
        """Calculate length of interval where join/split changes the border.

        Returns:
          Length of interval.
        """
        length = 0
        for js_pair in self._js_pairs:
            length += js_pair.change_interval[1] - js_pair.change_interval[0]

        return length

    def adjacent_width(self, is_split: bool) -> float:
        """Get width of adjacent lanelet at start of split or end of join.

        Returns:
          Width of adjacent lanelet at start or end.
        """
        if is_split:
            return self._js_pairs[0].adjacent_lanelet.calc_width_at_start()
        return self._js_pairs[0].adjacent_lanelet.calc_width_at_end()

    def add_adjacent_predecessor_or_successor(self):
        """Add the predecessor or successor of the adjacent lanelet to the main lanelet.

        This reflects that after the split, the main lanelet is also a successor
        of the predecessor of its adjacent lanelet.
        For a join, the main lanelet is a predecessor of the successor of its
        adjacent lanelet.
        """

        if not self._js_pairs:
            return
        lanelet = self._js_pairs[0].lanelet
        adjacent_lanelet = self._js_pairs[0].adjacent_lanelet
        if self.split:
            self.lanelet_network.add_predecessors_to_lanelet(
                lanelet, adjacent_lanelet.predecessor
            )

        if self.join:
            self.lanelet_network.add_successors_to_lanelet(
                lanelet, adjacent_lanelet.successor
            )

    def move_borders(self):
        """Move borders of lanelets to reflect the split/join.

        All lanelet pairs in self._js_pairs are used for the border movement.
        """

        if not self._js_pairs:
            return

        if self.split_and_join:
            self._move_borders_if_split_and_join()
        else:
            self._move_borders_if_split_or_join()

    def _move_borders_if_split_or_join(self):
        """Move borders of lanelets if it is not split and join.

        Interpolate width interval for each js_pair.
        Then move the borders of its lanelet.
        """
        length = self.complete_js_interval_length()
        adj_width = self.adjacent_width(is_split=self.split)
        if self.join:
            js_pairs = list(reversed(self._js_pairs))
            # norm running position so that running_pos + pos_start
            # is at zero at first js_pair
            running_pos = -1 * self._js_pairs[0].change_interval[0]
            width_start = self.change_width
            width_end = adj_width
        else:
            js_pairs = self._js_pairs
            running_pos = 0
            width_start = adj_width
            width_end = self.change_width
        for js_pair in js_pairs:
            [pos_start, pos_end] = js_pair.change_interval
            distance = np.interp(
                [pos_start + running_pos, pos_end + running_pos],
                [0, length],
                [width_start, width_end],
            )
            js_pair.move_border(width=distance, linking_side=self.linking_side)
            running_pos += pos_end - pos_start

    def _move_borders_if_split_and_join(self):
        """Move borders of lanelets if it is split and join.

        Calculate the new vertices twice:
        1. Only for the split (first pair in self._js_pairs)
        2. Only for the join (second pair in self._js_pairs)
        Then talk the first half of the vertices of the split and
        the seconds half of the vertices of the join and merge them.
        """
        lanelet = self._js_pairs[0].lanelet

        start_width_split = self.adjacent_width(is_split=True)
        lanelet_split = self._js_pairs[0].move_border(
            width=[start_width_split, self.change_width[0]],
            linking_side=self.linking_side,
        )
        left_vertices = lanelet_split.left_vertices
        right_vertices = lanelet_split.right_vertices
        center_vertices = lanelet_split.center_vertices
        start_width_join = self.adjacent_width(is_split=False)
        self._js_pairs[1].move_border(
            width=[self.change_width[1], start_width_join],
            linking_side=self.linking_side,
        )

        # take first half of lanelet which does the split
        # take second half of lanelet which does the join
        half_length = int(left_vertices[:, 0].size / 2)
        lanelet.left_vertices = np.vstack(
            (left_vertices[:half_length, :], lanelet.left_vertices[half_length:, :])
        )
        lanelet.right_vertices = np.vstack(
            (right_vertices[:half_length, :], lanelet.right_vertices[half_length:, :])
        )
        lanelet.center_vertices = np.vstack(
            (center_vertices[:half_length, :], lanelet.center_vertices[half_length:, :])
        )

    def determine_apt_js_pairs(self):
        """Determine pairs of lanelet and adjacent lanelet for the join/split.

        Add lanelets as long as one of the break conditions is not matched.
        The determined pairs are saved in self._js_pairs.
        """
        # for first lanelet
        adjacent_lanelet = self._determine_main_adjacent_lanelet()
        if not adjacent_lanelet:
            return
        lanelet = self.main_lanelet
        while True:
            algo_has_finished = self._add_join_split_pair(lanelet, adjacent_lanelet)
            if algo_has_finished or self.use_only_single_lanelet():
                break
            if (
                self.split
                and self.lanelet_network.successor_is_neighbor_of_neighbors_successor(
                    lanelet
                )
                # and lanelet.successor[0] not in global_adjacent_lanelets
            ):
                lanelet = self._find_lanelet_by_id(lanelet.successor[0])
                adjacent_lanelet = self._find_lanelet_by_id(
                    adjacent_lanelet.successor[0]
                )
            elif self.join and (
                self.lanelet_network.predecessor_is_neighbor_of_neighbors_predecessor(
                    lanelet
                )
                # and lanelet.predecessor[0] not in global_adjacent_lanelets
            ):
                lanelet = self._find_lanelet_by_id(lanelet.predecessor[0])
                adjacent_lanelet = self._find_lanelet_by_id(
                    adjacent_lanelet.predecessor[0]
                )

            else:
                break

    def _add_join_split_pair(
        self, lanelet: ConversionLanelet, adjacent_lanelet: ConversionLanelet
    ) -> bool:
        """Add a pair of lanelet and adjacent lanelet to self._js_pairs.

        Decide if it is advisable to add another pair to increase join/split area.

        Args:
          lanelet: Lanelet to be added.
          adjacent_lanelet: Lanelet adjacent to lanelet to be added.
        Returns:
          Indicator whether this was the last pair to be added. False means
           it is advisable to add another lanelet pair.
        """
        if self.split_and_join:
            # one for split at start of lanelet
            change_pos, change_width = lanelet.optimal_join_split_values(
                is_split=True,
                split_and_join=self.split_and_join,
                reference_width=adjacent_lanelet.calc_width_at_start(),
            )
            self._js_pairs.append(
                _JoinSplitPair(lanelet, adjacent_lanelet, [0, change_pos])
            )
            self.change_width = [change_width]
            # one for join at the end of the lanelet
            change_pos, change_width = lanelet.optimal_join_split_values(
                is_split=False,
                split_and_join=self.split_and_join,
                reference_width=adjacent_lanelet.calc_width_at_end(),
            )
            self._js_pairs.append(
                _JoinSplitPair(lanelet, adjacent_lanelet, [change_pos, lanelet.length])
            )
            self.change_width.append(change_width)
            return True

        adjacent_width = (
            adjacent_lanelet.calc_width_at_start()
            if self.split
            else adjacent_lanelet.calc_width_at_end()
        )
        change_pos, change_width = lanelet.optimal_join_split_values(
            is_split=self.split,
            split_and_join=self.split_and_join,
            reference_width=adjacent_width,
        )
        if self.change_width is not None and change_width < self.change_width:
            # algorithm to add lanelet should terminate
            return True
        self.change_width = change_width
        if self.split:
            self._js_pairs.append(
                _JoinSplitPair(lanelet, adjacent_lanelet, [0, change_pos])
            )
            if np.isclose(lanelet.length, change_pos):
                return False
        else:
            self._js_pairs.append(
                _JoinSplitPair(lanelet, adjacent_lanelet, [change_pos, lanelet.length])
            )
            if np.isclose(0, change_pos):
                return False
        return True

    def _determine_main_adjacent_lanelet(self) -> ConversionLanelet:
        """Determine which is the adjacent lanelet to the main lanelet.

        Returns:
          The corresponding adjacent lanelet.
        """
        lanelet = self.main_lanelet
        potential_adjacent_lanelets = Queue()
        checked_lanelets = 0
        if lanelet.adj_left is not None and lanelet.adj_left_same_direction:
            potential_adjacent_lanelets.put(
                {"lanelet_id": lanelet.adj_left, "linking_side": "right"}
            )
            checked_lanelets -= 1
        if lanelet.adj_right is not None and lanelet.adj_right_same_direction:
            potential_adjacent_lanelets.put(
                {"lanelet_id": lanelet.adj_right, "linking_side": "left"}
            )
            checked_lanelets -= 1

        while potential_adjacent_lanelets.qsize() > 0:
            adjacent_lanelet = self._check_next_adjacent_lanelet(
                potential_adjacent_lanelets
            )
            checked_lanelets += 1

            if checked_lanelets > 0:
                # adjacent lanelet is not next neighbor
                # successor of adjacent lanelet cant be used
                self._single_lanelet_operation = True
            if adjacent_lanelet is not None:
                # found appropriate adjacent lanelet
                return adjacent_lanelet

        return None

    def _check_next_adjacent_lanelet(
        self, potential_adjacent_lanelets: Queue
    ) -> Optional[ConversionLanelet]:
        """Check next lanelet if it can act as adjacent lanelet to the main lanelet.

        If not, add its left and right neighbor, if they exists, to the potential_adjacent_lanelets Queue.

        Args:
          potential_adjacent_lanelets: Queue with dicts containing the pontential lanelets.
        Returns:
          Lanelet which fulfills the conditions if it exists, else None
        """
        adj_target = potential_adjacent_lanelets.get()
        adj_lanelet = self._find_lanelet_by_id(adj_target.get("lanelet_id"))
        linking_side = adj_target.get("linking_side")
        return_flag = 0

        if not adj_lanelet:
            return None
        if self.join:
            adj_width = adj_lanelet.calc_width_at_end()

        if self.split:
            adj_width = adj_lanelet.calc_width_at_start()
        if adj_width > 0:
            self.linking_side = adj_target.get("linking_side")
            return_flag = 1

        if return_flag:
            return adj_lanelet

        next_adj_neighbor = (
            adj_lanelet.adj_left if linking_side == "right" else adj_lanelet.adj_right
        )
        if next_adj_neighbor:
            potential_adjacent_lanelets.put(
                {"lanelet_id": next_adj_neighbor, "linking_side": linking_side}
            )
        return None


class _JoinSplitPair:
    "Pair of lanelet whose border is changed and its adjacent neighbor."

    def __init__(self, lanelet, adjacent_lanelet, change_interval):
        self.lanelet = lanelet
        self.adjacent_lanelet = adjacent_lanelet
        self.change_interval = change_interval

    def move_border(self, width: np.ndarray, linking_side: str) -> ConversionLanelet:
        """Move border of self.lanelet.

        Args:
          width: Start and end value of new width of lanelet.
          linking_side: Side on which the split/join happens (either "left" or "right").
        Returns:
          Resulting lanelet after border movement.
        """
        self.lanelet.move_border(
            mirror_border=linking_side,
            mirror_interval=self.change_interval,
            distance=width,
            adjacent_lanelet=self.adjacent_lanelet,
        )
        return self.lanelet
