from typing import List, Set, Tuple, Union

import numpy as np
from commonroad.common.validity import is_natural_number
from commonroad.scenario.intersection import Intersection, IntersectionIncomingElement
from commonroad.scenario.lanelet import (
    Lanelet,
    LaneletNetwork,
    LaneletType,
    LineMarking,
    RoadUser,
    StopLine,
)
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.traffic_light import (
    TrafficLight,
    TrafficLightCycle,
    TrafficLightCycleElement,
    TrafficLightState,
)
from commonroad.scenario.traffic_sign import (
    TrafficSign,
    TrafficSignElement,
    TrafficSignIDArgentina,
    TrafficSignIDBelgium,
    TrafficSignIDChina,
    TrafficSignIDCroatia,
    TrafficSignIDFrance,
    TrafficSignIDGermany,
    TrafficSignIDGreece,
    TrafficSignIDItaly,
    TrafficSignIDPuertoRico,
    TrafficSignIDRussia,
    TrafficSignIDSpain,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)
from scipy.interpolate import interp1d


# TODO: UNCERTAIN (either controller or model)
class MapCreator:
    """
    Collection of functions to work with lanelets
    """

    @staticmethod
    def create_straight(
        width: float,
        length: float,
        num_vertices: int,
        lanelet_id: int,
        lanelet_types: Set[LaneletType],
        predecessor: List[int] = None,
        successor: List[int] = None,
        adjacent_left: Union[int, None] = None,
        adjacent_right: Union[int, None] = None,
        adjacent_left_same_direction: bool = None,
        adjacent_right_same_direction: bool = None,
        road_user_one_way: Set[RoadUser] = None,
        road_user_bidirectional: Set[RoadUser] = None,
        line_marking_left: LineMarking = LineMarking.UNKNOWN,
        line_marking_right: LineMarking = LineMarking.UNKNOWN,
        stop_line: StopLine = None,
        traffic_signs: Set[int] = None,
        traffic_lights: Set[int] = None,
        stop_line_at_end: bool = False,
        stop_line_at_beginning: bool = False,
        backwards: bool = False,
    ) -> Lanelet:
        """
        Function for creating a straight lanelet given a length, width, and number of vertices.

        @param width: Width of the lanelet.
        @param length: Length of the lanelet.
        @param num_vertices: Number of vertices of the lanelet.
        @param lanelet_id: Id for new lanelet.
        @param lanelet_types: Lanelet types for new lanelet.
        @param adjacent_left: Left adjacent lanelet.
        @param adjacent_right Right adjacent lanelet.
        @param adjacent_left_same_direction: Boolean indicating whether adjacent left has same direction.
        @param adjacent_right_same_direction: Boolean indicating whether adjacent right has same direction.
        @param predecessor: Predecessor lanelets.
        @param successor: Successor lanelets.
        @param road_user_one_way: Allowed road users one way for new lanelet.
        @param road_user_bidirectional: Allowed road users bidirectional for new lanelet.
        @param line_marking_left: Line markings on the left for new lanelet.
        @param line_marking_right: Line markings on the right for new lanelet.
        @param stop_line: Stop line of new lanelet.
        @param traffic_signs: Referenced traffic signs by new lanelet.
        @param traffic_lights: Referenced traffic lights by new lanelet.
        @param backwards: Boolean indicating whether lanelet should be rotated by 180°.
        @param stop_line_at_end: Boolean indicating whether stop line positions should correspond with end of lanelet.
        @param stop_line_at_beginning: Boolean indicating whether stop line positions should correspond
        with beginning of lanelet.
        @return: Newly created lanelet.
        """
        eps = 0.1e-15
        length_div = length / (num_vertices - 1)
        left_vertices = []
        center_vertices = []
        right_vertices = []
        for i in range(num_vertices):
            left_vertices.append([length_div * i + eps, width / 2 + eps])
            center_vertices.append([length_div * i + eps, eps])
            right_vertices.append([length_div * i + eps, -(width / 2) + eps])

        left_vertices = np.array(left_vertices)
        center_vertices = np.array(center_vertices)
        right_vertices = np.array(right_vertices)

        if stop_line_at_end:
            stop_line.start = left_vertices[-1]
            stop_line.end = right_vertices[-1]
        elif stop_line_at_beginning:
            stop_line.start = left_vertices[0]
            stop_line.end = right_vertices[0]

        lanelet = Lanelet(
            left_vertices=left_vertices,
            right_vertices=right_vertices,
            predecessor=predecessor,
            successor=successor,
            adjacent_left=adjacent_left,
            adjacent_right=adjacent_right,
            adjacent_left_same_direction=adjacent_left_same_direction,
            adjacent_right_same_direction=adjacent_right_same_direction,
            lanelet_id=lanelet_id,
            center_vertices=center_vertices,
            lanelet_type=lanelet_types,
            user_one_way=road_user_one_way,
            user_bidirectional=road_user_bidirectional,
            line_marking_right_vertices=line_marking_right,
            line_marking_left_vertices=line_marking_left,
            stop_line=stop_line,
            traffic_signs=traffic_signs,
            traffic_lights=traffic_lights,
        )
        if backwards:
            lanelet.translate_rotate(-lanelet.center_vertices[0], np.pi)

        return lanelet

    @staticmethod
    def create_curve(
        width: float,
        radius: float,
        angle: float,
        num_vertices: int,
        lanelet_id: int,
        lanelet_types: Set[LaneletType],
        predecessor: List[int] = None,
        successor: List[int] = None,
        adjacent_left: Union[int, None] = None,
        adjacent_right: Union[int, None] = None,
        adjacent_left_same_direction: bool = None,
        adjacent_right_same_direction: bool = None,
        road_user_one_way: Set[RoadUser] = None,
        road_user_bidirectional: Set[RoadUser] = None,
        line_marking_left: LineMarking = LineMarking.UNKNOWN,
        line_marking_right: LineMarking = LineMarking.UNKNOWN,
        stop_line: StopLine = None,
        traffic_signs: Set[int] = None,
        traffic_lights: Set[int] = None,
        stop_line_at_end: bool = False,
        stop_line_at_beginning: bool = False,
    ) -> Lanelet:
        """
        Function for creating a straight lanelet given a length, width, and number of vertices.

        @param width: Width of the lanelet.
        @param radius: Radius of new curved lanelet.
        @param angle: Angle of new curved lanelet.
        @param num_vertices: Number of vertices of the lanelet.
        @param lanelet_id: Id for new lanelet.
        @param lanelet_types: Lanelet types for new lanelet.
        @param adjacent_left: Left adjacent lanelet.
        @param adjacent_right Right adjacent lanelet.
        @param adjacent_left_same_direction: Boolean indicating whether adjacent left has same direction.
        @param adjacent_right_same_direction: Boolean indicating whether adjacent right has same direction.
        @param predecessor: Predecessor lanelets.
        @param successor: Successor lanelets.
        @param road_user_one_way: Allowed road users one way for new lanelet.
        @param road_user_bidirectional: Allowed road users bidirectional for new lanelet.
        @param line_marking_left: Line markings on the left for new lanelet.
        @param line_marking_right: Line markings on the right for new lanelet.
        @param stop_line: Stop line of new lanelet.
        @param traffic_signs: Referenced traffic signs by new lanelet.
        @param traffic_lights: Referenced traffic lights by new lanelet.
        @param stop_line_at_end: Boolean indicating whether stop line positions should correspond with end of lanelet.
        @return: Newly created lanelet.
        """
        angle_div = angle / (num_vertices - 1)
        radius_left = radius - (width / 2)
        radius_right = radius + (width / 2)
        left_vert = []
        center_vert = []
        right_vert = []
        for i in range(num_vertices):
            left_vert.append(
                [np.cos(i * angle_div) * radius_left, np.sin(i * angle_div) * radius_left]
            )
            center_vert.append([np.cos(i * angle_div) * radius, np.sin(i * angle_div) * radius])
            right_vert.append(
                [np.cos(i * angle_div) * radius_right, np.sin(i * angle_div) * radius_right]
            )

        left_vertices = np.array(left_vert)
        center_vertices = np.array(center_vert)
        right_vertices = np.array(right_vert)

        angle_start = -np.pi / 2
        if angle < 0:
            left_vertices = np.array(right_vert)
            center_vertices = np.array(center_vert)
            right_vertices = np.array(left_vert)
            angle_start = -angle_start

        if stop_line_at_end:
            stop_line.start = left_vertices[-1]
            stop_line.end = right_vertices[-1]
        elif stop_line_at_beginning:
            stop_line.start = left_vertices[0]
            stop_line.end = right_vertices[0]

        lanelet = Lanelet(
            left_vertices=left_vertices,
            right_vertices=right_vertices,
            lanelet_id=lanelet_id,
            center_vertices=center_vertices,
            predecessor=predecessor,
            successor=successor,
            adjacent_left=adjacent_left,
            adjacent_right=adjacent_right,
            adjacent_left_same_direction=adjacent_left_same_direction,
            adjacent_right_same_direction=adjacent_right_same_direction,
            lanelet_type=lanelet_types,
            user_one_way=road_user_one_way,
            user_bidirectional=road_user_bidirectional,
            line_marking_right_vertices=line_marking_right,
            line_marking_left_vertices=line_marking_left,
            stop_line=stop_line,
            traffic_signs=traffic_signs,
            traffic_lights=traffic_lights,
        )
        lanelet.translate_rotate(np.array([0, 0]), angle_start)
        lanelet.translate_rotate(-lanelet.center_vertices[0], 0)

        return lanelet

    @staticmethod
    def create_adjacent_lanelet(
        create_adj_left: bool,
        base_lanelet: Lanelet,
        lanelet_id: int,
        same_direction: bool,
        width: float,
        lanelet_types: Set[LaneletType],
        predecessor: List[int] = None,
        successor: List[int] = None,
        road_user_one_way: Set[RoadUser] = None,
        road_user_bidirectional: Set[RoadUser] = None,
        line_marking_left: LineMarking = LineMarking.UNKNOWN,
        line_marking_right: LineMarking = LineMarking.UNKNOWN,
        stop_line: StopLine = None,
        traffic_signs: Set[int] = None,
        traffic_lights: Set[int] = None,
        stop_line_at_end: bool = False,
    ) -> Union[Lanelet, None]:
        """
        Creates adjacent left or adjacent right lanelet for given lanelet.

        @param create_adj_left: Boolean indicating whether adjacent left or right should be created.
        @param base_lanelet: Lanelet for which adjacent lanelet should be created.
        @param lanelet_id: ID of new lanelet.
        @param same_direction: Boolean indicating whether the newly created lanelet should have the same
        direction as the given lanelet.
        @param width: Width of the new lanelet.
        @param lanelet_types: Lanelet types for the new lanelet.
        @param predecessor: IDs of predecessor lanelets of the new lanelet.
        @param successor: IDs of successor lanelets of the new lanelet.
        @param road_user_one_way: Set of allowed road users one way.
        @param road_user_bidirectional: Set of allowed road users bidirectional.
        @param line_marking_left: Left line marking for the left lanelet.
        @param line_marking_right: Left line marking for the left lanelet.
        @param stop_line: Stop line of new lanelet.
        @param traffic_signs: Referenced traffic signs by new lanelet.
        @param traffic_lights: Referenced traffic lights by new lanelet.
        @param stop_line_at_end: Boolean indicating whether stop line positions should correspond with end of lanelet.
        @return: Newly created lanelet.
        """
        if base_lanelet.adj_left is None and create_adj_left:
            diff_left_vert_right_vert = base_lanelet.right_vertices - base_lanelet.left_vertices
            norm_left = np.array([np.linalg.norm(diff_left_vert_right_vert, axis=1)])
            left_vertices = (
                base_lanelet.left_vertices - (diff_left_vert_right_vert / norm_left.T) * width
            )
            center_vertices = (
                base_lanelet.left_vertices - (diff_left_vert_right_vert / norm_left.T) * width / 2
            )
            right_vertices = base_lanelet.left_vertices
            adjacent_right = base_lanelet.lanelet_id
            adjacent_right_same_direction = same_direction
            adjacent_left = None
            adjacent_left_same_direction = None
            base_lanelet.adj_left = lanelet_id
            base_lanelet.adj_left_same_direction = same_direction
        elif base_lanelet.adj_right is None and not create_adj_left:
            diff_left_vert_right_vert = base_lanelet.right_vertices - base_lanelet.left_vertices
            norm_left = np.array([np.linalg.norm(diff_left_vert_right_vert, axis=1)])
            left_vertices = base_lanelet.right_vertices
            center_vertices = (
                base_lanelet.right_vertices + (diff_left_vert_right_vert / norm_left.T) * width / 2
            )
            right_vertices = (
                base_lanelet.right_vertices + (diff_left_vert_right_vert / norm_left.T) * width
            )
            adjacent_right = None
            adjacent_right_same_direction = None
            adjacent_left = base_lanelet.lanelet_id
            adjacent_left_same_direction = same_direction
            base_lanelet.adj_right = lanelet_id
            base_lanelet.adj_right_same_direction = same_direction
        else:
            print("Adjacent lanelet already exists.")
            return None

        if same_direction is False:
            vertices_tmp = left_vertices
            adjacent_left_tmp = adjacent_left
            adjacent_left_same_direction_tmp = adjacent_left_same_direction
            left_vertices = np.flip(right_vertices, 0)
            center_vertices = np.flip(center_vertices, 0)
            right_vertices = np.flip(vertices_tmp, 0)
            adjacent_left = adjacent_right
            adjacent_right = adjacent_left_tmp
            adjacent_left_same_direction = adjacent_right_same_direction
            adjacent_right_same_direction = adjacent_left_same_direction_tmp

        if stop_line_at_end:
            stop_line.start = left_vertices[-1]
            stop_line.end = right_vertices[-1]

        lanelet = Lanelet(
            left_vertices=left_vertices,
            right_vertices=right_vertices,
            lanelet_id=lanelet_id,
            center_vertices=center_vertices,
            predecessor=predecessor,
            successor=successor,
            adjacent_right=adjacent_right,
            adjacent_left=adjacent_left,
            lanelet_type=lanelet_types,
            adjacent_right_same_direction=adjacent_right_same_direction,
            adjacent_left_same_direction=adjacent_left_same_direction,
            user_one_way=road_user_one_way,
            user_bidirectional=road_user_bidirectional,
            line_marking_right_vertices=line_marking_right,
            line_marking_left_vertices=line_marking_left,
            stop_line=stop_line,
            traffic_signs=traffic_signs,
            traffic_lights=traffic_lights,
        )

        return lanelet

    @staticmethod
    def lanelet_is_straight(lanelet: Lanelet):
        """
        Checks wether lanelet is straight

        @param lanelet: Lanelet of which it should be checked whether it is straight.
        @return: bool value of result
        """
        x_start = round(lanelet.left_vertices[0][0] - lanelet.right_vertices[0][0], 3)
        y_start = round(lanelet.left_vertices[0][1] - lanelet.right_vertices[0][1], 3)
        x_end = round(
            lanelet.left_vertices[len(lanelet.left_vertices) - 1][0]
            - lanelet.right_vertices[len(lanelet.right_vertices) - 1][0],
            3,
        )
        y_end = round(
            lanelet.left_vertices[len(lanelet.left_vertices) - 1][1]
            - lanelet.right_vertices[len(lanelet.right_vertices) - 1][1],
            3,
        )
        return x_start == x_end and y_start == y_end

    @staticmethod
    def fit_to_predecessor(predecessor: Lanelet, successor: Lanelet, intersection: bool = False):
        """
        Function to translate a lanelet so that it fits to a given predecessor lanelet.

        @param predecessor: Lanelet to which given lanelet should be attached.
        @param successor: Lanelet which should be attached to the predecessor lanelet.
        """

        len_suc = np.round(
            np.linalg.norm(successor.center_vertices[0] - successor.center_vertices[-1]), 2
        )
        len_pred = np.round(
            np.linalg.norm(predecessor.center_vertices[0] - predecessor.center_vertices[-1]), 2
        )
        wid_suc = np.round(
            np.linalg.norm(successor.left_vertices[0] - successor.right_vertices[0]), 2
        )
        wid_pred = np.round(
            np.linalg.norm(predecessor.left_vertices[0] - predecessor.right_vertices[0]), 2
        )
        same_length_width = len_suc == len_pred and wid_suc == wid_pred

        if (
            MapCreator.lanelet_is_straight(predecessor)
            and MapCreator.lanelet_is_straight(successor)
            and not intersection
            and same_length_width
        ):
            successor._left_vertices = predecessor.left_vertices
            successor._center_vertices = predecessor.center_vertices
            successor._right_vertices = predecessor.right_vertices

        if same_length_width:
            factor = np.linalg.norm(
                successor.left_vertices[0, :] - successor.right_vertices[0, :]
            ) / np.linalg.norm(
                (predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])
            )

            successor._left_vertices = successor.left_vertices / factor
            successor._right_vertices = successor.right_vertices / factor
            successor._center_vertices = successor.center_vertices / factor

        ang = MapCreator.calc_angle_between_lanelets(predecessor, successor)

        if not is_natural_number(ang) and not intersection and same_length_width:
            ang = 0
            if not MapCreator.lanelet_is_straight(predecessor):
                b = successor.right_vertices[0] - successor.center_vertices[0]
                a = predecessor.right_vertices[-1] - predecessor.center_vertices[-1]
                inner = np.inner(a, b)
                if inner == 0:
                    sign = np.cross(a, b)
                    if sign > 0:
                        ang = -np.pi / 2
                    else:
                        ang = np.pi / 2
                else:
                    norms = np.linalg.norm(a) * np.linalg.norm(b)
                    cos = inner / norms
                    ang = np.arccos(np.clip(cos, -1.0, 1.0))
            elif not MapCreator.lanelet_is_straight(successor):
                b = successor.right_vertices[0] - successor.center_vertices[0]
                a = predecessor.right_vertices[-1] - predecessor.center_vertices[-1]
                inner = np.inner(a, b)
                if inner == 0:
                    sign = np.cross(a, b)
                    if sign > 0:
                        ang = -np.pi / 2
                    else:
                        ang = np.pi / 2
                else:
                    norms = np.linalg.norm(a) * np.linalg.norm(b)
                    cos = inner / norms
                    ang = np.arccos(np.clip(cos, -1.0, 1.0))
                    if predecessor.center_vertices[0][1] > predecessor.center_vertices[-1][1]:
                        ang = -ang

        successor.translate_rotate(np.array([0, 0]), ang)
        trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
        successor.translate_rotate(trans, 0)
        if (
            not MapCreator.lanelet_is_straight(predecessor)
            and (
                np.round(predecessor.left_vertices[-1], 5)
                != np.round(successor.left_vertices[0], 5)
            ).any()
        ):
            ang *= -2
            successor.translate_rotate(np.array([0, 0]), ang)
            trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
            successor.translate_rotate(trans, 0)

        MapCreator.set_predecessor_successor_relation(predecessor, successor)

    @staticmethod
    def fit_to_successor(successor: Lanelet, predecessor: Lanelet):
        """
        Function to translate a lanelet so that it fits to a given successor lanelet.

        @param successor: Lanelet to which given lanelet should be attached.
        @param predecessor: Lanelet which should be attached to the successor lanelet.
        """
        pred_straight = MapCreator.lanelet_is_straight(predecessor)
        suc_straight = MapCreator.lanelet_is_straight(successor)

        len_suc = np.round(
            np.linalg.norm(successor.center_vertices[0] - successor.center_vertices[-1]), 2
        )
        len_pred = np.round(
            np.linalg.norm(predecessor.center_vertices[0] - predecessor.center_vertices[-1]), 2
        )
        wid_suc = np.round(
            np.linalg.norm(successor.left_vertices[0] - successor.right_vertices[0]), 2
        )
        wid_pred = np.round(
            np.linalg.norm(predecessor.left_vertices[0] - predecessor.right_vertices[0]), 2
        )
        same_length_width = len_suc == len_pred and wid_suc == wid_pred

        if pred_straight and suc_straight and same_length_width:
            predecessor._left_vertices = successor.left_vertices
            predecessor._center_vertices = successor.center_vertices
            predecessor._right_vertices = successor.right_vertices

        ang = MapCreator.calc_angle_between_lanelets(predecessor, successor)
        if not is_natural_number(ang):
            ang = 0
            if not suc_straight or not pred_straight or not same_length_width:
                a = predecessor.right_vertices[-1] - predecessor.center_vertices[-1]
                b = successor.right_vertices[0] - successor.center_vertices[0]
                inner = np.inner(a, b)
                norms = np.linalg.norm(a) * np.linalg.norm(b)
                cos = inner / norms
                ang = np.arccos(np.clip(cos, -1.0, 1.0))
                if (
                    not pred_straight
                    and successor.center_vertices[-1][0] > successor.center_vertices[0][0]
                    or not same_length_width
                    and successor.center_vertices[-1][1] < successor.center_vertices[0][1]
                ):
                    ang = -ang

        predecessor.translate_rotate(np.array([0, 0]), ang)

        if pred_straight and suc_straight and same_length_width:
            trans = predecessor.center_vertices[0] - successor.center_vertices[-1]
            predecessor.translate_rotate(trans, 0)
        else:
            trans = successor.center_vertices[0] - predecessor.center_vertices[-1]
            predecessor.translate_rotate(trans, 0)

        if (
            not suc_straight
            and (
                np.round(predecessor.left_vertices[-1], 5)
                != np.round(successor.left_vertices[0], 5)
            ).any()
            and same_length_width
        ):
            ang *= -2
            predecessor.translate_rotate(np.array([0, 0]), ang)
            trans = successor.center_vertices[0] - predecessor.center_vertices[-1]
            predecessor.translate_rotate(trans, 0)

        MapCreator.set_predecessor_successor_relation(predecessor, successor)

    @staticmethod
    def calc_angle_between_lanelets(predecessor: Lanelet, lanelet: Lanelet):
        """
        Computes the angle between two lanelets
        @param predecessor: Predecessor lanelet
        @param lanelet: Potential successor lanelet.
        @return: Calculated angle
        """
        line_predecessor = predecessor.left_vertices[-1] - predecessor.right_vertices[-1]
        line_lanelet = lanelet.left_vertices[0] - lanelet.right_vertices[0]
        norm_predecessor = np.linalg.norm(line_predecessor)
        norm_lanelet = np.linalg.norm(line_lanelet)
        dot_prod = np.dot(line_predecessor, line_lanelet)
        sign = line_lanelet[1] * line_predecessor[0] - line_lanelet[0] * line_predecessor[1]
        angle = np.arccos(dot_prod / (norm_predecessor * norm_lanelet))
        if sign > 0:
            angle = 2 * np.pi - angle
        return angle

    @staticmethod
    def set_predecessor_successor_relation(predecessor: Lanelet, successor: Lanelet):
        """
        Sets the predecessor and successor lanelet relationships between two given lanelets.

        @param predecessor: Predecessor lanelet.
        @param successor: Successor lanelet.
        """
        successor.add_predecessor(predecessor.lanelet_id)
        predecessor.add_successor(successor.lanelet_id)

    @staticmethod
    def remove_lanelet(lanelet_id: int, network: LaneletNetwork):
        """
        Removes a lanelet from a lanelet network of a CommonRoad scenario.

        @param lanelet_id: ID of lanelet which should be removed.
        @param network: Lanelet network from which the lanelet should be removed.
        """
        network.remove_lanelet(lanelet_id)

    @staticmethod
    def create_four_way_intersection(
        width: float,
        diameter_crossing: int,
        incoming_length: int,
        scenario: Scenario,
        add_traffic_signs: bool,
        add_traffic_lights: bool,
        country_signs: Union[
            TrafficSignIDArgentina,
            TrafficSignIDBelgium,
            TrafficSignIDChina,
            TrafficSignIDCroatia,
            TrafficSignIDFrance,
            TrafficSignIDGermany,
            TrafficSignIDGreece,
            TrafficSignIDItaly,
            TrafficSignIDPuertoRico,
            TrafficSignIDRussia,
            TrafficSignIDSpain,
            TrafficSignIDUsa,
            TrafficSignIDZamunda,
        ],
    ) -> Tuple[Intersection, List[TrafficSign], List[TrafficLight], List[Lanelet]]:
        """
        Creates a four way intersection with predefined line markings at the origin.

        @param width: The width of the created lanelets.
        @param diameter_crossing: The length of the main part of the intersection.
        @param incoming_length: Length of the incoming lanelets of the intersection.
        @param scenario: The scenario to which the intersection will be added.
        @param add_traffic_signs: Boolean indicating whether traffic signs should be added to intersection.
        @param add_traffic_lights: Boolean indicating whether traffic lights should be added to intersection.
        @param country_signs: List of supported traffic signs.
        @return: New intersection element and new lanelets.
        """
        rad = (diameter_crossing + width) / 2
        lanelet_ids = [scenario.generate_object_id() for i in range(0, 20)]
        new_lanelets = []
        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[0],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[0],
                lanelet_ids[1],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                diameter_crossing,
                10,
                lanelet_ids[2],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[0], new_lanelets[2], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[2],
                lanelet_ids[3],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[4],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[0], new_lanelets[4], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[4],
                lanelet_ids[5],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[6],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[4], new_lanelets[6], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[6],
                lanelet_ids[7],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[8],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[2], new_lanelets[8], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[8],
                lanelet_ids[9],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[10],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[7], new_lanelets[10], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[10],
                lanelet_ids[11],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                diameter_crossing,
                10,
                lanelet_ids[12],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[7], new_lanelets[12], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[12],
                lanelet_ids[13],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[14],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[12], new_lanelets[14], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[14],
                lanelet_ids[15],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[16],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[9], new_lanelets[16], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[16],
                lanelet_ids[17],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[18],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[15], new_lanelets[18], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[18],
                lanelet_ids[19],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        # missing dependencies
        MapCreator.set_predecessor_successor_relation(new_lanelets[0], new_lanelets[19])
        MapCreator.set_predecessor_successor_relation(new_lanelets[18], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[10], new_lanelets[8])
        MapCreator.set_predecessor_successor_relation(new_lanelets[9], new_lanelets[11])
        MapCreator.set_predecessor_successor_relation(new_lanelets[16], new_lanelets[14])
        MapCreator.set_predecessor_successor_relation(new_lanelets[15], new_lanelets[17])
        MapCreator.set_predecessor_successor_relation(new_lanelets[17], new_lanelets[8])
        MapCreator.set_predecessor_successor_relation(new_lanelets[13], new_lanelets[6])
        MapCreator.set_predecessor_successor_relation(new_lanelets[15], new_lanelets[13])
        MapCreator.set_predecessor_successor_relation(new_lanelets[11], new_lanelets[6])
        MapCreator.set_predecessor_successor_relation(new_lanelets[3], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[5], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[5], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[19], new_lanelets[14])
        MapCreator.set_predecessor_successor_relation(new_lanelets[9], new_lanelets[3])
        MapCreator.set_predecessor_successor_relation(new_lanelets[7], new_lanelets[5])

        incomings = [lanelet_ids[0], lanelet_ids[7], lanelet_ids[9], lanelet_ids[15]]
        successors_right = [lanelet_ids[19], lanelet_ids[5], lanelet_ids[11], lanelet_ids[17]]
        successors_straight = [lanelet_ids[2], lanelet_ids[12], lanelet_ids[3], lanelet_ids[13]]
        successors_left = [lanelet_ids[4], lanelet_ids[10], lanelet_ids[16], lanelet_ids[18]]
        incoming_ids = [scenario.generate_object_id() for i in range(len(incomings))]
        left_of = [incoming_ids[-1], incoming_ids[0], incoming_ids[1], incoming_ids[2]]
        map_incoming = []

        for n in range(len(incomings)):
            inc = {incomings[n]}
            right = {successors_right[n]}
            left = {successors_left[n]}
            straight = {successors_straight[n]}
            incoming_id = incoming_ids[n]
            map_incoming.append(
                IntersectionIncomingElement(
                    incoming_id,
                    incoming_lanelets=inc,
                    successors_right=right,
                    successors_straight=straight,
                    successors_left=left,
                    left_of=left_of[n],
                )
            )
        intersection_id = scenario.generate_object_id()
        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming)

        new_traffic_signs = []
        sign_ids = [set()] * 4
        new_traffic_lights = []
        light_ids = [set()] * 4
        # TODO compute first occurrences
        if (
            add_traffic_signs
            and "YIELD" in country_signs._member_names_
            and "PRIORITY" in country_signs._member_names_
        ):
            yield_sign = TrafficSignElement(country_signs.YIELD)
            priority_sign = TrafficSignElement(country_signs.PRIORITY)
            sign_priority_one = TrafficSign(
                scenario.generate_object_id(),
                [priority_sign],
                set(),
                new_lanelets[0].right_vertices[-1] + np.array([-4, -2]),
            )
            new_lanelets[0].add_traffic_sign_to_lanelet(sign_priority_one.traffic_sign_id)
            new_traffic_signs.append(sign_priority_one)
            sign_ids[0] = {sign_priority_one.traffic_sign_id}

            sign_priority_two = TrafficSign(
                scenario.generate_object_id(),
                [priority_sign],
                set(),
                new_lanelets[9].right_vertices[-1] + np.array([4, 2]),
            )
            new_lanelets[9].add_traffic_sign_to_lanelet(sign_priority_two.traffic_sign_id)
            new_traffic_signs.append(sign_priority_two)
            sign_ids[1] = {sign_priority_two.traffic_sign_id}

            sign_yield_one = TrafficSign(
                scenario.generate_object_id(),
                [yield_sign],
                set(),
                new_lanelets[15].right_vertices[-1] + np.array([2, -6]),
            )
            new_lanelets[15].add_traffic_sign_to_lanelet(sign_yield_one.traffic_sign_id)
            new_traffic_signs.append(sign_yield_one)
            sign_ids[2] = {sign_yield_one.traffic_sign_id}

            sign_yield_two = TrafficSign(
                scenario.generate_object_id(),
                [yield_sign],
                set(),
                new_lanelets[7].right_vertices[-1] + np.array([-2, 6]),
            )
            new_lanelets[7].add_traffic_sign_to_lanelet(sign_yield_two.traffic_sign_id)
            new_traffic_signs.append(sign_yield_two)
            sign_ids[3] = {sign_yield_two.traffic_sign_id}

        if add_traffic_lights:
            traffic_light_cycle_one = [
                TrafficLightCycleElement(TrafficLightState.GREEN, 100),
                TrafficLightCycleElement(TrafficLightState.YELLOW, 30),
                TrafficLightCycleElement(TrafficLightState.RED, 100),
                TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 30),
            ]
            traffic_light_cycle_two = [
                TrafficLightCycleElement(TrafficLightState.RED, 100),
                TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 30),
                TrafficLightCycleElement(TrafficLightState.GREEN, 100),
                TrafficLightCycleElement(TrafficLightState.YELLOW, 30),
            ]
            traffic_light_one = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[0].right_vertices[-1] + np.array([-1, -2]),
                TrafficLightCycle(traffic_light_cycle_one),
            )
            new_traffic_lights.append(traffic_light_one)
            new_lanelets[0].add_traffic_light_to_lanelet(traffic_light_one.traffic_light_id)
            light_ids[0] = {traffic_light_one.traffic_light_id}

            traffic_light_two = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[9].right_vertices[-1] + np.array([1, 2]),
                TrafficLightCycle(traffic_light_cycle_one),
            )
            new_traffic_lights.append(traffic_light_two)
            new_lanelets[9].add_traffic_light_to_lanelet(traffic_light_two.traffic_light_id)
            light_ids[1] = {traffic_light_two.traffic_light_id}

            traffic_light_three = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[15].right_vertices[-1] + np.array([2, -2]),
                TrafficLightCycle(traffic_light_cycle_two),
            )
            new_traffic_lights.append(traffic_light_three)
            new_lanelets[15].add_traffic_light_to_lanelet(traffic_light_three.traffic_light_id)
            light_ids[2] = {traffic_light_three.traffic_light_id}

            traffic_light_four = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[7].right_vertices[-1] + np.array([-2, 2]),
                TrafficLightCycle(traffic_light_cycle_two),
            )
            new_traffic_lights.append(traffic_light_four)
            new_lanelets[7].add_traffic_light_to_lanelet(traffic_light_four.traffic_light_id)
            light_ids[3] = {traffic_light_four.traffic_light_id}

        if add_traffic_lights or add_traffic_signs:
            for ref, la_idx in enumerate([0, 9, 15, 7]):
                new_lanelets[la_idx].stop_line = StopLine(
                    new_lanelets[la_idx].right_vertices[-1],
                    new_lanelets[la_idx].left_vertices[-1],
                    LineMarking.SOLID,
                    sign_ids[ref],
                    light_ids[ref],
                )

        return intersection, new_traffic_signs, new_traffic_lights, new_lanelets

    @staticmethod
    def create_three_way_intersection(
        width: float,
        diameter_crossing: int,
        incoming_length: int,
        scenario: Scenario,
        add_traffic_signs: bool,
        add_traffic_lights: bool,
        country_signs: Union[
            TrafficSignIDArgentina,
            TrafficSignIDBelgium,
            TrafficSignIDChina,
            TrafficSignIDCroatia,
            TrafficSignIDFrance,
            TrafficSignIDGermany,
            TrafficSignIDGreece,
            TrafficSignIDItaly,
            TrafficSignIDPuertoRico,
            TrafficSignIDRussia,
            TrafficSignIDSpain,
            TrafficSignIDUsa,
            TrafficSignIDZamunda,
        ],
    ) -> Tuple[Intersection, List[TrafficSign], List[TrafficLight], List[Lanelet]]:
        """
        Creates a four way intersection with predefined line markings at the origin.

        @param width: The width of the created lanelets.
        @param diameter_crossing: The length of the main part of the intersection.
        @param incoming_length: Length of the incoming lanelets of the intersection.
        @param scenario: The scenario to which the intersection will be added.
        @param add_traffic_signs: Boolean indicating whether traffic signs should be added to intersection.
        @param add_traffic_lights: Boolean indicating whether traffic lights should be added to intersection.
        @param country_signs: List of supported traffic signs.
        @return: New intersection element and new lanelets.
        """
        new_lanelets = []
        rad = (diameter_crossing + width) / 2
        lanelet_ids = [scenario.generate_object_id() for i in range(0, 12)]
        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[0],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[0],
                lanelet_ids[1],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[2],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[0], new_lanelets[2], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[2],
                lanelet_ids[3],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[4],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[2], new_lanelets[4], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[4],
                lanelet_ids[5],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                diameter_crossing,
                10,
                lanelet_ids[6],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[5], new_lanelets[6], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[6],
                lanelet_ids[7],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_straight(
                width,
                incoming_length,
                10,
                lanelet_ids[8],
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[6], new_lanelets[8], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[8],
                lanelet_ids[9],
                False,
                width,
                {LaneletType.UNKNOWN},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.DASHED,
                line_marking_right=LineMarking.SOLID,
            )
        )

        new_lanelets.append(
            MapCreator.create_curve(
                width,
                rad,
                np.pi * 0.5,
                20,
                lanelet_ids[10],
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.NO_MARKING,
            )
        )
        MapCreator.fit_to_predecessor(new_lanelets[9], new_lanelets[10], True)
        new_lanelets.append(
            MapCreator.create_adjacent_lanelet(
                True,
                new_lanelets[10],
                lanelet_ids[11],
                False,
                width,
                {LaneletType.INTERSECTION},
                road_user_one_way={RoadUser.VEHICLE},
                line_marking_left=LineMarking.NO_MARKING,
                line_marking_right=LineMarking.SOLID,
            )
        )

        # missing dependencies
        MapCreator.set_predecessor_successor_relation(new_lanelets[0], new_lanelets[11])
        MapCreator.set_predecessor_successor_relation(new_lanelets[10], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[3], new_lanelets[1])
        MapCreator.set_predecessor_successor_relation(new_lanelets[9], new_lanelets[7])
        MapCreator.set_predecessor_successor_relation(new_lanelets[11], new_lanelets[8])
        MapCreator.set_predecessor_successor_relation(new_lanelets[5], new_lanelets[3])
        MapCreator.set_predecessor_successor_relation(new_lanelets[7], new_lanelets[4])

        incomings = [lanelet_ids[0], lanelet_ids[5], lanelet_ids[9]]
        successors_right = [lanelet_ids[11], lanelet_ids[3], None]
        successors_straight = [None, lanelet_ids[6], lanelet_ids[7]]
        successors_left = [lanelet_ids[2], None, lanelet_ids[10]]
        incoming_ids = [scenario.generate_object_id() for i in range(len(incomings))]
        left_of = [incoming_ids[-1], incoming_ids[0], None]
        map_incoming = []

        for n in range(len(incomings)):
            inc = {incomings[n]}
            right = {successors_right[n]} if successors_right[n] is not None else set()
            left = {successors_left[n]} if successors_left[n] is not None else set()
            straight = {successors_straight[n]} if successors_straight[n] is not None else set()
            incoming_id = incoming_ids[n]
            map_incoming.append(
                IntersectionIncomingElement(
                    incoming_id,
                    incoming_lanelets=inc,
                    successors_right=right,
                    successors_straight=straight,
                    successors_left=left,
                    left_of=left_of[n],
                )
            )

        intersection_id = scenario.generate_object_id()
        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming)

        new_traffic_signs = []
        new_traffic_lights = []
        sign_ids = [set()] * 4
        light_ids = [set()] * 4
        # TODO compute first occurrences
        if (
            add_traffic_signs
            and "YIELD" in country_signs._member_names_
            and "PRIORITY" in country_signs._member_names_
        ):
            yield_sign = TrafficSignElement(country_signs.YIELD)
            priority_sign = TrafficSignElement(country_signs.PRIORITY)
            sign_priority_one = TrafficSign(
                scenario.generate_object_id(),
                [priority_sign],
                set(),
                new_lanelets[5].right_vertices[-1] + np.array([-2, 6]),
            )
            new_lanelets[5].add_traffic_sign_to_lanelet(sign_priority_one.traffic_sign_id)
            new_traffic_signs.append(sign_priority_one)
            sign_ids[0] = {sign_priority_one.traffic_sign_id}

            sign_priority_two = TrafficSign(
                scenario.generate_object_id(),
                [priority_sign],
                set(),
                new_lanelets[9].right_vertices[-1] + np.array([2, -6]),
            )
            new_lanelets[9].add_traffic_sign_to_lanelet(sign_priority_two.traffic_sign_id)
            new_traffic_signs.append(sign_priority_two)
            sign_ids[1] = {sign_priority_two.traffic_sign_id}

            sign_yield_one = TrafficSign(
                scenario.generate_object_id(),
                [yield_sign],
                set(),
                new_lanelets[0].right_vertices[-1] + np.array([-4, -2]),
            )
            new_lanelets[0].add_traffic_sign_to_lanelet(sign_yield_one.traffic_sign_id)
            new_traffic_signs.append(sign_yield_one)
            sign_ids[1] = {sign_yield_one.traffic_sign_id}

        if add_traffic_lights:
            traffic_light_cycle_one = [
                TrafficLightCycleElement(TrafficLightState.GREEN, 100),
                TrafficLightCycleElement(TrafficLightState.YELLOW, 30),
                TrafficLightCycleElement(TrafficLightState.RED, 100),
                TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 30),
            ]
            traffic_light_cycle_two = [
                TrafficLightCycleElement(TrafficLightState.RED, 100),
                TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 30),
                TrafficLightCycleElement(TrafficLightState.GREEN, 100),
                TrafficLightCycleElement(TrafficLightState.YELLOW, 30),
            ]
            traffic_light_one = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[5].right_vertices[-1] + np.array([-2, 2]),
                TrafficLightCycle(traffic_light_cycle_one),
            )
            new_traffic_lights.append(traffic_light_one)
            new_lanelets[5].add_traffic_light_to_lanelet(traffic_light_one.traffic_light_id)
            light_ids[0] = {traffic_light_one.traffic_light_id}

            traffic_light_two = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[9].right_vertices[-1] + np.array([2, -2]),
                TrafficLightCycle(traffic_light_cycle_one),
            )
            new_traffic_lights.append(traffic_light_two)
            new_lanelets[9].add_traffic_light_to_lanelet(traffic_light_two.traffic_light_id)
            light_ids[1] = {traffic_light_two.traffic_light_id}

            traffic_light_three = TrafficLight(
                scenario.generate_object_id(),
                new_lanelets[0].right_vertices[-1] + np.array([-1, -2]),
                TrafficLightCycle(traffic_light_cycle_two),
            )
            new_traffic_lights.append(traffic_light_three)
            new_lanelets[0].add_traffic_light_to_lanelet(traffic_light_three.traffic_light_id)
            light_ids[2] = {traffic_light_three.traffic_light_id}

        if add_traffic_lights or add_traffic_signs:
            for ref, la_idx in enumerate([5, 9, 0]):
                new_lanelets[la_idx].stop_line = StopLine(
                    new_lanelets[la_idx].right_vertices[-1],
                    new_lanelets[la_idx].left_vertices[-1],
                    LineMarking.SOLID,
                    sign_ids[ref],
                    light_ids[ref],
                )

        return intersection, new_traffic_signs, new_traffic_lights, new_lanelets

    @staticmethod
    def calc_radius(lanelet):
        line_predecessor = lanelet.left_vertices[0] - lanelet.right_vertices[0]
        line_lanelet = lanelet.left_vertices[-1] - lanelet.right_vertices[-1]
        b = (
            lanelet.center_vertices[0, 1] * line_predecessor[0]
            + line_predecessor[1] * lanelet.center_vertices[-1, 0]
            - lanelet.center_vertices[0, 0] * line_predecessor[1]
            - lanelet.center_vertices[-1, 1] * line_predecessor[0]
        ) / (line_lanelet[1] * line_predecessor[0] - line_predecessor[1] * line_lanelet[0])
        x = lanelet.center_vertices[-1] + b * line_lanelet
        rad = np.linalg.norm(x - lanelet.center_vertices[0])
        rad = round(rad, 0)
        return rad

    @staticmethod
    def calc_angle_between2(lanelet):
        line_predecessor = lanelet.left_vertices[-1] - lanelet.right_vertices[-1]
        line_lanelet = lanelet.left_vertices[0] - lanelet.right_vertices[0]
        norm_predecessor = np.linalg.norm(line_predecessor)
        norm_lanelet = np.linalg.norm(line_lanelet)
        dot_prod = np.dot(line_predecessor, line_lanelet)
        sign = line_lanelet[1] * line_predecessor[0] - line_lanelet[0] * line_predecessor[1]
        angle = np.arccos(dot_prod / (norm_predecessor * norm_lanelet))
        if sign < 0:
            angle = 2 * np.pi - angle

        return angle

    @staticmethod
    def fit_intersection_to_predecessor(predecessor, successor, intersection, network):
        if predecessor and successor and intersection:
            lanelet_ids = []
            x = []
            for i in intersection.incomings:
                if i._successors_left is not None:
                    left = list(i._successors_left)
                else:
                    left = []

                if i._successors_right is not None:
                    right = list(i._successors_right)
                else:
                    right = []

                if i._successors_straight is not None:
                    straight = list(i._successors_straight)
                else:
                    straight = []

                if i._incoming_lanelets is not None:
                    inc = list(i._incoming_lanelets)
                else:
                    inc = []
                x = x + left + right + straight + inc

            for idx in x:
                lanelet = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=idx)
                if lanelet:
                    lanelet_ids.append(idx)
                    if lanelet.adj_left:
                        lanelet_ids.append(lanelet.adj_left)
                    if lanelet.adj_right:
                        lanelet_ids.append(lanelet.adj_right)
            lanelet_ids = set(lanelet_ids)
            lanelet_ids = list(lanelet_ids)

            if predecessor.lanelet_id in lanelet_ids:
                print("Error: Intersection cannot be fit to lanelet belonging to same intersection")
                return

            if successor.lanelet_id not in lanelet_ids:
                print("Error: Successor lanelet must belong to intersection")
                return

            factor = np.linalg.norm(
                successor.left_vertices[0, :] - successor.right_vertices[0, :]
            ) / np.linalg.norm(
                (predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])
            )

            ang = MapCreator.calc_angle_between_lanelets(predecessor, successor)
            successor.translate_rotate(np.array([0, 0]), ang)
            successor._left_vertices = successor.left_vertices / factor
            successor._right_vertices = successor.right_vertices / factor
            successor._center_vertices = successor.center_vertices / factor
            trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
            for idx in lanelet_ids:
                lanelet = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=idx)
                if lanelet != successor:
                    lanelet._left_vertices = lanelet.left_vertices / factor
                    lanelet._right_vertices = lanelet.right_vertices / factor
                    lanelet._center_vertices = lanelet.center_vertices / factor
                    lanelet.translate_rotate(np.array([0, 0]), ang)
                lanelet.translate_rotate(trans, 0)

            # Relation
            successor._predecessor = []
            MapCreator.set_predecessor_successor_relation(predecessor, successor)

    @staticmethod
    def connect_lanelets(predecessor: Lanelet, successor: Lanelet, lanelet_id: int):
        if predecessor and successor:
            connecting_vec = successor.center_vertices[0] - predecessor.center_vertices[-1]
            length_con_vec = np.linalg.norm(connecting_vec)
            connecting_vec = connecting_vec / length_con_vec
            vec_width_pred = predecessor.left_vertices[-1] - predecessor.right_vertices[-1]
            vec_width_succ = successor.left_vertices[0] - successor.right_vertices[0]
            width_pred = np.linalg.norm(vec_width_pred)
            width_succ = np.linalg.norm(vec_width_succ)
            norm_vec_pred = np.array([vec_width_pred[1], -vec_width_pred[0]])
            norm_vec_succ = np.array([vec_width_succ[1], -vec_width_succ[0]])

            con_vec_factor = length_con_vec * 0.5

            middle_point = (
                predecessor.center_vertices[-1]
                + 0.5 * con_vec_factor * norm_vec_pred / width_pred
                - 0.5 * con_vec_factor * norm_vec_succ / width_succ
                + con_vec_factor * connecting_vec
            )
            center_vertices = np.concatenate(
                (
                    [predecessor.center_vertices[-1]],
                    [predecessor.center_vertices[-1] + 0.000001 * norm_vec_pred / width_pred],
                    [middle_point],
                    [successor.center_vertices[0] - 0.000001 * norm_vec_succ / width_succ],
                    [successor.center_vertices[0]],
                )
            )

            # Linear length along the line:
            distance_center = np.cumsum(
                np.sqrt(np.sum(np.diff(center_vertices, axis=0) ** 2, axis=1))
            )
            distance_center = np.insert(distance_center, 0, 0) / distance_center[-1]

            # Linear distance between points
            diff_dist = np.sqrt(np.sum(np.diff(center_vertices, axis=0) ** 2, axis=1))
            dist_sum = np.sum(diff_dist)
            diff_dist = diff_dist / dist_sum

            # Interpolation for different methods:
            num_points = 20
            alpha = np.linspace(0, 1, num_points)

            interpolator_center = interp1d(distance_center, center_vertices, kind="cubic", axis=0)
            interpolated_center = interpolator_center(alpha)

            # Create matrix for vectorized calculation
            lenght = len(interpolated_center) - 2
            a = np.zeros((lenght, lenght))
            b = np.zeros((lenght, lenght))
            np.fill_diagonal(a, 1)
            np.fill_diagonal(b, -1)
            d = np.zeros((lenght, 2))
            a = np.c_[d, a]
            b = np.c_[b, d]
            a = a + b  # Constructed matrix for calculation
            c = np.dot(a, interpolated_center)  # calculate tangent at point
            # Create normalvectors and normalize them
            e = np.zeros((c.shape))
            e[:, 0] = c[:, 1]
            e[:, 1] = -c[:, 0]
            f = np.sum(np.abs(e) ** 2, axis=-1) ** (1.0 / 2)
            f = np.array([f])
            e = e / f.T

            distance2 = np.cumsum(
                np.sqrt(np.sum(np.diff(interpolated_center, axis=0) ** 2, axis=1))
            )
            distance2 = np.insert(distance2, 0, 0) / distance2[-1]
            distance2 = np.array([distance2])

            h = ((width_pred - (distance2 * (width_pred - width_succ))) / 2).T
            h = h[1:-1]
            e = e * h

            e = np.concatenate((np.array([[0, 0]]), e), axis=0)
            e = np.concatenate((e, np.array([[0, 0]])), axis=0)

            interpolated_left = interpolated_center
            interpolated_left = interpolated_left - e
            interpolated_left[0] = predecessor.left_vertices[-1]
            interpolated_left[-1] = successor.left_vertices[0]

            interpolated_right = interpolated_center
            interpolated_right = interpolated_right + e
            interpolated_right[0] = predecessor.right_vertices[-1]
            interpolated_right[-1] = successor.right_vertices[0]

            connecting_lanelet = Lanelet(
                interpolated_left,
                interpolated_center,
                interpolated_right,
                lanelet_id,
                predecessor=[predecessor.lanelet_id],
                successor=[successor.lanelet_id],
                line_marking_left_vertices=predecessor.line_marking_left_vertices,
                line_marking_right_vertices=predecessor.line_marking_right_vertices,
                lanelet_type=predecessor.lanelet_type.union(successor.lanelet_type),
            )
            MapCreator.set_predecessor_successor_relation(predecessor, connecting_lanelet)
            MapCreator.set_predecessor_successor_relation(connecting_lanelet, successor)
            return connecting_lanelet

    @staticmethod
    def split_lanelet(
        lanelet: Lanelet,
        split_index: int,
        scenario: Scenario,
        network,
        direction: str = "",
        prev_first_lane_id: int = 0,
        prev_second_lane_id: int = 0,
        same_direction: bool = None,
    ):
        # Generate Lanelets
        first_lane_id = scenario.generate_object_id()
        second_lane_id = scenario.generate_object_id()

        left_vertices_first_lane = lanelet.left_vertices[: split_index + 1]
        center_vertices_first_lane = lanelet.center_vertices[: split_index + 1]
        right_vertices_first_lane = lanelet.right_vertices[: split_index + 1]
        predecessor_first_lane = lanelet.predecessor
        successor_first_lane = [second_lane_id]

        left_vertices_second_lane = lanelet.left_vertices[split_index:]
        center_vertices_second_lane = lanelet.center_vertices[split_index:]
        right_vertices_second_lane = lanelet.right_vertices[split_index:]
        predecessor_second_lane = [first_lane_id]
        successor_second_lane = lanelet.successor

        lanelet_first = Lanelet(
            left_vertices=left_vertices_first_lane,
            center_vertices=center_vertices_first_lane,
            right_vertices=right_vertices_first_lane,
            lanelet_id=first_lane_id,
            predecessor=predecessor_first_lane,
            successor=successor_first_lane,
        )
        lanelet_second = Lanelet(
            left_vertices=left_vertices_second_lane,
            center_vertices=center_vertices_second_lane,
            right_vertices=right_vertices_second_lane,
            lanelet_id=second_lane_id,
            predecessor=predecessor_second_lane,
            successor=successor_second_lane,
        )

        scenario.remove_lanelet(lanelet)
        scenario.add_objects([lanelet_first, lanelet_second])

        # Split adjacent Lanelets
        if direction == "" or direction == "l":
            if direction == "l":
                lanelet_first.adj_right = prev_first_lane_id
                lanelet_first.adj_right_same_direction = same_direction
                lanelet_second.adj_right = prev_second_lane_id
                lanelet_second.adj_right_same_direction = same_direction
            if lanelet.adj_left:
                left_adj = network.find_lanelet_by_id(lanelet.adj_left)
                first_adj_left_id, second_adj_left_id = MapCreator.split_lanelet(
                    left_adj,
                    split_index,
                    scenario,
                    network,
                    "l",
                    first_lane_id,
                    second_lane_id,
                    lanelet.adj_left_same_direction,
                )
                lanelet_first.adj_left = first_adj_left_id
                lanelet_first.adj_left_same_direction = lanelet.adj_left_same_direction
                lanelet_second.adj_left = second_adj_left_id
                lanelet_second.adj_left_same_direction = lanelet.adj_left_same_direction
        if direction == "" or direction == "r":
            if direction == "r":
                lanelet_first.adj_left = prev_first_lane_id
                lanelet_first.adj_left_same_direction = same_direction
                lanelet_second.adj_left = prev_second_lane_id
                lanelet_second.adj_left_same_direction = same_direction
            if lanelet.adj_right:
                right_adj = network.find_lanelet_by_id(lanelet.adj_right)
                first_adj_right_id, second_adj_right_id = MapCreator.split_lanelet(
                    right_adj,
                    split_index,
                    scenario,
                    network,
                    "r",
                    first_lane_id,
                    second_lane_id,
                    lanelet.adj_right_same_direction,
                )
                lanelet_first.adj_right = first_adj_right_id
                lanelet_first.adj_right_same_direction = lanelet.adj_right_same_direction
                lanelet_second.adj_right = second_adj_right_id
                lanelet_second.adj_right_same_direction = lanelet.adj_right_same_direction

        return first_lane_id, second_lane_id
