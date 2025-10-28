import numpy as np

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road_record import (
    RoadRecord,
)


class ElevationProfile:
    """
    The elevation profile record contains a series of elevation records
    which define the characteristics of
    the road's elevation along the reference line.

    (Section 5.3.5 of OpenDRIVE 1.4)
    """

    def __init__(self):
        self.elevations = []

    def calc_elevation(self, s_pos: float) -> float:
        """
        Calculate elevation at a given position along the reference line.

        :param s_pos: Position along the reference line in curve parameter ds
        :return: Elevation value at position s_pos
        """
        if not self.elevations:
            return 0.0

        # Find the correct elevation record for this position
        elevation_record = None
        for elev in self.elevations:
            if elev.start_pos <= s_pos:
                elevation_record = elev
            else:
                break

        if elevation_record is None:
            return 0.0

        # Calculate ds from start of this elevation record
        ds = s_pos - elevation_record.start_pos

        # Calculate elevation using polynomial: h = a + b*ds + c*ds² + d*ds³
        elevation = np.polynomial.polynomial.polyval(ds, elevation_record.polynomial_coefficients)

        return elevation


class ElevationRecord(RoadRecord):
    """
    The elevation record defines an elevation entry at a given reference line position.
    This is a subclass of the abstract class RoadRecord.

    (Section 5.3.5.1 of OpenDRIVE 1.4)
    """
