import matplotlib.pyplot as plt
from IPython import display
import numpy as np

from commonroad.visualization.draw_dispatch_cr import draw_object

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_writer import OverwriteExistingFile
from commonroad.scenario.scenario import Location
from commonroad.scenario.scenario import Tag
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.lanelet import LaneletType
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.intersection import Intersection
from commonroad.scenario.intersection import IntersectionIncomingElement


# from commonroad.scenario.lanelet import LineMarking

file_path = "/home/aaron/Downloads/ZAM_Tutorial-1_2_T-3.xml"  #
scenario, planning_problem_set = CommonRoadFileReader(file_path).open()
network = LaneletNetwork()


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

    def create_straight(self, width, length, num_vertices, network):
        eps = 0.1e-15
        length_div = length / num_vertices
        left_vertices = []
        center_vertices = []
        right_vertices = []
        for i in range(num_vertices + 1):
            left_vertices.append([length_div * i + eps, width / 2 + eps])
            center_vertices.append([length_div * i + eps, eps])
            right_vertices.append([length_div * i + eps, -(width / 2) + eps])

        left_vertices = np.array(left_vertices)
        center_vertices = np.array(center_vertices)
        right_vertices = np.array(right_vertices)

        idl = self.scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type={LaneletType.URBAN})
        self.latestid = idl
        network.add_lanelet(lanelet=lanelet)
        return lanelet

    def create_curve(self, width, radius, angle, num_vertices, network):
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

        if angle < 0:
            left_vertices = np.array(right_vert)
            center_vertices = np.array(center_vert)
            right_vertices = np.array(left_vert)

        idl = self.scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                          center_vertices=center_vertices, lanelet_type={LaneletType.URBAN})
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
        if sign >= 0:
            angle = 2 * np.pi - angle
        self.angle = angle

        return self.angle

    def fit_to_predecessor(self, predecessor, successor):
        if predecessor:
            #last_element = len(predecessor.center_vertices) - 1
            factor = (np.linalg.norm(successor.left_vertices[0, :] - successor.right_vertices[0, :])
                      / np.linalg.norm((predecessor.left_vertices[-1, :] - predecessor.right_vertices[-1, :])))

            successor._left_vertices = successor.left_vertices / factor
            successor._right_vertices = successor.right_vertices / factor
            successor._center_vertices = successor.center_vertices / factor

            ang = mapcreator.calc_angle_between(self, predecessor, successor)
            successor.translate_rotate(np.array([0, 0]), ang)
            trans = predecessor.center_vertices[-1] - successor.center_vertices[0]
            successor.translate_rotate(trans, 0)


            # Relation
            mapcreator.set_predecessor_successor_relation(self, predecessor, successor)

        return successor

    def adjacent_lanelet_left(self, adjacent_lanelet, network, same_direction=True):
        if adjacent_lanelet.adj_left is None:
            # Translation
            left_vertices = adjacent_lanelet.left_vertices - (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            center_vertices = adjacent_lanelet.center_vertices - (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            right_vertices = adjacent_lanelet.left_vertices

            idl = self.scenario.generate_object_id()
            self.latestid = idl
            lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                              center_vertices=center_vertices, lanelet_type={LaneletType.URBAN},
                              adjacent_right=adjacent_lanelet.lanelet_id, adjacent_right_same_direction=True)

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

    def adjacent_lanelet_right(self, adjacent_lanelet, network, same_direction=True):
        if adjacent_lanelet.adj_right is None:
            # Translation
            left_vertices = adjacent_lanelet.right_vertices
            center_vertices = adjacent_lanelet.center_vertices + (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
            right_vertices = adjacent_lanelet.right_vertices + (
                    adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)

            idl = self.scenario.generate_object_id()
            self.latestid = idl
            lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=idl,
                              center_vertices=center_vertices, lanelet_type={LaneletType.URBAN},
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

    # x crossing
    def x_crossing(self, width, diameter_crossing, network):
        rad = (diameter_crossing + width) / 2
        lanelet_1 = self.create_straight(width, diameter_crossing, 10, network)
        lanelet_2 = self.adjacent_lanelet_left(lanelet_1, network, False)

        lanelet_3 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_1, lanelet_3)
        lanelet_4 = self.adjacent_lanelet_left(lanelet_3, network, False)

        lanelet_5 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_1, lanelet_5)
        lanelet_6 = self.adjacent_lanelet_left(lanelet_5, network, False)

        lanelet_7 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_5, lanelet_7)
        lanelet_8 = self.adjacent_lanelet_left(lanelet_7, network, False)

        lanelet_9 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_3, lanelet_9)
        lanelet_10 = self.adjacent_lanelet_left(lanelet_9, network, False)

        lanelet_11 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_8, lanelet_11)
        lanelet_12 = self.adjacent_lanelet_left(lanelet_11, network, False)

        lanelet_13 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_8, lanelet_13)
        lanelet_14 = self.adjacent_lanelet_left(lanelet_13, network, False)

        lanelet_15 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_13, lanelet_15)
        lanelet_16 = self.adjacent_lanelet_left(lanelet_15, network, False)

        lanelet_17 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_10, lanelet_17)
        lanelet_18 = self.adjacent_lanelet_left(lanelet_17, network, False)

        lanelet_19 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_16, lanelet_19)
        lanelet_20 = self.adjacent_lanelet_left(lanelet_19, network, False)

        # missing dependencies
        self.set_predecessor_successor_relation(lanelet_1, lanelet_20)
        self.set_predecessor_successor_relation(lanelet_19, lanelet_2)
        self.set_predecessor_successor_relation(lanelet_11, lanelet_9)
        self.set_predecessor_successor_relation(lanelet_10, lanelet_12)
        self.set_predecessor_successor_relation(lanelet_17, lanelet_15)
        self.set_predecessor_successor_relation(lanelet_16, lanelet_18)

        incomings = [lanelet_1.lanelet_id, lanelet_8.lanelet_id, lanelet_10.lanelet_id, lanelet_16.lanelet_id]
        map_incoming = []
        for i in incomings:
            map_incoming.append(IntersectionIncomingElement(i, incomings, incomings, incomings, incomings))

        intersection_id = self.scenario.generate_object_id()

        crossings = {lanelet_3.lanelet_id, lanelet_4.lanelet_id, lanelet_5.lanelet_id,
                     lanelet_6.lanelet_id, lanelet_11.lanelet_id, lanelet_12.lanelet_id,
                     lanelet_13.lanelet_id, lanelet_14.lanelet_id, lanelet_17.lanelet_id,
                     lanelet_18.lanelet_id, lanelet_19.lanelet_id, lanelet_20.lanelet_id}

        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming, crossings=crossings)

        return intersection

    # t crossing
    def t_crossing(self, width, diameter_crossing, network):
        rad = (diameter_crossing + width) / 2
        lanelet_1 = self.create_straight(width, diameter_crossing, 10, network)
        lanelet_2 = self.adjacent_lanelet_left(lanelet_1, network, False)

        lanelet_3 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_1, lanelet_3)
        lanelet_4 = self.adjacent_lanelet_left(lanelet_3, network, False)

        lanelet_5 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_3, lanelet_5)
        lanelet_6 = self.adjacent_lanelet_left(lanelet_5, network, False)

        lanelet_7 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_6, lanelet_7)
        lanelet_8 = self.adjacent_lanelet_left(lanelet_7, network, False)

        lanelet_9 = self.create_straight(width, diameter_crossing, 10, network)
        self.fit_to_predecessor(lanelet_7, lanelet_9)
        lanelet_10 = self.adjacent_lanelet_left(lanelet_9, network, False)

        lanelet_11 = self.create_curve(width, rad, np.pi * 0.5, 20, network)
        self.fit_to_predecessor(lanelet_10, lanelet_11)
        lanelet_12 = self.adjacent_lanelet_left(lanelet_11, network, False)

        # missing dependencies
        self.set_predecessor_successor_relation(lanelet_1, lanelet_12)
        self.set_predecessor_successor_relation(lanelet_11, lanelet_2)

        incomings = {lanelet_1.lanelet_id, lanelet_6.lanelet_id, lanelet_10.lanelet_id}
        map_incoming = []
        for i in incomings:
            map_incoming.append(IntersectionIncomingElement(i, incomings,
                                                            successors_right={lanelet_1.lanelet_id, lanelet_6.lanelet_id},
                                                            successors_straight={lanelet_6.lanelet_id,
                                                                                 lanelet_10.lanelet_id},
                                                            successors_left={lanelet_1.lanelet_id, lanelet_10.lanelet_id}))

        intersection_id = self.scenario.generate_object_id()

        crossings = {lanelet_5.lanelet_id, lanelet_6.lanelet_id, lanelet_7.lanelet_id, lanelet_8.lanelet_id,
                     lanelet_11.lanelet_id, lanelet_12.lanelet_id}

        intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming, crossings=crossings)

        return intersection

