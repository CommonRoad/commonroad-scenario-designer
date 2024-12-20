import math
from functools import lru_cache
from typing import Any, List, Optional, Tuple

import numpy as np


class Border:
    """A lane border defines a path along a whole lane section. A lane always uses an inner and outer lane border.
    The reference can be another lane border or a plan view."""

    def __init__(self, ref_offset: float = 0.0):
        """Initializes a Border object.
        :param ref_offset: Offset in s-direction to the reference object after which the border begins.
        """
        self.ref_offset = float(ref_offset)
        self.width_coefficient_offsets = []
        self.width_coefficients = []

        self.reference = None

    def _get_width_index(self, s_pos: float, is_last_pos: bool) -> float:
        """Get the index of the width which applies at position s_pos.

        :param s_pos: Position on border in curve_parameter ds
        :param is_last_pos: Whether s_pos is the last position
        :return: Index of width that applies at position s_pos
        """
        return next(
            (
                self.width_coefficient_offsets.index(n)
                for n in self.width_coefficient_offsets[::-1]
                if ((n <= s_pos and (not is_last_pos or s_pos == 0)) or (n < s_pos and is_last_pos))
            ),
            len(self.width_coefficient_offsets) - 1,
        )

    def get_next_width_coeffs(self, s_pos: float, is_last_pos: bool = False) -> List[float]:
        """Get width coefficients which apply at position s_pos.

        :param s_pos: Position on border in curve_parameter ds
        :param is_last_pos: Whether s_pos is the last position
        :return: An array with coefficients [a, b, c, d] for the polynomial w = a + b*ds + c*ds² + d*ds³
        """
        width_idx = self._get_width_index(s_pos, is_last_pos)
        return self.width_coefficients[width_idx]

    # NOTE: might by more efficient to calculate each border once
    # instead of recalculating them over and over.
    @lru_cache(maxsize=200000)
    def calc(
        self,
        s_pos: float,
        width_offset: float = 0.0,
        is_last_pos: bool = False,
        reverse=False,
        compute_curvature=True,
    ) -> Tuple[Optional[Any], Any, Any, Any]:
        """Calculate the Cartesian coordinates and the tangential direction of
        the border by calculating position of reference border at s_pos
        and then adding the width in orthogonal direction to the reference position.

        :param s_pos: Position s_pos specified in curve parameter ds where to calculate the cartesian coordinates on
                        the border
        :param width_offset: Offset to add to calculated width at position s_pos
        :param is_last_pos: Whether s_pos is the last position
        :param reverse: Whether to calculate positions in a reverse order, default is False
        :param compute_curvature: Whether to computer curvature, default is True
        :return: coord: (x,y) tuple of cartesian coordinates, tangential at s_pos, curvature at s_pos,
        and maximum length of the geometry
        """
        # Last reference has to be a reference geometry (PlanView)
        # Offset of all inner lanes (Border)
        # calculate position of reference border
        if np.isclose(s_pos, 0):
            s_pos = 0

        try:
            ref_coord, tang_angle, curv, max_geometry_length = self.reference.calc(
                self.ref_offset + s_pos,
                is_last_pos=is_last_pos,
                reverse=reverse,
                compute_curvature=compute_curvature,
            )
        except TypeError:
            ref_coord, tang_angle, curv, max_geometry_length = self.reference.calc(
                np.round(self.ref_offset + s_pos, 3),
                reverse=reverse,
                compute_curvature=compute_curvature,
            )

        if not self.width_coefficients or not self.width_coefficient_offsets:
            raise Exception("No entries for width definitions.")

        # Find correct coefficients
        # find which width segment is at s_pos
        width_idx = self._get_width_index(s_pos, is_last_pos)
        # width_idx = min(width_idx, len(self.width_coefficient_offsets)-1)
        # Calculate width at s_pos
        distance = (
            np.polynomial.polynomial.polyval(
                s_pos - self.width_coefficient_offsets[width_idx],
                self.width_coefficients[width_idx],
            )
            + width_offset
        )

        # New point is in orthogonal direction
        ortho = tang_angle + np.pi / 2
        coord = ref_coord + np.array([distance * math.cos(ortho), distance * math.sin(ortho)])

        return coord, tang_angle, curv, max_geometry_length
