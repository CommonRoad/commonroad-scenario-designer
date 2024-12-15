import logging
from typing import Optional, Set, Tuple, Union

import numpy as np
from commonroad.scenario.lanelet import Lanelet, LaneletType, LineMarking, RoadUser
from pyproj import Transformer

from crdesigner.common.config.opendrive_config import OpenDriveConfig, open_drive_config


class ConversionLanelet(Lanelet):
    """Change some properties of the Lanelet class so that it can be used to conversions to Lanelet. This means
    especially that lanelet_ids can be other types than a natural number and that these ids can be changed
    more than once. Adjacent neighbors and pre- and successor can be changed more than once.
    This class is being used in Opendrive and Lanelet2 format conversions
    """

    # optimal_join_split_factor = 20

    def __init__(
        self,
        parametric_lane_group,
        left_vertices: np.ndarray,
        center_vertices: np.ndarray,
        right_vertices: np.ndarray,
        lanelet_id,
        predecessor=None,
        successor=None,
        adjacent_left=None,
        adjacent_left_same_direction=None,
        adjacent_right=None,
        adjacent_right_same_direction=None,
        line_marking_left_vertices=LineMarking.UNKNOWN,
        line_marking_right_vertices=LineMarking.UNKNOWN,
        stop_line=None,
        lanelet_type=None,
        user_one_way=None,
        user_bidirectional=None,
        traffic_signs=None,
        traffic_lights=None,
        speed=None,
        config: OpenDriveConfig = open_drive_config,
    ):
        if lanelet_type is None:
            lanelet_type = {LaneletType.UNKNOWN}
        self.parametric_lane_group = parametric_lane_group
        self._default_lanelet_type = (
            {
                (
                    LaneletType(config.general_lanelet_type)
                    if LaneletType(config.general_lanelet_type) is not None
                    else LaneletType.UNKNOWN
                )
            }
            if config.general_lanelet_type_activ
            else set()
        )
        self._driving_default_lanelet_type = (
            LaneletType(config.driving_default_lanelet_type)
            if LaneletType(config.driving_default_lanelet_type) is not None
            else LaneletType.UNKNOWN
        )
        self._lanelet_types_backwards_compatible = config.lanelet_types_backwards_compatible
        _user_bidirectional = None
        _user_one_way = None
        if user_one_way is not None:
            _user_one_way = set(map(lambda x: RoadUser(x), user_one_way))
        if user_bidirectional is not None:
            _user_bidirectional = set(map(lambda x: RoadUser(x), user_bidirectional))

        super().__init__(
            left_vertices=left_vertices,
            center_vertices=center_vertices,
            right_vertices=right_vertices,
            lanelet_id=lanelet_id,
            predecessor=predecessor,
            successor=successor,
            adjacent_left=adjacent_left,
            adjacent_left_same_direction=adjacent_left_same_direction,
            adjacent_right=adjacent_right,
            adjacent_right_same_direction=adjacent_right_same_direction,
            line_marking_left_vertices=line_marking_left_vertices,
            line_marking_right_vertices=line_marking_right_vertices,
            stop_line=stop_line,
            lanelet_type=lanelet_type,
            user_one_way=_user_one_way,
            user_bidirectional=_user_bidirectional,
            traffic_signs=traffic_signs,
            traffic_lights=traffic_lights,
        )

        self.speed = speed

    def __eq__(self, lanelet: "ConversionLanelet") -> bool:
        """Lanelets are equal if their id_ is equal.

        :param lanelet: Lanelet to be compared to equality
        :return: True if id_ is equal
        """
        if lanelet is None:
            return False
        return self.lanelet_id == lanelet.lanelet_id

    """
    Only type supported by commonroad_io is recorded here;
    waiting for future development
    """

    @property
    def lanelet_type(self) -> Set[LaneletType]:
        """Get the lanelet type

        :return: The lanelet type.
        """
        return self._lanelet_type

    @lanelet_type.setter
    def lanelet_type(self, value: str):
        if value in [
            "urban",
            "country",
            "highway",
            "interstate",
            "parking",
            "sidewalk",
            "crosswalk",
        ]:
            self._lanelet_type = {
                LaneletType(value) if LaneletType(value) is not None else LaneletType.UNKNOWN
            }
        elif value in ["restricted", "mainCarriageWay", "intersection"]:
            self._lanelet_type = {
                LaneletType(value) if LaneletType(value) is not None else LaneletType.UNKNOWN
            }.union(self._default_lanelet_type)
        elif value == "entry":
            self._lanelet_type = {LaneletType.ACCESS_RAMP}.union(self._default_lanelet_type)
        elif value == "exit":
            self._lanelet_type = {LaneletType.EXIT_RAMP}.union(self._default_lanelet_type)
        elif value == "onRamp":
            self._lanelet_type = {LaneletType.ACCESS_RAMP}.union(self._default_lanelet_type)
        elif value == "offRamp":
            self._lanelet_type = {LaneletType.EXIT_RAMP}.union(self._default_lanelet_type)
        elif value == "connectingRamp":
            self._lanelet_type = {LaneletType.ACCESS_RAMP}.union(self._default_lanelet_type)
        elif value == "shoulder":
            if self._lanelet_types_backwards_compatible:
                self._lanelet_type = set()
            else:
                self._lanelet_type = {LaneletType.BORDER}
        elif value == "border":
            if self._lanelet_types_backwards_compatible:
                self._lanelet_type = set()
            else:
                self._lanelet_type = {LaneletType.BORDER}
        elif value == "bus":
            self._lanelet_type = {LaneletType.BUS_LANE}.union(self._default_lanelet_type)
        elif value == "stop":
            self._lanelet_type = {LaneletType.SHOULDER}.union(self._default_lanelet_type)
        elif value == "biking":
            self._lanelet_type = {LaneletType.BICYCLE_LANE}
        elif value == "driving":
            self._lanelet_type = {LaneletType(self._driving_default_lanelet_type)}
        else:
            logging.warning("ConversionLanelet::lanelet_type: Unknown lane type: {}".format(value))
            self._lanelet_type = {LaneletType(self._driving_default_lanelet_type)}

    @property
    def lanelet_id(self) -> int:
        """Get or set id of this lanelet.

        :return: The ID of the lanelet.
        """
        return self._lanelet_id

    @lanelet_id.setter
    def lanelet_id(self, l_id: int):
        # pylint: disable=W0201
        self._lanelet_id = l_id

    @property
    def left_vertices(self) -> np.ndarray:
        """Get or set right vertices of this lanelet.

        :return: The left vertices of the lanelet.
        """
        return self._left_vertices

    @left_vertices.setter
    def left_vertices(self, polyline: np.ndarray):
        # pylint: disable=W0201
        self._left_vertices = polyline

    @property
    def right_vertices(self) -> np.ndarray:
        """Get or set right vertices of this lanelet.

        :return: The right vertices of the lanelet.
        """
        return self._right_vertices

    @right_vertices.setter
    def right_vertices(self, polyline: np.ndarray):
        # pylint: disable=W0201
        self._right_vertices = polyline

    @property
    def center_vertices(self) -> np.ndarray:
        """Get or set center vertices of this lanelet.

        :return: The center vertices of the lanelet.
        """
        return self._center_vertices

    @center_vertices.setter
    def center_vertices(self, polyline: np.ndarray):
        # pylint: disable=W0201
        self._center_vertices = polyline

    @property
    def predecessor(self) -> list:
        """Set or get the predecessor.

        :return: A list with IDs of the predecessors.
        """
        return self._predecessor

    @predecessor.setter
    def predecessor(self, predecessor: list):
        # pylint: disable=W0201
        self._predecessor = predecessor

    @property
    def successor(self) -> list:
        """Set or get the successor.

        :return: A list with IDs of the successors.
        """
        return self._successor

    @successor.setter
    def successor(self, successor: list):
        # pylint: disable=W0201
        self._successor = successor

    @property
    def adj_left(self) -> int:
        """Set or get adjacent left lanelet.

        :return: The ID of the left adjacent lanelet.
        """
        return self._adj_left

    @adj_left.setter
    def adj_left(self, l_id: int):
        # pylint: disable=W0201
        self._adj_left = l_id

    @property
    def adj_left_same_direction(self) -> bool:
        """Set or get if adjacent left lanelet has the same direction
        as this lanelet.

        :return: Whether the left adjacent lanelet has the same direction.
        """
        return self._adj_left_same_direction

    @adj_left_same_direction.setter
    def adj_left_same_direction(self, same: bool):
        # pylint: disable=W0201
        self._adj_left_same_direction = same

    @property
    def adj_right(self) -> int:
        """Set or get adjacent right lanelet.

        :return: The ID of the right adjacent lanelet.
        """
        return self._adj_right

    @adj_right.setter
    def adj_right(self, l_id: int):
        self._adj_right = l_id

    @property
    def adj_right_same_direction(self) -> bool:
        """Set or get if adjacent right lanelet has the same direction
        as this lanelet.

        :return: Whether the right adjacent lanelet has the same direction.
        """
        return self._adj_right_same_direction

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, s):
        self._speed = s

    @adj_right_same_direction.setter
    def adj_right_same_direction(self, same: bool):
        # pylint: disable=W0201
        self._adj_right_same_direction = same

    def concatenate(self, lanelet_conc: "ConversionLanelet", extend_plane_group: bool = True):
        """Concatenate this lanelet with lanelet_conc and assign the
        new lanelet_id to the resulting lanelet.

        :param lanelet_conc: Lanelet which will be included.
        :param extend_plane_group: Whether to extend the parametric_lane_group of this lanelet with the parametric lanes
            of the lanelet_conc.parametric_lane_group. Default is True.
        """
        # check connectedness
        if np.isclose(self.left_vertices[-1], lanelet_conc.left_vertices[0]).all():
            idx = 1
        else:
            idx = 0

        self.left_vertices = np.vstack((self.left_vertices, lanelet_conc.left_vertices[idx:]))
        self.center_vertices = np.vstack((self.center_vertices, lanelet_conc.center_vertices[idx:]))
        self.right_vertices = np.vstack((self.right_vertices, lanelet_conc.right_vertices[idx:]))
        if extend_plane_group:
            self.parametric_lane_group.extend(lanelet_conc.parametric_lane_group.parametric_lanes)
        self.successor = lanelet_conc.successor.copy()

    def calc_width_at_end(self) -> float:
        """Calc width of lanelet at its end.

        :return: Width at end of lanelet
        """
        return self.calc_width(self.length)

    def calc_width_at_start(self) -> float:
        """Calc width of lanelet at its start.

        :return: Width at start of lanelet
        """
        return self.calc_width(0)

    def calc_width(self, s_pos: float) -> float:
        """Calc width at position s_pos.

        :param s_pos: Position in curve parameter ds
        :return: Width at position s_pos
        """
        inner_pos = self.calc_border("inner", s_pos)[0]
        outer_pos = self.calc_border("outer", s_pos)[0]
        return np.linalg.norm(inner_pos - outer_pos)

    @property
    def length(self) -> float:
        """Get length of lanelet by calculating length of ParametricLaneGroup.

        :return: Length of lanelet
        """
        return self.parametric_lane_group.length

    def has_zero_width_everywhere(self) -> bool:
        """Checks if width is zero at every point of its ParametricLaneGroup.

        :return: True if every ParametricLane has width_coefficients equal to only zero.
        """
        return self.parametric_lane_group.has_zero_width_everywhere()

    def first_zero_width_change_position(
        self, reverse: bool = False, reference_width: float = 0.0
    ) -> Tuple[Optional[float], Optional[float]]:
        """Get the earliest point of the lanelet where the width change is zero.

        :param reverse: True if checking start from the end of the lanelet
        :param reference_width: Width for which width at zero width change position has to be greater as
        :return: Position of lanelet (in curve parameter ds) where width change is zero.
        """
        return self.parametric_lane_group.first_zero_width_change_position(reverse, reference_width)

    def maximum_width(self) -> float:
        """Get width by calculating maximum width of parametric lane group.

        :return: Maximum width of lanelet
        """
        return self.parametric_lane_group.maximum_width()

    def optimal_join_split_values(
        self, is_split: bool, split_and_join: bool, reference_width: float
    ) -> Tuple[Union[float, int], float]:
        """Calculate an optimal value, where the lanelet split or join starts or ends, respectively.

        :param is_split: True if lanelet splits from another lanelet, otherwise False if it is a join
        :param split_and_join: True if lanelet has a split at the start and join at the end.
        :param reference_width: Width for which width at zero width change position has to be greater as
        :return: The merge position and merge width.
        """

        merge_pos, merge_width = self.first_zero_width_change_position(
            reverse=(not is_split), reference_width=reference_width
        )
        if merge_pos is None:
            merge_pos = self.length if is_split else 0
            # merge_width = self.calc_width(merge_pos)

        if is_split:
            # if both a split at the start and merge at the end
            if split_and_join and merge_pos > 0.5 * self.length:
                merge_pos = 0.45 * self.length

        else:
            if split_and_join and merge_pos < 0.5 * self.length:
                merge_pos = 0.55 * self.length

        merge_width = self.calc_width(merge_pos)
        return merge_pos, merge_width

    def move_border(
        self,
        mirror_border: str,
        mirror_interval: Tuple[float, float],
        distance: np.ndarray,
        adjacent_lanelet: "ConversionLanelet",
        precision: float,
        transformer: Transformer,
    ):
        """Move vertices of one border by mirroring other border with
        a specified distance.

        :param mirror_border: Which border to mirror, either 'left' or 'right'.
        :param mirror_interval: Tuple of two values, specifying start and end of mirroring.
        :param distance: Specifying distance at start and at end of mirroring
        :param adjacent_lanelet: The adjacent conversion lanelet.
        :param precision: Specifies precision with which to convert the plane group to lanelet w. mirroring
        :param transformer: Coordinate projection transformer.
        """
        if mirror_border == "left":
            distance[:] = [-1 * x for x in distance]

        lanelet = self.parametric_lane_group.to_lanelet_with_mirroring(
            transformer=transformer,
            mirror_border=mirror_border,
            distance=distance,
            mirror_interval=mirror_interval,
            adjacent_lanelet=adjacent_lanelet,
            precision=precision,
        )

        self.left_vertices = lanelet.left_vertices
        self.center_vertices = lanelet.center_vertices
        self.right_vertices = lanelet.right_vertices

    def calc_border(
        self, border: str, s_pos: float, width_offset: float = 0.0, compute_curvature=True
    ) -> Tuple[Tuple[float, float], float, float, float]:
        """
        Calc border position according to parametric_lane_group. Note: This does not consider borders which have been
        moved due to joining / splitting.

        :param border: Which border to calculate (inner or outer):
        :param s_pos: Position of parameter ds where to calc the cartesian coordinates
        :param width_offset: Offset to add to calculated width in reference to the reference border, default is 0.0.
        :param compute_curvature: Boolean indicating whether curvature should be computed
        :return: Cartesian coordinates of point on inner border and tangential direction.
        """
        return self.parametric_lane_group.calc_border(
            border, s_pos, width_offset, compute_curvature=compute_curvature
        )
