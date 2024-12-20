"""
This module provides various methods to handle geometric problems.
"""

from typing import Iterable, List, Optional, Tuple

import numpy as np
import scipy.special

from crdesigner.common.config.osm_config import osm_config as config


class Point:
    """
    Class to represent a Point with cartesian coordinates
    """

    def __init__(self, id: Optional[int], x: float, y: float):
        """
        creates a point

        :param id: unique id
        :param x: x coordinate
        :param y: y coordinate
        """
        self.id = id
        self.x = x
        self.y = y

    def __str__(self):
        return "Point with id {}: [x: {}, y: {}]".format(self.id, self.x, self.y)

    def get_array(self):
        """
        converts point to numpy array

        :return: numpy array
        """
        return np.array([self.x, self.y])

    def set_position(self, pos: np.ndarray):
        """
        sets coordinates of point to values given in numpy array

        :param pos:
        :return:
        """
        self.x = pos[0]
        self.y = pos[1]


class Area:
    """
    Class to represent an Area, which can be used if points are inside it
    """

    def __init__(self, x_min, x_max, y_min, y_max):
        assert x_min <= x_max, f"xmin: {x_min}, xmax: {x_max}"
        assert y_min <= y_max, f"ymin: {y_min}, xyax: {y_max}"
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

    def __contains__(self, item):
        if isinstance(item, Point):
            return (self.x_min <= item.x <= self.x_max) and (self.y_min <= item.y <= self.y_max)
        elif isinstance(item, np.ndarray):
            return (self.x_min <= item[0] <= self.x_max) and (self.y_min <= item[1] <= self.y_max)
        else:
            raise TypeError("the tested Object must be either a Point or a numpy array")

    def __str__(self):
        return "Area: x in [{}, {}], y in [{}, {}]".format(
            self.x_min, self.x_max, self.y_min, self.y_max
        )


def points_to_array(points: List[Point]) -> np.ndarray:
    """
    converts a list of Points to a numpy array

    :param points:
    :return:
    """
    return np.array([point.get_array() for point in points])


def get_orthogonal(vector: np.ndarray) -> np.ndarray:
    """
    creates an orthogonal vector to a given vector

    :param vector: original vector
    :return: orthogonal vector
    """
    orthogonal_vector = np.array([vector[1], -vector[0]])
    magnitude = np.linalg.norm(orthogonal_vector)
    return orthogonal_vector / magnitude


def offset_polyline(waypoints: List[np.ndarray], size: float, at_first: bool) -> List[np.ndarray]:
    """
    offsets a polyline
    one end is offset by the full size, the other end remains unchanged
    intermediate points are offset by a linearly declining distance

    :param waypoints: list of way points specifying polyline
    :param size: distance of full offset
    :param at_first: True if full offset is performed at the first waypoints, else False
    :return: list of offset waypoints
    """
    assert len(waypoints) > 1
    new_line = []
    for index, point in enumerate(waypoints):
        if index > 0:
            vector1 = point - waypoints[index - 1]
        else:
            vector1 = np.array([0.0, 0.0])
        if index + 1 < len(waypoints):
            vector2 = waypoints[index + 1] - point
        else:
            vector2 = np.array([0.0, 0.0])
        vector = vector1 + vector2
        if at_first:
            stepsize = size * (1 - index / (len(waypoints) - 1))
        else:
            stepsize = size * index / (len(waypoints) - 1)
        orthogonal_vector = get_orthogonal(vector) * stepsize
        new_line.append(point + orthogonal_vector)
    return new_line


