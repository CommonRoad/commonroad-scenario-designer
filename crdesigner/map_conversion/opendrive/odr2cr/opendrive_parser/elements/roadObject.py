import logging


class Object:
    """
    Describes items that influence a road by expanding, delimiting and supplementing its course.
    E.g. Parking spaces, crosswalks, and traffic barriers. Objects are defined per road.

    Class is not yet supported. It is not used in the conversion to CommonRoad.

    :ivar _type: type of the object
    :ivar _name: name of the object
    :ivar _width: width of the object bounding box
    :ivar _height: height of the object's bounding box
    :ivar _zOffset: z-offset of object's origin relative to the elevation of the reference line
    :ivar _id: ID of object
    :ivar _s: s-coordinate of the object's origin
    :ivar _t: t-coordinate of the object's origin
    :ivar _validLength: validity of object along s-axis
    :ivar _orientation: orientation of the object
    :ivar _hdg: heading angle of the object
    :ivar _pitch: pitch angle relative to the x/y-plane
    :ivar _roll: roll angle relative to the x/y-plane
    """

    def __init__(self):
        self._type = None
        self._name = None
        self._width = None
        self._height = None
        self._zOffset = None
        self._id = None
        self._s = None
        self._t = None
        self._validLength = None
        self._orientation = None
        self._hdg = None
        self._pitch = None
        self._roll = None
        self._outline = None
        # TODO: Check potential use of missing attributes length, perpToRoad, radius, subtype

    @property
    def type(self) -> str:
        """
        Type of object.

        :getter: returns type of object
        :setter: sets type of object
        """
        return self._type

    @type.setter
    def type(self, value):
        road_types = [
            "barrier",
            "bike",
            "building",
            "bus",
            "car",
            "crosswalk",
            "ZebraCrossing",
            "gantry",
            "motorbike",
            "none",
            "obstacle",
            "parkingSpace",
            "patch",
            "pedestrian",
            "pole",
            "RoadSignPole",
            "railing",
            "roadMark",
            "roadmark",
            "soundBarrier",
            "streetLamp",
            "Streetlamp",
            "trafficIsland",
            "trailer",
            "train",
            "tram",
            "tree",
            "van",
            "vegetation",
            "wind",
            "Guidepost",
            "Areas",
            "portal",
        ]
        customs = [
            "permanentDelineator",
            "emergencyCallBox",
            "tunnel",
            "arrowStraight",
            "arrowRight",
            "arrowMergeLeft",
            "arrowLeft",
            "arrowLeftRight",
            "arrowStraightLeft",
            "arrowMergeRight",
            "island",
            "guidepost",
            "roadpainting",
        ]
        if value == "-1":
            value = "none"
        if value not in road_types and value not in customs:
            logging.warning(f"Value {value} is not a supported road object type!")
        self._type = str(value)

    @property
    def name(self) -> str:
        """
        Name of object.

        :getter: returns name of object
        :setter: sets name of object
        """
        return self._name

    @name.setter
    def name(self, value):
        if value is not None:
            self._name = str(value)

    @property
    def width(self) -> float:
        """
        Width of object's bounding box.

        :getter: returns width of object's bounding box
        :setter: sets width of object's bounding box
        """
        return self._width

    @width.setter
    def width(self, value):
        if value is not None:
            self._width = float(value)
        else:
            self._width = None

    @property
    def height(self) -> float:
        """
        Height of object's bounding box.

        :getter: returns height of object's bounding box
        :setter: sets height of object's bounding box
        """
        return self._height

    @height.setter
    def height(self, value):
        if value is not None:
            self._height = float(value)

    @property
    def zOffset(self) -> float:
        """
        z-offset of object's origin relative to the elevation of the reference line.

        :getter: returns zOffset
        :setter: sets zOffset
        """
        return self._zOffset

    @zOffset.setter
    def zOffset(self, value):
        if value is not None:
            self._zOffset = float(value)

    @property
    def id(self) -> int:
        """
        ID of object.

        :getter: returns ID
        :setter: sets ID
        """
        return self._id

    @id.setter
    def id(self, value):
        if value is not None:
            self._id = int(value)

    @property
    def s(self) -> float:
        """
        s-coordinate of object's origin.

        :getter: returns s-coordinate
        :setter: sets s-coordinate
        """
        return self._s

    @s.setter
    def s(self, value):
        if value is not None:
            self._s = float(value)

    @property
    def t(self) -> float:
        """
        t-coordinate of object's origin.

        :getter: returns t-coordinate
        :setter: sets t-coordinate
        """
        return self._t

    @t.setter
    def t(self, value):
        if value is not None:
            self._t = float(value)

    @property
    def validLength(self) -> float:
        """
        Validity of object along s-axis. (0.0 for point object)

        :getter: returns validity of object
        :setter: sets validity
        """
        return self._validLength

    @validLength.setter
    def validLength(self, value):
        self._validLength = float(value)

    @property
    def orientation(self) -> str:
        """
        Orientation of object which describes validity in positive/negative s-direction.
        '+' -> valid in positive s-direction, '-' -> valid in negative s-direction, 'none' -> valid in both directions.
        Does not affect heading.

        :getter: returns orientation
        :setter: sets orientation
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        if value not in ["+", "-", "none"]:
            raise AttributeError("Value is not a valid orientation!")
        self._orientation = str(value)

    @property
    def hdg(self) -> float:
        """
        Heading angle of object relative to road direction.

        :getter: returns heading angle
        :setter: sets heading angle
        """
        return self._hdg

    @hdg.setter
    def hdg(self, value):
        if value is not None:
            self._hdg = float(value)

    @property
    def pitch(self) -> float:
        """
        Pitch angle relative to the x/y-plane.

        :getter: returns pitch angle
        :setter: sets pitch angle
        """
        return self._pitch

    @pitch.setter
    def pitch(self, value):
        if value is not None:
            self._pitch = float(value)

    @property
    def roll(self) -> float:
        """
        Roll angle relative to the x/y-plane.

        :getter: returns roll angle
        :setter: sets roll angle
        """
        return self._roll

    @roll.setter
    def roll(self, value):
        if value is not None:
            self._roll = float(value)

    @property
    def outline(self):
        return self._outline

    @outline.setter
    def outline(self, value):
        self._outline = value


class ObjectOutlineCorner:
    def __init__(self):
        self._height = None
        self._id = None
        self._u = None
        self._v = None
        self._z = None

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value is not None:
            self._height = float(value)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value is not None:
            self._id = int(value)

    @property
    def u(self):
        return self._u

    @u.setter
    def u(self, value):
        if value is not None:
            self._u = float(value)

    @property
    def v(self):
        return self._v

    @v.setter
    def v(self, value):
        if value is not None:
            self._v = float(value)

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        if value is not None:
            self._z = value
