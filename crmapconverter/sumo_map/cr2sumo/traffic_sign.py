from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement, TrafficSignIDGermany, TrafficSignIDUsa, \
    TrafficSignIDZamunda
from commonroad.scenario.lanelet import Lanelet
from crmapconverter.sumo_map.sumolib_net import Edge, EdgeType, EdgeTypes, SumoNodeType
from crmapconverter.sumo_map.util import compute_max_curvature_from_polyline
import logging
import numpy as np
from collections import defaultdict
from typing import Optional, Dict, List, Set
from copy import copy


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
        for edge, elements in copy(self.edge_traffic_signs).items():
            for element in elements:
                id = element.traffic_sign_element_id
                if id == TrafficSignIDGermany.MAX_SPEED:
                    self._set_max_speed(element, edge)
                elif id == TrafficSignIDGermany.PRIORITY:
                    self._set_priority(element, edge)
                elif id == TrafficSignIDGermany.STOP:
                    self._set_all_way_stop(element, edge)
                elif id == TrafficSignIDGermany.YIELD:
                    self._set_yield(element, edge)
                elif id == TrafficSignIDGermany.RIGHT_BEFORE_LEFT:
                    self._set_right_before_left(element, edge)
                else:
                    logging.warning(f"{element.traffic_sign_element_id} cannot be converted.")

    def _set_max_speed(self, traffic_sign_element: TrafficSignElement, edge: Edge):
        """
        Sets max_speed of this edge and all reachable outgoing edges, until another traffic sign is set
        :param traffic_sign_element:
        :param edge:
        :return:
        """
        assert len(traffic_sign_element.additional_values) == 1, \
            f"MAX_SPEED, can only have one additional attribute, has: {traffic_sign_element.additional_values}"
        max_speed = float(traffic_sign_element.additional_values[0])  # in m/s
        new_type = self.edge_types.create_from_update_speed(edge.getType(), max_speed)
        # According to https://gitlab.lrz.de/tum-cps/commonroad-scenarios/-/blob/master/documentation/XML_commonRoad_2020a.pdf
        # MAX_SPEED is valid from the start of the specified lanelet, until another speed sign is set
        for e in self._bfs_until(edge, traffic_sign_element):
            e.setType(new_type.id)
            for lane in e.getLanes():
                lane.speed = max_speed

    def _bfs_until(self, start: Edge, element: TrafficSignElement) -> List[Edge]:
        start_id = element.traffic_sign_element_id
        queue = [start]
        visited = set()
        res = []
        while queue:
            edge = queue.pop()
            if edge in visited:
                continue
            visited.add(edge)
            if any(elem.traffic_sign_element_id == start_id for elem in self.edge_traffic_signs[edge]
                   if edge != start):
                continue
            res.append(edge)
            queue += edge.getOutgoing()
        return res

    def _set_priority(self, element: TrafficSignElement, edge: Edge, max_curvature: float = 1):
        """
        Increases priority of edge and all it's successors whose curvature is less than max_curvature
        :param element:
        :param edge:
        :param max_curvature: Maximal curvature for successors
        :return:
        """
        assert len(element.additional_values) == 0, \
            f"PRIORITY can only have none additional attribute, has: {element.additional_values}"
        old_type = self.edge_types.types[edge.getType()]
        new_type = self.edge_types.create_from_update_priority(old_type.id, old_type.priority + 1)
        queue = list(edge.getOutgoing())
        parents: Dict[edge, List[edge]] = defaultdict(list)
        # memoized curvatures
        curvatures: Dict[edge, float] = dict()
        visited = set()

        def compute_max_path_curvature(edge: Edge):
            if edge in curvatures:
                return curvatures[edge]

            curvature = np.max([
                compute_max_curvature_from_polyline(np.array(lane._shape))
                for lane in edge.getLanes()
            ]) if edge.getLanes() else float("-inf")
            curvature = np.max([curvature] + [compute_max_path_curvature(parent) for parent in parents[edge]])
            curvatures[edge] = curvature
            return curvature

        # BFS
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            current.setType(new_type.id)
            for outgoing in current.getOutgoing():
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
        assert len(element.additional_values) == 0, \
            f"STOP can only have none additional attribute, has: {element.additional_values}"
        edge.getToNode().setType(SumoNodeType.ALLWAY_STOP.value)

    def _set_yield(self, element: TrafficSignElement, edge: Edge):
        """
        Sets the outgoing edges to have lower priority and the edges to_node to have type PRIORITY_STOP
        :param element:
        :param edge:
        :return:
        """
        assert len(element.additional_values) == 0, \
            f"GIVEWAY can only have none additional attribute, has: {element.additional_values}"
        edge.getToNode().setType(SumoNodeType.PRIORITY_STOP)
        for outgoing in edge.getOutgoing():
            old_type = self.edge_types.types[outgoing.getType()]
            new_type = self.edge_types.create_from_update_priority(old_type.id, max(old_type.priority - 1, 0))
            outgoing.setType(new_type.id)

    def _set_right_before_left(self, element: TrafficSignElement, edge: Edge):
        """
        Sets the edge's to_nodes type to RIGHT_BEFORE_LEFT
        :param element:
        :param edge:
        :return:
        """
        assert len(element.additional_values) == 0, \
            f"RIGHT_BEFORE_LEFT can only have none additional attribute, has: {element.additional_values}"
        edge.getToNode().setType(SumoNodeType.RIGHT_BEFORE_LEFT.value)