def create_parallels(
    waypoints: List[np.ndarray], width: float, points: bool = False
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    creates left and right parallels to a given polygonal chain

    :param waypoints: list waypoints
    :param width: distance between the created parallels
    :param points: if true waypoints are point objects else waypoints are arrays
    :return: left_bound, right_bound
    """
    right_bound = []
    left_bound = []
    if not points:
        waypoints = [Point(None, x[0], x[1]) for x in waypoints]
    for waypoint_counter, current_point in enumerate(waypoints):
        x1 = current_point.x
        y1 = current_point.y
        if waypoint_counter + 1 < len(waypoints):
            x2 = waypoints[waypoint_counter + 1].x
            y2 = waypoints[waypoint_counter + 1].y
        else:
            x1 = waypoints[waypoint_counter - 1].x
            y1 = waypoints[waypoint_counter - 1].y
            x2 = current_point.x
            y2 = current_point.y
        vector = [x2 - x1, y2 - y1]
        orthogonal_vector = np.array([vector[1], -vector[0]])
        magnitude = np.linalg.norm(orthogonal_vector)
        orthogonal_vector = orthogonal_vector / magnitude * width
        left_bound.append(
            np.array(
                [
                    current_point.x - orthogonal_vector[0],
                    current_point.y - orthogonal_vector[1],
                ]
            )
        )
        right_bound.append(
            np.array(
                [
                    current_point.x + orthogonal_vector[0],
                    current_point.y + orthogonal_vector[1],
                ]
            )
        )
    return left_bound, right_bound


def create_tilted_parallels(
    waypoints: List[np.ndarray], width1: float, width2: float, points: bool = False
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    creates tilted left and right parallels to a given polyline
    one end is offset by the width1, the other end is offset by width2
    intermediate points are offset by a linearly changing distance

    :param waypoints: list of way points
    :param width1: distance between the created parallels at the start
    :param width2: distance between the created parallels at the end
    :param points: if true waypoints are point objects else waypoints are arrays
    :return: left_bound, right_bound
    """
    right_bound = []
    left_bound = []
    if not points:
        waypoints = [Point(None, x[0], x[1]) for x in waypoints]
    for waypoint_counter, current_point in enumerate(waypoints):
        x1 = current_point.x
        y1 = current_point.y
        if waypoint_counter + 1 < len(waypoints):
            x2 = waypoints[waypoint_counter + 1].x
            y2 = waypoints[waypoint_counter + 1].y
        else:
            x1 = waypoints[waypoint_counter - 1].x
            y1 = waypoints[waypoint_counter - 1].y
            x2 = current_point.x
            y2 = current_point.y
        vector = [x2 - x1, y2 - y1]
        orthogonal_vector = np.array([vector[1], -vector[0]])
        magnitude = np.linalg.norm(orthogonal_vector)
        width = width1 * (
            1 - waypoint_counter / (len(waypoints) - 1)
        ) + width2 * waypoint_counter / (len(waypoints) - 1)
        orthogonal_vector = orthogonal_vector / magnitude * width
        left_bound.append(
            np.array(
                [
                    current_point.x - orthogonal_vector[0],
                    current_point.y - orthogonal_vector[1],
                ]
            )
        )
        right_bound.append(
            np.array(
                [
                    current_point.x + orthogonal_vector[0],
                    current_point.y + orthogonal_vector[1],
                ]
            )
        )
    return left_bound, right_bound


def bernstein(n: int, i: int, t: float) -> float:
    """
    computes the bernstein polynomial B_{i,n}(t)

    :param n: degree of the polynomial
    :param i: parameter of the polynomial
    :param t: point at which polynomial is evaluated, should be in [0,1]
    :return: result of the polynomialt
    """
    return scipy.special.binom(n, i) * t**i * (1 - t) ** (n - i)


def bezier(points: np.ndarray, t: float) -> np.ndarray:
    """
    evaluates a bezier curve at a certain point

    :param points: array of control points
    :param t: point at which the curve is evaluated, should be in [0,1]
    :return: coordinates of the resulting point
    """
    sum = np.array([0.0, 0.0])
    n = len(points) - 1
    for index, point in enumerate(points):
        sum += bernstein(n, index, t) * point
    return sum


def evaluate_bezier(points: np.ndarray, n: int) -> List[np.ndarray]:
    """
    evaluates a bezier curve at n equidistant points

    :param points: control points of the bezier curve
    :param n: number of resulting points
    :return: points on curve
    """
    curve_points = []
    for i in range(n):
        curve_points.append(bezier(points, i / n))
    curve_points = set_line_points(curve_points, n)
    return curve_points


def get_inner_bezier_point(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, d: float) -> np.ndarray:
    """
    calculates the location for a control point to generate a bezier curve
    the control point is created between p2 and p3 at a distance of d*||p2-p3|| to p2
    it leads orthogonal to the bisector between the vectors from p2 to the other points

    :param p1: predecessor of p2
    :param p2: current way point and start of curve
    :param p3: successor of p2 and target of curve
    :param d: ration of distance between new point and p2, should be within [0, 1]. Values in [0, 0.5] are advised
    :return: the new control point
    """
    vector1 = p1 - p2
    vector1 /= np.linalg.norm(vector1)
    vector2 = p3 - p2
    vector2 /= np.linalg.norm(vector2)
    bisector = vector1 + vector2
    if np.linalg.norm(bisector) < 0.000001:
        # if vectors are almost parallel use vector2 instead of orthogonal of bisector
        orthogonal_vector = vector2
    else:
        orthogonal_vector = np.array([bisector[1], -bisector[0]])
    orthogonal_vector /= np.linalg.norm(orthogonal_vector)
    orthogonal_vector *= d * np.linalg.norm(p2 - p3)
    # orthogonal_vector has to point in direction of p3
    if np.linalg.norm(p2 + orthogonal_vector - p3) > np.linalg.norm(p2 - orthogonal_vector - p3):
        orthogonal_vector *= -1
    return p2 + orthogonal_vector


def get_bezier_points_of_segment(
    segment_points: np.ndarray, d: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    creates control points for bezier curve between two way points

    :param segment_points: four way points. The first is the predecessor of the current interval,
        the last is the successor of the current interval
    :param d: ratio of distance between inner control points and outer control points,
        should be within [0, 1]. Values in [0, 0.5] are advised
    :return: tuple of all four control points
    """
    p1 = segment_points[1]
    p4 = segment_points[2]
    # calculate p2:
    p2 = get_inner_bezier_point(segment_points[0], p1, p4, d)
    # calculate p3:
    p3 = get_inner_bezier_point(segment_points[3], p4, p1, d)
    return p1, p2, p3, p4


def distance(point: np.ndarray, polyline: Iterable[np.ndarray]) -> float:
    """
    calculates the distance of a point to a polyline

    :param point: location of the point
    :param polyline: way points of the polyline
    :return: distance between point and polylinet
    """
    distances = []
    for linepoint in polyline:
        distances.append(np.linalg.norm(point - linepoint))
    return min(distances)


def create_middle_line(
    polyline1: List[np.ndarray], polyline2: List[np.ndarray]
) -> List[np.ndarray]:
    """
    creates a line between two polylines
    the lines should have the same amount of way points for good results

    :param polyline1: first polyline
    :param polyline2: second polyline
    :return: new polyline
    """
    result = []
    if len(polyline1) <= len(polyline2):
        smaller = polyline1
        larger = polyline2
    else:
        smaller = polyline2
        larger = polyline1
    differential = len(larger) / len(smaller)

    for index, point1 in enumerate(smaller[:-1]):
        point2 = larger[int(differential * index)]
        result.append(point1 + (point2 - point1) / 2)
    result.append(smaller[-1] + (larger[-1] - smaller[-1]) / 2)
    return result


def offset_over_line(polyline1: List[np.ndarray], polyline2: List[np.ndarray]) -> List[np.ndarray]:
    """
    offsets a polyline over another polyline
    the lines should have the same amount of way points for good results

    :param polyline1: the line to sett off
    :param polyline2: the line to set polyline1 over
    :return: the offset polyline
    """
    result = []
    differential = len(polyline2) / len(polyline1)
    for index, point1 in enumerate(polyline1[:-1]):
        point2 = polyline2[int(differential * index)]
        result.append(point1 + (point2 - point1) * 2)
    result.append(polyline1[-1] + (polyline2[-1] - polyline1[-1]) * 2)
    return result


def angle_to(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    calculates angle between vectors in degrees

    :param v1: one vector
    :param v2: another vector
    :return: angle between vectors in degrees
    """
    x = [v1[0], v2[0]]
    y = [v1[1], v2[1]]
    angles = np.arctan2(y, x) + np.pi
    diff1 = abs(angles[0] - angles[1])
    diff2 = np.pi * 2 - diff1
    angle = min(diff1, diff2)
    angle = angle / np.pi * 180
    return angle


def get_angle(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Get clockwise angle between vectors

    :param v1: one vector
    :param v2: another vector
    :return: clockwise angle between vectors in degrees
    """
    x = [v1[0], v2[0]]
    y = [v1[1], v2[1]]
    angles = np.arctan2(y, x) + np.pi
    diff1 = angles[0] - angles[1]
    angle = diff1 / np.pi * 180
    return angle


def curvature(polyline: List[np.ndarray]) -> float:
    """
    calculates the angle between start and end of a polyline in degrees

    :param polyline: a polyline
    :return: angle in degrees
    """
    if len(polyline) < 3:
        return False
    else:
        v1 = polyline[0] - polyline[1]
        v2 = polyline[-1] - polyline[-2]
        angle = angle_to(v1, v2)
        return angle


def intersection(
    point1: np.ndarray, point2: np.ndarray, vector1: np.ndarray, vector2: np.ndarray
) -> Tuple[float, float, Optional[np.ndarray]]:
    """
    calculates the intersection point of two lines

    :param point1: starting point of the first line
    :param point2: starting point of the second line
    :param vector1: direction of the first line
    :param vector2: direction of the second line
    :return: length of vector1 and vector2 to the intersection point and the intersection point
    """
    denom = vector1[1] * vector2[0] - vector1[0] * vector2[1]
    if denom == 0:
        # vectors do not intersect
        return -1, -1, None
    a1 = np.dot([vector2[1], -vector2[0]], point1 - point2) / denom
    a2 = np.dot([vector1[1], -vector1[0]], point1 - point2) / denom
    intersection_point = point1 + vector1 * a1
    return a1, a2, intersection_point


def line_length(line: List[np.ndarray]) -> float:
    """
    calculates the length of a polyline

    :param line: a polyline
    :return: length of the line
    """
    if len(line) < 2:
        raise ValueError("line has not enough points")
    length = 0
    for index, point in enumerate(line[:-1]):
        length += np.linalg.norm(point - line[index + 1])
    return length


def get_evaluation_point(line: List[np.ndarray], start_point: int, length: float):
    """
    return the point last point before length from start_point is reached

    :param line:
    :param start_point:
    :param length:
    :return:
    """
    current_length = 0
    current_point = start_point
    next_step = np.linalg.norm(line[start_point] - line[start_point + 1])
    while length > current_length + next_step:
        current_length += next_step
        current_point += 1
        next_step = np.linalg.norm(line[current_point] - line[current_point + 1])
    remaining_length = length - current_length
    return current_point, remaining_length


def evaluate_line(
    line: List[np.ndarray], length: float, start_point: int = 0
) -> Tuple[np.ndarray, int, float]:
    """
    returns the point after a given length on a polyline

    :param start_point: the point to start at
    :param line: polyline to find the point on
    :param length: the distance on the polyline from the start to the point
    :return: point on line after length, index of the last point on line before the resulting point
    """
    current_point, remaining_length = get_evaluation_point(line, start_point, length)
    if remaining_length > 0:
        vector = line[current_point + 1] - line[current_point]
        vector = vector / np.linalg.norm(vector) * remaining_length
        return line[current_point] + vector, current_point, remaining_length
    else:
        return line[current_point], current_point, remaining_length


def set_line_points(line: List[np.ndarray], n: int) -> List[np.ndarray]:
    """
    sets n new equidistant way points for a polyline

    :param line: a polyline
    :param n: number of new way points
    :return: new list of way points
    """
    assert n > 1
    total_length = line_length(line)
    newline = [line[0]]
    current_point = 0
    remaining_length = 0
    delta = total_length / (n - 1)
    for i in range(n - 2):
        new_point, current_point, remaining_length = evaluate_line(
            line, delta + remaining_length, current_point
        )
        newline.append(new_point)
    newline.append(line[-1])
    return newline


def intersection_polylines(pline1: List[np.ndarray], pline2: List[np.ndarray]) -> np.ndarray:
    """
    calculates the intersection point of two polylines

    :param pline1: a polyline
    :param pline2: another polyline
    :return: the intersection point
    """
    for index1, point1 in enumerate(pline1[:-1]):
        vector1 = pline1[index1 + 1] - point1
        for index2, point2 in enumerate(pline2[:-1]):
            vector2 = pline2[index2 + 1] - point2
            a1, a2, point = intersection(point1, point2, vector1, vector2)
            if 0 <= a1 <= 1 and 0 <= a2 <= 1:
                print("intersection at index1: {}, index2: {}".format(index1, index2))
                return point
    # Return false if polylines do not intersect
    return False
    # raise ValueError("no intersection")


def find_point(line: List[np.ndarray], point: int, overhang: float) -> np.ndarray:
    """
    finds a point on a polyline between point at index point and its successor

    :param line: a polyline
    :param point: index of the point after which is searched
    :param overhang: ratio of distance between points
    :return: point on the line
    """
    assert 0 < overhang < 1
    assert point + 1 < len(line)
    result = line[point] + (line[point + 1] - line[point]) * overhang
    return result


def split_line(
    line: List[np.ndarray], index: int, split_point: Optional[np.ndarray] = None
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    splits a polyline at a point on the line in two parts, line1 and line2

    :param line: a polyline to split
    :param index: index of the last element of line1
    :param split_point: optional point both lines share
    :return: line1, line2: two lines]]
    """
    line1 = line[: index + 1]
    line2 = line[index + 1 :]
    if split_point is not None:
        line1 = line1 + [split_point]
        line2 = [split_point] + line2
    return line1, line2


def is_corner(index: int, waypoints: List[Point]) -> bool:
    if index == 0 or index == len(waypoints) - 1:
        return False
    prev_point = waypoints[index - 1]
    current_point = waypoints[index]
    next_point = waypoints[index + 1]
    v1 = prev_point.get_array() - current_point.get_array()
    v2 = next_point.get_array() - current_point.get_array()
    return 85 <= angle_to(v1, v2) <= 95


def get_lon_lat_constants(origin):
    lat = origin[0]
    lon_constant = np.pi / 180 * config.EARTH_RADIUS * np.cos(np.radians(lat))
    lat_constant = np.pi / 180 * config.EARTH_RADIUS
    return abs(lon_constant), abs(lat_constant)


def lon_lat_to_cartesian(waypoint: np.ndarray, origin: np.ndarray) -> np.ndarray:
    lon_constant, lat_constant = get_lon_lat_constants(origin)
    diff = waypoint - origin
    lon_d, lat_d = diff[1], diff[0]
    x = lon_constant * lon_d
    y = lat_constant * lat_d
    return np.array([x, y])


def point_to_line_distance(
    point: np.ndarray, line_start: np.ndarray, line_end: np.ndarray
) -> float:
    """
    calculates the distance of a point to a line defined by two points

    :param point:
    :param line_start:
    :param line_end:
    :return: the perpendicular distance of the point to the line
    """
    return np.linalg.norm(np.cross(line_end - line_start, line_start - point)) / np.linalg.norm(
        line_end - line_start
    )


def pre_filter_points(lines: List[List[np.ndarray]]) -> List[List[np.ndarray]]:
    """


    :param lines: poly-lines of same direction
    :return:
    """

    def is_straight(line: List[np.ndarray], index: int) -> bool:
        if index == 0 or index == len(line) - 1:
            return False
        v1 = line[index - 1] - line[index]
        v2 = line[index + 1] - line[index]
        angle = angle_to(v1, v2)
        return angle >= 179.99

    negligible = [
        all([is_straight(line, index) for line in lines]) for index in range(len(lines[0]))
    ]
    result = [
        [point for index, point in enumerate(line) if not negligible[index]] for line in lines
    ]

    # set waypoints to at least three
    if len(result[0]) == 2:
        for line in result:
            line.insert(1, (line[0] + line[1]) / 2)
    return result


def filter_points(lines: List[List[np.ndarray]], threshold: float) -> List[List[np.ndarray]]:
    """
    filters points of poly-lines so that only points which affect the course of the line remain
    returns lines with at least three way points

    :param lines: a list of poly-lines which lead in the same direction
    :param threshold: the allowed delta of the resulting line if a point is deleted
    :return:
    """

    def point_negligible(
        original_lines: List[List[np.ndarray]], omitted_point_interval: Tuple[int, int]
    ) -> bool:
        """
        checks if the resulting lines will have a distance below the threshold to the original lines


        :param original_lines: poly-lines of same direction
        :param omitted_point_interval: the interval of points which will be deleted
        :return:
        """
        assert omitted_point_interval[0] > 0, "the first point of a line cannot be ommited"
        assert omitted_point_interval[1] + 1 < len(
            original_lines[0]
        ), "the last point of a line cannot be omitted"
        for line in original_lines:
            new_line_start = line[omitted_point_interval[0] - 1]
            new_line_end = line[omitted_point_interval[1] + 1]
            for point_index in range(omitted_point_interval[0], omitted_point_interval[1] + 1):
                if (
                    point_to_line_distance(line[point_index], new_line_start, new_line_end)
                    > threshold
                ):
                    return False
        return True

    nr_of_waypoints = len(lines[0])
    for line in lines:
        assert len(line) == nr_of_waypoints, "all lines must have the same number of waypoints"

    result = [line[:1] for line in lines]
    delete_interval = (1, 1)

    while delete_interval[1] < len(lines[0]):
        while delete_interval[1] + 1 < len(lines[0]) and point_negligible(lines, delete_interval):
            delete_interval = (delete_interval[0], delete_interval[1] + 1)
        # found a point which cannot be deleted
        next_point: int = delete_interval[1]
        for index, line in enumerate(lines):
            result[index].append(line[next_point])
        delete_interval = (next_point + 1, next_point + 1)

    # set waypoints to at least three
    if len(result[0]) == 2:
        for line in result:
            line.insert(1, (line[0] + line[1]) / 2)

    assert len(result[0]) >= 3, f"len is: {len(result[0])}"
    for i, line in enumerate(lines):
        assert line[-1] is result[i][-1], (
            f"point at {line[-1]} results in {result[i][-1]},\n"
            f"line: {line}, len: {len(line)},\n"
            f"result: {result[i]}, len: {len(result[i])}"
        )

    return result


def get_gradient(polyline: List[np.ndarray]):
    a = polyline[0]
    b = polyline[-1]

    m = (b[1] - a[1]) / (b[0] - a[0])
    return m


def is_clockwise(polyline: List[np.ndarray]):
    """
    determines if points in a polyline are ordered clockwise or anti-clockwise.
    If result > 0, points are orderered clockwise.
    If result < 0, points are ordered anti_clockwise.
    If result = 0, we have a straight line.

    Source: https://stackoverflow.com/a/61991493/13700747

    :param polyline: a polyline
    :return: s
    """

    assert len(polyline) > 0
    s = 0.0
    for p1, p2 in zip(polyline, polyline[1:] + [polyline[0]]):
        s += (p2[0] - p1[0]) * (p2[1] + p1[1])
    return s
