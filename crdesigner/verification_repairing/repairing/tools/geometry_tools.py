import collections
import math
from typing import List

import numpy as np
import shapely
from commonroad.scenario.lanelet import Lanelet
from shapely.geometry import LineString, Point, Polygon

Line = collections.namedtuple("Line", "x1 y1 x2 y2")
LPoint = collections.namedtuple("Point", "x y")


def check_line_intersection_efficient(line1: List[List[float]], line2: List[List[float]]) -> bool:
    """
    Checks intersection of two lines defined by start and end point.

    :param line1: Line consisting of two 2D points.
    :param line2: Line consisting of two 2D points.
    :return: Boolean indicating whether lines intersect.
    """

    def ccw(p1: List[float], p2: List[float], p3: List[float]):
        return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0])

    # Return true if line segments AB and CD intersect
    return ccw(line1[0], line2[0], line2[1]) != ccw(line1[1], line2[0], line2[1]) and ccw(
        line1[0], line1[1], line2[0]
    ) != ccw(line1[0], line1[1], line2[1])


def check_intersected_lines(
    line1: np.ndarray, line2: np.ndarray = None, excluded_points=None
) -> bool:
    """
    Checks whether two lines intersect each other. If the second line is none self-intersection will be considered. If
    the computed intersection point is equal to one of the excluded points it is treated as if no crossing is present.

    :param line1: First line
    :param line2: Second line
    :param excluded_points: Points excluded as the intersection point
    :return: Is intersection or not
    """
    if excluded_points is None:
        excluded_points = []
    line_string1 = LineString([(x, y, z[0]) if z else (x, y) for x, y, *z in line1])
    if line2 is None:
        return not line_string1.is_simple
    line_string2 = LineString([(x, y, z[0]) if z else (x, y) for x, y, *z in line2])
    intersection = line_string1.intersection(line_string2)

    if isinstance(intersection, LineString):
        return False

    if isinstance(intersection, Point):
        intersection_point = [intersection.x, intersection.y]
        for excluded_point in excluded_points:
            if excluded_point == intersection_point:
                return False

    return True


def contains_points(lanelet: Lanelet, polyline: np.ndarray) -> List[bool]:
    """
    Verifies whether the points of a polyline are contained by the lanelet.

    :param lanelet: Considered lanelet
    :param polyline: Polyline
    :return: Respective points are contained or not
    """
    left_lanelet_points = list(lanelet.left_vertices)
    right_lanelet_points: list = list(lanelet.right_vertices)
    right_lanelet_points.reverse()

    polyline_points = list(polyline)

    poly = Polygon(left_lanelet_points + right_lanelet_points)

    is_points_contained = []
    for x, y in polyline_points:
        is_points_contained = is_points_contained + [poly.contains(Point(x, y))]

    return is_points_contained


def fill_number_of_vertices(vertices: np.ndarray, number: int) -> np.ndarray:
    """
    Modifies the line so that the distance between points is equal and the line is constructed of
    the specified number of points.

    :param vertices: Polyline
    :param number: Number of points
    :return: Modified polyline with the specified number of points
    """
    coords = [[adj_vert[i] for i in range(len(adj_vert))] for adj_vert in vertices]
    line = LineString(coords)
    distances = np.linspace(0, line.length, number)
    points = [line.interpolate(distance) for distance in distances]
    suited_coords = list()
    for point in points:
        # check if the point is 3d
        try:
            has_z = hasattr(point, "z")
        except shapely.errors.DimensionError:
            has_z = False
        if has_z:
            suited_coords.append([point.x, point.y, point.z])
        else:
            suited_coords.append([point.x, point.y])
    suited_vertices = np.array(suited_coords)
    return suited_vertices


def average_vertices(
    left_vertices: np.ndarray, right_vertices: np.ndarray, reverse: bool
) -> np.ndarray:
    if reverse:
        right_vertices = right_vertices[::-1]
    avg_vertices = []
    size = left_vertices.shape[0]
    for index in range(size):
        avg_x = (left_vertices[index][0] + right_vertices[index][0]) / 2
        avg_y = (left_vertices[index][1] + right_vertices[index][1]) / 2
        # check if the vertex is 3d
        if len(left_vertices[index]) == 3:
            avg_z = (left_vertices[index][2] + right_vertices[index][2]) / 2
            avg_vertices.append([avg_x, avg_y, avg_z])
        else:
            avg_vertices.append([avg_x, avg_y])

    return np.array(avg_vertices)


