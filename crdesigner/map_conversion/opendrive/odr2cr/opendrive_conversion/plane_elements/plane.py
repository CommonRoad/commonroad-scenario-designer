from typing import List, Optional, Tuple

import numpy as np
from numpy.polynomial import polynomial
from pyproj import Transformer

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.plane_elements.border import (
    Border,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    RoadMark,
)


class ParametricLaneBorderGroup:
    """Group Borders and BorderOffsets of ParametricLanes into one class."""

    # NOTE: not checking types with getter/setter because duck typing
    # should be possible
    def __init__(
        self,
        inner_border: Optional[Border] = None,
        inner_border_offset: Optional[float] = None,
        outer_border: Optional[Border] = None,
        outer_border_offset: Optional[float] = None,
    ):
        """Initializes a ParametricLaneBorderGroup object.

        :param inner_border: Inner Border of a ParametricLane
        :param outer_border: Outer Border of a ParametricLane
        :param inner_border_offset: Offset of start of parametric lane to start of border.
                                    This is necessary as a Border can be used by multiple ParametricLanes
        :param outer_border_offset: Same concept as inner_border_offset, but for outer border.
        """
        self.inner_border: Border = inner_border
        self.inner_border_offset = inner_border_offset
        self.outer_border: Border = outer_border
        self.outer_border_offset = outer_border_offset

    def calc_border_position(
        self,
        border: str,
        s_pos: float,
        width_offset: float,
        is_last_pos: bool = False,
        reverse=False,
        compute_curvature: bool = True,
    ) -> Tuple[Tuple[float, float], float]:
        """Calc vertices point of inner or outer Border.

        :param border: Which border to calculate (inner or outer)
        :param s_pos: Position of parameter ds where to calc the cartesian coordinates
        :param width_offset: Offset to add to calculated width in reference to the reference border
        :param is_last_pos: Whether it's the last position, default is False
        :param reverse: Whether to calculate in reverse order
        :param compute_curvature: Whether to computer curvature, default is True
        :return: Cartesian coordinates of point on inner border and tangential direction.
        """
        if border not in ("inner", "outer"):
            raise ValueError("Border specified must be 'inner' or 'outer'!")

        select_border = self.inner_border if border == "inner" else self.outer_border
        select_offset = self.inner_border_offset if border == "inner" else self.outer_border_offset

        return select_border.calc(
            select_offset + s_pos,
            width_offset=width_offset,
            is_last_pos=is_last_pos,
            reverse=reverse,
            compute_curvature=compute_curvature,
        )

    def get_width_coefficients(self) -> List:
        """Get the width coefficients which apply to this ParametricLane.

        :return: The width coefficients in format [a, b, c, distance_from_other_border]
        """
        # TODO: expand implementation to consider border offset record
        return self.outer_border.get_next_width_coeffs(self.outer_border_offset)


