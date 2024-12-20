import warnings
from typing import List, Tuple, Union

import numpy as np

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.geometry import (
    Arc,
    Geometry,
    Line,
    ParamPoly3,
    Poly3,
    Spiral,
    calc_next_s,
)


class PlanView:
    """
    The plan view record contains a series of geometry records
    which define the layout of the road's
    reference line in the x/y-plane (plan view).

    (Section 5.3.4 of OpenDRIVE 1.4)

    :ivar _geometries: list of geometries describing the road reference line
    :ivar _precalculation: precalculated coordinates of planview
    :ivar should_precalculate: describes whether precalculation should be done or not
    :ivar _geo_lengths: list of positions of the geometries defined for the road
    :ivar _error_tolerance_s: max. error for computing next longitudinal sampling position
    :ivar _min_delta_s: minimal step length to avoid getting stuck for computing next longitudinal sampling position
    """

    def __init__(self, error_tolerance_s=0.2, min_delta_s=0.3):
        self._geometries: List[Geometry] = []
        self._precalculation = None
        self.should_precalculate = 0
        self._geo_lengths = np.array([0.0])
        self._error_tolerance_s = error_tolerance_s
        self._min_delta_s = min_delta_s

    def _add_geometry(self, geometry: Geometry, should_precalculate: bool):
        """
        Adds a geometry to the _geometries list and extends the _geo_lengths list.

        :param geometry: instance of Geometry()
        :param should_precalculate: decides whether a precalculation for reducing memory and computation should be
            applied
        """
        self._geometries.append(geometry)
        if should_precalculate:
            self.should_precalculate += 1
        else:
            self.should_precalculate -= 1
        self._add_geo_length(geometry.length)

    def add_line(self, start_pos: np.ndarray, heading: float, length: float):
        """
        Calls _add_geometry for Line elements.

        :param start_pos: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        """
        self._add_geometry(Line(start_pos, heading, length), False)

    def add_spiral(
        self,
        start_pos: np.ndarray,
        heading: float,
        length: float,
        curv_start: float,
        curv_end: float,
    ):
        """
        Calls _add_geometry for Spiral elements.

        :param start_pos: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param curv_start: curvature at the start of the spiral
        :param curv_end: curvature at the end of the spiral
        """
        self._add_geometry(Spiral(start_pos, heading, length, curv_start, curv_end), True)

    def add_arc(self, start_pos: np.ndarray, heading: float, length: float, curvature: float):
        """
        Calls _add_geometry for Arc elements.

        :param start_pos: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param curvature: (constant) curvature of the arc
        """
        self._add_geometry(Arc(start_pos, heading, length, curvature), True)

    def add_param_poly3(
        self,
        start_pos: np.ndarray,
        heading: float,
        length: float,
        aU: float,
        bU: float,
        cU: float,
        dU: float,
        aV: float,
        bV: float,
        cV: float,
        dV: float,
        pRange: float,
    ):
        """
        Calls _add_geometry for ParamPoly3 elements.

        :param start_pos: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param aU: parameter a for u
        :param bU: parameter b for u
        :param cU: parameter c for u
        :param dU: parameter d for u
        :param aV: parameter a for v
        :param bV: parameter b for v
        :param cV: parameter c for v
        :param dV: parameter d for v
        :param pRange: range of p;
            case type=arcLength -> p in [0, length of geometry]
            case type=normalized -> p in [0, 1]
        """
        self._add_geometry(
            ParamPoly3(start_pos, heading, length, aU, bU, cU, dU, aV, bV, cV, dV, pRange),
            True,
        )

    def add_poly3(
        self,
        start_pos: np.ndarray,
        heading: float,
        length: float,
        a: float,
        b: float,
        c: float,
        d: float,
    ):
        """
        Calls _add_geometry for Poly3 elements.

        :param start_pos: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param a: a of polynom
        :param b: b of polynom
        :param c: c of polynom
        :param d: d of polynom
        """
        self._add_geometry(Poly3(start_pos, heading, length, a, b, c, d), True)

    def _add_geo_length(self, length: float):
        """
        Add length of a geometry to the array which keeps track at which position
        which geometry is placed. This array is used for quickly accessing the proper geometry
        for calculating a position.

        :param length: length of the geometry which is added
        """
        self._geo_lengths = np.append(self._geo_lengths, length + self._geo_lengths[-1])

    @property
    def length(self) -> float:
        """
        Get length of whole plan view.
        """
        return self._geo_lengths[-1]

    def calc(
        self, s_pos: float, compute_curvature: bool = True, reverse: bool = True
    ) -> Tuple[np.ndarray, float, float, Union[None, float]]:
        """
        Calculate position, tangent, curvature and max. length of the geometry at s_pos.
        Either interpolate values if possible or delegate calculation to geometries.

        :param s_pos: position on PlanView in ds
        :param compute_curvature: decides whether curvature should be calculated
        :param reverse: decides whether order of geometry positions should be reversed
        :return: x and y position, orientation, curvature and max. possible residual length of the geometry in the
            form ([x, y], orientation, curvature, max_geometry_length)
        """

        # if self._precalculation is not None:
        #     # interpolate values
        #     return self.interpolate_cached_values(s_pos)

        # start = time.time()
        result_pos, result_tang, curv, max_geometry_length = self.calc_geometry(
            s_pos, compute_curvature, reverse
        )
        # end = time.time()
        # self.normal_time += end - start
        return result_pos, result_tang, curv, max_geometry_length

    def interpolate_cached_values(self, s_pos: float) -> Tuple[np.ndarray, float, None]:
        """
        Calc position and tangent at s_pos by interpolating values in _precalculation array.
        Function is not used at the moment.

        :param s_pos: position on PlanView in ds
        :return: position (x,y) in cartesion coordinates and angle in radians at position s
        """
        warnings.warn(
            "Function interpolate_cached_calues is not used at the moment. There are some lines commented"
            " with # which used the function in earlier versions.",
            DeprecationWarning,
        )
        # start = time.time()
        # we need idx for angle interpolation
        # so idx can be used anyway in the other np.interp function calls
        idx = np.abs(self._precalculation[:, 0] - s_pos).argmin()
        if s_pos - self._precalculation[idx, 0] < 0 or idx + 1 == len(self._precalculation):
            idx -= 1

        result_pos_x = np.interp(
            s_pos,
            self._precalculation[idx : idx + 2, 0],
            self._precalculation[idx : idx + 2, 1],
        )

        result_pos_y = np.interp(
            s_pos,
            self._precalculation[idx : idx + 2, 0],
            self._precalculation[idx : idx + 2, 2],
        )
        result_tang = self.interpolate_angle(idx, s_pos)
        result_pos = np.array((result_pos_x, result_pos_y))
        # end = time.time()
        # self.cache_time += end - start
        return result_pos, result_tang, None

    def interpolate_angle(self, idx: int, s_pos: float) -> float:
        """
        Interpolate two angular values using the shortest angle between both values.
        Function is not called in this version.

        :param idx: index of values in _precalculation
        :param s_pos: position at which an interpolated angle should be calculated
        :return: interpolated angle in radians
        """
        warnings.warn(
            "Function interpolate_cached_calues is not used at the moment. There are some lines commented"
            " with # which used the function in earlier versions.",
            DeprecationWarning,
        )
        angle_prev = self._precalculation[idx, 3]
        angle_next = self._precalculation[idx + 1, 3]
        pos_prev = self._precalculation[idx, 0]
        pos_next = self._precalculation[idx + 1, 0]

        shortest_angle = ((angle_next - angle_prev) + np.pi) % (2 * np.pi) - np.pi
        return angle_prev + shortest_angle * (s_pos - pos_prev) / (pos_next - pos_prev)

    def calc_geometry(
        self, s_pos: float, compute_curvature=True, reverse=False
    ) -> Tuple[np.ndarray, float, Union[None, float], float]:
        """
        Calc position and tangent at s_pos by delegating calculation to geometry.

        :param s_pos: position on geometry to calculate position in cartesian coordinates and tangent from
        :param compute_curvature: decides whether curvature should be calculated
        :param reverse: defines if order of geometries is reversed (opposite lane direction)
        :return: x and y position, orientation, curvature and max. possible residual length of the geometry in the
            form ([x, y], orientation, curvature, max_length_geometry)
        """
        try:
            # get index of geometry which is at s_pos
            mask = self._geo_lengths > s_pos
            sub_idx = np.argmin(self._geo_lengths[mask] - s_pos)
            geo_idx = np.arange(self._geo_lengths.shape[0])[mask][sub_idx] - 1
        except ValueError:
            # s_pos is after last geometry because of rounding error
            if np.isclose(s_pos, self._geo_lengths[-1], 0.01, 0.01):  # todo parameter
                geo_idx = self._geo_lengths.size - 2
            else:
                raise Exception(
                    f"Tried to calculate a position outside of the borders of the reference path at s={s_pos}"
                    f", but path has only length of l={ self._geo_lengths[-1]}"
                )

        if reverse:
            max_s_geometry = self.length - self._geo_lengths[geo_idx]
        else:
            max_s_geometry = self._geo_lengths[geo_idx + 1]
        # geo_idx is index which geometry to use
        return self._geometries[geo_idx].calc_position(
            s_pos - self._geo_lengths[geo_idx], compute_curvature=compute_curvature
        ) + (max_s_geometry,)

    def precalculate(self):
        """
        Precalculate coordinates of planView to save computing resources and time.
        Save result in _precalculation array.
        """
        warnings.warn(
            "Function precalculate is called but its results are stored in the variable _precalculation "
            "which is not used at the moment. It is called in the interpolation functions, which are not "
            "called.",
            DeprecationWarning,
        )

        # start = time.time()
        # this threshold was determined by quick prototyping tests
        # (trying different numbers and minimizing runtime)
        if self.should_precalculate < 1:
            return

        _precalculation = []
        s = 0
        # i = 0
        while s <= self.length:
            coord, tang, curv, remaining_length = self.calc_geometry(s)
            _precalculation.append([s, coord[0], coord[1], tang])
            if s >= self.length:
                break

            if s == remaining_length:
                s += self._min_delta_s
            else:
                s = calc_next_s(
                    s, curv, self._error_tolerance_s, self._min_delta_s, remaining_length
                )
            s = min(self.length, s)
            # i += 1

        self._precalculation = np.array(_precalculation)
