import itertools
import logging
import warnings
from queue import Queue
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import shapely
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.scenario.lanelet import LaneletNetwork, StopLine
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from pyproj import Transformer
from shapely.validation import make_valid

from crdesigner.common.config.opendrive_config import OpenDriveConfig, open_drive_config
from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.common.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.common.utils import (
    convert_to_new_lanelet_id,
    generate_unique_id,
)


class ConversionLaneletNetwork(LaneletNetwork):
    """
    Add functions to LaneletNetwork which further enable it to modify its Lanelets.
    This class is being used in OpenDrive and Lanelet2 format conversions
    """

    def __init__(
        self, config: OpenDriveConfig = open_drive_config, transformer: Optional[Transformer] = None
    ):
        """
        Initializes a ConversionLaneletNetwork

        :param config: OpenDRIVE config parameters.
        :param transformer: Coordinate projection transformer.
        """
        super().__init__()
        self._config = config
        self._old_lanelet_ids = {}
        self._transformer = transformer

    def old_lanelet_ids(self) -> Dict[str, int]:
        """Get the old lanelet ids.

        :return: Dict containing all old lanelet IDs.
        """
        return self._old_lanelet_ids

    def remove_lanelet(self, lanelet_id: str, remove_references: bool = False):
        """
        Remove a lanelets with the specific lanelet_id from the _lanelets dict.

        :param lanelet_id: id of lanelet to be removed.
        :param remove_references: Also remove references which point to the removed lanelet. Default is False.
        """
        del self._lanelets[lanelet_id]
        if remove_references:
            for lanelet in self.lanelets:
                lanelet.predecessor[:] = [
                    pred for pred in lanelet.predecessor if pred != lanelet_id
                ]

                lanelet.successor[:] = [succ for succ in lanelet.successor if succ != lanelet_id]
                if lanelet.adj_right == lanelet_id:
                    lanelet.adj_right = None
                if lanelet.adj_left == lanelet_id:
                    lanelet.adj_left = None

    def find_lanelet_by_id(self, lanelet_id: int) -> ConversionLanelet:
        """
        Find a lanelet for a given lanelet_id.
        Disable natural number check of parent class.

        :param lanelet_id: The id of the lanelet to find.
        :return: The lanelet object if the id exists and None otherwise
        """
        return self._lanelets.get(lanelet_id)

    def find_traffic_light_by_id(self, traffic_light_id: int) -> TrafficLight:
        """Find a traffic light for a given traffic light id.

        :param traffic_light_id: The ID of the traffic light to find
        :return: The traffic light object if the id exists and None otherwise
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

    def convert_all_lanelet_ids(self):
        """
        Convert lanelet ids to numbers which comply with the Commonroad specification.
        These numbers have to be positive integers.
        """
        old_ids = self._old_lanelet_ids.copy()

        for lanelet in self.lanelets:
            lanelet.description = lanelet.lanelet_id
            self.remove_lanelet(str(lanelet.lanelet_id))
            lanelet.lanelet_id = convert_to_new_lanelet_id(
                str(lanelet.lanelet_id), self._old_lanelet_ids
            )
            lanelet.predecessor = [
                convert_to_new_lanelet_id(x, self._old_lanelet_ids) for x in lanelet.predecessor
            ]
            lanelet.successor = [
                convert_to_new_lanelet_id(x, self._old_lanelet_ids) for x in lanelet.successor
            ]
            if lanelet.adj_left is not None:
                lanelet.adj_left = convert_to_new_lanelet_id(
                    str(lanelet.adj_left), self._old_lanelet_ids
                )
            if lanelet.adj_right is not None:
                lanelet.adj_right = convert_to_new_lanelet_id(
                    str(lanelet.adj_right), self._old_lanelet_ids
                )
            self.add_lanelet(lanelet)

        new_lanelet_ids_assigned = {}
        for key in self._old_lanelet_ids.keys():
            if old_ids.get(key, False) is False:
                new_lanelet_ids_assigned[key] = self._old_lanelet_ids[key]
                generate_unique_id(self._old_lanelet_ids[key])
        return new_lanelet_ids_assigned

    def prune_network(self):
        """Remove references in predecessor, successor etc. to
        non-existing lanelets.
        """
        self.delete_zero_width_parametric_lanes()

        lanelet_ids = [x.lanelet_id for x in self.lanelets]

        for lanelet in self.lanelets:
            lanelet.predecessor[:] = [pred for pred in lanelet.predecessor if pred in lanelet_ids]
            lanelet.successor[:] = [succ for succ in lanelet.successor if succ in lanelet_ids]
            if lanelet.adj_left not in lanelet_ids:
                lanelet.adj_left = None
                lanelet.adj_left_same_direction = False
            if lanelet.adj_right not in lanelet_ids:
                lanelet.adj_right = None
                lanelet.adj_right_same_direction = False

    def delete_zero_width_parametric_lanes(self):
        """Remove all ParametricLaneGroup which have zero width at every point from this network."""
        for lanelet in self.lanelets:
            if lanelet.has_zero_width_everywhere():
                if lanelet.adj_right:
                    adj_right = self.find_lanelet_by_id(lanelet.adj_right)
                    if adj_right:
                        if adj_right.adj_left == lanelet.lanelet_id:
                            adj_right.adj_left = lanelet.adj_left
                            adj_right.adj_left_same_direction = lanelet.adj_left_same_direction
                        else:
                            adj_right.adj_right = lanelet.adj_left
                            adj_right.adj_right_same_direction = not lanelet.adj_left_same_direction

                if lanelet.adj_left:
                    adj_left = self.find_lanelet_by_id(lanelet.adj_left)
                    if adj_left:
                        if adj_left.adj_right == lanelet.lanelet_id:
                            adj_left.adj_right = lanelet.adj_right
                            adj_left.adj_right_same_direction = lanelet.adj_right_same_direction
                        else:
                            adj_left.adj_left = lanelet.adj_right
                            adj_left.adj_left_same_direction = not lanelet.adj_right_same_direction

                self.remove_lanelet(lanelet.lanelet_id, remove_references=True)

    def update_lanelet_id_references(self, old_id: str, new_id: str):
        """Update all references to the old lanelet_id with the new_lanelet_id.

        :param old_id: Old lanelet_id which has changed.
        :param new_id: New lanelet_id the old_id has changed into.
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

    def concatenate_possible_lanelets(self) -> Dict[str, str]:
        """Iterate trough lanelets in network and concatenate possible lanelets together.

        Check for each lanelet if it can be concatenated with its successor and if its neighbors can be concatenated
        as well. If yes, do the concatenation.

        :return: A dictionary containing the replacement IDs.
        """
        concatenate_lanelets = []
        for lanelet in self.lanelets:
            possible_concat_lanes = None
            if lanelet.adj_right is None:
                possible_concat_lanes = self.check_concatenation_potential(lanelet, "left")
            elif lanelet.adj_left is None:
                possible_concat_lanes = self.check_concatenation_potential(lanelet, "right")
            if possible_concat_lanes:
                concatenate_lanelets.append(possible_concat_lanes)

        # this dict saves the lanelet_ids which point to another lanelet_id
        # because they were concatenated together and the resulting lanelet
        # can only have one lanelet_id.
        # key in dict has been renamed to value
        replacement_ids = dict()

        for possible_concat_lanes in concatenate_lanelets:
            # prevent chains of more than one lanelet being renamed
            replacement_ids = {k: replacement_ids.get(v, v) for k, v in replacement_ids.items()}

            possible_concat_lanes = [
                (
                    replacement_ids.get(pair[0], pair[0]),
                    replacement_ids.get(pair[1], pair[1]),
                )
                for pair in possible_concat_lanes
            ]

            replacement_ids.update(self._concatenate_lanelet_pairs_group(possible_concat_lanes))

        return replacement_ids

    def _concatenate_lanelet_pairs_group(
        self, lanelet_pairs: List[Tuple[str, str]]
    ) -> Dict[str, str]:
        """Concatenate a group of lanelet_pairs, with setting correctly the new lanelet_ids
        at neighbors.

        :param lanelet_pairs: List with tuples of lanelet_ids which should be concatenated.
        :return: Dict with information which lanelet_id was converted to a new one.
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
            self.update_lanelet_id_references(str(lanelet_2.lanelet_id), str(lanelet_1.lanelet_id))
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
                lanelet.left_vertices[0], lanelet.right_vertices[0], rtol=0
            ):
                lanelet_split = True

            if not lanelet.successor and np.allclose(
                lanelet.left_vertices[-1], lanelet.right_vertices[-1], rtol=0
            ):
                lanelet_join = True

            if lanelet_join or lanelet_split:
                js_targets.append(
                    _JoinSplitTarget(
                        self,
                        lanelet,
                        lanelet_split,
                        lanelet_join,
                        self._transformer,
                        self._config.precision,
                    )
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

        :param lanelet: Lanelet to check neighbor requirement for.
        :return: True if this neighbor requirement is fulfilled.
        """
        if not self.has_unique_pred_succ_relation(-1, lanelet):
            return False

        predecessor = self.find_lanelet_by_id(lanelet.predecessor[0])
        return self.successor_is_neighbor_of_neighbors_successor(predecessor)

    def add_successors_to_lanelet(self, lanelet: ConversionLanelet, successor_ids: List[str]):
        """Add a successor to a lanelet, but add the lanelet also to the predecessor
        of the successor.

        :param lanelet: Lanelet to add successor to.
        :param successor_ids: ID of successor to add to lanelet:
        """
        for successor_id in successor_ids:
            lanelet.successor.append(successor_id)
            successor = self.find_lanelet_by_id(successor_id)
            successor.predecessor.append(lanelet.lanelet_id)

    def add_predecessors_to_lanelet(self, lanelet: ConversionLanelet, predecessor_ids: List[str]):
        """Add a predecessor to a lanelet, but add the lanelet also to the successor
        of the predecessor.

        :param lanelet: Lanelet to add predecessor to.
        :param predecessor_ids: ID of predecessor to add to lanelet.
        """
        for predecessor_id in predecessor_ids:
            lanelet.predecessor.append(predecessor_id)
            predecessor = self.find_lanelet_by_id(predecessor_id)
            predecessor.successor.append(lanelet.lanelet_id)

    def set_adjacent_left(
        self, lanelet: ConversionLanelet, adj_left_id: str, same_direction: bool = True
    ) -> bool:
        """Set the adj_left of a lanelet to a new value.

        Update also the lanelet which is the new adjacent left to
        have new adjacent right.

        :param lanelet: Lanelet which adjacent left should be updated.
        :param adj_left_id: New value for update.
        :param same_direction: New adjacent lanelet has same direction as lanelet.
        :return: True if operation successful, else False.
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
    ) -> bool:
        """Set the adj_right of a lanelet to a new value.

        Update also the lanelet which is the new adjacent right to
        have new adjacent left.

        :param lanelet: Lanelet which adjacent right should be updated.
        :param adj_right_id: New value for update.
        :param same_direction: New adjacent lanelet has same direction as lanelet.
        :return: True if operation successful, else False.
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
    ) -> Optional[List[Tuple[str, str]]]:
        """Check if lanelet could be concatenated with its successor.

        :param lanelet: Lanelet to check concatenation potential with its successor.
        :param adjacent_direction: "Left" or "Right", determining which lanelet.
        :return: A list of pairs of lanelets which can be concatenated. None if it is not possible.
        """
        mergeable_lanelets = []

        # neglect conflicting references (references pointing to each other) since this can cause errors in later processing steps when working with references
        if (
            lanelet.parametric_lane_group
            and lanelet.parametric_lane_group.id_
            and any(
                [
                    int(lanelet.parametric_lane_group.id_.split(".")[2])
                    * int(self.find_lanelet_by_id(lane_id).parametric_lane_group.id_.split(".")[2])
                    < 0
                    for lane_id in lanelet.successor
                ]
            )
        ):
            return None

        if not self.successor_is_neighbor_of_neighbors_successor(lanelet):
            return None

        # in some CARLA maps sidewalk lanelets point together
        # (lanelets have completely wrong successors) -> skip merging
        for suc in lanelet.successor:
            if (
                np.linalg.norm(
                    lanelet.left_vertices[-1] - self.find_lanelet_by_id(suc).left_vertices[0]
                )
                > 1
            ):
                return None
        for pre in lanelet.predecessor:
            if (
                np.linalg.norm(
                    lanelet.left_vertices[0] - self.find_lanelet_by_id(pre).left_vertices[-1]
                )
                > 1
            ):
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

        recursive_merge = self.check_concatenation_potential(next_neighbor, new_direction)
        if recursive_merge is None:
            return None

        mergeable_lanelets.extend(recursive_merge)
        return mergeable_lanelets

    def successor_is_neighbor_of_neighbors_successor(self, lanelet: ConversionLanelet) -> bool:
        """Checks if neighbors of successor are the successor of the adjacent neighbors
        of the lanelet.

        :param lanelet: Lanelet to check specified relation for.
        :return: True if this neighbor requirement is fulfilled.
        """
        if not self.has_unique_pred_succ_relation(1, lanelet):
            return False

        return self.adj_left_consistent_nb(lanelet) and self.adj_right_consistent_nb(lanelet)

    def has_unique_pred_succ_relation(self, direction: int, lanelet: ConversionLanelet) -> bool:
        """Checks if lanelet has only one successor/predecessor and the
        successor/predecessor has only one predecessor/successor, s.t.
        it is a one-to-one relation.

        :param direction: 1 if the successor should be checked. -1 (or all other values) for the predecessor.
        :param lanelet: Lanelet for which relation should be checked.
        :return: True if the relation is unique, False otherwise.
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

        :param lanelet: Lanelet to check specified relation for.
        :return: True if this neighbor requirement is fulfilled, else False.
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

        :param lanelet: Lanelet to check specified relation for.
        :return: True if this neighbor requirement is fulfilled.
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

    def create_intersection(
        self, intersection_map: Dict[int, List[int]], all_incoming_lanelets: Set[int]
    ):
        """
        Creates an intersection inside the lanelet network object

        :param intersection_map: Information about the successors of a lanelet in a junction.
        :param all_incoming_lanelets: Set of all incoming lanelets in the intersection.
        """
        # If different incoming lanelets have same successors, combine into set
        incoming_lanelet_ids = self.combine_common_incoming_lanelets(intersection_map)
        intersection_incoming_lanes = list()
        successors = list()

        for incoming_lanelet_set in incoming_lanelet_ids:
            # Since all the lanes have the same successors,
            # we simply use the first one to check for the successor directions
            # if more than one incoming lanes exist
            successor_right = set()
            successor_left = set()
            successor_straight = set()

            for incoming_lane in incoming_lanelet_set:
                self.set_intersection_lanelet_type(
                    incoming_lane, intersection_map, all_incoming_lanelets
                )
                successor_directions = self.get_successor_directions(
                    self.find_lanelet_by_id(incoming_lane)
                )
                for successor, direction in successor_directions.items():
                    if direction == "right":
                        successor_right.add(successor)
                        successors.append(successor)
                    elif direction == "left":
                        successor_left.add(successor)
                        successors.append(successor)
                    elif direction == "straight":
                        successor_straight.add(successor)
                        successors.append(successor)
                    else:
                        warnings.warn(
                            "Incorrect direction assigned to successor of incoming lanelet in intersection"
                        )
            intersection_incoming_lane = IntersectionIncomingElement(
                generate_unique_id(),
                set(incoming_lanelet_set),
                successor_right,
                successor_straight,
                successor_left,
            )

            intersection_incoming_lanes.append(intersection_incoming_lane)
            # TODO: Add crossings to intersections
            # Increment id counter to generate next unique intersection id. See To Do.

        if self.check_if_successor_is_intersecting(intersection_map, successors):
            intersection = Intersection(generate_unique_id(), intersection_incoming_lanes)
            self.find_left_of(intersection.incomings)
            self.add_intersection(intersection)

    def set_intersection_lanelet_type(
        self,
        incoming_lane: int,
        intersection_map: Dict[int, List[int]],
        incoming_lanelet_ids: Set[int],
    ):
        """Set the lanelet type of all the lanelets inside an intersection to Intersection from the enum class

        :param incoming_lane: ID of incoming lanelet
        :param intersection_map: Dictionary that contains all the incomings of a particular intersection.
        :param incoming_lanelet_ids: Set of all incoming lanelets in the intersection.
        """
        for successor_incoming in self.find_lanelet_by_id(incoming_lane).successor:
            successor_incoming_lanelet = self.find_lanelet_by_id(successor_incoming)
            successor_incoming_lanelet.lanelet_type = "intersection"
            # Also check if the successor of a incoming successor intersects with another successor of an incoming
            self.check_lanelet_type_for_successor_of_successor(
                successor_incoming_lanelet, intersection_map, incoming_lanelet_ids
            )

    def check_lanelet_type_for_successor_of_successor(
        self,
        successor_incoming_lanelet: ConversionLanelet,
        intersection_map: Dict[int, List[int]],
        incoming_lanelet_ids: Set[int],
    ):
        """
        Check if the successor of an incoming successor in an intersection is also a part of the lanelet.
        This is done by checking if this lanelet intersects with successors of all the incomings in the intersection
        If the test passes, then the successor of the incoming successor is also set as intersection lanelet type

        :param successor_incoming_lanelet: Lanelet for which we require to test if it is a part of a particular
            intersection
        :param intersection_map: Dict of the particular intersection for which the test is being conducted.
        :param incoming_lanelet_ids: Set of all incoming lanelets in the intersection.
        """
        for successor_successor_incoming in successor_incoming_lanelet.successor:
            successor_successor_incoming_lanelet = self.find_lanelet_by_id(
                successor_successor_incoming
            )
            if (
                self.check_if_lanelet_in_intersection(
                    successor_successor_incoming_lanelet, intersection_map
                )
                and successor_successor_incoming_lanelet.lanelet_id not in incoming_lanelet_ids
            ):
                successor_successor_incoming_lanelet.lanelet_type = "intersection"

    def check_if_lanelet_in_intersection(
        self, lanelet: ConversionLanelet, intersection_map: Dict[int, List[int]]
    ) -> bool:
        """
        Check if a particular lanelet intersects any of the lanelets that are part of a particular intersection
        using the shapely crosses method.

        :param lanelet: Lanelet which is being tested for being part of the intersection.
        :param intersection_map: Dict of the particular intersection for which the test is being conducted.
        :return: True if any intersection found, otherwise False.
        """
        for incoming_lane in intersection_map.keys():
            for successor in self.find_lanelet_by_id(incoming_lane).successor:
                if successor != lanelet.lanelet_id:
                    successor_lane_polygon = self.find_lanelet_by_id(successor).polygon
                    lanelet_polygon = lanelet.polygon
                    if not lanelet_polygon.shapely_object.is_valid:
                        make_valid(lanelet_polygon.shapely_object)
                    if not successor_lane_polygon.shapely_object.is_valid:
                        make_valid(successor_lane_polygon.shapely_object)
                    try:
                        if successor_lane_polygon.shapely_object.intersects(
                            lanelet_polygon.shapely_object
                        ):
                            return True
                    except shapely.errors.GEOSException:
                        logging.error(
                            "ConversionLaneletNetwork::check_if_lanelet_in_intersection: "
                            "Invalid lanelet shape lanelet {} or {}. "
                            "We assume this lanelet is not part of "
                            "the intersection.".format(successor, lanelet.lanelet_id)
                        )
                        continue
        return False

    def check_if_successor_is_intersecting(
        self, intersection_map: Dict[int, List[int]], successors_list: List[int]
    ) -> bool:
        """
        Check if successors of an incoming intersect with successors of other incoming of the intersection
        using the shapely crosses method.

        :param intersection_map: Dict of the particular intersection for which the test is being conducted.
        :param successors_list: List of all the successors of an intersection
        :return: True if successors of an incoming intersect with successors of other incoming of the intersection,
            otherwise False.
        """
        for incoming_lane in intersection_map.keys():
            for incoming_successor in self.find_lanelet_by_id(incoming_lane).successor:
                for successor in successors_list:
                    if successor not in self.find_lanelet_by_id(incoming_lane).successor:
                        successor_lane_polygon = self.find_lanelet_by_id(successor).polygon
                        incoming_successor_lane_polygon = self.find_lanelet_by_id(
                            incoming_successor
                        ).polygon
                        if successor_lane_polygon.shapely_object.intersects(
                            incoming_successor_lane_polygon.shapely_object
                        ):
                            return True
        return False

    def find_left_of(self, incomings: List[IntersectionIncomingElement]):
        """
        Find and add isLeftOf property for the incomings using the right before left rule.

        :param incomings: List of incomings to find their left of.
        """
        # Choose a reference incoming vector
        ref = (
            self.find_lanelet_by_id(list(incomings[0].incoming_lanelets)[0]).center_vertices[-1]
            - self.find_lanelet_by_id(list(incomings[0].incoming_lanelets)[0]).center_vertices[-3]
        )
        angles = [(0, 0)]
        # calculate all incoming angle from the reference incoming vector
        for index in range(1, len(incomings)):
            new_v = (
                self.find_lanelet_by_id(
                    list(incomings[index].incoming_lanelets)[0]
                ).center_vertices[-1]
                - self.find_lanelet_by_id(
                    list(incomings[index].incoming_lanelets)[0]
                ).center_vertices[-2]
            )
            angle = geometry.get_angle(ref, new_v)
            if angle < 0:
                angle += 360
            angles.append((index, angle))
        prev = -1

        # take the incomings which have less than 90 degrees in between
        index = 0
        min_angle = 360
        while index < len(incomings):
            angle = angles[index][1] - angles[prev][1]
            if angle < 0:
                angle += 360
            if (
                self._config.lane_segment_angle < angle <= 180 - self._config.lane_segment_angle
                and angle < min_angle
            ):
                # is left of the previous incoming
                is_left_of = angles[prev][0]
                data_index = angles[index][0]
                incomings[data_index].left_of = incomings[is_left_of].incoming_id
                min_angle = angle
                if abs(prev) >= len(incomings):
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

    def combine_common_incoming_lanelets(
        self, intersection_map: Dict[int, List[int]]
    ) -> List[List[int]]:
        """
        Returns a list of tuples which are pairs of adj incoming lanelets and the union of their successors

        :param intersection_map: Dict containing the information regarding a particular intersection.
        :return: List of tuples that are pairs of adjacent incoming lanelets and the union of their successors
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
        combined_incoming_lane_ids = list(
            k for k, _ in itertools.groupby(combined_incoming_lane_ids)
        )
        return combined_incoming_lane_ids

    def get_successor_directions(self, incoming_lane: ConversionLanelet) -> Dict[int, str]:
        """
        Find all directions of an incoming lane's successors

        :param incoming_lane: incoming lane from intersection
        :return: Dict containing the directions "left", "right" or "through"
        """
        straight_threshold_angel = self._config.intersection_straight_threshold
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
            directions = {
                sorted_keys[0]: "left",
                sorted_keys[1]: "straight",
                sorted_keys[2]: "right",
            }

        # if 2 successors we assume that they both cannot have the same direction
        if len(sorted_angels) == 2:
            directions = dict.fromkeys(sorted_angels)

            if (abs(sorted_values[0]) > straight_threshold_angel) and (
                abs(sorted_values[1]) > straight_threshold_angel
            ):
                directions[sorted_keys[0]] = "left"
                directions[sorted_keys[1]] = "right"
            elif abs(sorted_values[0]) < abs(sorted_values[1]):
                directions[sorted_keys[0]] = "straight"
                directions[sorted_keys[1]] = "right"
            elif abs(sorted_values[0]) > abs(sorted_values[1]):
                directions[sorted_keys[0]] = "left"
                directions[sorted_keys[1]] = "straight"
            else:
                directions[sorted_keys[0]] = "straight"
                directions[sorted_keys[1]] = "straight"

        # if we have 1 or more than 3 successors it's hard to make predictions,
        # therefore only straight_threshold_angel is used
        if len(sorted_angels) == 1 or len(sorted_angels) > 3:
            directions = dict.fromkeys(sorted_angels, "straight")
            for key in sorted_angels:
                if sorted_angels[key] < -straight_threshold_angel:
                    directions[key] = "left"
                if sorted_angels[key] > straight_threshold_angel:
                    directions[key] = "right"

        return directions

    def add_traffic_lights_to_network(self, traffic_lights: List[TrafficLight]):
        """
        Adds all the traffic lights in the network object to the lanelet network
        Requires a list of all the traffic lights in the entire map

        :param traffic_lights: List of all the traffic lights in the lanelet network.
        """
        incoming_lanelet_ids = self.map_inc_lanelets_to_intersections.keys()
        for traffic_light in traffic_lights:
            id_for_adding = set()
            for lanelet in self.lanelets:
                if (
                    traffic_light.traffic_light_id in lanelet.traffic_lights
                    and lanelet.lanelet_id in incoming_lanelet_ids
                ):
                    id_for_adding.add(lanelet.lanelet_id)
                elif (
                    traffic_light.traffic_light_id in lanelet.traffic_lights
                    and lanelet.lanelet_id not in incoming_lanelet_ids
                ):
                    lanelet.traffic_lights = set()
                    for pre in lanelet.predecessor:
                        if pre in incoming_lanelet_ids:
                            id_for_adding.add(pre)
            if len(id_for_adding) == 0:
                min_distance = float("inf")
                for lanelet in incoming_lanelet_ids:
                    lane = self.find_lanelet_by_id(lanelet)
                    # Lanelet cannot have more traffic lights than number of successors
                    if len(lane.successor) > len(lane.traffic_lights):
                        pos_1 = traffic_light.position
                        pos_2 = lane.center_vertices[-1]
                        dist = np.linalg.norm(pos_1 - pos_2)
                        if dist < min_distance:
                            min_distance = dist
                            id_for_adding.add(lanelet)
            if len(id_for_adding) == 0:
                warnings.warn(
                    "For traffic light with ID {} no referencing lanelet was found!".format(
                        traffic_light.traffic_light_id
                    )
                )
                self.add_traffic_light(traffic_light, set())
            else:
                self.add_traffic_light(traffic_light, id_for_adding)

    def add_traffic_signs_to_network(self, traffic_signs: List[TrafficSign]):
        """
        Adds all the traffic signs in the network object to the lanelet network
        Requires a list of all the traffic signs in the entire map

        :param traffic_signs: List of all the traffic signs.
        """

        # Assign traffic signs to lanelets
        for traffic_sign in traffic_signs:
            id_for_adding = None
            min_distance = float("inf")
            for lanelet in self.lanelets:
                # Find closest lanelet to traffic signal
                pos_1 = traffic_sign.position
                pos_2 = lanelet.center_vertices[0]
                dist = np.linalg.norm(pos_1 - pos_2)
                if dist < min_distance:
                    min_distance = dist
                    id_for_adding = lanelet.lanelet_id
            if id_for_adding is None:
                warnings.warn(
                    "For traffic sign with ID {} no referencing lanelet was found!".format(
                        traffic_sign.traffic_sign_id
                    )
                )
                self.add_traffic_sign(traffic_sign, set())
            else:
                self.add_traffic_sign(traffic_sign, {id_for_adding})

    def add_stop_lines_to_network(self, stop_lines: List[StopLine]):
        """
        Adds all the stop lines in the network object to the lanelet network
        Requires a list of all the stop lines in the entire map

        :param stop_lines: List of all the stop lines
        """
        # Assign stop lines to lanelets

        for stop_line in stop_lines:
            min_start = float("inf")
            min_end = float("inf")
            lane_to_add_stop_line = None
            for intersection in self.intersections:
                for incoming in intersection.incomings:
                    for lanelet in incoming.incoming_lanelets:
                        lane = self.find_lanelet_by_id(lanelet)
                        lanelet_position_left = lane.left_vertices[-1]
                        lanelet_position_right = lane.right_vertices[-1]
                        stop_line_position_end = stop_line.start
                        stop_line_position_start = stop_line.end
                        if (
                            np.linalg.norm(lanelet_position_right - stop_line_position_start)
                            < min_start
                            and np.linalg.norm(lanelet_position_left - stop_line_position_end)
                            < min_end
                        ):
                            lane_to_add_stop_line = lane
                            min_start = np.linalg.norm(
                                lanelet_position_right - stop_line_position_start
                            )
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
    join and/or split can be performed. Additionally, a method to
    change the borders of the determined lanelets.

    :var :class:`ConversionLanelet` main_lanelet: Lanelet where split starts or join ends.
    :var :class:`ConversionLanelet` main_lanelet : Lanelet where split starts or join end.
    :var lanelet_network :class:`ConversionLaneletNetwork`: LaneletNetwork where join/split occurs.
    :var _mode int: Number denoting if join (0), split (1), or join and split (2) occurs.
    :var change_width float: Width at start of split or end of join. List with two elements, [split_width, join_width]
        if _mode == 2
    :var linking_side str: Side on which the split/join happens, either "left" or "right"
    :var _js_pairs list: List of :class:`._JoinSplitPair` elements
    :var _single_lanelet_operation bool: Indicates whether only one lanelet and its adjacent lanelet can be used for the
        join/split
    """

    def __init__(
        self,
        lanelet_network: ConversionLaneletNetwork,
        main_lanelet: ConversionLanelet,
        split: bool,
        join: bool,
        transformer: Optional[Transformer] = None,
        precision: float = open_drive_config.precision,
    ):
        """

        :param lanelet_network: LaneletNetwork where join/split occurs.
        :param main_lanelet: Lanelet where split starts or join ends.
        :param split: Boolean indicating whether a lanelet split should be performed.
        :param join: Boolean indicating whether a lanelet join should be performed.
        :param transformer: Coordinate projection transformer.
        :param precision: precision with which to convert plane group to lanelet
        """

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
        self.precision = precision
        self._transformer = transformer

    @property
    def split(self) -> bool:
        """Lanelet splits at start.

        :return: True if lanelet splits from other lanelet at start.
        """
        return self._mode >= 1

    @property
    def join(self) -> bool:
        """Lanelet joins at end.

        :return: True if lanelet joins to other lanelet at end.
        """
        return self._mode != 1

    @property
    def split_and_join(self) -> bool:
        """Lanelet splits at start and joins at end.

        :return: True if it has a join and a split
        """
        return self.split and self.join

    def use_only_single_lanelet(self) -> bool:
        """Only single lanelet can be used for join/split.

        :return: True if only one can be used.
        """
        return self._single_lanelet_operation and self.split_and_join

    def _find_lanelet_by_id(self, lanelet_id: str) -> ConversionLanelet:
        """Runs :func:`ConversionLaneletNetwork.find_lanelet_by_id`.

        :param lanelet_id: The lanelet id identifying the lanelet that should be found.
        :return: Lanelet matching the lanelet_id
        """
        return self.lanelet_network.find_lanelet_by_id(lanelet_id)

    def complete_js_interval_length(self) -> float:
        """Calculate length of interval where join/split changes the border.

        :return: Length of interval.
        """
        length = 0
        for js_pair in self._js_pairs:
            length += js_pair.change_interval[1] - js_pair.change_interval[0]

        return length

    def adjacent_width(self, is_split: bool) -> float:
        """Get width of adjacent lanelet at start of split or end of join.

        :param is_split: Whether width should be calculated at start of split or end of join
        :return: Width of adjacent lanelet at start or end.

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
            self.lanelet_network.add_predecessors_to_lanelet(lanelet, adjacent_lanelet.predecessor)

        if self.join:
            self.lanelet_network.add_successors_to_lanelet(lanelet, adjacent_lanelet.successor)

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
            js_pair.move_border(
                width=distance, linking_side=self.linking_side, transformer=self._transformer
            )
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
                and self.lanelet_network.successor_is_neighbor_of_neighbors_successor(lanelet)
                # and lanelet.successor[0] not in global_adjacent_lanelets
            ):
                lanelet = self._find_lanelet_by_id(lanelet.successor[0])
                adjacent_lanelet = self._find_lanelet_by_id(adjacent_lanelet.successor[0])
            elif self.join and (
                self.lanelet_network.predecessor_is_neighbor_of_neighbors_predecessor(lanelet)
                # and lanelet.predecessor[0] not in global_adjacent_lanelets
            ):
                lanelet = self._find_lanelet_by_id(lanelet.predecessor[0])
                adjacent_lanelet = self._find_lanelet_by_id(adjacent_lanelet.predecessor[0])

            else:
                break

    def _add_join_split_pair(
        self, lanelet: ConversionLanelet, adjacent_lanelet: ConversionLanelet
    ) -> bool:
        """Add a pair of lanelet and adjacent lanelet to self._js_pairs.

        Decide if it is advisable to add another pair to increase join/split area.

        :param lanelet: Lanelet to be added.
        :param adjacent_lanelet: Lanelet adjacent to lanelet to be added.
        :return: Indicator whether this was the last pair to be added. False means it is advisable to add
            another lanelet pair.
        """
        if self.split_and_join:
            # one for split at start of lanelet
            change_pos, change_width = lanelet.optimal_join_split_values(
                is_split=True,
                split_and_join=self.split_and_join,
                reference_width=adjacent_lanelet.calc_width_at_start(),
            )
            self._js_pairs.append(
                _JoinSplitPair(lanelet, adjacent_lanelet, [0, change_pos], self.precision)
            )
            self.change_width = [change_width]
            # one for join at the end of the lanelet
            change_pos, change_width = lanelet.optimal_join_split_values(
                is_split=False,
                split_and_join=self.split_and_join,
                reference_width=adjacent_lanelet.calc_width_at_end(),
            )
            self._js_pairs.append(
                _JoinSplitPair(
                    lanelet, adjacent_lanelet, [change_pos, lanelet.length], self.precision
                )
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
                _JoinSplitPair(lanelet, adjacent_lanelet, [0, change_pos], self.precision)
            )
            if np.isclose(lanelet.length, change_pos):
                return False
        else:
            self._js_pairs.append(
                _JoinSplitPair(
                    lanelet, adjacent_lanelet, [change_pos, lanelet.length], self.precision
                )
            )
            if np.isclose(0, change_pos):
                return False
        return True

    def _determine_main_adjacent_lanelet(self) -> ConversionLanelet:
        """Determine which is the adjacent lanelet to the main lanelet.

        :return: The corresponding adjacent lanelet
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
            adjacent_lanelet = self._check_next_adjacent_lanelet(potential_adjacent_lanelets)
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

        If not, add its left and right neighbor, if they exist, to the potential_adjacent_lanelets Queue.

        :param potential_adjacent_lanelets: Queue with dicts containing the potential lanelets.
        :return: Lanelet which fulfills the conditions if it exists, else None.
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
    """Pair of lanelet whose border is changed and its adjacent neighbor."""

    def __init__(
        self,
        lanelet,
        adjacent_lanelet,
        change_interval,
        precision: float = open_drive_config.precision,
    ):
        self.lanelet = lanelet
        self.adjacent_lanelet = adjacent_lanelet
        self.change_interval = change_interval
        self.precision = precision

    def move_border(
        self, width: np.ndarray, linking_side: str, transformer: Optional[Transformer] = None
    ) -> ConversionLanelet:
        """Move border of self.lanelet.

        :param width: Start and end value of new width of lanelet.
        :param linking_side: Side on which the split/join happens, either "left" or "right"
        :param transformer: Coordinate projection transformer.
        :return: Resulting lanelet after border movement.
        """
        self.lanelet.move_border(
            mirror_border=linking_side,
            mirror_interval=self.change_interval,
            distance=width,
            adjacent_lanelet=self.adjacent_lanelet,
            precision=self.precision,
            transformer=transformer,
        )
        return self.lanelet
