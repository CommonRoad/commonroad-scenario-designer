import copy
import math
import warnings
from typing import List, Optional, Tuple

import numpy as np
from commonroad.scenario.lanelet import LineMarking
from pyproj import Transformer

from crdesigner.map_conversion.common.conversion_lanelet import ConversionLanelet
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.plane import (
    ParametricLane,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    RoadMark,
)


def convert_line_marking(plane_line_marking: RoadMark) -> LineMarking:
    """
    Function that converts the Opendrive road mark type to the corresponding CommonRoad lanelet linemarking type.
    :param plane_line_marking: road mark of the parametric lane
    :return: corresponding linemarking type
    """
    mark = LineMarking.UNKNOWN

    if plane_line_marking.type == "solid":
        if plane_line_marking.weight == "standard":
            mark = LineMarking.SOLID
        elif plane_line_marking.weight == "bold":
            mark = LineMarking.BROAD_SOLID

    elif plane_line_marking.type == "broken":
        if plane_line_marking.weight == "standard":
            mark = LineMarking.DASHED
        elif plane_line_marking.weight == "bold":
            mark = LineMarking.BROAD_DASHED

    elif plane_line_marking.type == "solid solid":
        mark = LineMarking.SOLID_SOLID

    elif plane_line_marking.type == "broken broken":
        mark = LineMarking.DASHED_DASHED

    elif plane_line_marking.type == "curb":
        mark = LineMarking.CURB

    elif plane_line_marking.type == "none":
        mark = LineMarking.NO_MARKING

    elif plane_line_marking.type == "solid dashed":
        mark = LineMarking.SOLID_DASHED

    elif plane_line_marking.type == "dashed solid":
        mark = LineMarking.DASHED_SOLID

    return mark


