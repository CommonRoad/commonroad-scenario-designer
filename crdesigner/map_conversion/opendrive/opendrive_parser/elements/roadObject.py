__author__ = "Benjamin Orthen, Stefan Urban"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


class Object:

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

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = str(value)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = float(value)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = float(value)

    @property
    def zOffset(self):
        return self._zOffset

    @zOffset.setter
    def zOffset(self, value):
        self._zOffset = float(value)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def s(self):
        return self._s

    @s.setter
    def s(self, value):
        self._s = float(value)

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, value):
        self._t = float(value)

    @property
    def validLength(self):
        return self._validLength

    @validLength.setter
    def validLength(self, value):
        self._validLength = float(value)

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = str(value)

    @property
    def hdg(self):
        return self._hdg

    @hdg.setter
    def hdg(self, value):
        self._hdg = float(value)

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, value):
        self._pitch = float(value)

    @property
    def roll(self):
        return self._roll

    @roll.setter
    def roll(self, value):
        self._roll = float(value)
