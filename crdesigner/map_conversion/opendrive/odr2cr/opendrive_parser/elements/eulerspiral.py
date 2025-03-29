from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy import special


class EulerSpiral:
    """
    Class which finds the parameters of the ASAM OpenDrive spiral element.
    """

    def __init__(self, gamma):
        self._gamma = gamma

    def curvature(self, s: float, kappa0: float = 0) -> Tuple[float, float]:
        """
        Returns curvature at position s
        The curvature in the Euler curve is represented as K(s) = gamma * s + k

        :param s: position on the spiral
        :param kappa0: curvature at the starting point
        :return: The new curvature at position s and the magnitude by which the curvature
            changes with s in the form of (new curvature, magnitude of change)
        """
        return self._gamma * s + kappa0, self._gamma

    @staticmethod
    def create_from_length_and_curvature(
        length: float, curv_start: float, curv_end: float
    ) -> EulerSpiral:
        """
        Create an EulerSpiral from a given length with curveStart
        and curvEnd. This is how the OpenDrive format specifies
        EulerSpirals.

        :param length: Length of EulerSpiral
        :param curv_start: Curvature at start of EulerSpiral
        :param curv_end: Curvature at end of EulerSpiral
        :return: EulerSpiral - a new clothoid
        """
        # if length is zero, assume zero curvature
        if length == 0:
            return EulerSpiral(0)
        return EulerSpiral(1 * (curv_end - curv_start) / length)

    def calc(
        self, s: float, x0: float = 0, y0: float = 0, kappa0: float = 0, theta0: float = 0
    ) -> Tuple[float, float, float, Tuple[float, float]]:
        """
        Calculates x and y position, angle of the tangent and the curvature at position s.
        The position is described in complex representation with x being the real part of the
        number and y the imaginary part. The angle of the tangent is measured w.r.t.
        the x-axis.

        :param s: position on the spiral
        :param x0: initial x position
        :param y0:  initial y position
        :param kappa0: curvature at the starting position
        :param theta0: angle of the tangent at the initial position
        :return: x and y positions, theta and the curvature at point s in the form
            (x-position, y-position, theta, curvature)
        """

        # Start
        c0 = x0 + 1j * y0

        if self._gamma == 0 and kappa0 == 0:
            # Straight line
            cs = c0 + np.exp(1j * theta0) * s

        elif self._gamma == 0 and kappa0 != 0:
            # Arc, (1/kappa) = radius
            cs = c0 + np.exp(1j * theta0) / kappa0 * (
                np.sin(kappa0 * s) + 1j * (1 - np.cos(kappa0 * s))
            )

        else:
            # Fresnel integrals
            cs = self._calc_fresnel_integral(s, kappa0, theta0, c0)

        # Tangent at each point
        theta = self._gamma * s**2 / 2 + kappa0 * s + theta0

        return cs.real, cs.imag, theta, self.curvature(s, kappa0)

    def _calc_fresnel_integral(
        self, s: float, kappa0: float, theta0: float, C0: complex
    ) -> complex:
        """
        Calculates the fresnel integral.

        :param s: position on the spiral
        :param kappa0: curvature at the starting position
        :param theta0: angle of the tangent at the initial position
        :param C0: initial x and y position represented in complex form
        :return: new x and y position represented in complex form (x + 1j * y)
        """
        Sa, Ca = special.fresnel((kappa0 + self._gamma * s) / np.sqrt(np.pi * np.abs(self._gamma)))
        Sb, Cb = special.fresnel(kappa0 / np.sqrt(np.pi * np.abs(self._gamma)))

        # Euler Spiral
        Cs1 = np.sqrt(np.pi / np.abs(self._gamma)) * np.exp(
            1j * (theta0 - kappa0**2 / 2 / self._gamma)
        )
        Cs2 = np.sign(self._gamma) * (Ca - Cb) + 1j * Sa - 1j * Sb

        Cs = C0 + Cs1 * Cs2

        return Cs
