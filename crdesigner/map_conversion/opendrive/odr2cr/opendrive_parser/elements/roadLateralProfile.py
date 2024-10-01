import warnings

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road_record import (
    RoadRecord,
)


class LateralProfile:
    """
    The lateral profile record contains a series of superelevation and crossfall records which define the
    characteristics of the road surface's banking along the reference line.
    (Section 5.3.6 of OpenDRIVE 1.4)

    Lateral profile and its components are not yet supported in CommonRoad! Thus, they are extracted from the
    OpenDRIVE file but not used.
    """

    def __init__(self):
        self._superelevations = []
        self._crossfalls = []
        self._shapes = []

    @property
    def superelevations(self) -> list:
        """
        The superelevations of a LateralProfile.

        :getter: returns superelevations of the road
        :setter: sets superelevations of the road
        """
        self._superelevations.sort(key=lambda x: x.start_pos)
        return self._superelevations

    @superelevations.setter
    def superelevations(self, value):
        if not isinstance(value, list) or not all(isinstance(x, Superelevation) for x in value):
            raise TypeError("Value must be a list of Superelevation.")

        self._superelevations = value

    @property
    def crossfalls(self) -> list:
        """
        Crossfalls of a LateralProfile.

        :getter: returns crossfalls of the road
        :setter: sets crossfalls of the road
        """
        self._crossfalls.sort(key=lambda x: x.start_pos)
        return self._crossfalls

    @crossfalls.setter
    def crossfalls(self, value):
        if not isinstance(value, list) or not all(isinstance(x, Crossfall) for x in value):
            raise TypeError("Value must be a list of Crossfall.")

        self._crossfalls = value

    @property
    def shapes(self) -> list:
        """
        Defined as the road section’s surface relative to the reference plane.
        There may be several shape definitions at one s-position that have different t-values,
        thereby describing the curvy shape of the road.

        :getter: returns shape of the road
        :getter: sets shape of the road
        """
        self._shapes.sort(key=lambda x: (x.start_pos, x.start_pos_t))
        return self._shapes

    @shapes.setter
    def shapes(self, value):
        if not isinstance(value, list) or not all(isinstance(x, Shape) for x in value):
            raise TypeError("Value must be a list of instances of Shape.")

        self._shapes = value


class Superelevation(RoadRecord):
    """The superelevation of the road is defined as the
    road section’s roll angle around the s-axis.

    (Section 5.3.6.1 of OpenDRIVE 1.4)
    """


class Crossfall(RoadRecord):
    """
    The crossfall of the road is defined as the road surface ́s angle relative to the t-axis.
    (Section 5.3.6.2 of OpenDRIVE 1.4)

    Crossfall does not exist anymore in OpenDRIVE 1.7! Crossfalls are now defined with the element <shape> which is
    implemented by the Shape class.
    """

    def __init__(self, *polynomial_coefficients: float, start_pos: float = None, side: str = None):
        super().__init__(*polynomial_coefficients, start_pos=start_pos)
        self.side = side
        warnings.warn(
            "Crossfalls are not an own element of OpenDRIVE anymore. They are defined within shapes!",
            DeprecationWarning,
        )

    @property
    def side(self) -> str:
        """
        The side of the crossfall.

        :getter: returns the side as a string
        :setter: sets the side, only allows to set the side for 'left', 'right' or 'both'
        """
        return self._side

    @side.setter
    def side(self, value):
        if value not in ["left", "right", "both"]:
            raise TypeError("Value must be string with content 'left', 'right' or 'both'.")

        self._side = value


class Shape(RoadRecord):
    """
    The shape of the road is defined as the road section’s surface relative to the reference plane.
    This shape may be described as a series of 3 order polynomials for a given "s" station.
    The absolute position of a shape value is calculated by:
       t = start_pos_t + dt
    h_shape is the height above the reference path at a given position and is calculated by:
       h_shape = a + b*dt + c*dt² + d*dt³
    dt being the distance perpendicular to the reference line between the start of the entry and the actual position.
    (Section 5.3.6.3 of OpenDRIVE 1.4)

    :ivar start_pos_t: t-coordinate of start position
    """

    def __init__(
        self,
        *polynomial_coefficients: float,
        start_pos: float = None,
        start_pos_t: float = None,
    ):
        """
        Constructor of class shape.

        :param polynomial_coefficients: coefficients of a polynomial function. If more than one argument is given, this
            results in a tuple with the given arguments
        :param start_pos: s-coordinate of start position
        :param start_pos_t: t-coordinate of start position
        """
        super().__init__(*polynomial_coefficients, start_pos=start_pos)
        self.start_pos_t = start_pos_t
