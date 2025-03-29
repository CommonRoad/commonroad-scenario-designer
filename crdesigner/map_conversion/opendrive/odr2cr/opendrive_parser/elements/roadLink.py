from __future__ import annotations

import warnings
from typing import Union


class Link:
    """
    Road link classes for OpenDRIVE. Desribes the connections between roads and junctions.
    """

    def __init__(self, predecessor=None, successor=None, neighbors=None):
        """
        Constructor of class.

        :param predecessor: preceding road/junction
        :param successor: succeeding road/junction
        :param neighbors: neighbors -> not used anymore
        """
        self.predecessor = predecessor
        self.successor = successor
        self.neighbors = [] if neighbors is None else neighbors

    def __str__(self):
        return "successor: " + str(self._successor)

    @property
    def predecessor(self) -> Predecessor:
        """
        Preceding road/junction.

        :getter: returns preceding road/junction
        :setter: sets preceding road/junction
        """
        return self._predecessor

    @predecessor.setter
    def predecessor(self, value: Union[None, Predecessor]):
        if not isinstance(value, Predecessor) and value is not None:
            raise TypeError("Value must be Predecessor")

        # pylint: disable=W0201
        self._predecessor = value

    @property
    def successor(self) -> Successor:
        """
        Succeeding road/junction.

        :getter: returns succeeding road/junction
        :setter: sets succeeding road/junction
        """
        return self._successor

    @successor.setter
    def successor(self, value: Union[None, Successor]):
        if not isinstance(value, Successor) and value is not None:
            raise TypeError("Value must be Successor")

        # pylint: disable=W0201
        self._successor = value

    @property
    def neighbors(self) -> list:
        """
        Neighbors of road.

        :getter: returns neighbors
        :setter: sets neighbors
        """
        warnings.warn(
            "Neighbors element was used in OpenDRIVE V1.4 for legacy purposes. V1.7 does not contain"
            " neighbors elements. It is also not used for conversion into lanelet network.",
            DeprecationWarning,
        )
        return self._neighbors

    @neighbors.setter
    def neighbors(self, value: list[Neighbor]):
        if not isinstance(value, list) or not all(isinstance(x, Neighbor) for x in value):
            raise TypeError("Value must be list of instances of Neighbor.")

        # pylint: disable=W0201
        self._neighbors = value

    def addNeighbor(self, value: Neighbor):
        warnings.warn("Same issue as in neighbors getter and setter.", DeprecationWarning)
        if not isinstance(value, Neighbor):
            raise TypeError("Value must be Neighbor")

        self._neighbors.append(value)


class Predecessor:
    """
    Class describing the preceding road or junction.
    A road uses element_type, element_id and contact_point as attributes.
    A common junction uses element_type and element_id as attributes.
    A virtual junction uses element_type, element_id, element_s and element_dir as attributes.
    """

    def __init__(self, element_type=None, element_id=None, contact_point=None):
        """
        Constructor of the class.

        :param element_type: type of the linked element (junction or road)
        :param element_id: id of the linked element
        :param contact_point: contact point of linked element (start or end)
        """
        self.elementType = element_type
        self.element_id = element_id
        self.contactPoint = contact_point

    def __str__(self):
        return (
            str(self._elementType)
            + " with id "
            + str(self._elementId)
            + " contact at "
            + str(self._contactPoint)
        )

    @property
    def elementType(self) -> str:
        """
        Describes the type of the preceding element.

        :getter: returns type
        :setter: sets type of the preceding element
        """
        return self._elementType

    @elementType.setter
    def elementType(self, value):
        if value not in ["road", "junction"]:
            raise AttributeError("Value must be road or junction")

        # pylint: disable=W0201
        self._elementType = value

    @property
    def element_id(self) -> int:
        """
        Id of preceding element.

        :getter: returns ID
        :setter: sets ID
        """
        return self._elementId

    @element_id.setter
    def element_id(self, value):
        # pylint: disable=W0201
        self._elementId = int(value)

    @property
    def contactPoint(self) -> Union[None, str]:
        """
        Contact point of linked element.

        :getter: returns contact point
        :setter: sets contact point
        """
        return self._contactPoint

    @contactPoint.setter
    def contactPoint(self, value):
        if value not in ["start", "end"] and value is not None:
            raise AttributeError("Value must be start or end")

        # pylint: disable=W0201
        self._contactPoint = value


class Successor(Predecessor):
    """
    Class describing the succeeding road or junction. It has defined equivalent to the predecessor of the road link.
    Thus, it inherits all methods and attributes.
    """


class Neighbor:
    """
    Describes information about neighbor of the road. Neighbor entry was introduced for legacy purposes in OpenDRIVE
    1.4 but is no longer part of V1.7.
    Road networks are now defined along the reference line and don't use a neighbors entry anymore.

    This class is not used for the conversion into lanelet networks later on.
    """

    def __init__(self, side=None, element_id=None, direction=None):
        """
        Constructor of class.

        :param side: information which neighbor is being configured
        :param element_id: ID of the linked road
        :param direction: direction of the neighbor relative to own direction
        """
        self.side = side
        self.element_id = element_id
        self.direction = direction

    @property
    def side(self) -> str:
        """
        Information which neighbor is referred to.

        :getter: returns whether left or right neighbor is meant
        :setter: sets neighbor
        """
        return self._side

    @side.setter
    def side(self, value):
        if value not in ["left", "right"]:
            raise AttributeError("Value must be left or right")

        # pylint: disable=W0201
        self._side = value

    @property
    def element_id(self) -> int:
        """
        ID of the linked road.

        :getter: returns road ID
        :setter: sets road ID
        """
        return self._elementId

    @element_id.setter
    def element_id(self, value):
        # pylint: disable=W0201
        self._elementId = int(value)

    @property
    def direction(self) -> str:
        """
        Direction of the neighbor relative to own direction.

        :getter: returns direction of neighbor relative to own
        :setter: sets direction of neighbor relative to own
        """
        return self._direction

    @direction.setter
    def direction(self, value):
        if value not in ["same", "opposite"]:
            raise AttributeError("Value must be same or opposite")

        self._direction = value
