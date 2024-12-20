from abc import ABC


class RoadRecord(ABC):
    """
    Abstract base class to model Records (e.g. ElevationRecord) of the OpenDRIVE
    specification.

    These Records all have attributes start_pos, a, b, c, d.
    The attribute attr which is defined the RoadRecord at a given reference line position
    is calculated with the following equation:

    attr = a + b*ds + c*ds² + d*ds³

    where ds being the distance along the reference line between the start of the entry
    and the actual position.
    ds starts at zero for each RoadRecord.
    The absolute position of an elevation value is calculated by    s = start_pos + ds

    :ivar start_pos: Position in curve parameter ds where the RoadRecord starts
    :ivar polynomial_coefficients: List of values [a, b, c, d, ...] which can be evaluated with a
        polynomial function.
    """

    def __init__(self, *polynomial_coefficients: float, start_pos: float = None):
        """
        Constructor of Road Record abstract class

        :param polynomial_coefficients: coefficients of a polynomial function. If more than one argument is given, this
            results in a tuple with the given arguments
        :param start_pos: starting position of the Road Record
        """
        self.start_pos = start_pos
        self.polynomial_coefficients = []
        for coeff in polynomial_coefficients:
            self.polynomial_coefficients.append(coeff)
