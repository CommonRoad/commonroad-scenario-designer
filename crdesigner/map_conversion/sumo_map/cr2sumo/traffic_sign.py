import logging
from collections import defaultdict
from copy import copy
from typing import Dict, Generator, List, Optional, Set

import numpy as np
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDGermany,
    TrafficSignIDZamunda,
)

from crdesigner.map_conversion.sumo_map.sumolib_net import (
    Edge,
    EdgeTypes,
    NodeType,
    VehicleType,
)
from crdesigner.map_conversion.sumo_map.util import compute_max_curvature_from_polyline


class TrafficSignEncoder:
    def __init__(self, edge_types: EdgeTypes):
        self.edge_types = edge_types
        self.traffic_sign: Optional[TrafficSign] = None
        self.lanelet: Optional[Lanelet] = None
        self.edge_traffic_signs: Dict[Edge, Set[TrafficSignElement]] = defaultdict(set)
        self.edge: Optional[Edge] = None

    def apply(self, traffic_sign: TrafficSign, edge: Edge):
        """
        Adds the given traffic sign to be encoded.
        Needs to be called for _all_ traffic signs before encode()
        :param traffic_sign:
        :param edge:
        :return:
        """
        for element in traffic_sign.traffic_sign_elements:
            self.edge_traffic_signs[edge].add(element)

    def encode(self):
        """
        Encodes the given traffic sign to the edge / adjacent ones
        :return:
        """

        def safe_eq(traffic_type, attr) -> bool:
            try:
                return getattr(traffic_type, attr) == traffic_type
            except AttributeError:
                return False

        for edge, elements in copy(self.edge_traffic_signs).items():
            for element in elements:
                try:
                    t_type = element.traffic_sign_element_id
                    if safe_eq(t_type, "MAX_SPEED"):
                        self._set_max_speed(element, edge)
                    elif safe_eq(t_type, "PRIORITY"):
                        self._set_priority(element, edge)
                    elif safe_eq(t_type, "STOP"):
                        self._set_all_way_stop(element, edge)
                    elif safe_eq(t_type, "YIELD"):
                        self._set_yield(element, edge)
                    elif safe_eq(t_type, "RIGHT_BEFORE_LEFT"):
                        self._set_right_before_left(element, edge)
                    elif safe_eq(t_type, "BAN_CAR_TRUCK_BUS_MOTORCYCLE"):
                        self._set_ban_car_truck_bus_motorcycle(element, edge)
                    elif safe_eq(t_type, "TOWN_SIGN"):
                        if isinstance(t_type, TrafficSignIDGermany) or isinstance(
                            t_type, TrafficSignIDZamunda
                        ):
                            element = copy(element)
                            element._additional_values = [str(50 / 3.6)]
                            self._set_max_speed(element, edge)
                        # TODO: Implement speed limits for additional countries
                        else:
                            raise NotImplementedError(
                                "TOWN_SIGN for this country is not implemented"
                            )
                    else:
                        raise NotImplementedError(f"Attribute {t_type} not implemented")
                except NotImplementedError as e:
                    logging.warning(f"{element} cannot be converted. Reason: {e}")

    def _set_max_speed(self, traffic_sign_element: TrafficSignElement, edge: Edge):
        """
        Sets max_speed of this edge and all reachable outgoing edges, until another traffic sign is set
        :param traffic_sign_element:
        :param edge:
        :return:
        """
        assert (
            len(traffic_sign_element.additional_values) == 1
        ), f"MAX_SPEED, can only have one additional attribute, has: {traffic_sign_element.additional_values}"
        max_speed = float(traffic_sign_element.additional_values[0])  # in m/s
        new_type = self.edge_types.create_from_update_speed(edge.type_id, max_speed)
        # According to CommonRoad 2020a spec
        # MAX_SPEED is valid from the start of the specified lanelet, until another speed sign is set
        for e in self._bfs_until(edge, traffic_sign_element):
            e.type_id = new_type.id
            for lane in e.lanes:
                lane.speed = max_speed

    def _bfs_until(self, start: Edge, element: TrafficSignElement) -> Generator[Edge, None, None]:
        """
        Find all Edges which are not assigned to have the same element. Includes start Edge
        :param start: starting Edge
        :param element: find Edges with different element than the given one
        :return:
        """
        start_id = element.traffic_sign_element_id
        queue = [start]
        visited = set()
        while queue:
            edge = queue.pop()
            if edge in visited:
                continue
            visited.add(edge)
            if any(
                elem.traffic_sign_element_id == start_id
                for elem in self.edge_traffic_signs[edge]
                if edge != start
            ):
                continue
            queue += edge.outgoing
            yield edge

    def _set_priority(self, element: TrafficSignElement, edge: Edge, max_curvature: float = 1):
        """
        Increases priority of edge and all it's successors whose curvature is less than max_curvature
        :param element:
        :param edge:
        :param max_curvature: Maximal curvature for successors
        :return:
        """
        assert (
            len(element.additional_values) == 0
        ), f"PRIORITY can only have none additional attribute, has: {element.additional_values}"
        old_type = self.edge_types.types[edge.type_id]
        new_type = self.edge_types.create_from_update_priority(old_type.id, old_type.priority + 1)
        edge.to_node.type = NodeType.PRIORITY_STOP
        queue = [edge]
        parents: Dict[edge, List[edge]] = defaultdict(list)
        # memoized curvatures
        curvatures: Dict[edge, float] = dict()
        visited = set()

        def compute_max_path_curvature(edge: Edge, checked_parents=()):
            if edge in curvatures:
                return curvatures[edge]

            curvature = (
                np.max(
                    [
                        compute_max_curvature_from_polyline(np.array(lane.shape))
                        for lane in edge.lanes
                    ]
                )
                if edge.lanes
                else float("-inf")
            )
            curvature = np.max(
                [curvature]
                + [
                    compute_max_path_curvature(parent, checked_parents + tuple(parents[edge]))
                    for parent in parents[edge]
                    if parent not in checked_parents
                ]
            )
            curvatures[edge] = curvature
            return curvature

        # BFS
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            current.type_id = new_type.id
            for outgoing in current.outgoing:
                parents[outgoing].append(current)
                curvature = compute_max_path_curvature(outgoing)
                if curvature < max_curvature:
                    queue.append(outgoing)

    def _set_all_way_stop(self, element: TrafficSignElement, edge: Edge):
        """
        Sets the edges to_node to type ALLWAY_STOP
        :param element:
        :param edge:
        :return:
        """
        assert (
            len(element.additional_values) == 0
        ), f"STOP can only have none additional attribute, has: {element.additional_values}"
        edge.to_node.type = NodeType.ALLWAY_STOP

    def _set_yield(self, element: TrafficSignElement, edge: Edge):
        """
        Sets the outgoing edges to have lower priority and the edges to_node to have type PRIORITY_STOP
        :param element:
        :param edge:
        :return:
        """
        assert (
            len(element.additional_values) == 0
        ), f"GIVEWAY can only have none additional attribute, has: {element.additional_values}"
        edge.to_node.type = NodeType.PRIORITY_STOP
        for outgoing in [edge] + edge.outgoing:
            old_type = self.edge_types.types[outgoing.type_id]
            new_type = self.edge_types.create_from_update_priority(
                old_type.id, max(old_type.priority - 1, 0)
            )
            outgoing.type_id = new_type.id

    def _set_right_before_left(self, element: TrafficSignElement, edge: Edge):
        """
        Sets the edge's to_nodes type to RIGHT_BEFORE_LEFT
        :param element:
        :param edge:
        :return:
        """
        assert (
            len(element.additional_values) == 0
        ), f"RIGHT_BEFORE_LEFT can only have none additional attribute, has: {element.additional_values}"
        edge.to_node.type = NodeType.RIGHT_BEFORE_LEFT

    def _set_ban_car_truck_bus_motorcycle(self, element: TrafficSignElement, edge: Edge):
        """
        Removes all multi-lane vehicles from the edge's allowed list.
        :param element:
        :param edge:
        :return:
        """
        assert (
            len(element.additional_values) == 0
        ), f"BAN_CAR_TRUCK_BUS_MOTORCYCLE can only have none additional attribute, has: {element.additional_values}"
        old_type = self.edge_types.types[edge.type_id]
        disallow = {v_type for v_type in old_type.disallow} | {
            VehicleType.PASSENGER,
            VehicleType.HOV,
            VehicleType.TAXI,
            VehicleType.BUS,
            VehicleType.COACH,
            VehicleType.DELIVERY,
            VehicleType.TRUCK,
            VehicleType.TRAILER,
            VehicleType.MOTORCYCLE,
            VehicleType.EVEHICLE,
        }
        new_type = self.edge_types.create_from_update_allow(
            old_type.id, list(set(VehicleType) - disallow)
        )
        for successor in self._bfs_until(edge, element):
            successor.type_id = new_type.id