class ParametricLane:
    """A lane defines a part of a road along a
    reference trajectory (plan view), using lane borders
    and start/stop positions (parametric)"""

    def __init__(
        self,
        id_: str,
        type_: str,
        border_group: ParametricLaneBorderGroup,
        length: Optional[float] = None,
        line_marking: Optional[RoadMark] = None,
        side: Optional[str] = None,
        speed: Optional[float] = None,
        access: Optional[List] = None,
        driving_direction: bool = True,
    ):
        """Initializes a ParametricLane object.

        :param border_group: Reference to object which manages borders.
        :param id_: Unique string identifier.
        :param type_: Identifies type of ParametricLane
        :param length: Length of ParametricLane, default is None
        :param line_marking: Line marking object. Default is None
        :param side: the side in lane section. Used for determining the line marking side. Default is None
        :param speed: Speed limit for this individual plane
        :param access: equivalent to access restrictions from opendrive lanes
        :param driving_direction: driving direction, right if true
        """
        self.border_group = border_group
        self.id_ = id_
        self.type_ = type_
        self.length = length
        self.reverse = False
        self.line_marking = line_marking
        self.side = side
        self.speed = speed
        self.access = access if access is not None else []
        self.driving_direction = driving_direction

    def calc_border(
        self, border: str, s_pos: float, width_offset: float = 0.0, compute_curvature: bool = True
    ) -> Tuple[Tuple[float, float], float, float, float]:
        """Calc vertices point of inner or outer Border.

        :param border: Which border to calculate (inner or outer).
        :param s_pos: Position of parameter ds where to calc the cartesian coordinates
        :param width_offset: Offset to add to calculated width in reference to the reference border. Default is 0.0.
        :param compute_curvature: Whether to computer curvature. Default is True.
        :return: Cartesian coordinates of point on inner border and tangential direction.
        """
        if self.reverse:
            border_pos = self.length - s_pos
        else:
            border_pos = s_pos

        is_last_pos = np.isclose(self.length, border_pos)
        r1, r2, r3, la = self.border_group.calc_border_position(
            border,
            border_pos,
            width_offset,
            is_last_pos,
            self.reverse,
            compute_curvature=compute_curvature,
        )
        return r1, r2, r3, la

    def calc_width(self, s_pos: float) -> float:
        """Calc width of border at position s_pos.

        :param s_pos: Position of ParametricLane (in curve parameter ds) where width should be calculated.
        :return: The width at position s_pos
        """
        inner_coords = self.calc_border("inner", s_pos)
        outer_coords = self.calc_border("outer", s_pos)

        return np.linalg.norm(inner_coords[0] - outer_coords[0])

    def has_zero_width_everywhere(self) -> bool:
        """Checks if width is zero at every point of this ParametricLaneGroup.

        :return: True if every ParametricLane has width_coefficients equal to only zero.
        """
        # TODO: expand this method to include border offset records
        return self.border_group.get_width_coefficients() == [0, 0, 0, 0]

    # def to_lanelet_with_mirroring(
    #     self,
    #     mirror_border: str,
    #     distance: list,
    #     mirror_interval: list,
    #     precision: float = 0.5,
    # ) -> ConversionLanelet:
    #     """Convert a ParametricLane to Lanelet.

    #     Args:
    #       plane_group: PlaneGroup which should be referenced by created Lanelet.
    #       precision: Number which indicates at which space interval (in curve parameter ds)
    #         the coordinates of the boundaries should be calculated.
    #       mirror_border: Which lane to mirror, if performing merging or splitting of lanes.
    #       distance: Distance at start and end of lanelet, which mirroring lane should
    #         have from the other lane it mirrors.

    #     Returns:
    #        Created Lanelet, with left, center and right vertices and a lanelet_id.

    #     """

    #     num_steps = int(max(3, np.ceil(self.length / float(precision))))

    #     poses = np.linspace(0, self.length, num_steps)

    #     left_vertices = []
    #     right_vertices = []

    #     # width difference between original_width and width with merge algo applied
    #     last_width_difference = distance[2]
    #     distance_slope = (distance[1] - distance[0]) / self.length
    #     # calculate left and right vertices of lanelet
    #     for _, pos in enumerate(poses):
    #         inner_pos = self.calc_border("inner", pos)[0]
    #         outer_pos = self.calc_border("outer", pos)[0]
    #         original_width = np.linalg.norm(inner_pos - outer_pos)

    #         # if not mirroring lane or outside of range
    #         if (
    #             pos < mirror_interval[0] or pos > mirror_interval[1]
    #         ) and not np.isclose(pos, mirror_interval[1]):
    #             left_vertices.append(inner_pos)
    #             right_vertices.append(outer_pos)
    #             last_width_difference = 0

    #         else:
    #             # t = distance[0]

    #             distance_from_other_border = distance_slope * pos + distance[0]

    #             if mirror_border == "left":
    #                 new_outer_pos = self.calc_border(
    #                     "inner", pos, distance_from_other_border
    #                 )[0]
    #                 modified_width = np.linalg.norm(new_outer_pos - inner_pos)

    #                 # change width s.t. it does not mirror inner border but instead
    #                 # outer border
    #                 distance_from_other_border = (
    #                     math.copysign(1, distance_from_other_border)
    #                     * last_width_difference
    #                 )
    #                 if modified_width < original_width:
    #                     right_vertices.append(
    #                         self.calc_border("outer", pos, distance_from_other_border)[
    #                             0
    #                         ]
    #                     )
    #                 else:
    #                     right_vertices.append(new_outer_pos)
    #                     last_width_difference = abs(modified_width - original_width)

    #                 left_vertices.append(inner_pos)
    #             elif mirror_border == "right":
    #                 new_inner_pos = self.calc_border(
    #                     "outer", pos, distance_from_other_border
    #                 )[0]
    #                 modified_width = np.linalg.norm(new_inner_pos - outer_pos)

    #                 distance_from_other_border = (
    #                     math.copysign(1, distance_from_other_border)
    #                     * last_width_difference
    #                 )
    #                 if modified_width < original_width:
    #                     left_vertices.append(
    #                         self.calc_border("inner", pos, distance_from_other_border)[
    #                             0
    #                         ]
    #                     )
    #                 else:
    #                     left_vertices.append(new_inner_pos)
    #                     last_width_difference = abs(modified_width - original_width)

    #                 right_vertices.append(outer_pos)

    #     return (
    #         np.array(left_vertices),
    #         np.array(right_vertices),
    #         last_width_difference,
    #     )

    def calc_vertices(
        self, error_tolerance: float, min_delta_s: float, transformer: Optional[Transformer] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert a ParametricLane to Lanelet.

        :param error_tolerance: Max. error between reference geometry and polyline of vertices.
        :param min_delta_s: Min. step length between two sampling positions on the reference geometry
        :param transformer: Coordinate transformer/projection.
        :return: left and right vertices of the created Lanelet
        """
        left_vertices = []
        right_vertices = []
        # calculate left and right vertices of lanelet
        # s = 0
        # check_3 = True

        # old version from opendrive2lanelet start
        # no sampling of s and "distance" between two consecutive s is similar
        #
        if self.length < 0:
            return np.array(left_vertices), np.array(right_vertices)
        num_steps = int(max(3, np.ceil(self.length / float(0.5))))
        poses = np.linspace(0, self.length, num_steps)
        for s in poses:
            #
            # old version end

            # version with sampling
            # while s <= self.length:
            # s_cache = s + 0.0
            inner_pos, _, curvature, max_geometry_length = self.calc_border("inner", s)
            outer_pos = self.calc_border("outer", s, compute_curvature=False)[0]
            if transformer is not None:
                left_vertices.append(transformer.transform(inner_pos[0], inner_pos[1]))
                right_vertices.append(transformer.transform(outer_pos[0], outer_pos[1]))
            else:
                left_vertices.append(inner_pos)
                right_vertices.append(outer_pos)

            # version with sampling
            # if s >= self.length:
            #     break
            #
            # if s == max_geometry_length:
            #     s += min_delta_s
            # else:
            #     s = calc_next_s(s, curvature, error_tolerance=error_tolerance, min_delta_s=min_delta_s,
            #                     s_max=max_geometry_length)
            #
            # # ensure total road length is not exceeded
            # s = min(self.length, s)
            # # ensure lanelet has >= 3 vertices
            # if check_3 and s >= self.length:
            #     s = (s_cache + self.length) * 0.5
            #
            # check_3 = False
        # assert len(left_vertices) >= 3, f"Not enough vertices, len: {len(left_vertices)}"
        return np.array(left_vertices), np.array(right_vertices)

    def zero_width_change_positions(self) -> float:
        """Position where the inner and outer Border have zero minimal distance change.

        :return: Positions (in curve parameter ds) where width change is zero.
        """

        width_coefficients = self.border_group.get_width_coefficients()
        if width_coefficients[0] > 0.0 and all(coeff == 0.0 for coeff in width_coefficients[1:]):
            # this is not correct as it should be an interval
            return [0, self.length]
        # but useful because only start and end of ParametricLane should be considered

        # get roots of derivative
        roots = polynomial.polyroots(polynomial.polyder(width_coefficients))
        real_roots = roots[(np.isreal(roots)) & (roots >= 0) & (roots <= self.length)]
        if self.reverse:
            real_roots[:] = [self.length - x for x in real_roots]
        return real_roots

    def maximum_width(self, reverse: bool = False) -> Tuple[float, float]:
        """Get position and value of maximum width.
        Position is the distance of the maximum to the start or end
        of ParametricLane (end if reverse==True).

        :param reverse: If True and there are two equal maxima, take maxima closer to the end of the ParametricLane.
                        Default is False.
        :return: (pos, max) tuple of position and value of maximum
        """
        width_coefficients = self.border_group.get_width_coefficients()
        width_derivative = polynomial.polyder(width_coefficients)
        # width_second_derivative = P.polyder(width_derivative)
        roots = polynomial.polyroots(width_derivative)
        # is_local_maximum = P.polyval(roots, width_second_derivative) < 0
        restricted_roots = roots[
            (np.isreal(roots))
            & (roots >= 0)
            # & (is_local_maximum)
            & (roots <= self.length)
        ]

        # append start and end of ParametricLane because maximum could be there, too
        restricted_roots = np.append(restricted_roots, [0, self.length])

        # calculate maximum values
        max_values = polynomial.polyval(restricted_roots, width_coefficients)

        # width of one ParametricLane is either always positive or negative
        max_values = abs(max_values)
        pos_and_val = np.column_stack((restricted_roots, max_values))
        if self.reverse:
            pos_and_val = np.array([[self.length - x[0], x[1]] for x in pos_and_val])

        # sort by position
        if reverse:
            # pos_and_val[:] = pos_and_val[::-1]
            pos_and_val = pos_and_val[pos_and_val[:, 0].argsort()[::-1]]
        else:
            pos_and_val = pos_and_val[pos_and_val[:, 0].argsort()]

        max_idx = np.argmax(pos_and_val, axis=0)[1]
        return tuple(pos_and_val[max_idx])
