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

#Set Predecessor relation
def set_predecessor_successor_relation(predecessor, successor):
    a = successor.predecessor
    a.append(predecessor.lanelet_id)
    a = set(a)
    successor._predecessor = list(a)
    b = predecessor.successor
    b.append(successor.lanelet_id)
    b = set(b)
    predecessor._successor = list(b)


def create_straight(width, length, num_vertices, network):
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

    id = scenario.generate_object_id()
    lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=id,
                      center_vertices=center_vertices, lanelet_type={LaneletType.URBAN})

    network.add_lanelet(lanelet=lanelet)
    return lanelet


def create_curve(width, radius, angle, num_vertices, network):
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

    id = scenario.generate_object_id()
    lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=id,
                      center_vertices=center_vertices, lanelet_type={LaneletType.URBAN})

    network.add_lanelet(lanelet=lanelet)
    return lanelet


def rotate_lanelet(angle, lanelet):
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


def calc_angle_between(predecessor, lanelet):
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

    return angle


def fit_to_predecessor(predecessor=None, lanelet=None):
    if predecessor:
        last_element = len(predecessor.center_vertices) - 1
        ang = calc_angle_between(predecessor, lanelet)
        lanelet.translate_rotate(np.array([0, 0]), ang)
        trans = predecessor.center_vertices[last_element] - lanelet.center_vertices[0]
        lanelet.translate_rotate(trans, 0)

        # Relation
        set_predecessor_successor_relation(predecessor, lanelet)

    return lanelet


