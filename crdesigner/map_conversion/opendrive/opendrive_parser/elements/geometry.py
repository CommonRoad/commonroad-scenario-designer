import abc
import math
from enum import IntEnum
from typing import Tuple

import numpy as np
import scipy.optimize
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.eulerspiral import EulerSpiral

__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class CurvatureRes(IntEnum):
    CONST_ZERO = 0


class Geometry(abc.ABC):
    """A road geometry record defines the layout of the road's reference
    line in the in the x/y-plane (plan view).

    The geometry information is split into a header which is common to all geometric elements.

    (Section 5.3.4.1 of OpenDRIVE 1.4)
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, start_position: float, heading: float, length: float):
        self._start_position = np.array(start_position)
        self._length = length
        self._heading = heading

    @property
    def start_position(self) -> np.ndarray:
        """Returns the overall geometry start position"""
        return self._start_position

    @property
    def length(self) -> float:
        """Returns the overall geometry length"""
        return self._length

    @property
    def heading(self) -> float:
        """Get heading of geometry.

        Returns:
          Heading, in which direction the geometry heads at start.
        """
        return self._heading

    @abc.abstractmethod
    def calc_position(self, s_pos, compute_curvature=True) -> Tuple[np.ndarray, np.ndarray, float]:
        """Calculates the position of the geometry as if the starting point is (0/0)

        Args:
          s_pos:
          compute_curvature: computes curvature, otherwise returns None

        Returns:

        """
        return


class Line(Geometry):
    """This record describes a straight line as part of the road’s reference line.


    (Section 5.3.4.1.1 of OpenDRIVE 1.4)
    """

    def calc_position(self, s_pos, compute_curvature=True):
        """

        Args:
          s_pos:

        Returns:
        :param compute_curvature:

        """
        pos = self.start_position + np.array(
            [s_pos * np.cos(self.heading), s_pos * np.sin(self.heading)]
        )
        tangent = self.heading

        return pos, tangent, CurvatureRes.CONST_ZERO


class Arc(Geometry):
    """This record describes an arc as part of the road’s reference line.


    (Section 5.3.4.1.3 of OpenDRIVE 1.4)
    """

    def __init__(self, start_position, heading, length, curvature):
        self.curvature = curvature
        super().__init__(start_position=start_position, heading=heading, length=length)

    def calc_position(self, s_pos, compute_curvature=True):
        """

        Args:
          s_pos:

        Returns:
        :param compute_curvature:

        """
        c = self.curvature
        hdg = self.heading - np.pi / 2

        a = 2 / c * np.sin(s_pos * c / 2)
        alpha = (np.pi - s_pos * c) / 2 - hdg

        dx = -1 * a * np.cos(alpha)
        dy = a * np.sin(alpha)

        pos = self.start_position + np.array([dx, dy])
        tangent = self.heading + s_pos * self.curvature

        return pos, tangent, self.curvature


class Spiral(Geometry):
    """This record describes a spiral as part of the road’s reference line.

    For this type of spiral, the curvature
    change between start and end of the element is linear.

    (Section 5.3.4.1.2 of OpenDRIVE 1.4)
    """

    def __init__(self, start_position, heading, length, curvStart, curvEnd):
        self._curvStart = curvStart
        self._curvEnd = curvEnd

        super().__init__(start_position=start_position, heading=heading, length=length)
        self._spiral = EulerSpiral.createFromLengthAndCurvature(
            self.length, self._curvStart, self._curvEnd
        )

    def calc_position(self, s_pos, compute_curvature=True):
        """

        Args:
          s_pos:

        Returns:
        :param compute_curvature:

        """
        (x, y, t, curvature) = self._spiral.calc(
            s_pos,
            self.start_position[0],
            self.start_position[1],
            self._curvStart,
            self.heading
        )
        return np.array([x, y]), t, curvature


class Poly3(Geometry):
    """This record describes a cubic polynomial as part of the road’s reference line.


    (Section 5.3.4.1.4 of OpenDRIVE 1.4)
    """

    def __init__(self, start_position, heading, length, a, b, c, d):
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self.coeffs = [self._a, self._b, self._c, self._d]
        self.d_coeffs = self.coeffs[1:] * np.array(np.arange(1, len(self.coeffs)))
        self.d2_coeffs = self.d_coeffs[1:] * np.array(np.arange(1, len(self.d_coeffs)))
        #
        super().__init__(start_position=start_position, heading=heading, length=length)

        # raise NotImplementedError()

    def calc_position(self, s_pos, compute_curvature=True):
        """

        Args:
          s_pos:

        Returns:
        :param compute_curvature:

        """
        # TODO untested

        # Calculate new point in s_pos/t coordinate system

        t = np.polynomial.polynomial.polyval(s_pos, self.coeffs)

        # Rotate and translate
        cos_heading = math.cos(self.heading)
        sin_heading = math.sin(self.heading)
        srot = s_pos * cos_heading - t * sin_heading
        trot = s_pos * sin_heading + t * cos_heading

        # Derivate to get heading change

        tangent = np.polynomial.polynomial.polyval(s_pos, self.d_coeffs)
        curvature = None
        if compute_curvature:
            curvature = (np.polynomial.polynomial.polyval(s_pos, self.d2_coeffs),
                         self._d)

        return self.start_position + np.array([srot, trot]), self.heading + tangent, curvature


class ParamPoly3(Geometry):
    """This record describes a parametric cubic curve as part
    of the road’s reference line in a local u/v co-ordinate system.

    This record describes an arc as part of the road’s reference line.


    (Section 5.3.4.1.5 of OpenDRIVE 1.4)
    """

    def __init__(
        self, start_position, heading, length, aU, bU, cU, dU, aV, bV, cV, dV, pRange
    ):
        super().__init__(start_position=start_position, heading=heading, length=length)

        self._aU = aU
        self._bU = bU
        self._cU = cU
        self._dU = dU
        self._aV = aV
        self._bV = bV
        self._cV = cV
        self._dV = dV

        self.curvature_derivative_max = max(self._dV, self._dU)
        self.curvature_derivative_min = min(self._dV, self._dU)

        self.coeffs_u = [self._aU, self._bU, self._cU, self._dU]
        self.coeffs_v = [self._aV, self._bV, self._cV, self._dV]

        self.d_coeffs_u = self.coeffs_u[1:] * np.array(np.arange(1, len(self.coeffs_u)))
        self.d_coeffs_v = self.coeffs_v[1:] * np.array(np.arange(1, len(self.coeffs_v)))

        self.d2_coeffs_u = self.d_coeffs_u[1:] * np.array(np.arange(1, len(self.d_coeffs_u)))
        self.d2_coeffs_v = self.d_coeffs_v[1:] * np.array(np.arange(1, len(self.d_coeffs_v)))

        if pRange is None:
            self._pRange = 1.0
        else:
            self._pRange = pRange

    def max_abs_curvature(self, pos):
        """
        Maximal curvature at position s
        :param pos:
        :return:
        """
        if abs(np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u)) > \
           abs(np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v)):
            if np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u) > 0:
                return np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u), self.curvature_derivative_max
            else:
                return np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u), self.curvature_derivative_min
        else:
            if np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v) > 0:
                return np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v), self.curvature_derivative_max
            else:
                return np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v), self.curvature_derivative_min

    def calc_position(self, s_pos, compute_curvature=True):
        """

        Args:
          s_pos:

        Returns:
        :param compute_curvature:

        """

        # Position
        pos = (s_pos / self.length) * self._pRange

        x = np.polynomial.polynomial.polyval(pos, self.coeffs_u)
        y = np.polynomial.polynomial.polyval(pos, self.coeffs_v)

        cos_heading = math.cos(self.heading)
        sin_heading = math.sin(self.heading)
        xrot = x * cos_heading - y * sin_heading
        yrot = x * sin_heading + y * cos_heading

        # Tangent is defined by derivation
        dx = np.polynomial.polynomial.polyval(pos, self.d_coeffs_u)
        dy = np.polynomial.polynomial.polyval(pos, self.d_coeffs_v)

        tangent = np.arctan2(dy, dx)
        curvature = self.max_abs_curvature(pos) if compute_curvature else None
        return self.start_position + np.array([xrot, yrot]), self.heading + tangent, curvature


def calc_next_s(s_current, curvature: float, error_tolerance: float, min_delta_s, s_max) -> float:
    """
    Adaptive computation of next longitudinal sampling position considering approximated error using the curvature
    ```
    math  error_tolerance(curvature) <= \frac{curvature^2}{8}*max_{[a,b]}(|f''(s)|)
    ```
    :param curvature: curvature at current position
    :param error_tolerance: max. error
    :param min_delta_s: minimal step length to avoids getting stuck
    :param s_max: maximal length of current road element
    :return:
    """
    def calc_delta_s(curvature):
        if type(curvature) == tuple:
            curvature, curv_derivative = curvature
            if curvature < 0:
                curv_derivative = -curv_derivative
        else:
            curv_derivative = None

        curvature = abs(curvature)
        if curvature is None:
            raise RuntimeError("curvature has to be != None")
        elif curvature == CurvatureRes.CONST_ZERO:
            return np.inf
        else:
            if curv_derivative is not None and abs(curv_derivative) > 2.0:
                def f(ds):
                    return (math.pow(ds, 2) * curvature + math.pow(ds, 3) * curv_derivative) / 8 - error_tolerance

                def f_p(ds):
                    return ds * 0.25 * curvature + math.pow(ds, 2) * 0.375 * curv_derivative

                def f_p2(ds):
                    return 0.25 * curvature + ds * 0.75 * curv_derivative

                ds_0 = math.sqrt(8 * error_tolerance / curvature)
                res = scipy.optimize.root_scalar(f, fprime=f_p, fprime2=f_p2, x0=ds_0)
                if res.converged is True and res.root > 0:
                    ds = res.root
                else:
                    ds = ds_0
            else:
                ds = math.sqrt(8 * error_tolerance / curvature)
            return ds

    s_next = s_current + max(min_delta_s, calc_delta_s(curvature))

    # round up when almost at the end
    if 0 < s_max - s_next < 1e-2:
        s_next = s_max

    s_next = min(s_max, s_next)
    # print(s_next, curvature)
    return s_next
