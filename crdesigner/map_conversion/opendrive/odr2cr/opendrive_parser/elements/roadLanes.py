from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, List, Optional, Union

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road_record import (
    RoadRecord,
)

if TYPE_CHECKING:
    from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser import Road


class Lanes:
    """
    Class which describes the lanes of a road. It corresponds to the lanes element of OpenDRIVE.

    :ivar _lane_offsets: laneOffset elements in the Lane element
    :ivar _lane_sections: laneSection elements in the Lane element
    """

    def __init__(self):
        self._lane_offsets = []
        self._lane_sections = []

    @property
    def lane_offsets(self) -> List[LaneOffset]:
        """
        Offset of the lane from road reference line. Offsets are defined in ascending order according to their
        s-coordinate. A new offset starts when the underlying polynomial function changes.

        :getter: returns lane offsets
        """
        self._lane_offsets.sort(key=lambda x: x.start_pos)
        return self._lane_offsets

    @property
    def lane_sections(self) -> List[LaneSection]:
        """
        Lane sections of the lane. Lane sections are defined in ascending order according to their s-coordinate.

        :getter: returns lane sections
        """
        self._lane_sections.sort(key=lambda x: x.sPos)
        return self._lane_sections

    def get_lane_section(self, lane_section_idx: int) -> Optional[LaneSection]:
        """
        Returns the corresponding Lane section of a Lane Section Index.

        :param lane_section_idx: lane section idx
        :return: instance of class LaneSection
        """
        for lane_section in self.lane_sections:
            if lane_section.idx == lane_section_idx:
                return lane_section

        return None

    def get_last_lane_section_idx(self) -> int:
        """
        Returns the Index of the last LaneSection.

        :return: idx of the last Lane Section
        """

        num_lane_sections = len(self.lane_sections)

        if num_lane_sections > 1:
            return num_lane_sections - 1

        return 0


class LaneOffset(RoadRecord):
    """
    The lane offset record defines a lateral shift of the lane reference line
    (which is usually identical to the road reference line).
    This class is a subclass of the abstract class RoadRecord.

    (Section 5.3.7.1 of OpenDRIVE 1.4)

    """


class LeftLanes:
    """
    Lane Sections are divided into left, right and center lane. One center lane and at least one entry in either left
    lane or right lane must be present.
    This class describes the left lanes in a lane section.

    """

    sort_direction = False

    def __init__(self):
        self._lanes = []

    @property
    def lanes(self) -> List[Lane]:
        """
        Describes the lane elements of the left/center/right lane of the lane section.

        :getter: returns lane elements of left/center/right lane
        """
        self._lanes.sort(key=lambda x: x.id, reverse=self.sort_direction)
        return self._lanes


class CenterLanes(LeftLanes):
    """
    Lane Sections are divided into left, right and center lane. One center lane and at least one entry in either left
    lane or right lane must be present.
    This class describes the one center lane in a lane section.
    It is a subclass of LeftLanes and inherits the attributes and methods.
    """


class RightLanes(LeftLanes):
    """
    Lane Sections are divided into left, right and center lane. One center lane and at least one entry in either left
    lane or right lane must be present.
    This class describes the right lanes in a lane section.
    It is a subclass of LeftLanes and inherits the attributes and methods.
    """

    sort_direction = True


