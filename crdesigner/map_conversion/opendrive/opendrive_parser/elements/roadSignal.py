from typing import Union


class Signal:
    """
    Class which describes the signal element in OpenDRIVE. It provides information about signals along a road.

    :ivar _s: s-coordinate
    :ivar _t: t-coordinate
    :ivar _id: ID of the signal
    :ivar _name: name of the signal
    :ivar _dynamic: indicates whether the signal is dynamic or static
    :ivar _orientation: indicates in which s-direction the traffic is valid
    :ivar _type: type identifier of the signal
    :ivar _subtype: subtype identifier of the signal
    :ivar _country: country code of the road according to ISO 3166-1
    :ivar _signal_value: value of the signal
    :ivar _unit: unit of the signal value (mandatory if signal value is given)
    :ivar _text: additional text associated with the signal
    """

    def __init__(self):
        self._s = None
        self._t = None
        self._id = None
        self._name = None
        self._dynamic = None
        self._orientation = None
        self._type = None
        self._subtype = None
        self._country = None
        self._signal_value = None
        self._unit = None
        self._text = None
        self._validity_from = None
        self._validity_to = None
        self._signal_id = None

        """
        ###not supported in CommonRoad Signs/Lights###
        #self._zOffset = None
        #self._countryRevision = None

        self._height = None
        self._width = None
        self._hOffset = None
        self._pitch = None
        self._roll = None

        """

    @property
    def s(self) -> float:
        """
        s-coordinate of the signal.

        :getter: returns s-coordinate
        :setter: sets s-coordinate
        """
        return self._s

    @s.setter
    def s(self, value):
        self._s = float(value)

    @property
    def t(self) -> float:
        """
        t-coordinate of the signal.

        :getter: returns t-coordinate
        :setter: sets t-coordinate
        """
        return self._t

    @t.setter
    def t(self, value):
        self._t = float(value)

    @property
    def id(self) -> int:
        """
        ID of the signal.

        :getter: returns ID
        :setter: sets ID
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def name(self) -> str:
        """
        Name of the signal.

        :getter: returns name of the signal
        :setter: sets name
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def dynamic(self) -> str:
        """
        Indicates whether signal is static or dynamic. ("Yes" for dynamic, "No" for static)

        :getter: returns whether signal is dynamic
        :setter: sets whether signal is dynamic
        """
        return self._dynamic

    @dynamic.setter
    def dynamic(self, value):
        if value not in ["yes", "no"]:
            raise AttributeError("Invalid input!")
        self._dynamic = str(value)

    @property
    def orientation(self) -> str:
        """
        Indicates direction in which signal is enforced. ("+" = valid in positive s-direction, "-" = valid
        in negative s-direction, "none" = valid in both directions)

        :getter: returns orientation
        :setter: sets orientation
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        if value not in ["+", "-", "none"]:
            raise AttributeError("Invalid input!")
        self._orientation = str(value)

    @property
    def country(self) -> str:
        """
        Country code of road.

        :getter: returns country code
        :setter: sets country code
        """
        return self._country

    @country.setter
    def country(self, value):
        self._country = str(value)

    @property
    def signal_value(self) -> float:
        """
        Value of the signal.

        :getter: returns value of the signal
        :setter: sets value of the signal
        """
        return self._signal_value

    @signal_value.setter
    def signal_value(self, value):
        if isinstance(value, str):
            self._signal_value = float(value)
        else:
            self._signal_value = value

    @property
    def unit(self) -> Union[None, str]:
        """
        Unit of the signal value.

        :getter: returns unit
        :setter: sets unit
        """
        return self._unit

    @unit.setter
    def unit(self, value):
        if value is not None:
            self._unit = str(value)
        else:
            self._unit = value

    @property
    def text(self) -> Union[None, str]:
        """
        Additional text associated with signal.

        :getter: returns text
        :setter: sets text
        """
        return self._text

    @text.setter
    def text(self, value):
        if value is not None:
            self._text = str(value)
        else:
            self._text = value

    @property
    def type(self) -> Union[None, str]:
        """
        Type identifier of the signal according to country code.

        :getter: returns type ID
        :setter: sets type ID
        """
        return self._type

    @type.setter
    def type(self, value):
        if value is not None:
            self._type = str(value)
        else:
            self._type = value

    @property
    def subtype(self) -> str:
        """
        Subtype identifier according to country code.

        :getter: returns subtype ID
        :setter: sets subtype ID
        """
        return self._subtype

    @subtype.setter
    def subtype(self, value):
        self._subtype = value

    @property
    def validity_from(self) -> int:
        """Indicates starting lane of road for which signal is valid."""
        return self._validity_from

    @validity_from.setter
    def validity_from(self, value: int):
        self._validity_from = int(value)

    @property
    def validity_to(self) -> int:
        """Indicates starting lane of road for which signal is valid."""
        return self._validity_to

    @validity_to.setter
    def validity_to(self, value: int):
        self._validity_to = int(value)

    @property
    def signal_id(self) -> str:
        """ID of related dynamic signal."""
        return self._signal_id

    @signal_id.setter
    def signal_id(self, value: str):
        self._signal_id = str(value)


class SignalReference:
    """
    In OpenDRIVE, a reference to another signal for reuse of signal information
    is represented by the <signalReference> element within the <signal> element.
    (Do not mistake it with the <reference> element within the <signal> element!!!)

    Rules:
    The following rules apply for the purpose of reusing signal information:
    A lane validity element may be added for every <signalReference> element.
    Signal reference shall be used for signals only.
    For the signal that reuses the content of another signal, the direction for which it is valid shall be specified.

    :ivar _s: s-coordinate
    :ivar _t: t-coordinate
    :ivar _id: ID of the referenced signal within the database
    :ivar _orientation: indicates in which s-direction the traffic is valid
    """

    def __init__(self):
        self._s = None
        self._t = None
        self._id = None
        self._orientation = None
        self._validity_from = None
        self._validity_to = None
        self._signal_id = None
        self._turn_relation = None

    @property
    def s(self) -> float:
        """s-coordinate of the signal."""
        return self._s

    @s.setter
    def s(self, value):
        self._s = float(value)

    @property
    def t(self) -> float:
        """t-coordinate of the signal."""
        return self._t

    @t.setter
    def t(self, value):
        self._t = float(value)

    @property
    def id(self) -> int:
        """ID of the signal."""
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def orientation(self) -> str:
        """
        Indicates direction in which signal is enforced. ("+" = valid in positive s-direction, "-" = valid
        in negative s-direction, "none" = valid in both directions)
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        if value not in ["+", "-", "none"]:
            raise AttributeError("Invalid input!")
        self._orientation = str(value)

    @property
    def validity_from(self) -> int:
        """Indicates starting lane of road for which signal is valid."""
        return self._validity_from

    @validity_from.setter
    def validity_from(self, value: int):
        self._validity_from = int(value)

    @property
    def validity_to(self) -> int:
        """Indicates starting lane of road for which signal is valid."""
        return self._validity_to

    @validity_to.setter
    def validity_to(self, value: int):
        self._validity_to = int(value)

    @property
    def signal_id(self) -> str:
        return self._signal_id

    @signal_id.setter
    def signal_id(self, value: str):
        self._signal_id = str(value)

    @property
    def turn_relation(self) -> str:
        return self._turn_relation

    @turn_relation.setter
    def turn_relation(self, value: str):
        self._turn_relation = str(value)
