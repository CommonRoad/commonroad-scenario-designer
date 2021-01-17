import matplotlib.pyplot as plt
from IPython import display
import numpy as np
from scipy.interpolate import interp1d

from commonroad.visualization.draw_dispatch_cr import draw_object

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_writer import OverwriteExistingFile
from commonroad.scenario.scenario import Location, Tag
from commonroad.scenario.lanelet import LaneletType, RoadUser, LaneletNetwork, Lanelet, LineMarking
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.intersection import IntersectionIncomingElement


# from commonroad.scenario.lanelet import LineMarking


class mapcreator:
    """ functionality to create lanelets and Obstacles for a Scenario """
    def __init__(self):
        self.predecessor = None
        self.successor = None
        self.width = None
        self.length = None
        self.num_vertices = None
        self.network = None
        self.radius = None
        self.angle = None
        self.lanelet = None
        self.adjacent_lanelet = None
        self.same_direction = None
        self.diameter_crossing = None

    #Set Predecessor Successor relation
    def set_predecessor_successor_relation(self, predecessor, successor):
        a = successor.predecessor
        a.append(predecessor.lanelet_id)
        a = set(a)
        successor._predecessor = list(a)
        b = predecessor.successor
        b.append(successor.lanelet_id)
        b = set(b)
        predecessor._successor = list(b)

    def create_straight(self, width, length, num_vertices, network, scenario, pred, lanelettype=set(), roaduser="vehicle",
                        linemarkingleft="no_marking", linemarkingright="no_marking", backwards=False):
        eps = 0.1e-15
        length_div = length / (num_vertices-1)
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

        idl = scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type=lanelettype,
                          user_one_way={RoadUser(roaduser)}, line_marking_right_vertices=LineMarking(linemarkingright),
                          line_marking_left_vertices=LineMarking(linemarkingleft))
        if backwards:
            lanelet.translate_rotate(-lanelet.center_vertices[0], np.pi)

        if pred:
            if self.latestid != None:
                mapcreator.fit_to_predecessor(self, network.find_lanelet_by_id(self.latestid),lanelet)
        self.latestid = idl
        network.add_lanelet(lanelet=lanelet)
        return lanelet

    def edit_straight(self, id, width, length, num_vertices, network, scenario, pred, lanelettype={LaneletType("urban")}, roaduser="vehicle",
                        linemarkingleft="no_marking", linemarkingright="no_marking", backwards=False):
        eps = 0.1e-15
        length_div = length / (num_vertices-1)
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
        """lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type=lanelettype,
                          user_one_way={RoadUser(roaduser)}, line_marking_right_vertices=LineMarking(linemarkingright),
                          line_marking_left_vertices=LineMarking(linemarkingleft))"""
        if backwards:
            lanelet.translate_rotate(-lanelet.center_vertices[0], np.pi)

        if pred:
            if self.latestid != None:
                mapcreator.fit_to_predecessor(self, network.find_lanelet_by_id(self.latestid),lanelet)
        self.latestid = id
        #network.add_lanelet(lanelet=lanelet)
        return lanelet


    def create_curve(self, width, radius, angle, num_vertices, network, scenario, pred, lanelettype="urban", roaduser="vehicle",
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

        angle_start = -np.pi/2
        if angle < 0:
            left_vertices = np.array(right_vert)
            center_vertices = np.array(center_vert)
            right_vertices = np.array(left_vert)
            angle_start = -angle_start

        idl = scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type={LaneletType(lanelettype), LaneletType("busLane")},
                          user_one_way={RoadUser(roaduser)}, line_marking_right_vertices=LineMarking(linemarkingright),
                          line_marking_left_vertices=LineMarking(linemarkingleft))
        lanelet.translate_rotate(np.array([0,0]),angle_start)
        lanelet.translate_rotate(-lanelet.center_vertices[0],0)

        if pred:
            if self.latestid != None:
                mapcreator.fit_to_predecessor(self, network.find_lanelet_by_id(self.latestid), lanelet)

        self.latestid = idl
        network.add_lanelet(lanelet=lanelet)
        return lanelet

    def rotate_lanelet(self, angle, lanelet):
        trans_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        transform_left = []
        transform_center = []
        transform_right = []
        num_vertices = len(lanelet.left_vertices)

        for i in range(num_vertices):
            transform_left.append(np.dot(trans_matrix, lanelet.left_vertices[i]))
            transform_center.append(np.dot(trans_matrix, lanelet.center_vertices[i]))
            transform_right.append(np.dot(trans_matrix, lanelet.right_vertices[i]))

        lanelet._left_vertices = np.array(transform_left)
        lanelet._center_vertices = np.array(transform_center)
        lanelet._right_vertices = np.array(transform_right)

    def calc_angle_between(self, predecessor, lanelet):
        last_element = len(predecessor.left_vertices) - 1
        line_predecessor = predecessor.left_vertices[last_element] - predecessor.right_vertices[last_element]
        line_lanelet = lanelet.left_vertices[0] - lanelet.right_vertices[0]
        norm_predecessor = np.linalg.norm(line_predecessor)
        norm_lanelet = np.linalg.norm(line_lanelet)
        dot_prod = np.dot(line_predecessor, line_lanelet)
        sign = line_lanelet[1] * line_predecessor[0] - line_lanelet[0] * line_predecessor[1]
        angle = np.arccos(dot_prod / (norm_predecessor * norm_lanelet))
        if sign > 0:
            angle = 2 * np.pi - angle

        return angle

    def fit_to_predecessor(self, predecessor, successor):
        if predecessor:
            #last_element = len(predecessor.center_vertices) - 1
            factor = (np.linalg.norm(successor.left_vertices[0, :] - successor.right_vertices[0, :])
                      / np.linalg.norm((predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])))

            successor._left_vertices = successor.left_vertices / factor
            successor._right_vertices = successor.right_vertices / factor
            successor._center_vertices = successor.center_vertices / factor

            ang = mapcreator.calc_angle_between(mapcreator, predecessor, successor)
            successor.translate_rotate(np.array([0, 0]), ang)
            trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
            successor.translate_rotate(trans, 0)

            # Relation
            mapcreator.set_predecessor_successor_relation(self, predecessor, successor)

        return successor


    def fit_intersection_to_predecessor(self, predecessor, successor, intersection, network, scenario):
        if predecessor and successor and intersection:
            lanelet_ids = []
            lanelet_ids = lanelet_ids + list(intersection.crossings)
            for id in intersection.incomings:
                lanelet = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=id.incoming_id)
                if lanelet:
                    lanelet_ids.append(id.incoming_id)
                    if lanelet.adj_left:
                        lanelet_ids.append(lanelet.adj_left)
                    if lanelet.adj_right:
                        lanelet_ids.append(lanelet.adj_right)
            lanelet_ids = set(lanelet_ids)
            lanelet_ids = list(lanelet_ids)

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

    def adjacent_lanelet_left(self, adjacent_lanelet, network, scenario, same_direction=True):
        if adjacent_lanelet.adj_left is None:
            # Translation
            left_vertices = adjacent_lanelet.left_vertices - (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            center_vertices = adjacent_lanelet.center_vertices - (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            right_vertices = adjacent_lanelet.left_vertices

            idl = scenario.generate_object_id()
            self.latestid = idl
            lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                              center_vertices=center_vertices, lanelet_type=adjacent_lanelet._lanelet_type,
                              user_one_way=adjacent_lanelet._user_one_way, line_marking_right_vertices=adjacent_lanelet._line_marking_right_vertices,
                              line_marking_left_vertices=adjacent_lanelet._line_marking_left_vertices,
                              adjacent_left=adjacent_lanelet.lanelet_id, adjacent_left_same_direction=True)



            # Relation
            adjacent_lanelet._adj_left = lanelet.lanelet_id
            adjacent_lanelet._adj_left_same_direction = True

            # Find Predecessors
            preds = adjacent_lanelet.predecessor
            succs = adjacent_lanelet.successor

            for i in preds:
                lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
                if lanelet_find.adj_left is not None:
                    lanelet_adj_left = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_left)
                    if lanelet_find.adj_left_same_direction is True:
                        mapcreator.set_predecessor_successor_relation(self, lanelet_adj_left, lanelet)

                    else:
                        mapcreator.set_predecessor_successor_relation(self, lanelet, lanelet_adj_left)

            for i in succs:
                lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
                if lanelet_find.adj_left is not None:
                    lanelet_adj_left = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_left)
                    if lanelet_find.adj_left_same_direction is True:
                        mapcreator.set_predecessor_successor_relation(self, lanelet, lanelet_adj_left)

                    else:
                        mapcreator.set_predecessor_successor_relation(self, lanelet_adj_left, lanelet)

            if same_direction is False:
                lanelet._left_vertices = np.flip(right_vertices, 0)
                lanelet._center_vertices = np.flip(center_vertices, 0)
                lanelet._right_vertices = np.flip(left_vertices, 0)
                lanelet._adjacent_right_same_direction = None
                lanelet._adj_right = None
                lanelet._adj_left = adjacent_lanelet.lanelet_id
                lanelet._adj_left_same_direction = False
                adjacent_lanelet._adj_left_same_direction = False

            network.add_lanelet(lanelet=lanelet)
            return lanelet
        else:
            print("Adjacent lanelet already exists")

    def adjacent_lanelet_right(self, adjacent_lanelet, network, scenario, same_direction=True):
        if adjacent_lanelet.adj_right is None:
            # Translation
            left_vertices = adjacent_lanelet.right_vertices
            center_vertices = adjacent_lanelet.center_vertices + (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            right_vertices = adjacent_lanelet.right_vertices + (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)

            idl = scenario.generate_object_id()
            self.latestid = idl
            lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                              center_vertices=center_vertices, lanelet_type=adjacent_lanelet._lanelet_type,
                              user_one_way=adjacent_lanelet._user_one_way, line_marking_right_vertices=adjacent_lanelet._line_marking_right_vertices,
                              line_marking_left_vertices=adjacent_lanelet._line_marking_left_vertices,
                              adjacent_left=adjacent_lanelet.lanelet_id, adjacent_left_same_direction=True)


            # Relation
            adjacent_lanelet._adj_right = lanelet.lanelet_id
            adjacent_lanelet._adj_right_same_direction = True

            # Find Predecessors
            preds = adjacent_lanelet.predecessor
            succs = adjacent_lanelet.successor

            for i in preds:
                lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
                if lanelet_find.adj_right is not None:
                    lanelet_adj_right = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_right)
                    if lanelet_find.adj_right_same_direction is True:
                        mapcreator.set_predecessor_successor_relation(self, lanelet_adj_right, lanelet)

                    else:
                        mapcreator.set_predecessor_successor_relation(self, lanelet, lanelet_adj_right)

            for i in succs:
                lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
                if lanelet_find.adj_right is not None:
                    lanelet_adj_right = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_right)
                    if lanelet_find.adj_right_same_direction is True:
                        mapcreator.set_predecessor_successor_relation(self, lanelet, lanelet_adj_right)

                    else:
                        mapcreator.set_predecessor_successor_relation(self, lanelet_adj_right, lanelet)

            if same_direction is False:
                lanelet._left_vertices = np.flip(right_vertices, 0)
                lanelet._center_vertices = np.flip(center_vertices, 0)
                lanelet._right_vertices = np.flip(left_vertices, 0)
                lanelet._adjacent_left_same_direction = None
                lanelet._adj_left = None
                lanelet._adj_right = adjacent_lanelet.lanelet_id
                lanelet._adj_right_same_direction = False
                adjacent_lanelet._adj_right_same_direction = False

            network.add_lanelet(lanelet=lanelet)
            return lanelet
        else:
            print("Adjacent lanelet already exists")

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
            mapcreator.set_predecessor_successor_relation(self, predecessor, connecting_lanelet)
            mapcreator.set_predecessor_successor_relation(self, connecting_lanelet, successor)
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
            norm_vec_pred = np.array([vec_width_pred[1],-vec_width_pred[0]])
            norm_vec_succ = np.array([vec_width_succ[1],-vec_width_succ[0]])
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
                                              [successor.center_vertices[0] -  con_vec_factor * norm_vec_succ /
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
            a = a + b       #Constructed matrix for calculation
            c = np.dot(a, interpolated_center)    #calculate tangent at point
            #Create normalvectors and normalize them
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
            mapcreator.set_predecessor_successor_relation(self, predecessor, connecting_lanelet)
            mapcreator.set_predecessor_successor_relation(self, connecting_lanelet, successor)
            return connecting_lanelet

    def remove_lanelet(self, lanelet, network, scenario):
        del network._lanelets[lanelet.lanelet_id]
        network.cleanup_lanelet_references()
        scenario._lanelet_network = network

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

        incomings = {lanelet_1.lanelet_id, lanelet_8.lanelet_id, lanelet_10.lanelet_id, lanelet_16.lanelet_id}
        map_incoming = []
        for i in incomings:
            map_incoming.append(IntersectionIncomingElement(i, incomings, incomings, incomings, incomings))

        intersection_id = scenario.generate_object_id()


        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming)
        scenario.add_objects([intersection])
        return intersection

    # t crossing
    def t_crossing(self, width, diameter_crossing, network, scenario):
        rad = (diameter_crossing + width) / 2
        lanelet_1 = self.create_straight(self, width, diameter_crossing, 10, network, scenario, None)
        lanelet_2 = self.adjacent_lanelet_left(self, lanelet_1, network, scenario, False)

        lanelet_3 = self.create_curve(self, width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(self, lanelet_1, lanelet_3)
        lanelet_4 = self.adjacent_lanelet_left(self, lanelet_3, network, scenario, False)

        lanelet_5 = self.create_straight(self, width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(self, lanelet_3, lanelet_5)
        lanelet_6 = self.adjacent_lanelet_left(self, lanelet_5, network, scenario, False)

        lanelet_7 = self.create_straight(self, width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(self, lanelet_6, lanelet_7)
        lanelet_8 = self.adjacent_lanelet_left(self, lanelet_7, network, scenario, False)

        lanelet_9 = self.create_straight(self, width, diameter_crossing, 10, network, scenario, None)
        self.fit_to_predecessor(self, lanelet_7, lanelet_9)
        lanelet_10 = self.adjacent_lanelet_left(self, lanelet_9, network, scenario, False)

        lanelet_11 = self.create_curve(self, width, rad, np.pi * 0.5, 20, network, scenario, None)
        self.fit_to_predecessor(self, lanelet_10, lanelet_11)
        lanelet_12 = self.adjacent_lanelet_left(self, lanelet_11, network, scenario, False)

        # missing dependencies
        self.set_predecessor_successor_relation(self, lanelet_1, lanelet_12)
        self.set_predecessor_successor_relation(self, lanelet_11, lanelet_2)

        incomings = {lanelet_1.lanelet_id, lanelet_6.lanelet_id, lanelet_10.lanelet_id}
        map_incoming = []
        for i in incomings:
            map_incoming.append(IntersectionIncomingElement(i, incomings,
                                                            successors_right={lanelet_1.lanelet_id,
                                                                              lanelet_6.lanelet_id},
                                                            successors_straight={lanelet_6.lanelet_id,
                                                                                 lanelet_10.lanelet_id},
                                                            successors_left={lanelet_1.lanelet_id,
                                                                             lanelet_10.lanelet_id}))

        intersection_id = scenario.generate_object_id()

        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming, crossings=crossings)

        return intersection