class Lane:
    """
    Class which describes the Lane properties. These are defined per lane section but can vary within that section.

    :ivar laneTypes: defines the main purpose of a lane and its corresponding traffic rules
    :ivar parentRoad: describes which road the lane belongs to
    :ivar _id: lane ID
    :ivar _type: type of the lane
    :ivar _level: defines whether superelevation should be applied on this lane or not (boolean)
    :ivar _link: provides linkage information by means of predecessor and successor information of each lane
    :ivar _widths: width of a lane along the t-coordinate, may change within a lane section
    :ivar _borders: another method to describe the width of lanes by describing outer limits of a lane,
        independent of the parameters of their inner borders. Normally lane width and lane border are mutually
        exclusive within the same lane group, in case both are existent, choose width element over border element
    :ivar lane_section: describes which lane section the lane belongs to
    :ivar has_border_record: describes whether information in the form of a border element is available
    :ivar _road_mark: describes lane markings, defines the style of the line at the lane's outer border
    """

    laneTypes = [
        "none",
        "driving",
        "stop",
        "shoulder",
        "biking",
        "sidewalk",
        "border",
        "restricted",
        "parking",
        "bidirectional",  # not available in ASAM OpenDRIVE 1.7.0 (n.a.)
        "median",
        "special1",  # n.a.
        "special2",  # n.a.
        "special3",  # n.a.
        "roadWorks",  # n.a.
        "tram",  # n.a.
        "rail",  # n.a.
        "entry",
        "exit",
        "offRamp",
        "onRamp",
        # newly added in ASAM OpenDRIVE 1.7.0
        "curb",
        "connectingRamp",
    ]

    def __init__(self, parentRoad: Road, lane_section: LaneSection):
        """
        Constructor of Lane class.

        :param parentRoad: Road which includes the lane instance
        :param lane_section: Lane section which includes the lane instance
        """
        self._parent_road = parentRoad
        self._id = None
        self._type = None
        self._level = None
        self._link = LaneLink()
        self._widths = []
        self._borders = []
        self.lane_section = lane_section
        self.has_border_record = False
        self._road_mark = []
        self.speed = None
        self.access = []
        # TODO material -> see parser.py
        # TODO speed limit -> see parser.py
        # TODO height -> see parser.py
        # TODO rules -> see parser.py

    @property
    def parent_road(self) -> Road:
        """
        Road including the lane.

        :getter: returns the road which has includes the lane
        """
        return self._parent_road

    @property
    def id(self) -> int:
        """
        ID of the Lane.

        :getter: returns the ID
        :setter: sets the lane ID
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def type(self) -> str:
        """
        Type of the lane.

        :getter: returns the type of the lane
        :setter: sets the type of the lane
        """
        return self._type

    @type.setter
    def type(self, value):
        if value not in self.laneTypes:
            raise Exception()

        self._type = str(value)

    @property
    def level(self) -> bool:
        """
        Describes whether the lane is level or not, i.e. whether superelevation is to applied ("false") or not ("true").

        :getter: returns level attribute
        :setter: sets level attribute
        """
        return self._level

    @level.setter
    def level(self, value):
        if value not in ["true", "false"] and value is not None:
            raise AttributeError("Value must be true or false.")

        self._level = value == "true"

    @property
    def link(self) -> LaneLink:
        """
        Describes linkage information of the lane.

        :getter: returns the instance of class LaneLink
        """
        return self._link

    @property
    def widths(self) -> List[LaneWidth]:
        """
        Describes the widths of a lane.

        :getter: returns the width element
        :setter: sets the width of the lane
        """
        self._widths.sort(key=lambda x: x.start_offset)
        return self._widths

    @widths.setter
    def widths(self, value):
        self._widths = value

    def getWidth(self, widthIdx: int) -> Optional[LaneWidth]:
        """
        Returns the width corresponding to an index, i.e. the width of a certain part of the lane.

        :param widthIdx: Index of the widths in the lane
        """
        for width in self._widths:
            if width.idx == widthIdx:
                return width

        return None

    def get_last_lane_width_idx(self) -> int:
        """
        Returns the index of the last width sector of the lane.
        """

        num_widths = len(self._widths)

        if num_widths > 1:
            return num_widths - 1

        return 0

    @property
    def borders(self) -> List[LaneBorder]:
        """
        Describes the width of a lane. It is mutually exclusive to the width element/attribute and is only used,
        if there is no width attribute given.

        :getter: returns instance of class border
        """
        self._borders.sort(key=lambda x: x.start_offset)
        return self._borders

    @property
    def road_mark(self) -> List[RoadMark]:
        """
        Describes the road/lane markings. It defines the style of the line at the lane's outer border.

        :getter: returns instance of class RoadMark
        :setter: sets the attribute _road_mark
        """
        return self._road_mark

    @road_mark.setter
    def road_mark(self, value: List[RoadMark]):
        self._road_mark = value


class LaneLink:
    """
    Class which describes the linkage information for lanes. Linkage is described by means of predecessor and successor.
    Lane linkage is independent of the driving direction.

    :ivar _predecessor: predecessor of a given lane is a lane connected to the start of its lane section in its
        reference line direction
    :ivar _successor: successor of a given lane is a lane connected to the end of its lane section in
        reference line direction
    """

    def __init__(self):
        self._predecessor = None
        self._successor = None

    @property
    def predecessorId(self) -> int:
        """
        Describes the preceding lane of a lane.

        :getter: returns preceding lane ID
        :setter: sets preceding lane ID
        """
        return self._predecessor

    @predecessorId.setter
    def predecessorId(self, value):
        self._predecessor = int(value)

    @property
    def successorId(self) -> int:
        """
        Describes the succeeding lane of a lane.

        :getter: returns succeeding lane ID
        :setter: sets succeeding lane ID
        """
        return self._successor

    @successorId.setter
    def successorId(self, value):
        self._successor = int(value)


class LaneSection:
    """
    The lane section record defines the characteristics of a road cross-section.
    Every time the number of lanes changes, a new lane section is required. For easier navigation through an
    ASAM OpenDRIVE road description, the lanes within a lane section are grouped into left, center, and right lanes.
    One center lane and at least one entry in either left lane or right lane must be defined.

    (Section 5.3.7.2 of OpenDRIVE 1.4)

    :ivar idx: Index of lane section corresponding to its position in the ascending order of lane section elements in
        lanes element
    :ivar sPos: s-coordinate of start position
    :ivar _single_side: Describes whether lane section element is valid for one side only, used to simplify the use of
        lane sections for complex roads
    :ivar _left_lanes: left lanes in a lane section
    :ivar _center_lanes: center lanes in a lane section
    :ivar _right_lanes: right lanes in a lane section
    :ivar _parent_road: road the lane section belongs to
    """

    def __init__(self, road: Road = None):
        """
        Constructor of LaneSection class.

        :param road: road the lane section belongs to
        """
        self.idx = None
        self.sPos = None
        self._single_side = None
        self._left_lanes = LeftLanes()
        self._center_lanes = CenterLanes()
        self._right_lanes = RightLanes()

        self._parent_road = road

    @property
    def single_side(self) -> bool:
        """
        Indicator if lane section entry is valid for one side only.

        :getter: Returns whether singleSide value
        :setter: sets singleSide value
        """
        return self._single_side

    @single_side.setter
    def single_side(self, value):
        if value not in ["true", "false"] and value is not None:
            raise AttributeError("Value must be true or false.")

        self._single_side = value == "true"

    @property
    def left_lanes(self) -> List[Lane]:
        """
        Get list of sorted lanes always starting in the middle (lane id -1).

        :getter: Returns the left lanes of the lane section
        """
        return self._left_lanes.lanes

    @property
    def center_lanes(self) -> List[Lane]:
        """
        Get list of the one center lane element.

        :getter: Returns the center lane of the lane section
        """
        return self._center_lanes.lanes

    @property
    def right_lanes(self) -> List[Lane]:
        """
        Get list of sorted lanes always starting in the middle (lane id 1).

        :getter: Returns the right lanes of the lane section
        """
        return self._right_lanes.lanes

    @property
    def all_lanes(self) -> List[Lane]:
        """
        Attention! lanes are not sorted by id.
        Get list of all lanes in the lane section.

        :getter: Returns all lanes in the lane section
        """
        return self._left_lanes.lanes + self._center_lanes.lanes + self._right_lanes.lanes

    def get_lane(self, lane_id: int) -> Union[None, Lane]:
        """
        Gets corresponding lane to lane ID.

        :param lane_id: lane ID
        :returns: lane, if lane is part of the lane section
        """
        for lane in self.all_lanes:
            if lane.id == lane_id:
                return lane

        return None

    @property
    def parent_road(self) -> Road:
        """
        Road the lane section belongs to.

        :getter: returns road which the lane section is a part of
        """
        return self._parent_road


class LaneWidth(RoadRecord):
    """
    Entry for a lane describing the width for a given position.
    (Section 5.3.7.2.1.1.2 of OpenDRIVE 1.4)
    This is a subclass of the abstract class RoadRecord and inherits its attributes and methods.
    Class LaneWidth has some additional attributes and functionalities.

    :ivar length: length of the position on the lane corresponding to the width
    """

    def __init__(
        self, *polynomial_coefficients: float, idx: int = None, start_offset: float = None
    ):
        """
        Constructor of class LaneWidth.

        :param polynomial_coefficients: coefficients of a polynomial function. If more than one argument is given, this
            results in a tuple with the given arguments
        :param idx: Index of the width corresponding to a part of the lane section (width can change within a lane section
        :param start_offset: offset of the entry relative to the preceding lane section record
        """
        self.idx = idx
        self.length = 0
        super().__init__(*polynomial_coefficients, start_pos=start_offset)

    @property
    def start_offset(self):
        """
        Return start_offset, which is the offset of the entry to the start of the lane section.

        :getter: returns start_offset
        """
        return self.start_pos


class LaneBorder(LaneWidth):
    """
    Describe lane by width in respect to reference path.

    (Section 5.3.7.2.1.1.3 of OpenDRIVE 1.4)

    Instead of describing lanes by their width entries and, thus, invariably depending on influences of inner
    lanes on outer lanes, it might be more convenient to just describe the outer border of each lane
    independent of any inner lanes’ parameters.

    It is a subclass of LaneWidth and has not additional attributes or methods. It has therefore identical attributes
    and methods.
    """


class RoadMark:
    """
    Lanes on roads can have different lane markings, for example lines of different colors and styles.
    The road mark information defines the style of the line at the lane’s outer border. For left lanes, this is the
    left border, for right lanes the right one. The style of the center line that separates left and right lanes is
    determined by the road mark element for the center lane.

    (Section 9.6 ASAM OpenDRIVE 1.7)

    :ivar _SOffset: s-coordinate of start position of the road mark - relative to the position of the preceding
        lane section
    :ivar _type: type of the road mark
    :ivar _weight: weight of the road mark
    :ivar _color: color of the road mark
    :ivar _material: material of the road mark
    :ivar _width: width of the road mark
    :ivar _lane_change: Allows a lane change in the indicated direction, taking into account that lanes are numbered
        in ascending order from right to left. If the attribute is missing, “both” is used as default.
    :ivar _height: height of the road mark
    """

    def __init__(self):
        self._SOffset = None
        self._type = None
        self._weight = "standard"
        self._color = None
        self._material = None
        self._width = None
        self._lane_change = None
        self._height = None

    @property
    def SOffset(self) -> float:
        """
        s-coordinate of the start position of the road mark.

        :getter: returns sOffset
        :setter: sets sOffset
        """
        return self._SOffset

    @SOffset.setter
    def SOffset(self, value: float):
        """
        Setter of the s-coordinate of the start position of the road mark

        :param value: value the SOffset is set to
        """
        if value is None:
            warnings.warn(
                "Parser could not find value for road_mark.SOffset, 0 is used per default."
            )
            value = 0
        self._SOffset = float(value)

    @property
    def type(self) -> str:
        """
        Type of the road mark.

        :getter: returns road mark type
        :setter: sets road mark type
        """
        return self._type

    @type.setter
    def type(self, value):
        self._type = str(value)

    @property
    def weight(self) -> str:
        """
        Weight of the road mark.

        :getter: returns road mark weight
        :setter: sets road mark weight
        """
        return self._weight

    @weight.setter
    def weight(self, value: str):
        """
        Setter of the weight of the road mark.
        :param value: Value the weight is set to
        """
        if value is None:
            logging.warning(
                "RoadMark::weight: Parser could not find value for road_mark.weight, standard is used per default."
            )
            value = "standard"
        self._weight = str(value)

    @property
    def color(self) -> str:
        """
        Color of the road mark.

        :getter: returns the color of the road mark
        :setter: sets the color of the road mark
        """
        logging.warning(
            "RoadMark::color: Attribute color is not used for conversion!", DeprecationWarning
        )
        return self._color

    @color.setter
    def color(self, value):
        self._color = str(value)

    @property
    def material(self):
        """
        Material of the road mark.

        :getter: returns material of the road mark
        """
        logging.warning(
            "RoadMark::material: Attribute material is not used for conversion!", DeprecationWarning
        )
        return self._material

    @property
    def width(self):
        """
        Width of the road mark.

        :getter: returns the width of the road mark
        """
        logging.warning(
            "RoadMark::width: Attribute width is not used for conversion!", DeprecationWarning
        )
        return self._width

    @property
    def lane_change(self):
        """
        Allows lane change according to value.

        :getter: returns allowed lane change
        :setter: sets lane_change
        """
        logging.warning(
            "RoadMark::lane_change: Attribute lane_change is not used for conversion",
            DeprecationWarning,
        )
        return self._lane_change

    @lane_change.setter
    def lane_change(self, value):
        self._lane_change = value

    @property
    def height(self):
        """
        Height of the road mark.

        :getter: returns the height of the road mark
        """
        logging.warning(
            "RoadMark::height: Attribute height is not used for conversion!", DeprecationWarning
        )
        return self._height
