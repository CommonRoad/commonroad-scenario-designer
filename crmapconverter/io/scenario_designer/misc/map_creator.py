from typing import Set, List, Union
import numpy as np
from scipy.interpolate import interp1d

from commonroad.scenario.intersection import Intersection
from commonroad.scenario.intersection import IntersectionIncomingElement
from commonroad.scenario.lanelet import RoadUser, LaneletNetwork, Lanelet, LineMarking, LaneletType
from commonroad.scenario.scenario import Scenario


class MapCreator:
    """
    Collection of functions to work with lanelets
    """

    @staticmethod
    def create_straight(width: float, length: float, num_vertices: int, lanelet_id: int,
                        lanelet_types: Set[LaneletType], predecessor: List[int], successor: List[int],
                        adjacent_left: Union[int, None], adjacent_right: Union[int, None],
                        adjacent_left_same_direction: bool, adjacent_right_same_direction: bool,
                        road_user_one_way: Set[RoadUser], road_user_bidirectional: Set[RoadUser],
                        line_marking_left: LineMarking = LineMarking.UNKNOWN,
                        line_marking_right: LineMarking = LineMarking.UNKNOWN, backwards: bool = False):
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
        @param backwards: Boolean indicating whether lanelet should be rotated by 180°.
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

        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, predecessor=predecessor,
                          successor=successor, adjacent_left=adjacent_left, adjacent_right=adjacent_right,
                          adjacent_left_same_direction=adjacent_left_same_direction,
                          adjacent_right_same_direction=adjacent_right_same_direction,
                          lanelet_id=lanelet_id, center_vertices=center_vertices, lanelet_type=lanelet_types,
                          user_one_way=road_user_one_way, user_bidirectional=road_user_bidirectional,
                          line_marking_right_vertices=line_marking_left,
                          line_marking_left_vertices=line_marking_right)
        if backwards:
            lanelet.translate_rotate(-lanelet.center_vertices[0], np.pi)

        return lanelet

    @staticmethod
    def create_curve(width: float, radius: float, angle: float, num_vertices: int, lanelet_id: int,
                     lanelet_types: Set[LaneletType], predecessor: List[int], successor: List[int],
                     adjacent_left: Union[int, None], adjacent_right: Union[int, None],
                     adjacent_left_same_direction: bool, adjacent_right_same_direction: bool,
                     road_user_one_way: Set[RoadUser], road_user_bidirectional: Set[RoadUser],
                     line_marking_left: LineMarking = LineMarking.UNKNOWN,
                     line_marking_right: LineMarking = LineMarking.UNKNOWN):
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
        @return: Newly created lanelet.
        """
        angle_div = angle / (num_vertices - 1)
        radius_left = radius - (width / 2)
        radius_right = radius + (width / 2)
        left_vert = []
        center_vert = []
        right_vert = []
        for i in range(num_vertices):
            left_vert.append([np.cos(i * angle_div) * radius_left, np.sin(i * angle_div) * radius_left])
            center_vert.append([np.cos(i * angle_div) * radius, np.sin(i * angle_div) * radius])
            right_vert.append([np.cos(i * angle_div) * radius_right, np.sin(i * angle_div) * radius_right])

        left_vertices = np.array(left_vert)
        center_vertices = np.array(center_vert)
        right_vertices = np.array(right_vert)

        angle_start = -np.pi / 2
        if angle < 0:
            left_vertices = np.array(right_vert)
            center_vertices = np.array(center_vert)
            right_vertices = np.array(left_vert)
            angle_start = -angle_start

        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=lanelet_id,
                          center_vertices=center_vertices, predecessor=predecessor, successor=successor,
                          adjacent_left=adjacent_left, adjacent_right=adjacent_right,
                          adjacent_left_same_direction=adjacent_left_same_direction,
                          adjacent_right_same_direction=adjacent_right_same_direction, lanelet_type=lanelet_types,
                          user_one_way=road_user_one_way, user_bidirectional=road_user_bidirectional,
                          line_marking_right_vertices=LineMarking(line_marking_right),
                          line_marking_left_vertices=LineMarking(line_marking_left))
        lanelet.translate_rotate(np.array([0, 0]), angle_start)
        lanelet.translate_rotate(-lanelet.center_vertices[0], 0)

        return lanelet

    @staticmethod
    def create_adjacent_lanelet(create_adj_left: bool, base_lanelet: Lanelet, scenario: Scenario,
                                same_direction: bool, width: float, lanelet_types: Set[LaneletType],
                                predecessor: List[int], successor: List[int], road_user_one_way: Set[RoadUser],
                                road_user_bidirectional: Set[RoadUser],
                                line_marking_left: LineMarking = LineMarking.UNKNOWN,
                                line_marking_right: LineMarking = LineMarking.UNKNOWN):
        """
        Creates adjacent left or adjacent right lanelet for given lanelet.

        @param create_adj_left: Boolean indicating whether adjacent left or right should be created.
        @param base_lanelet: Lanelet for which adjacent lanelet should be created.
        @param scenario: CommonRoad scenario.
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
        @return: Newly created lanelet.
        """
        lanelet_id = scenario.generate_object_id()
        if base_lanelet.adj_left is None and create_adj_left:
            diff_left_vert_right_vert = base_lanelet.right_vertices - base_lanelet.left_vertices
            norm_left = np.array([np.linalg.norm(diff_left_vert_right_vert, axis=1)])
            left_vertices = base_lanelet.left_vertices - (diff_left_vert_right_vert / norm_left.T) * width
            center_vertices = base_lanelet.left_vertices - (diff_left_vert_right_vert / norm_left.T) * width / 2
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
            center_vertices = base_lanelet.right_vertices + (
                    diff_left_vert_right_vert / norm_left.T) * width / 2
            right_vertices = base_lanelet.right_vertices + (diff_left_vert_right_vert / norm_left.T) * width
            adjacent_right = None
            adjacent_right_same_direction = None
            adjacent_left = base_lanelet.lanelet_id
            adjacent_left_same_direction = same_direction
            base_lanelet.adj_right = lanelet_id
            base_lanelet.adj_right_same_direction = same_direction
        else:
            print("Adjacent lanelet already exists.")
            return

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

        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=lanelet_id,
                          center_vertices=center_vertices, predecessor=predecessor, successor=successor,
                          adjacent_right=adjacent_right, adjacent_left=adjacent_left, lanelet_type=lanelet_types,
                          adjacent_right_same_direction=adjacent_right_same_direction,
                          adjacent_left_same_direction=adjacent_left_same_direction,
                          user_one_way=road_user_one_way, user_bidirectional=road_user_bidirectional,
                          line_marking_right_vertices=LineMarking(line_marking_right),
                          line_marking_left_vertices=LineMarking(line_marking_left))

        return lanelet

    @staticmethod
    def fit_to_predecessor(predecessor: Lanelet, lanelet: Lanelet):
        """
        Function to translate a lanelet so that it fits to a given predecessor lanelet.

        @param predecessor: Lanelet to which given lanelet should be attached.
        @param lanelet: Lanelet which should be attached to the predecessor lanelet.
        """
        if predecessor:
            factor = (np.linalg.norm(lanelet.left_vertices[0, :] - lanelet.right_vertices[0, :])
                      / np.linalg.norm((predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])))

            lanelet._left_vertices = lanelet.left_vertices / factor
            lanelet._right_vertices = lanelet.right_vertices / factor
            lanelet._center_vertices = lanelet.center_vertices / factor

            ang = MapCreator.calc_angle_between(predecessor, lanelet)
            lanelet.translate_rotate(np.array([0, 0]), ang)
            trans = predecessor.center_vertices[-1] - lanelet.center_vertices[0]
            lanelet.translate_rotate(trans, 0)

            MapCreator.set_predecessor_successor_relation(predecessor, lanelet)

    @staticmethod
    def fit_to_successor(successor: Lanelet, lanelet: Lanelet):
        """
        Function to translate a lanelet so that it fits to a given successor lanelet.

        @param successor: Lanelet to which given lanelet should be attached.
        @param lanelet: Lanelet which should be attached to the successor lanelet.
        """
        if successor:
            factor = (np.linalg.norm(lanelet.left_vertices[-1, :] - lanelet.right_vertices[-1, :])
                      / np.linalg.norm((successor.left_vertices[0, :] - successor.right_vertices[0, :])))

            lanelet._left_vertices = lanelet.left_vertices / factor
            lanelet._right_vertices = lanelet.right_vertices / factor
            lanelet._center_vertices = lanelet.center_vertices / factor

            ang = MapCreator.calc_angle_between(lanelet, successor)
            lanelet.translate_rotate(np.array([0, 0]), ang)
            trans = lanelet.center_vertices[0] - successor.center_vertices[-1]
            lanelet.translate_rotate(trans, 0)

            MapCreator.set_predecessor_successor_relation(lanelet, successor)

    @staticmethod
    def calc_angle_between(predecessor: Lanelet, lanelet: Lanelet):
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
        @param successor:  Successor lanelet.
        """
        successor.add_predecessor(predecessor.lanelet_id)
        predecessor.add_successor(successor.lanelet_id)

    def edit_straight(self, id, width, length, num_vertices, network, scenario, pred, lanelettype=set(),
                      roaduser_oneway=set(), roaduser_bidirectional=set(), linemarkingleft="no_marking",
                      linemarkingright="no_marking", backwards=False):
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

        lanelet = network.find_lanelet_by_id(id)
        lanelet._left_vertices = left_vertices
        lanelet._right_vertices = right_vertices
        lanelet._center_vertices = center_vertices
        lanelet._user_one_way = roaduser_oneway
        lanelet._user_bidirectional = roaduser_bidirectional
        lanelet._lanelet_type = lanelettype
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type=lanelettype,
                          user_one_way={RoadUser(roaduser)}, line_marking_right_vertices=LineMarking(linemarkingright),
                          line_marking_left_vertices=LineMarking(linemarkingleft))
        if backwards:
            lanelet.translate_rotate(-lanelet.center_vertices[0], np.pi)

        self.latestid = id
        # network.add_lanelet(lanelet=lanelet)
        return lanelet

    def edit_curve(self, id, width, radius, angle, num_vertices, network, scenario, pred, lanelettype=set(),
                   roaduser_oneway="vehicle",
                   linemarkingleft="no_marking", linemarkingright="no_marking"):
        angle_div = angle / (num_vertices - 1)
        radius_left = radius - (width / 2)
        radius_right = radius + (width / 2)
        left_vert = []
        center_vert = []
        right_vert = []
        for i in range(num_vertices):
            left_vert.append([np.cos(i * angle_div) * radius_left, np.sin(i * angle_div) * radius_left])
            center_vert.append([np.cos(i * angle_div) * radius, np.sin(i * angle_div) * radius])
            right_vert.append([np.cos(i * angle_div) * radius_right, np.sin(i * angle_div) * radius_right])

        left_vertices = np.array(left_vert)
        center_vertices = np.array(center_vert)
        right_vertices = np.array(right_vert)

        angle_start = -np.pi / 2
        if angle < 0:
            left_vertices = np.array(right_vert)
            center_vertices = np.array(center_vert)
            right_vertices = np.array(left_vert)
            angle_start = -angle_start

        lanelet = network.find_lanelet_by_id(id)
        lanelet._left_vertices = left_vertices
        lanelet._right_vertices = right_vertices
        lanelet._center_vertices = center_vertices
        lanelet._user_one_way = roaduser_oneway

        lanelet.translate_rotate(np.array([0, 0]), angle_start)
        lanelet.translate_rotate(-lanelet.center_vertices[0], 0)

        return lanelet

    def calc_radius(self, lanelet):
        line_predecessor = lanelet.left_vertices[0] - lanelet.right_vertices[0]
        line_lanelet = lanelet.left_vertices[-1] - lanelet.right_vertices[-1]
        b = (lanelet.center_vertices[0, 1] * line_predecessor[0] + line_predecessor[1] * lanelet.center_vertices[
            -1, 0] - lanelet.center_vertices[0, 0] * line_predecessor[1] - lanelet.center_vertices[-1, 1] *
             line_predecessor[0]) / (line_lanelet[1] * line_predecessor[0] - line_predecessor[1] * line_lanelet[0])
        x = lanelet.center_vertices[-1] + b * line_lanelet
        rad = np.linalg.norm(x - lanelet.center_vertices[0])
        rad = round(rad, 0)
        return rad

    def calc_angle_between2(self, lanelet):
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

    def fit_intersection_to_predecessor(self, predecessor, successor, intersection, network, scenario):
        if predecessor and successor and intersection:
            lanelet_ids = []
            x = []
            for i in intersection.incomings:
                if i._successors_left != None:
                    left = list(i._successors_left)
                else:
                    left = []

                if i._successors_right != None:
                    right = list(i._successors_right)
                else:
                    right = []

                if i._successors_straight != None:
                    straight = list(i._successors_straight)
                else:
                    straight = []

                if i._incoming_lanelets != None:
                    inc = list(i._incoming_lanelets)
                else:
                    inc = []
                x = x + left + right + straight + inc

            for id in x:
                lanelet = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=id)
                if lanelet:
                    lanelet_ids.append(id)
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

            factor = (np.linalg.norm(successor.left_vertices[0, :] - successor.right_vertices[0, :])
                      / np.linalg.norm((predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])))

            ang = self.calc_angle_between(predecessor, successor)
            successor.translate_rotate(np.array([0, 0]), ang)
            successor._left_vertices = successor.left_vertices / factor
            successor._right_vertices = successor.right_vertices / factor
            successor._center_vertices = successor.center_vertices / factor
            trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
            for id in lanelet_ids:
                lanelet = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=id)
                if lanelet != successor:
                    lanelet._left_vertices = lanelet.left_vertices / factor
                    lanelet._right_vertices = lanelet.right_vertices / factor
                    lanelet._center_vertices = lanelet.center_vertices / factor
                    lanelet.translate_rotate(np.array([0, 0]), ang)
                lanelet.translate_rotate(trans, 0)

            # Relation
            successor._predecessor = []
            self.set_predecessor_successor_relation(predecessor, successor)


    def connect_lanelets(self, predecessor, successor, network, scenario):
        if predecessor and successor:
            left_vertices = np.concatenate(([predecessor.left_vertices[-1]], [successor.left_vertices[0]]))
            right_vertices = np.concatenate(([predecessor.right_vertices[-1]], [successor.right_vertices[0]]))
            center_vertices = np.concatenate(([predecessor.center_vertices[-1]], [successor.center_vertices[0]]))

            idl = scenario.generate_object_id()
            self.latestid = idl
            connecting_lanelet = Lanelet(left_vertices, center_vertices, right_vertices, idl,
                                         predecessor=[predecessor.lanelet_id], successor=[successor.lanelet_id])
            network.add_lanelet(lanelet=connecting_lanelet)
            MapCreator.set_predecessor_successor_relation(self, predecessor, connecting_lanelet)
            MapCreator.set_predecessor_successor_relation(self, connecting_lanelet, successor)
            return connecting_lanelet

    def connect_lanelets4(self, predecessor, successor, network, scenario):
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
            print(norm_vec_pred)
            print(norm_vec_succ)
            con_vec_factor = (length_con_vec) * 0.5

            center_vertices = np.concatenate(([predecessor.center_vertices[-1]],
                                              [predecessor.center_vertices[-1] + norm_vec_pred],
                                              [predecessor.center_vertices[-1] + 2 * norm_vec_pred + con_vec_factor *
                                               connecting_vec], [successor.center_vertices[0] - 2 * norm_vec_succ -
                                                                 (con_vec_factor * connecting_vec)],
                                              [successor.center_vertices[0] - norm_vec_succ],
                                              [successor.center_vertices[0]]))

            center_vertices = np.concatenate(([predecessor.center_vertices[-1]],
                                              [predecessor.center_vertices[-1] + con_vec_factor * norm_vec_pred /
                                               width_pred + con_vec_factor * connecting_vec],
                                              [successor.center_vertices[0] - con_vec_factor * norm_vec_succ /
                                               width_succ - (con_vec_factor * connecting_vec)],
                                              [successor.center_vertices[0]]))

            middle_point = (predecessor.center_vertices[-1] + 0.5 * con_vec_factor * norm_vec_pred /
                            width_pred - 0.5 * con_vec_factor * norm_vec_succ / width_succ +
                            con_vec_factor * connecting_vec)
            center_vertices = np.concatenate(([predecessor.center_vertices[-1]],
                                              [predecessor.center_vertices[-1] + 0.000001 * norm_vec_pred / width_pred],
                                              [middle_point],
                                              [successor.center_vertices[0] - 0.000001 * norm_vec_succ / width_succ],
                                              [successor.center_vertices[0]]))
            print(center_vertices)

            # Linear length along the line:
            distance_center = np.cumsum(np.sqrt(np.sum(np.diff(center_vertices, axis=0) ** 2, axis=1)))
            distance_center = np.insert(distance_center, 0, 0) / distance_center[-1]

            # Linear distance between points
            diff_dist = np.sqrt(np.sum(np.diff(center_vertices, axis=0) ** 2, axis=1))
            dist_sum = np.sum(diff_dist)
            diff_dist = diff_dist / dist_sum

            # Interpolation for different methods:
            num_points = 20
            alpha = np.linspace(0, 1, num_points)

            interpolator_center = interp1d(distance_center, center_vertices, kind='cubic', axis=0)
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
            f = np.sum(np.abs(e) ** 2, axis=-1) ** (1. / 2)
            f = np.array([f])
            e = e / f.T

            distance2 = np.cumsum(np.sqrt(np.sum(np.diff(interpolated_center, axis=0) ** 2, axis=1)))
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

            idl = scenario.generate_object_id()
            self.latestid = idl
            connecting_lanelet = Lanelet(interpolated_left, interpolated_center, interpolated_right, idl,
                                         predecessor=[predecessor.lanelet_id], successor=[successor.lanelet_id])
            network.add_lanelet(lanelet=connecting_lanelet)
            MapCreator.set_predecessor_successor_relation(self, predecessor, connecting_lanelet)
            MapCreator.set_predecessor_successor_relation(self, connecting_lanelet, successor)
            return connecting_lanelet

    @staticmethod
    def remove_lanelet(lanelet_id: int, network: LaneletNetwork):
        """
        Removes a lanelet from a lanelet network of a CommonRoad scenario.

        @param lanelet_id: ID of lanelet which should be removed.
        @param network: Lanelet network from which the lanelet should be removed.
        """
        network.remove_lanelet(lanelet_id)

    # x crossing
    def x_crossing(self, width, diameter_crossing, network, scenario):
        rad = (diameter_crossing + width) / 2
        lanelet_1 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        lanelet_2 = self.adjacent_lanelet_left(lanelet_1, network, scenario, False)

        lanelet_3 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_1, lanelet_3)
        lanelet_4 = self.adjacent_lanelet_left(lanelet_3, network, scenario, False)

        lanelet_5 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_1, lanelet_5)
        lanelet_6 = self.adjacent_lanelet_left(lanelet_5, network, scenario, False)

        lanelet_7 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_5, lanelet_7)
        lanelet_8 = self.adjacent_lanelet_left(lanelet_7, network, scenario, False)

        lanelet_9 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_3, lanelet_9)
        lanelet_10 = self.adjacent_lanelet_left(lanelet_9, network, scenario, False)

        lanelet_11 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_8, lanelet_11)
        lanelet_12 = self.adjacent_lanelet_left(lanelet_11, network, scenario, False)

        lanelet_13 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_8, lanelet_13)
        lanelet_14 = self.adjacent_lanelet_left(lanelet_13, network, scenario, False)

        lanelet_15 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_13, lanelet_15)
        lanelet_16 = self.adjacent_lanelet_left(lanelet_15, network, scenario, False)

        lanelet_17 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_10, lanelet_17)
        lanelet_18 = self.adjacent_lanelet_left(lanelet_17, network, scenario, False)

        lanelet_19 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_16, lanelet_19)
        lanelet_20 = self.adjacent_lanelet_left(lanelet_19, network, scenario, False)

        # missing dependencies
        self.set_predecessor_successor_relation(lanelet_1, lanelet_20)
        self.set_predecessor_successor_relation(lanelet_19, lanelet_2)
        self.set_predecessor_successor_relation(lanelet_11, lanelet_9)
        self.set_predecessor_successor_relation(lanelet_10, lanelet_12)
        self.set_predecessor_successor_relation(lanelet_17, lanelet_15)
        self.set_predecessor_successor_relation(lanelet_16, lanelet_18)

        incomings = [lanelet_1.lanelet_id, lanelet_8.lanelet_id, lanelet_10.lanelet_id, lanelet_16.lanelet_id]
        successors_right = [lanelet_6.lanelet_id, lanelet_12.lanelet_id, lanelet_18.lanelet_id, lanelet_20.lanelet_id]
        successors_straight = [lanelet_3.lanelet_id, lanelet_4.lanelet_id, lanelet_13.lanelet_id, lanelet_14.lanelet_id]
        successors_left = [lanelet_5.lanelet_id, lanelet_11.lanelet_id, lanelet_17.lanelet_id, lanelet_19.lanelet_id]
        map_incoming = []
        n = 0
        for i in incomings:
            inc = incomings[n]
            inc = {inc}
            right = successors_right[n]
            right = {right}
            left = successors_left[n]
            left = {left}
            straight = successors_straight[n]
            straight = {straight}
            map_incoming.append(IntersectionIncomingElement(n, incoming_lanelets=inc, successors_right=right,
                                                            successors_straight=straight, successors_left=left))
            n = n + 1
        intersection_id = scenario.generate_object_id()

        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming)
        scenario.add_objects([intersection])
        return intersection

    # t crossing
    def t_crossing(self, width, diameter_crossing, network, scenario):
        rad = (diameter_crossing + width) / 2
        lanelet_1 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        lanelet_2 = self.adjacent_lanelet_left(lanelet_1, network, scenario, False)

        lanelet_3 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_1, lanelet_3)
        lanelet_4 = self.adjacent_lanelet_left(lanelet_3, network, scenario, False)

        lanelet_5 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_3, lanelet_5)
        lanelet_6 = self.adjacent_lanelet_left(lanelet_5, network, scenario, False)

        lanelet_7 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_6, lanelet_7)
        lanelet_8 = self.adjacent_lanelet_left(lanelet_7, network, scenario, False)

        lanelet_9 = self.create_straight(width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(lanelet_7, lanelet_9)
        lanelet_10 = self.adjacent_lanelet_left(lanelet_9, network, scenario, False)

        lanelet_11 = self.create_curve(width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(lanelet_10, lanelet_11)
        lanelet_12 = self.adjacent_lanelet_left(lanelet_11, network, scenario, False)

        # missing dependencies
        self.set_predecessor_successor_relation(lanelet_1, lanelet_12)
        self.set_predecessor_successor_relation(lanelet_11, lanelet_2)

        incomings = [lanelet_1.lanelet_id, lanelet_6.lanelet_id, lanelet_10.lanelet_id]
        map_incoming = []
        successors_right = [lanelet_12.lanelet_id, lanelet_4.lanelet_id]
        successors_straight = [lanelet_7.lanelet_id, lanelet_8.lanelet_id]
        successors_left = [lanelet_3.lanelet_id, lanelet_11.lanelet_id]
        map_incoming = []

        map_incoming.append(IntersectionIncomingElement(0, incoming_lanelets={lanelet_1.lanelet_id},
                                                        successors_right={lanelet_12.lanelet_id},
                                                        successors_straight={lanelet_7.lanelet_id},
                                                        successors_left={lanelet_3.lanelet_id}))
        map_incoming.append(IntersectionIncomingElement(1, incoming_lanelets={lanelet_6.lanelet_id},
                                                        successors_right={lanelet_4.lanelet_id},
                                                        successors_straight={lanelet_8.lanelet_id},
                                                        successors_left={lanelet_11.lanelet_id}))
        map_incoming.append(IntersectionIncomingElement(2, incoming_lanelets={lanelet_10.lanelet_id}))
        intersection_id = scenario.generate_object_id()

        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming)
        scenario.add_objects([intersection])

        return intersection
