import math
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

import numpy as np
from commonroad.scenario.lanelet import Lanelet, LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from similaritymeasures import similaritymeasures

from crdesigner.verification_repairing.config import MapVerParams


class Mapping(ABC):
    """
    The class is responsible for mapping the CommonRoad elements to supported instances by the corresponding solver.
    """

    def __init__(
        self,
        network: LaneletNetwork,
        config: MapVerParams = MapVerParams(),
        scenario_id: ScenarioID = ScenarioID(),
    ):
        """
        Constructor.

        :param network: Lanelet network.
        :param config: Configuration.
        :param scenario_id: ScenarioID.
        """
        self._complete_map_name = (
            str(scenario_id.country_id)
            + "_"
            + str(scenario_id.map_name)
            + "-"
            + str(scenario_id.map_id)
        )
        self._network = network
        self._config = config

    @abstractmethod
    def map_lanelet_network(self):
        pass

    @abstractmethod
    def map_verification_paras(self):
        pass


class Preprocessing(ABC):
    """The class preprocesses some information which should not calculated during solving."""

    def __init__(self, network: LaneletNetwork, config: MapVerParams = MapVerParams()):
        self._network = network
        self._config = config

        self._adjacency_types = None
        self._adjacency_types = self.adjacency_types

        self._left_topological_adjs = None
        self._left_topological_adjs = self.left_topological_adjs

        self._right_topological_adjs = None
        self._right_topological_adjs = self.right_topological_adjs

        self._similar_polylines = None
        self._similar_polylines = self.similar_polylines

    @property
    def adjacency_types(self) -> Dict[int, Tuple[str, str]]:
        """
        Checks the types for the left and right adjacency of all lanelets. An adjacency type can be Parallel, Merge,
        and Fork.

        :return: Adjacency types.
        """
        if self._adjacency_types is None:
            self._adjacency_types = {}
            for lan in self._network.lanelets:
                left_adj_type = None
                if lan.adj_left is not None:
                    adj = self._network.find_lanelet_by_id(lan.adj_left)
                    if adj is not None:
                        left_adj_type = self.identify_adj_type(
                            lan, adj, True, lan.adj_left_same_direction
                        )
                right_adj_type = None
                if lan.adj_right is not None:
                    adj = self._network.find_lanelet_by_id(lan.adj_right)
                    if adj is not None:
                        right_adj_type = self.identify_adj_type(
                            lan, adj, False, lan.adj_right_same_direction
                        )

                self._adjacency_types.update({lan.lanelet_id: (left_adj_type, right_adj_type)})

        return self._adjacency_types

    @property
    def similar_polylines(self) -> Dict[int, List[np.ndarray]]:
        """
        Checks similarity between two polylines for all polylines in the map and collects the computed information.

        :return: Similarities between polylines.
        """
        if self._similar_polylines is None:
            self._similar_polylines = {}

            id_count = 0
            for lanelet in self._network.lanelets:
                for vertices in [
                    lanelet.left_vertices,
                    lanelet.right_vertices,
                    lanelet.center_vertices,
                ]:
                    new_poly = True
                    for poly_id, polylines in self._similar_polylines.items():
                        if len(polylines) > 0 and self.are_similar_polylines(
                            vertices, polylines[0]
                        ):
                            new_poly = False
                            polylines.append(vertices)
                            continue
                    if new_poly:
                        self._similar_polylines.update({id_count: [vertices]})
                        id_count = id_count + 1

        return self._similar_polylines

    @property
    def left_topological_adjs(self):
        if self._left_topological_adjs is None:
            self._left_topological_adjs = self.topological_adjs(is_left=True)
        return self._left_topological_adjs

    @property
    def right_topological_adjs(self):
        if self._right_topological_adjs is None:
            self._right_topological_adjs = self.topological_adjs(is_left=False)
        return self._right_topological_adjs

    @staticmethod
    def identify_adj_type(lanelet: Lanelet, adj: Lanelet, is_left: bool, is_same_dir: bool) -> str:
        """
        Identifies the type of adjacency of lanelet. The types include parallel, merging, and forking adjacencies.

        :param lanelet: Lanelet.
        :param adj: Adjacency.
        :param is_left: Left or right adj.
        :param is_same_dir: Same of opposite direction.
        :return: Adjacency type.
        """
        parallel = "Parallel"
        merge = "Merge"
        fork = "Fork"

        if not is_same_dir:
            return parallel

        if is_left:
            adj_poly = adj.right_vertices
        else:
            adj_poly = adj.left_vertices

        left_poly = lanelet.left_vertices
        right_poly = lanelet.right_vertices

        adj_size = len(adj_poly)
        lan_size = len(left_poly)

        left_start_dist = np.linalg.norm(left_poly[0] - adj_poly[0])
        left_end_dist = np.linalg.norm(left_poly[lan_size - 1] - adj_poly[adj_size - 1])

        right_start_dist = np.linalg.norm(right_poly[0] - adj_poly[0])
        right_end_dist = np.linalg.norm(right_poly[lan_size - 1] - adj_poly[adj_size - 1])

        if left_start_dist > right_start_dist and left_end_dist < right_end_dist:
            adj_type = fork if is_left else merge
        elif left_start_dist < right_start_dist and left_end_dist > right_end_dist:
            adj_type = merge if is_left else fork
        else:
            adj_type = parallel

        return adj_type

    def are_similar_polylines(self, polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
        """
        Checks whether a polyline is similar to another polyline.

        :param polyline_0: First polyline.
        :param polyline_1: Second polyline.
        :return: Boolean indicates whether two polylines are similar to each other.
        """
        flipped_polyline_0 = np.flip(polyline_0, 0)

        polylines_0 = [polyline_0, flipped_polyline_0]

        is_near = False
        for polyline in polylines_0:
            start_v_0 = polyline[0]
            end_v_0 = polyline[len(polyline) - 1]
            start_v_1 = polyline_1[0]
            end_v_1 = polyline_1[len(polyline_1) - 1]

            thresh = 5.0

            near_points = True
            for v_0, v_1 in zip([start_v_0, end_v_0], [start_v_1, end_v_1]):
                dist = math.hypot(v_1[0] - v_0[0], v_1[1] - v_0[1])
                near_points = near_points and dist < thresh
            is_near = is_near or near_points

        if not is_near:
            return False

        for polyline in polylines_0:
            area_diff = similaritymeasures.frechet_dist(polyline, polyline_1)

            thresh = float(self._config.verification.potential_border_thresh)

            if area_diff < thresh:
                return True

        return False

    def topological_adjs(self, is_left: bool) -> Dict[int, List[int]]:
        adjacencies = {}
        for lanelet in self._network.lanelets:
            adjs = []
            adj_id = lanelet.adj_left if is_left else lanelet.adj_right

            valid_dir = (
                lanelet.adj_left_same_direction if is_left else lanelet.adj_right_same_direction
            )
            while adj_id is not None:
                if adj_id in adjs:
                    break
                adjs.append(adj_id)
                adj = self._network.find_lanelet_by_id(adj_id)

                if adj is None:
                    break

                if is_left:
                    if valid_dir:
                        adj_id = adj.adj_left
                    else:
                        adj_id = adj.adj_right
                else:
                    if valid_dir:
                        adj_id = adj.adj_right
                    else:
                        adj_id = adj.adj_left

                if (is_left and not adj.adj_left_same_direction) or (
                    not is_left and not adj.adj_right_same_direction
                ):
                    valid_dir = False

            adjacencies.update({lanelet.lanelet_id: adjs})

        return adjacencies