class ParametricLaneGroup:
    """A group of parametric_lanes can be converted to a
    lanelet just like a single parametric_lane.
    """

    def __init__(
        self,
        id_: str = None,
        parametric_lanes=None,
        inner_neighbour=None,
        inner_neighbour_same_direction=True,
        outer_neighbour=None,
        inner_linemarking=None,
        driving_direction=True,
    ):
        """Initializes a ParametricLaneGroup object.

        :param id_: ID of the ParametricLaneGroup.
        :param parametric_lanes: Lanes of the group.
        :param inner_neighbour: ID of the inner neighbor of this group.
        :param outer_neighbour: ID of the outer neighbor of this group.
        :param inner_linemarking: inside road mark present in 2 central inner lanelets, closest to the center line
        :param driving_direction: driving direction. right if true.
        """
        self._geo_lengths = [np.array([0.0])]
        self.parametric_lanes: List[ParametricLane] = []
        self.id_ = id_
        self.inner_neighbour = inner_neighbour
        self.inner_neighbour_same_direction = inner_neighbour_same_direction
        self.outer_neighbour = outer_neighbour
        self.traffic_lights = []
        self.traffic_signs = []
        self.stop_lines = []
        self.signal_references = []
        if inner_linemarking is None:
            inner_linemarking = RoadMark()
            inner_linemarking.type = "unknown"
        self.inner_linemarking = inner_linemarking

        if parametric_lanes is not None:
            if isinstance(parametric_lanes, list):
                self.extend(parametric_lanes)
            else:
                self.append(parametric_lanes)

        self.driving_direction = driving_direction

    def append(self, parametric_lane: ParametricLane):
        """Append lane to start or end of internal list of ParametricLane objects. If the parametric_lane is reverse,
        it is inserted at the start.

        :param parametric_lane: Lane to be inserted either at beginning or end of list.
        """
        if parametric_lane.reverse:
            self.parametric_lanes.insert(0, parametric_lane)
        else:
            self.parametric_lanes.append(parametric_lane)

        self._add_geo_length(parametric_lane.length, parametric_lane.reverse)

    def extend(self, plane_list: list):
        """Extend own ParametricLanes with new ones. Assumes ParametricLane objects in plane_list are already in order.

        :param plane_list: List with ParametricLane Objects
        """
        for plane in plane_list:
            self.parametric_lanes.append(plane)
            self._add_geo_length(plane.length)

    def _add_geo_length(self, length: float, reverse: bool = False):
        """Add length of a ParametricLane to the array which keeps track
        at which position which ParametricLane is placed.
        This array is used for quickly accessing
        the proper ParametricLane for calculating a position.

        :param length: Length of ParametricLane to be added.
        :param reverse: Whether the lane is reversed. Default is False.
        """
        if reverse:
            self._geo_lengths = np.insert(self._geo_lengths, 1, length)
            self._geo_lengths[2:] = [x + length for i, x in enumerate(self._geo_lengths) if i > 1]
        else:
            self._geo_lengths = np.append(self._geo_lengths, length + self._geo_lengths[-1])

    @property
    def type(self) -> str:
        """Get type of ParametricLaneGroup.

        :return: Type of first ParametricLane in this group.
        """
        return self.parametric_lanes[0].type_

    @property
    def length(self) -> float:
        """Length of all ParametricLanes which are collected in this ParametricLaneGroup.

        :return: Accumulated length of ParametricLaneGroup
        """

        return sum([x.length for x in self.parametric_lanes])

    @property
    def access(self):
        """Access restrictions of the first ParametricLane in this ParametricLaneGroup.

        :return: The access restrictions of the first Plane
        """
        return self.parametric_lanes[0].access

    def has_zero_width_everywhere(self) -> bool:
        """Checks if width is zero at every point of this ParametricLaneGroup.

        :return: True if every ParametricLane has width_coefficients equal to only zero
        """
        return all([plane.has_zero_width_everywhere() for plane in self.parametric_lanes])

    def to_lanelet(
        self, error_tolerance, min_delta_s, transformer: Transformer, driving_direction: bool = True
    ) -> ConversionLanelet:
        """Convert a ParametricLaneGroup to a Lanelet.

        :param error_tolerance: Max. error between reference geometry and polyline of vertices.
        :param min_delta_s: Min. step length between two sampling positions on the reference geometry
        :param transformer: Coordinate projection transformer.
        :param driving_direction: Driving direction, right if true.
        :return: Created Lanelet.
        """
        left_vertices, right_vertices = np.array([]), np.array([])
        line_marking_right_vertices = LineMarking.UNKNOWN

        for parametric_lane in self.parametric_lanes:
            local_left_vertices, local_right_vertices = parametric_lane.calc_vertices(
                error_tolerance=error_tolerance, min_delta_s=min_delta_s, transformer=transformer
            )
            # check whether parametric lane cannot be used,
            # e.g., if to small it is possible that no vertices are generated
            if local_left_vertices is None or len(local_left_vertices) == 0:
                continue

            if len(left_vertices) > 0:  # check for first iteration
                if np.isclose(left_vertices[-1], local_left_vertices[0]).all():
                    idx = 1
                else:
                    idx = 0
                left_vertices = np.vstack((left_vertices, local_left_vertices[idx:]))
                right_vertices = np.vstack((right_vertices, local_right_vertices[idx:]))
            else:
                left_vertices = local_left_vertices
                right_vertices = local_right_vertices

        for parametric_lane in self.parametric_lanes:
            line_marking = parametric_lane.line_marking
            if line_marking is not None:
                # for the right-hand driving, outer lanelet is always on the right side
                # assumed right-hand driving
                line_marking_right_vertices = convert_line_marking(line_marking)
            else:
                pass

        center_vertices = np.array(
            [(left + right) / 2 for (left, right) in zip(left_vertices, right_vertices)]
        )
        # access to user conversion
        user_list = [set(), set()]
        user_set = {
            "car",
            "truck",
            "bus",
            "motorcycle",
            "priorityVehicle",
            "taxi",
            "bicycle",
            "pedestrian",
            "train",
        }
        direct_map_set = {"truck", "bus", "motorcycle", "pedestrian", "bicycle", "taxi"}
        vehicle_set = {"car", "truck", "bus", "motorcycle", "priorityVehicle", "taxi"}

        def access_map(_set: list, allow: bool, _user: str):
            """
            Nested helper function that unclutters the code bit.
            :param allow: decides whether the current access type should be restricted or permitted
            :param _user: the user to be added or excluded from the user list
            :param _set: the already accumulated set
            """
            _user_list = [set(), set()]
            if allow:
                _user_list = [set.union(_set[0], {_user}), _user_list[1]]
            else:
                _user_list = [_user_list[0], set.union(_set[1], {_user})]
            return _user_list

        for restriction in self.access:
            if not np.isclose(0.0, restriction[2]):
                warnings.warn(
                    "There exist an offset in the lane access restrictions that is currently ignored"
                )
            if restriction[0] in direct_map_set:
                user = restriction[0]
            elif restriction[0] == "passengerCar":
                user = "car"
            elif restriction[0] == "emergency":
                user = "priorityVehicle"
            elif restriction[0] == "trucks":
                user = "truck"
            else:  # ignore other lane access types
                continue
            user_list = access_map(user_list, restriction[1] == "allow", user)
        users = (user_set if user_list[0] == set() else user_list[0]).difference(user_list[1])
        if vehicle_set.issubset(users):
            users = set.union({"vehicle"}, set.difference(users, vehicle_set))
        if self.type == "bidirectional":
            lanelet = ConversionLanelet(
                copy.deepcopy(self),
                left_vertices,
                center_vertices,
                right_vertices,
                self.id_,
                lanelet_type=self.type,
                line_marking_left_vertices=convert_line_marking(self.inner_linemarking),
                line_marking_right_vertices=line_marking_right_vertices,
                speed=self.parametric_lanes[0].speed,
                user_bidirectional=users,
                traffic_signs=set(sign.traffic_sign_id for sign in self.traffic_signs),
                traffic_lights=set(light.traffic_light_id for light in self.traffic_lights),
                stop_line=self.stop_lines[0] if len(self.stop_lines) > 0 else None,
            )
        else:
            lanelet = ConversionLanelet(
                copy.deepcopy(self),
                left_vertices,
                center_vertices,
                right_vertices,
                self.id_,
                lanelet_type=self.type,
                line_marking_left_vertices=convert_line_marking(self.inner_linemarking),
                line_marking_right_vertices=line_marking_right_vertices,
                speed=self.parametric_lanes[0].speed,
                user_one_way=users,
                traffic_signs=set(sign.traffic_sign_id for sign in self.traffic_signs),
                traffic_lights=set(light.traffic_light_id for light in self.traffic_lights),
                stop_line=self.stop_lines[0] if len(self.stop_lines) > 0 else None,
            )
        # Adjacent lanes
        self._set_adjacent_lanes(lanelet, driving_direction)

        return lanelet

    def calc_border(
        self, border: str, s_pos: float, width_offset: float = 0.0, compute_curvature: bool = True
    ) -> Tuple[Tuple[float, float], float, float, float]:
        """Calc vertices point of inner or outer Border.

        :param border: Which border to calculate (inner or outer)
        :param s_pos: Position of parameter ds where to calc the cartesian coordinates
        :param width_offset: Offset to add to calculated width in reference to the reference border. Default is 0.0.
        :param compute_curvature: Whether to computer curvature. Default is True.
        :return: Cartesian coordinates of point on inner border and tangential direction.
        """
        try:
            # get index of geometry which is at s_pos
            mask = self._geo_lengths > s_pos
            sub_idx = np.argmin(self._geo_lengths[mask] - s_pos)
            plane_idx = np.arange(self._geo_lengths.shape[0])[mask][sub_idx] - 1
        except ValueError:
            # s_pos is after last geometry because of rounding error
            if np.isclose(s_pos, self._geo_lengths[-1]):
                plane_idx = self._geo_lengths.size - 2
            else:
                raise Exception(
                    f"Tried to calculate a position outside of the borders of the reference path at s={s_pos}"
                    f", but path has only length of l={self._geo_lengths[-1]}"
                )

        return self.parametric_lanes[plane_idx].calc_border(
            border,
            s_pos - self._geo_lengths[plane_idx],
            width_offset,
            compute_curvature=compute_curvature,
        )

    def to_lanelet_with_mirroring(
        self,
        mirror_border: str,
        distance: Tuple[float, float],
        mirror_interval: Tuple[float, float],
        adjacent_lanelet: ConversionLanelet,
        precision: float = 0.5,
        transformer: Optional[Transformer] = None,
    ):
        """Convert a ParametricLaneGroup to a Lanelet with mirroring one of the borders.

        :param mirror_border: Which lane to mirror, if performing merging or splitting of lanes.
        :param distance: Distance at start and end of lanelet, which mirroring lane should have from the other lane it
                        mirrors
        :param mirror_interval: Position at start and end of mirroring
        :param adjacent_lanelet: The adjacent lanelet.
        :param precision: Number which indicates at which space interval (in curve parameter ds) the coordinates of the
                        boundaries should be calculated. Default is 0.5.
        :param transformer: Coordinate projection transformer.
        :return: Created Lanelet.
        """
        linear_distance_poly = np.polyfit(mirror_interval, distance, 1)
        distance_poly1d = np.poly1d(linear_distance_poly)
        global_distance = distance_poly1d([0, self.length])

        if self.parametric_lanes[0].reverse:
            global_distance[:] = [-x for x in global_distance]
        left_vertices, right_vertices = [], []

        last_width_difference = 0
        poses = self._calc_border_positions(precision)
        distance_slope = (global_distance[1] - global_distance[0]) / self.length
        for pos in poses:
            inner_pos = self.calc_border("inner", pos)[0]
            outer_pos = self.calc_border("outer", pos)[0]
            original_width = np.linalg.norm(inner_pos - outer_pos)

            # if not mirroring lane or outside of range
            if (pos < mirror_interval[0] or pos > mirror_interval[1]) and not np.isclose(
                pos, mirror_interval[1]
            ):
                if transformer is not None:
                    left_vertices.append(transformer.transform(inner_pos[0], inner_pos[1]))
                    right_vertices.append(transformer.transform(outer_pos[0], outer_pos[1]))
                else:
                    left_vertices.append(inner_pos)
                    right_vertices.append(outer_pos)
                last_width_difference = 0

            else:
                # calculate positions of adjacent lanelet because new width of lanelet
                # cannot be more than width of adjacent lanelet and original width
                adj_inner_pos = adjacent_lanelet.calc_border("inner", pos)[0]
                adj_outer_pos = adjacent_lanelet.calc_border("outer", pos)[0]
                adjacent_width = np.linalg.norm(adj_inner_pos - adj_outer_pos)
                local_width_offset = distance_slope * pos + global_distance[0]

                if mirror_border == "left":
                    new_outer_pos = self.calc_border("inner", pos, local_width_offset)[0]
                    modified_width = np.linalg.norm(new_outer_pos - inner_pos)

                    # change width s.t. it does not mirror inner border but instead
                    # outer border
                    local_width_offset = (
                        math.copysign(1, local_width_offset) * last_width_difference
                    )
                    if modified_width < original_width:
                        new_vertex = self.calc_border("outer", pos, local_width_offset)[0]
                        if transformer is not None:
                            right_vertices.append(
                                transformer.transform(new_vertex[0], new_vertex[1])
                            )
                        else:
                            right_vertices.append(new_vertex)
                    elif modified_width > original_width + adjacent_width:
                        if transformer is not None:
                            right_vertices.append(
                                transformer.transform(adj_outer_pos[0], adj_outer_pos[1])
                            )
                        else:
                            right_vertices.append(adj_outer_pos)
                    else:
                        if transformer is not None:
                            right_vertices.append(
                                transformer.transform(new_outer_pos[0], new_outer_pos[1])
                            )
                        else:
                            right_vertices.append(new_outer_pos)
                        last_width_difference = abs(modified_width - original_width)

                    if transformer is not None:
                        left_vertices.append(transformer.transform(inner_pos[0], inner_pos[1]))
                    else:
                        left_vertices.append(inner_pos)
                elif mirror_border == "right":
                    new_inner_pos = self.calc_border("outer", pos, local_width_offset)[0]
                    modified_width = np.linalg.norm(new_inner_pos - outer_pos)

                    local_width_offset = (
                        math.copysign(1, local_width_offset) * last_width_difference
                    )
                    if modified_width < original_width:
                        new_vertex = self.calc_border("inner", pos, local_width_offset)[0]
                        if transformer is not None:
                            left_vertices.append(
                                transformer.transform(new_vertex[0], new_vertex[1])
                            )
                        else:
                            left_vertices.append(new_vertex)
                    elif modified_width > original_width + adjacent_width:
                        if transformer is not None:
                            left_vertices.append(
                                transformer.transform(adj_inner_pos[0], adj_inner_pos[1])
                            )
                        else:
                            left_vertices.append(adj_inner_pos)
                    else:
                        if transformer is not None:
                            left_vertices.append(
                                transformer.transform(new_inner_pos[0], new_inner_pos[1])
                            )
                        else:
                            left_vertices.append(new_inner_pos)
                        last_width_difference = abs(modified_width - original_width)

                    if transformer is not None:
                        right_vertices.append(transformer.transform(outer_pos[0], outer_pos[1]))
                    else:
                        right_vertices.append(outer_pos)

        left_vertices, right_vertices = (
            np.array(left_vertices),
            np.array(right_vertices),
        )
        # right_vertices = np.array(right_vertices)

        center_vertices = np.array(
            [(left + right) / 2 for (left, right) in zip(left_vertices, right_vertices)]
        )
        lanelet = ConversionLanelet(
            copy.deepcopy(self), left_vertices, center_vertices, right_vertices, self.id_
        )

        # Adjacent lanes
        self._set_adjacent_lanes(lanelet)

        return lanelet

    def _calc_border_positions(self, precision: float) -> np.ndarray:
        """Determine the positions along the border where the coordinates
        of the border should be calculated.

        :param precision: Number which indicates at which space interval (in curve parameter ds)
                        the coordinates of the boundaries should be calculated.
        :return: Array with the ordered positions.
        """
        poses = np.array([])
        for i, parametric_lane in enumerate(self.parametric_lanes):
            num_steps = int(max(2, np.ceil(parametric_lane.length / float(precision))))
            if not i:
                idx = 0
            else:
                idx = 1

            poses = np.append(
                poses,
                np.linspace(0, parametric_lane.length, num_steps)[idx::] + self._geo_lengths[i],
            )

        return poses

    def _set_adjacent_lanes(self, lanelet: ConversionLanelet, driving_direction: bool = True):
        """
        While converting a ParametricLaneGroup to a Lanelet, set
        the proper attributes relating to adjacent lanes.

        :param lanelet: The lanelet which is created from the ParametricLaneGroup
        :param driving_direction: Driving direction, right if true.
        """
        # check the driving side
        if driving_direction is True:
            # RHT
            if self.inner_neighbour is not None:
                lanelet.adj_left = self.inner_neighbour
                lanelet.adj_left_same_direction = self.inner_neighbour_same_direction

            if self.outer_neighbour is not None:
                lanelet.adj_right = self.outer_neighbour
                lanelet.adj_right_same_direction = True
        else:
            # LHT
            if self.inner_neighbour is not None:
                lanelet.adj_right = self.inner_neighbour
                lanelet.adj_right_same_direction = self.inner_neighbour_same_direction

            if self.outer_neighbour is not None:
                lanelet.adj_left = self.outer_neighbour
                lanelet.adj_left_same_direction = True

    def maximum_width(self) -> float:
        """Get the maximum width of the lanelet.

        :return: Maximum width of all ParametricLanes in this group.
        """
        total_maximum = 0

        for plane in self.parametric_lanes:
            _, maximum = plane.maximum_width()
            if maximum > total_maximum:
                total_maximum = maximum

        return total_maximum

    def first_zero_width_change_position(
        self, reverse: bool = False, reference_width: float = 0.0
    ) -> Tuple[Optional[float], Optional[float]]:
        """Get the earliest point of the ParametricLaneGroup where the width change is zero.

        :param reverse: True if checking should start from end of lanelet. Default is False
        :param reference_width: Width for which width at zero width change position has
                            to be greater as. Default is 0.0.
        :return: Position of ParametricLaneGroup (in curve parameter ds) where width change is zero.
        """
        s_pos = 0
        positions = []

        # total_maximum = self.maximum_width()

        for plane in self.parametric_lanes:
            zero_change_positions = plane.zero_width_change_positions()
            for pos in zero_change_positions:
                positions.append((pos + s_pos, plane.calc_width(pos)))
            s_pos += plane.length

        if reverse:
            positions = list(reversed(positions))

        # if lanelet has zero width change and its width
        # is either near the maximum or it is greater than the reference width
        # the position can be used
        for pos, val in positions:
            if val > 0.9 * reference_width or val > 0.9 * self.maximum_width():
                if (pos == 0.0 and not reverse) or (pos == self.length and reverse):
                    continue
                return pos, val

        return None, None