"""lanelet_1 = create_straight(20,100,10,network)
    #rotate_lanelet(np.pi*0.9,lanelet_1)
    lanelet_2 = create_curve(20,90,np.pi*-0.5,20,network)
    fit_to_predecessor(lanelet_1,lanelet_2)
    lanelet_3 = create_curve(20,90,np.pi*-0.5,20,network)
    fit_to_predecessor(lanelet_2,lanelet_3)
    lanelet_4 = create_straight(20,100,10,network)
    rotate_lanelet(np.pi,lanelet_4)
    fit_to_predecessor(lanelet_3,lanelet_4)
    lanelet_4_1 = adjacent_lanelet_right(lanelet_2,network, False)
    lanelet_5 = create_curve(20,130,-np.pi*0.6,20,network)
    fit_to_predecessor(lanelet_4,lanelet_5)
    lanelet_6 = create_straight(20,150,10,network)
    fit_to_predecessor(lanelet_1,lanelet_6)
    lanelet_7 = create_curve(20,150,-np.pi*0.6,20,network)
    fit_to_predecessor(lanelet_1,lanelet_7)
    lanelet_8 = adjacent_lanelet_left(lanelet_5,network, False)
    lanelet_9 = adjacent_lanelet_right(lanelet_5,network, False)
    lanelet_10 = adjacent_lanelet_right(lanelet_6,network, False)"""

"""#intersection_1 = t_crossing(3, 50, network)



scenario.add_objects([network])

author = 'Max Mustermann'
affiliation = 'Technical University of Munich, Germany'
source = ''
tags = {Tag.CRITICAL, Tag.INTERSTATE}

# write new scenario
fw = CommonRoadFileWriter(scenario, planning_problem_set, author, affiliation, source, tags)

filename = "ZAM_Tutorial-1_2_T-3.xml"
fw.write_to_file(filename, OverwriteExistingFile.ALWAYS)

# plot the scenario for each time step
for i in range(0, 1):
    # uncomment to clear previous graph
    display.clear_output(wait=True)
    plt.figure(figsize=(25, 10))
    draw_object(scenario, draw_params={'time_begin': i})
    draw_object(planning_problem_set)
    plt.gca().set_aspect('equal')
    plt.show()"""
