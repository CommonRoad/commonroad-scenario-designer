from __future__ import annotations


class Junction:
    """
    Class which describes some attributes of the junction element in OpenDrive.

    :ivar _id: ID of the junction element
    :ivar _name: name of the junction
    :ivar _connections: list of connection elements associated with the junction
    """

    # TODO priority
    # TODO controller

    def __init__(self):
        self._id = None
        self._name = None
        self._connections = []

    @property
    def id(self) -> int:
        """
        Junction ID.

        :getter: returns the junction ID
        :setter: sets the junction ID
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def name(self) -> str:
        """
        Junction name.

        :getter: returns the junction name
        :setter: sets the junction name
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = str(value)

    @property
    def connections(self) -> list[Connection]:
        """
        Shows the connections associated with the junction.

        :getter: returns the connection objects in the form of a list [connection1, connection2, ...]
        """
        return self._connections

    def addConnection(self, connection: Connection):
        """
        Adds new connections which are associated with the junction element.

        :param: connection which needs to be an object of class Connection
        :return: appended list of connections
        """
        if not isinstance(connection, Connection):
            raise TypeError("Has to be of instance Connection")

        self._connections.append(connection)


class Connection:
    """
    Class which describes connecting roads and correspond to the connection elements on a junction element.
    It corresponds to the t_junction_connection element in the UML model of ASAM OpenDrive.

    :ivar _id: ID of the connection element
    :ivar _incomingRoad: ID of the incoming road
    :ivar _connectingRoad: ID of the connecting road
    :ivar _contactPoint: contact point of the connecting road
    :ivar _laneLinks: list of laneLinks associated with the connection
    """

    def __init__(self):
        self._id = None
        self._incomingRoad = None
        self._connectingRoad = None
        self._contactPoint = None
        self._laneLinks = []

    @property
    def id(self) -> int:
        """
        ID of the connection.

        :getter: returns the ID of the connection
        :setter: sets the ID of the connection
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def incomingRoad(self) -> int:
        """
        ID of the incoming road.

        :getter: returns the ID of the incoming road
        :setter: sets the ID of the incoming road
        """
        return self._incomingRoad

    @incomingRoad.setter
    def incomingRoad(self, value):
        self._incomingRoad = int(value)

    @property
    def connectingRoad(self) -> int:
        """
        ID of the connecting road.

        :getter: returns the ID of the connecting road
        :setter: sets the ID of the connecting road
        """
        return self._connectingRoad

    @connectingRoad.setter
    def connectingRoad(self, value):
        self._connectingRoad = int(value)

    @property
    def contactPoint(self) -> str:
        """
        Contact Point on the connecting road. Valid options are "start" and "end".

        :getter: returns the contact point
        :setter: sets the contact point
        """
        return self._contactPoint

    @contactPoint.setter
    def contactPoint(self, value):
        if value not in ["start", "end"]:
            raise AttributeError("Contact point can only be start or end.")

        self._contactPoint = value

    @property
    def laneLinks(self) -> list[LaneLink]:
        """
        Shows the laneLinks associated with the connection element.

        :getter: returns the laneLink objects in the form of a list [laneLink1, laneLink2, ...]
        """
        return self._laneLinks

    def addLaneLink(self, laneLink: LaneLink):
        """
        Adds new laneLinks which are associated with the connection element.

        :param: laneLink which needs to be an object of class LaneLink
        :return: appended list of laneLinks
        """
        if not isinstance(laneLink, LaneLink):
            raise TypeError("Has to be of instance LaneLink")

        self._laneLinks.append(laneLink)


class LaneLink:
    """
    Class which describes the lanes that are linked between an incoming road and a connecting road.
    It corresponds to the t_junction_connection_laneLink element in the UML model in ASAM OpenDrive.

    :ivar _from: ID of the incoming lane
    :ivar _to: ID of the connection lane
    """

    def __init__(self):
        self._from = None
        self._to = None

    def __str__(self):
        return str(self._from) + " > " + str(self._to)

    @property
    def fromId(self) -> int:
        """
        ID of the incoming lane.

        :getter: returns ID
        :setter: sets ID
        """
        return self._from

    @fromId.setter
    def fromId(self, value):
        self._from = int(value)

    @property
    def toId(self) -> int:
        """
        ID of the connection lane.

        :getter: returns ID
        :setter: sets ID
        """
        return self._to

    @toId.setter
    def toId(self, value):
        self._to = int(value)