def adjacent_lanelet_left(adjacent_lanelet, network, same_direction=True):
    if adjacent_lanelet.adj_left is None:
        # Translation
        left_vertices = adjacent_lanelet.left_vertices - (
                adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
        center_vertices = adjacent_lanelet.center_vertices - (
                adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
        right_vertices = adjacent_lanelet.left_vertices

        id = scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=id,
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
                    set_predecessor_successor_relation(lanelet_adj_left, lanelet)

                else:
                    set_predecessor_successor_relation(lanelet, lanelet_adj_left)

        for i in succs:
            lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
            if lanelet_find.adj_left is not None:
                lanelet_adj_left = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_left)
                if lanelet_find.adj_left_same_direction is True:
                    set_predecessor_successor_relation(lanelet, lanelet_adj_left)

                else:
                    set_predecessor_successor_relation(lanelet_adj_left, lanelet)

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


def adjacent_lanelet_right(adjacent_lanelet, network, same_direction=True):
    if adjacent_lanelet.adj_right is None:
        # Translation
        left_vertices = adjacent_lanelet.right_vertices
        center_vertices = adjacent_lanelet.center_vertices + (
                adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)
        right_vertices = adjacent_lanelet.right_vertices + (
                adjacent_lanelet.right_vertices - adjacent_lanelet.left_vertices)

        id = scenario.generate_object_id()
        lanelet = Lanelet(left_vertices=left_vertices, right_vertices=right_vertices, lanelet_id=id,
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
                    set_predecessor_successor_relation(lanelet_adj_right, lanelet)

                else:
                    set_predecessor_successor_relation(lanelet, lanelet_adj_right)

        for i in succs:
            lanelet_find = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=i)
            if lanelet_find.adj_right is not None:
                lanelet_adj_right = LaneletNetwork.find_lanelet_by_id(network, lanelet_id=lanelet_find.adj_right)
                if lanelet_find.adj_right_same_direction is True:
                    set_predecessor_successor_relation(lanelet, lanelet_adj_right)

                else:
                    set_predecessor_successor_relation(lanelet_adj_right, lanelet)

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


"""lanelet_1 = create_straight(20,100,10,network)
#rotate_lanelet(np.pi*0.9,lanelet_1)
lanelet_2 = create_curve(20,90,np.pi*-0.5,20,network)
fit_to_predecessor(lanelet_1,lanelet_2)
lanelet_3 = create_curve(20,90,np.pi*-0.5,20,network)
fit_to_predecessor(lanelet_2,lanelet_3)
lanelet_4 = create_straight(20,100,10,network)
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


# x crossing
def x_crossing(width, diameter_crossing, network):
    rad = (diameter_crossing + width) / 2
    lanelet_1 = create_straight(width, diameter_crossing, 10, network)
    lanelet_2 = adjacent_lanelet_left(lanelet_1, network, False)

    lanelet_3 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_1, lanelet_3)
    lanelet_4 = adjacent_lanelet_left(lanelet_3, network, False)

    lanelet_5 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_1, lanelet_5)
    lanelet_6 = adjacent_lanelet_left(lanelet_5, network, False)

    lanelet_7 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_5, lanelet_7)
    lanelet_8 = adjacent_lanelet_left(lanelet_7, network, False)

    lanelet_9 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_3, lanelet_9)
    lanelet_10 = adjacent_lanelet_left(lanelet_9, network, False)

    lanelet_11 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_8, lanelet_11)
    lanelet_12 = adjacent_lanelet_left(lanelet_11, network, False)

    lanelet_13 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_8, lanelet_13)
    lanelet_14 = adjacent_lanelet_left(lanelet_13, network, False)

    lanelet_15 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_13, lanelet_15)
    lanelet_16 = adjacent_lanelet_left(lanelet_15, network, False)

    lanelet_17 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_10, lanelet_17)
    lanelet_18 = adjacent_lanelet_left(lanelet_17, network, False)

    lanelet_19 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_16, lanelet_19)
    lanelet_20 = adjacent_lanelet_left(lanelet_19, network, False)

    # missing dependencies
    set_predecessor_successor_relation(lanelet_1, lanelet_20)
    set_predecessor_successor_relation(lanelet_19, lanelet_2)
    set_predecessor_successor_relation(lanelet_11, lanelet_9)
    set_predecessor_successor_relation(lanelet_10, lanelet_12)
    set_predecessor_successor_relation(lanelet_17, lanelet_15)
    set_predecessor_successor_relation(lanelet_16, lanelet_18)

    incomings = [lanelet_1.lanelet_id, lanelet_8.lanelet_id, lanelet_10.lanelet_id, lanelet_16.lanelet_id]
    map_incoming = []
    for i in incomings:
        map_incoming.append(IntersectionIncomingElement(i, incomings, incomings, incomings, incomings))

    intersection_id = scenario.generate_object_id()

    crossings = {lanelet_3.lanelet_id, lanelet_4.lanelet_id, lanelet_5.lanelet_id,
                 lanelet_6.lanelet_id, lanelet_11.lanelet_id, lanelet_12.lanelet_id,
                 lanelet_13.lanelet_id, lanelet_14.lanelet_id, lanelet_17.lanelet_id,
                 lanelet_18.lanelet_id, lanelet_19.lanelet_id, lanelet_20.lanelet_id}

    intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming, crossings=crossings)

    return intersection


# t crossing
def t_crossing(width, diameter_crossing, network):
    rad = (diameter_crossing + width) / 2
    lanelet_1 = create_straight(width, diameter_crossing, 10, network)
    lanelet_2 = adjacent_lanelet_left(lanelet_1, network, False)

    lanelet_3 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_1, lanelet_3)
    lanelet_4 = adjacent_lanelet_left(lanelet_3, network, False)

    lanelet_5 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_3, lanelet_5)
    lanelet_6 = adjacent_lanelet_left(lanelet_5, network, False)

    lanelet_7 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_6, lanelet_7)
    lanelet_8 = adjacent_lanelet_left(lanelet_7, network, False)

    lanelet_9 = create_straight(width, diameter_crossing, 10, network)
    fit_to_predecessor(lanelet_7, lanelet_9)
    lanelet_10 = adjacent_lanelet_left(lanelet_9, network, False)

    lanelet_11 = create_curve(width, rad, np.pi * 0.5, 20, network)
    fit_to_predecessor(lanelet_10, lanelet_11)
    lanelet_12 = adjacent_lanelet_left(lanelet_11, network, False)

    # missing dependencies
    set_predecessor_successor_relation(lanelet_1, lanelet_12)
    set_predecessor_successor_relation(lanelet_11, lanelet_2)

    incomings = {lanelet_1.lanelet_id, lanelet_6.lanelet_id, lanelet_10.lanelet_id}
    map_incoming = []
    for i in incomings:
        map_incoming.append(IntersectionIncomingElement(i, incomings,
                                                        successors_right={lanelet_1.lanelet_id, lanelet_6.lanelet_id},
                                                        successors_straight={lanelet_6.lanelet_id,
                                                                             lanelet_10.lanelet_id},
                                                        successors_left={lanelet_1.lanelet_id, lanelet_10.lanelet_id}))

    intersection_id = scenario.generate_object_id()

    crossings = {lanelet_5.lanelet_id, lanelet_6.lanelet_id, lanelet_7.lanelet_id, lanelet_8.lanelet_id,
                 lanelet_11.lanelet_id, lanelet_12.lanelet_id}

    intersection = Intersection(intersection_id=intersection_id, incomings=map_incoming, crossings=crossings)

    return intersection


intersection_1 = t_crossing(3, 50, network)



scenario.add_objects([network, intersection_1])

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
    plt.show()