def insert_vertices(long_polyline: np.ndarray, short_polyline: np.ndarray) -> np.ndarray:
    """
    Inserts vertices into a polyline to be of the same length than other polyline.

    :param long_polyline: Polyline with higher number of vertices
    :param short_polyline: Polyline with lower number of vertices
    :return: Short polyline with equal length as long polyline
    """
    path_length_long = compute_path_length_from_polyline(long_polyline)
    path_length_percentage_long = path_length_long / path_length_long[-1]
    if len(short_polyline) > 2:
        path_length_short = compute_path_length_from_polyline(short_polyline)
        path_length_percentage_short = path_length_short / path_length_short[-1]
    else:
        path_length_percentage_short = [0, 1]

    index_mapping = create_mapping(path_length_percentage_long, path_length_percentage_short)

    org_polyline = short_polyline
    last_key = 0
    counter = 0
    for key, value in enumerate(index_mapping):
        if value == -1:
            counter += 1
        elif counter > 0 and value > -1:
            ub = org_polyline[value]
            lb = short_polyline[last_key]
            for idx in range(1, counter + 1):
                insertion_factor = (
                    path_length_percentage_long[last_key + idx]
                    - path_length_percentage_long[last_key]
                ) / (path_length_percentage_long[key] - path_length_percentage_long[last_key])
                new_vertex = insertion_factor * (ub - lb) + lb
                short_polyline_updated = np.insert(short_polyline, last_key + idx, new_vertex, 0)
                short_polyline = short_polyline_updated
            last_key = key
            counter = 0
        else:
            last_key = key
    return short_polyline


def create_mapping(
    path_length_percentage_long: np.ndarray, path_length_percentage_short: np.ndarray
) -> List[int]:
    """
    Extracts places (indices) where new vertices have to be added in shorter lanelet.

    :param path_length_percentage_long: Proportional path length along longer polyline
    :param path_length_percentage_short: Proportional path length along shorter polyline
    :return: Mapping of existing indices of shorter polyline to longer polyline
    """
    index_mapping = [-1] * len(path_length_percentage_long)
    index_mapping[0] = 0
    index_mapping[-1] = len(path_length_percentage_short) - 1

    finished = False

    last_idx_long = 1
    for key in range(1, len(path_length_percentage_short) - 1):
        value = path_length_percentage_short[key]
        threshold = 0.01
        while key not in index_mapping and not finished:
            for idx_long in range(
                last_idx_long,
                len(path_length_percentage_long) - (len(path_length_percentage_short) - key) + 1,
            ):
                if (
                    abs(path_length_percentage_long[idx_long] - value) < threshold
                    and index_mapping[idx_long] == -1
                ):
                    index_mapping[idx_long] = key
                    last_idx_long = idx_long
                    if (
                        len(path_length_percentage_short) - key + 1
                        == len(index_mapping) - idx_long + 1
                    ):
                        for idx in range(idx_long + 1, len(index_mapping)):
                            index_mapping[idx] = key + 1
                            key += 1
                        finished = True
                    break
            threshold *= 2
        if finished:
            break

    return index_mapping


def compute_path_length_from_polyline(polyline: np.ndarray) -> np.ndarray:
    """
    Computes the path length of a given polyline.

    :param polyline: Polyline with 2D points
    :return: Path length of the polyline
    """
    assert (
        isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(polyline[:, 0]) > 2
    ), "Polyline malformed for pathlength computation p={}".format(polyline)
    distance = [0]
    for i in range(1, len(polyline)):
        distance.append(distance[i - 1] + np.linalg.norm(polyline[i] - polyline[i - 1]))
    return np.array(distance)


def line_length(line: Line) -> float:
    """
    Computes the path length of a line.

    :param line: Line with a specified number of points
    :return: Distance of the line
    """
    distance = math.sqrt((line.x2 - line.x1) ** 2 + (line.y2 - line.y1) ** 2)
    return distance
