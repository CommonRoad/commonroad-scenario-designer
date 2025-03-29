import abc
import math
from enum import IntEnum
from typing import Tuple, Union

import numpy as np
import scipy.optimize

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.eulerspiral import (
    EulerSpiral,
)


class CurvatureRes(IntEnum):
    CONST_ZERO = 0


class Geometry(abc.ABC):
    """
    A road geometry record defines the layout of the road's reference
    line in the x/y-plane (plan view).

    The geometry information is split into a header which is common to all geometric elements.

    (Section 5.3.4.1 of OpenDRIVE 1.4)

    :ivar _start_position: start position in the form np.array([x, y]), private attribute
    :ivar _length: length of the geometric object, private attribute
    :ivar _heading: inertial heading/start orientation, private attribute
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, start_position: np.ndarray, heading: float, length: float):
        self._start_position = np.array(start_position)
        self._length = length
        self._heading = heading

    @property
    def start_position(self) -> np.ndarray:
        """
        Returns the overall geometry start position
        """
        return self._start_position

    @property
    def length(self) -> float:
        """
        Returns the overall geometry length
        """
        return self._length

    @property
    def heading(self) -> float:
        """
        Returns heading, in which direction the geometry heads at start.
        """
        return self._heading

    @abc.abstractmethod
    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Calculates the position of the geometry as if the starting point is (0/0)

        :param s_pos: position along the geometry
        :param compute_curvature: computes curvature, otherwise returns None
        :return: None
        """
        pass


class Line(Geometry):
    """
    This record describes a straight line as part of the road’s reference line.
    (Section 5.3.4.1.1 of OpenDRIVE 1.4)
    This class is a subclass of Geometry
    """

    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, float, int]:
        """
        Calculates x and y coordinates at position s along the line and returns additionally the orientation and
        curvature. It overrides the abstract method of the superclass Geometry.

        :param s_pos: position along the geometry, i.e. the line
        :param compute_curvature: decides whether curvature should be calculated
        :return: x and y position, orientation and curvature in the form ([x, y], orientation, curvature=0)
        """
        pos = self.start_position + np.array(
            [s_pos * np.cos(self.heading), s_pos * np.sin(self.heading)]
        )
        tangent = self.heading

        return pos, tangent, CurvatureRes.CONST_ZERO


