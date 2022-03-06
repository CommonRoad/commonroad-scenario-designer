import math
from typing import Tuple, List, Union

import matplotlib.pyplot as plt
import numpy as np

from crdesigner.map_conversion.opendrive.opendrive_parser.elements.geometry import (
    Geometry,
    Line,
    Spiral,
    ParamPoly3,
    Arc,
    Poly3, CurvatureRes, calc_next_s,
)


__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class PlanView:
    """The plan view record contains a series of geometry records
    which define the layout of the road's
    reference line in the x/y-plane (plan view).

    (Section 5.3.4 of OpenDRIVE 1.4)
    """

    def __init__(self, error_tolerance_s=0.2, min_delta_s=0.3):
        self._geometries: List[Geometry] = []
        self._precalculation = None
        self.should_precalculate = 0
        self._geo_lengths = np.array([0.0])
        self.cache_time = 0
        self.normal_time = 0
        self._error_tolerance_s = error_tolerance_s
        self._min_delta_s = min_delta_s

    def _add_geometry(self, geometry: Geometry, should_precalculate: bool):
        """

        Args:
          geometry:
          should_precalculate:

        """
        self._geometries.append(geometry)
        if should_precalculate:
            self.should_precalculate += 1
        else:
            self.should_precalculate -= 1
        self._add_geo_length(geometry.length)

    def addLine(self, start_pos, heading, length):
        """

        Args:
          start_pos:
          heading:
          length:

        """
        self._add_geometry(Line(start_pos, heading, length), False)

    def addSpiral(self, start_pos, heading, length, curvStart, curvEnd):
        """

        Args:
          start_pos:
          heading:
          length:
          curvStart:
          curvEnd:

        """
        self._add_geometry(Spiral(start_pos, heading, length, curvStart, curvEnd), True)

    def addArc(self, start_pos, heading, length, curvature):
        """

        Args:
          start_pos:
          heading:
          length:
          curvature:

        """
        self._add_geometry(Arc(start_pos, heading, length, curvature), True)

    def addParamPoly3(
        self, start_pos, heading, length, aU, bU, cU, dU, aV, bV, cV, dV, pRange
    ):
        """

        Args:
          start_pos:
          heading:
          length:
          aU:
          bU:
          cU:
          dU:
          aV:
          bV:
          cV:
          dV:
          pRange:

        """
        self._add_geometry(
            ParamPoly3(
                start_pos, heading, length, aU, bU, cU, dU, aV, bV, cV, dV, pRange
            ),
            True,
        )

    def addPoly3(self, start_pos, heading, length, a, b, c, d):
        """

        Args:
          start_pos:
          heading:
          length:
          a:
          b:
          c:
          d:
        """
        self._add_geometry(Poly3(start_pos, heading, length, a, b, c, d), True)

    def _add_geo_length(self, length: float):
        """Add length of a geometry to the array which keeps track at which position
        which geometry is placed. This array is used for quickly accessing the proper geometry
        for calculating a position.

        Args:
          length: Length of geometry to be added.

        """

        self._geo_lengths = np.append(self._geo_lengths, length + self._geo_lengths[-1])
        # print("Adding geo length",self._geo_lengths)

    @property
    def length(self) -> float:
        """Get length of whole plan view"""

        return self._geo_lengths[-1]

    def calc(self, s_pos: float, compute_curvature=True, reverse=True) -> Tuple[np.ndarray, float, Union[None, float]]:
        """Calculate position and tangent at s_pos.

        Either interpolate values if it possible or delegate calculation
        to geometries.

        Args:
          s_pos: Position on PlanView in ds.

        Returns:
          Position (x,y) in cartesion coordinates.
          Angle in radians at position s_pos.
        """

        # if self._precalculation is not None:
        #     # interpolate values
        #     return self.interpolate_cached_values(s_pos)

        # start = time.time()
        result_pos, result_tang, curv, max_geometry_length = self.calc_geometry(s_pos, compute_curvature, reverse)
        # end = time.time()
        # self.normal_time += end - start
        return result_pos, result_tang, curv, max_geometry_length

    def interpolate_cached_values(self, s_pos: float) -> Tuple[np.ndarray, float, None]:
        """Calc position and tangent at s_pos by interpolating values
        in _precalculation array.

        Args:
          s_pos: Position on PlanView in ds.

        Returns:
          Position (x,y) in cartesion coordinates.
          Angle in radians at position s_pos.

        """
        # start = time.time()
        # we need idx for angle interpolation
        # so idx can be used anyway in the other np.interp function calls
        idx = np.abs(self._precalculation[:, 0] - s_pos).argmin()
        if s_pos - self._precalculation[idx, 0] < 0 or idx + 1 == len(self._precalculation):
            idx -= 1

        result_pos_x = np.interp(s_pos, self._precalculation[idx: idx + 2, 0], self._precalculation[idx: idx + 2, 1],)

        result_pos_y = np.interp(s_pos, self._precalculation[idx: idx + 2, 0], self._precalculation[idx: idx + 2, 2],)
        result_tang = self.interpolate_angle(idx, s_pos)
        result_pos = np.array((result_pos_x, result_pos_y))
        # end = time.time()
        # self.cache_time += end - start
        return result_pos, result_tang, None

    def interpolate_angle(self, idx: int, s_pos: float) -> float:
        """Interpolate two angular values using the shortest angle between both values.

        Args:
          idx: Index where values in _precalculation should be accessed.
          s_pos: Position at which interpolated angle should be calculated.

        Returns:
          Interpolated angle in radians.

        """
        angle_prev = self._precalculation[idx, 3]
        angle_next = self._precalculation[idx + 1, 3]
        pos_prev = self._precalculation[idx, 0]
        pos_next = self._precalculation[idx + 1, 0]

        shortest_angle = ((angle_next - angle_prev) + np.pi) % (2 * np.pi) - np.pi
        return angle_prev + shortest_angle * (s_pos - pos_prev) / (pos_next - pos_prev)

    def calc_geometry(self, s_pos: float, compute_curvature=True, reverse=False) \
            -> Tuple[np.ndarray, float, Union[None, float], float]:
        """Calc position and tangent at s_pos by delegating calculation to geometry.

        Args:
          s_pos: Position on PlanView in ds.

        Returns:
          Position (x,y) in cartesion coordinates.
          Angle in radians at position s_pos.

        """
        try:
            # get index of geometry which is at s_pos
            mask = self._geo_lengths > s_pos
            sub_idx = np.argmin(self._geo_lengths[mask] - s_pos)
            geo_idx = np.arange(self._geo_lengths.shape[0])[mask][sub_idx] - 1
        except ValueError:
            # s_pos is after last geometry because of rounding error
            if np.isclose(s_pos, self._geo_lengths[-1]):
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
            s_pos - self._geo_lengths[geo_idx], compute_curvature=compute_curvature) + (max_s_geometry,)

    def precalculate(self):
        """Precalculate coordinates of planView to save computing resources and time.
        Save result in _precalculation array.

        Args:
        """

#        print("Checking required lanelet mesh", self._geo_lengths)

        # start = time.time()
        # this threshold was determined by quick prototyping tests
        # (trying different numbers and minimizing runtime)
        if self.should_precalculate < 1:
            return

        # print("Checking required lanelet mesh", self._geo_lengths, num_steps)
        _precalculation = []
        s = 0
        i = 0
        while s <= self.length:
            coord, tang, curv, remaining_length = self.calc_geometry(s)
            _precalculation.append([s, coord[0], coord[1], tang])
            if s >= self.length:
                break

            if s == remaining_length:
                s += self._min_delta_s
            else:
                s = calc_next_s(s, curv, self._error_tolerance_s, self._min_delta_s, remaining_length)
            s = min(self.length, s)
            i += 1

        self._precalculation = np.array(_precalculation)
        # plt.figure()
        # plt.plot(self._precalculation[:,1], self._precalculation[:,2])
        # plt.axis("equal")
        # plt.show(block=True)
