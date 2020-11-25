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