class Arc(Geometry):
    """
    This record describes an arc as part of the road’s reference line.
    (Section 5.3.4.1.3 of OpenDRIVE 1.4)
    This class is a subclass of Geometry
    """

    def __init__(self, start_position: np.ndarray, heading: float, length: float, curvature: float):
        """
        Constructor of Arc().

        :param start_position: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param curvature: (constant) curvature of the arc
        """
        self.curvature = curvature
        super().__init__(start_position=start_position, heading=heading, length=length)

    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, float, float]:
        """
        Calculates x and y coordinates at position s along the line and returns additionally the orientation and
        curvature. The chord a connecting the arc's endpoints is described as a = 2*r*sin(0.5*theta) and the
        difference between the orientation of the endpoints theta is equal to s*curvature.
        This overrides the abstract method of the superclass Geometry.

        :param s_pos: position along the geometry, i.e. the line
        :param compute_curvature: decides whether curvature should be calculated
        :return: x and y position, orientation and curvature in the form ([x, y], orientation, curvature=0)
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
    """
    This record describes a spiral as part of the road’s reference line.
    For this type of spiral, the curvature
    change between start and end of the element is linear.
    (Section 5.3.4.1.2 of OpenDRIVE 1.4)
    This class is a subclass of Geometry and uses the EulerSpiral class from eulerspiral.py
    """

    def __init__(
        self,
        start_position: np.ndarray,
        heading: float,
        length: float,
        curv_start: float,
        curv_end: float,
    ):
        """
        Constructor of Spiral().

        :param start_position: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param curv_start: curvature at the start of the spiral
        :param curv_end: curvature at the end of the spiral
        """
        self._curv_start = curv_start
        self._curv_end = curv_end

        super().__init__(start_position=start_position, heading=heading, length=length)
        self._spiral = EulerSpiral.create_from_length_and_curvature(
            self.length, self._curv_start, self._curv_end
        )

    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """
        Calculates x and y coordinates at position s along the line and returns additionally the orientation and
        curvature. It overrides the abstract method of the superclass Geometry. Is just calls a function from
        eulerspiral.py

        :param s_pos: position along the geometry, i.e. the line
        :param compute_curvature: decides whether curvature should be calculated
        :return: x and y position, orientation and curvature in the form ([x, y], orientation, curvature=0)
        """
        (x, y, t, curvature) = self._spiral.calc(
            s_pos, self.start_position[0], self.start_position[1], self._curv_start, self.heading
        )
        return np.array([x, y]), t, curvature


class Poly3(Geometry):
    """This record describes a cubic polynomial as part of the road’s reference line.
    (Section 5.3.4.1.4 of OpenDRIVE 1.4)
    This class is a subclass of Geometry

    :ivar coeffs: list of coefficients of polynom in the form [a, b, c, d]
    :ivar d_coeffs: list of coefficients of derivative of polynom in the form [b', c', d']
    :ivar d2_coeffs: list of coefficients of second derivative in the form [c'', d'']
    """

    def __init__(
        self,
        start_position: np.ndarray,
        heading: float,
        length: float,
        a: float,
        b: float,
        c: float,
        d: float,
    ):
        """
        Constructor of Cubic polynom of the form y(x) = a + b*x + c*x^2 + d*x^3

        :param start_position: start position in the form np.array([x, y])
        :param heading: inertial heading/start orientation
        :param length: length of the geometric object
        :param a: a of polynom
        :param b: b of polynom
        :param c: c of polynom
        :param d: d of polynom
        """
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

    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, float, Union[Tuple[float, float], None]]:
        """
        Calculates x and y coordinates at position s along the line and returns additionally the orientation and
        curvature. It overrides the abstract method of the superclass Geometry. The coordinate frame of the
        polynomial is transformed into the global frame.

        :param s_pos: position along the geometry, i.e. the line
        :param compute_curvature: decides whether curvature should be calculated
        :return: x and y position, orientation and curvature in the form ([x, y], orientation, curvature=0)
        """
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
            # only called in calc_geometry in roadPlanView.py which expects either None or a float, not a tuple
            curvature = (np.polynomial.polynomial.polyval(s_pos, self.d2_coeffs), self._d)
            # curvature = np.polynomial.polynomial.polyval(s_pos, self.d2_coeffs)

        return self.start_position + np.array([srot, trot]), self.heading + tangent, curvature


class ParamPoly3(Geometry):
    """
    This record describes a parametric cubic curve as part
    of the road’s reference line in a local u/v co-ordinate system.
    This record describes an arc as part of the road’s reference line.
    (Section 5.3.4.1.5 of OpenDRIVE 1.4)
    This class is a subclass of Geometry

    :ivar coeffs_u: list of coefficients of polynom in the form [aU, bU, cU, dU]
    :ivar d_coeffs_u: list of coefficients of derivative of polynom in the form [bU', cU', dU']
    :ivar d2_coeffs_u: list of coefficients of second derivative in the form [cU'', dU'']
    :ivar coeffs_v: list of coefficients of polynom in the form [aV, bV, cV, dV]
    :ivar d_coeffs_v: list of coefficients of derivative of polynom in the form [bV', cV', dV']
    :ivar d2_coeffs_v: list of coefficients of second derivative in the form [cV'', dV'']
    """

    def __init__(
        self,
        start_position: np.ndarray,
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
        Constructor of Parametric Cubic curve
        u(p) = aU + bU*p + cU*p^2 + dU*p^3
        v(p) = aV + bV*p + cV*p^2 + dV*p^3

        :param start_position: start position in the form np.array([x, y])
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

    def max_abs_curvature(self, pos: float) -> Tuple[float, float]:
        """
        Chooses maximum curvature between u and v curve.

        :param pos: position on the parametric cubic curve
        :return: max curvature
        """
        if abs(np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u)) > abs(
            np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v)
        ):
            if np.polynomial.polynomial.polyval(pos, self.d2_coeffs_u) > 0:
                return np.polynomial.polynomial.polyval(
                    pos, self.d2_coeffs_u
                ), self.curvature_derivative_max
            else:
                return np.polynomial.polynomial.polyval(
                    pos, self.d2_coeffs_u
                ), self.curvature_derivative_min

        else:
            if np.polynomial.polynomial.polyval(pos, self.d2_coeffs_v) > 0:
                return np.polynomial.polynomial.polyval(
                    pos, self.d2_coeffs_v
                ), self.curvature_derivative_max
            else:
                return np.polynomial.polynomial.polyval(
                    pos, self.d2_coeffs_v
                ), self.curvature_derivative_min

    def calc_position(
        self, s_pos: float, compute_curvature: bool = True
    ) -> Tuple[np.ndarray, float, Union[None, Tuple[float, float]]]:
        """
        Calculates x and y coordinates at position s along the line and returns additionally the orientation and
        curvature. It overrides the abstract method of the superclass Geometry.

        :param s_pos: position along the geometry, i.e. the line
        :param compute_curvature: decides whether curvature should be calculated
        :return: x and y position, orientation and curvature in the form ([x, y], orientation, curvature=0)
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


def calc_next_s(
    s_current: float, curvature: float, error_tolerance: float, min_delta_s: float, s_max: float
) -> float:
    """
    Adaptive computation of next longitudinal sampling position considering approximated error using the curvature.
    Formula: error_tolerance(curvature) <= (curvature^2)/8 * max_{[a,b]}(|f''(s)|)

    :param s_current: current s position
    :param curvature: curvature at current position
    :param error_tolerance: max. error
    :param min_delta_s: minimal step length to avoid getting stuck
    :param s_max: maximal length of current road element
    :return: next s-value / next position of geometry
    """
    delta_s = calc_delta_s(curvature, error_tolerance)
    # if curvature is close to 0, delta_s will become infinity, resulting in s_next to become s_max. If s_current is
    # much smaller than s_max, this will result in a line instead of a curve.
    # introducing a max_delta will avoid this, but will also restrict the sampling. For the scenarios curve_road.xodr
    # and adp-carla-road.xodr max_delta = 60 works fine, but for 02-cut_in_aheadof_ego_slow_automap.xodr it needs to be
    # decreased to 10

    # changes start
    #
    # max_delta = 60
    # s_next = s_current + max(min_delta_s, min(delta_s, max_delta))
    #
    # changes end

    # current implementation start
    #
    s_next = s_current + max(min_delta_s, delta_s)
    #
    # current implementaion end

    # round up when almost at the end
    if 0 < s_max - s_next < 1e-2:
        s_next = s_max

    s_next = min(s_max, s_next)
    return s_next


def calc_delta_s(
    curvature: Union[None, float, Tuple[float, float]], error_tolerance: float
) -> float:
    """
    Calculates the difference to the next s_position.

    :param curvature: curvature at current position
    :param error_tolerance: max. error
    :return: delta s
    """
    if isinstance(curvature, tuple):
        curvature, curv_derivative = curvature
        if curvature < 0:
            curv_derivative = -curv_derivative
    else:
        curv_derivative = None

    if curvature is None:
        raise RuntimeError("curvature has to be != None")
    elif np.isclose(curvature, 0.0, atol=1e-4):
        ds = np.inf
    else:
        curvature = abs(curvature)
        if curv_derivative is not None and abs(curv_derivative) > 2.0:

            def f(ds):
                return (
                    math.pow(ds, 2) * curvature + math.pow(ds, 3) * curv_derivative
                ) / 8 - error_tolerance

            def f_p(ds):
                return ds * 0.25 * curvature + math.pow(ds, 2) * 0.375 * curv_derivative

            def f_p2(ds):
                return 0.25 * curvature + ds * 0.75 * curv_derivative

            ds_0 = math.sqrt(8 * error_tolerance / curvature)
            # find roots of function and its derivatives
            res = scipy.optimize.root_scalar(f, fprime=f_p, fprime2=f_p2, x0=ds_0)
            # check if algorithm exited successfully
            if res.converged is True and res.root > 0:
                ds = res.root
            else:
                ds = ds_0
        else:
            ds = math.sqrt(8 * error_tolerance / curvature)
    return ds
