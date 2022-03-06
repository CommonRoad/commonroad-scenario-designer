import numpy as np
from lxml import etree
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.opendrive import OpenDrive, Header
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLink import Predecessor as RoadLinkPredecessor, \
    Successor as RoadLinkSuccessor, Neighbor as RoadLinkNeighbor
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadtype import RoadType, Speed as RoadTypeSpeed
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadElevationProfile \
    import ElevationRecord as RoadElevationProfile
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLateralProfile \
    import Superelevation as RoadLateralProfileSuperelevation, Crossfall as RoadLateralProfileCrossfall, \
    Shape as RoadLateralProfileShape
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import LaneOffset as RoadLanesLaneOffset, \
    Lane as RoadLaneSectionLane, LaneSection as RoadLanesSection, LaneWidth as RoadLaneSectionLaneWidth, \
    LaneBorder as RoadLaneSectionLaneBorder, RoadMark as RoadLaneRoadMark
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.junction import Junction, \
    Connection as JunctionConnection, LaneLink as JunctionConnectionLaneLink
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadSignal import Signal as RoadSignal, \
    SignalReference

__author__ = "Benjamin Orthen, Stefan Urban, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


def parse_opendrive(root_node: etree.ElementTree) -> OpenDrive:
    """
    Tries to parse XML tree, returns OpenDRIVE object

    :param root_node: loaded OpenDRIVE data
    :return: The object representing an OpenDrive specification.
    """
    # Only accept lxml element
    if not etree.iselement(root_node):
        raise TypeError("Argument root_node is not a xml element")

    opendrive = OpenDrive()

    # Header
    header = root_node.find("header")
    if header is not None:
        parse_opendrive_header(opendrive, header)

    # Junctions
    for junction in root_node.findall("junction"):
        parse_opendrive_junction(opendrive, junction)

    # Load roads
    for road in root_node.findall("road"):
        parse_opendrive_road(opendrive, road)

    return opendrive


def parse_opendrive_road_link(new_road: Road, opendrive_road_link: etree.ElementTree):
    """
    Parses OpenDRIVE Road Link element

    :param new_road: Road element where link should be added.
    :param opendrive_road_link: Loaded OpenDRIVE link.
    """
    predecessor = opendrive_road_link.find("predecessor")

    if predecessor is not None:
        new_road.link.predecessor = RoadLinkPredecessor(
            predecessor.get("elementType"),
            predecessor.get("elementId"),
            predecessor.get("contactPoint"),
        )

    successor = opendrive_road_link.find("successor")

    if successor is not None:
        new_road.link.successor = RoadLinkSuccessor(
            successor.get("elementType"),
            successor.get("elementId"),
            successor.get("contactPoint"),
        )

    for neighbor in opendrive_road_link.findall("neighbor"):
        new_neighbor = RoadLinkNeighbor(
            neighbor.get("side"), neighbor.get("elementId"), neighbor.get("direction")
        )

        new_road.link.neighbors.append(new_neighbor)


def parse_opendrive_road_type(road: Road, opendrive_xml_road_type: etree.ElementTree):
    """
    Parse opendrive road type and appends it to road object.

    :param road: Road to append the parsed road_type to types.
    :param opendrive_xml_road_type: XML element which contains the information.
    """
    speed = None
    if opendrive_xml_road_type.find("speed") is not None:
        speed = RoadTypeSpeed(
            max_speed=opendrive_xml_road_type.find("speed").get("max"),
            unit=opendrive_xml_road_type.find("speed").get("unit"),
        )

    road_type = RoadType(
        s_pos=opendrive_xml_road_type.get("s"),
        use_type=opendrive_xml_road_type.get("type"),
        speed=speed,
    )
    road.types.append(road_type)


def parse_opendrive_road_geometry(new_road: Road, road_geometry: etree.ElementTree):
    """
    Parse OpenDRIVE road geometry and appends it to road object.

    :param new_road: Road to append the parsed road geometry.
    :param road_geometry: XML element which contains the information.
    """
    start_coord = [float(road_geometry.get("x")), float(road_geometry.get("y"))]

    if road_geometry.find("line") is not None:
        new_road.planView.addLine(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
        )

    elif road_geometry.find("spiral") is not None:
        new_road.planView.addSpiral(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(road_geometry.find("spiral").get("curvStart")),
            float(road_geometry.find("spiral").get("curvEnd")),
        )

    elif road_geometry.find("arc") is not None:
        new_road.planView.addArc(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(road_geometry.find("arc").get("curvature")),
        )

    elif road_geometry.find("poly3") is not None:
        new_road.planView.addPoly3(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(road_geometry.find("poly3").get("a")),
            float(road_geometry.find("poly3").get("b")),
            float(road_geometry.find("poly3").get("c")),
            float(road_geometry.find("poly3").get("d")),
        )
        # raise NotImplementedError()

    elif road_geometry.find("paramPoly3") is not None:
        if road_geometry.find("paramPoly3").get("pRange"):

            if road_geometry.find("paramPoly3").get("pRange") == "arcLength":
                p_max = float(road_geometry.get("length"))
            else:
                p_max = None
        else:
            p_max = None

        new_road.planView.addParamPoly3(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(road_geometry.find("paramPoly3").get("aU")),
            float(road_geometry.find("paramPoly3").get("bU")),
            float(road_geometry.find("paramPoly3").get("cU")),
            float(road_geometry.find("paramPoly3").get("dU")),
            float(road_geometry.find("paramPoly3").get("aV")),
            float(road_geometry.find("paramPoly3").get("bV")),
            float(road_geometry.find("paramPoly3").get("cV")),
            float(road_geometry.find("paramPoly3").get("dV")),
            p_max,
        )

    else:
        raise Exception("invalid xml")


def parse_opendrive_road_elevation_profile(new_road: Road, road_elevation_profile: etree.ElementTree):
    """
    Parse OpenDRIVE road elevation profile and appends it to road object.

    :param new_road: Road to append the parsed road elevation profile.
    :param road_elevation_profile: XML element which contains the information.
    """
    for elevation in road_elevation_profile.findall("elevation"):
        new_elevation = (
            RoadElevationProfile(
                float(elevation.get("a")),
                float(elevation.get("b")),
                float(elevation.get("c")),
                float(elevation.get("d")),
                start_pos=float(elevation.get("s")),
            ),
        )

        new_road.elevationProfile.elevations.append(new_elevation)


def parse_opendrive_road_lateral_profile(new_road: Road, road_lateral_profile: etree.ElementTree):
    """
    Parse OpenDRIVE road lateral profile and appends it to road object.

    :param new_road: Road to append the parsed road lateral profile.
    :param road_lateral_profile: XML element which contains the information.
    """
    for super_elevation in road_lateral_profile.findall("superelevation"):
        new_super_elevation = RoadLateralProfileSuperelevation(
            float(super_elevation.get("a")),
            float(super_elevation.get("b")),
            float(super_elevation.get("c")),
            float(super_elevation.get("d")),
            start_pos=float(super_elevation.get("s")),
        )

        new_road.lateralProfile.superelevations.append(new_super_elevation)

    for crossfall in road_lateral_profile.findall("crossfall"):
        new_crossfall = RoadLateralProfileCrossfall(
            float(crossfall.get("a")),
            float(crossfall.get("b")),
            float(crossfall.get("c")),
            float(crossfall.get("d")),
            side=crossfall.get("side"),
            start_pos=float(crossfall.get("s")),
        )

        new_road.lateralProfile.crossfalls.append(new_crossfall)

    for shape in road_lateral_profile.findall("shape"):
        new_shape = RoadLateralProfileShape(
            float(shape.get("a")),
            float(shape.get("b")),
            float(shape.get("c")),
            float(shape.get("d")),
            start_pos=float(shape.get("s")),
            start_pos_t=float(shape.get("t")),
        )

        new_road.lateralProfile.shapes.append(new_shape)


def parse_opendrive_road_lane_offset(new_road: Road, lane_offset: etree.ElementTree):
    """
    Parse OpenDRIVE road lane offset and appends it to road object.

    :param new_road: Road to append the parsed road lane offset.
    :param lane_offset: XML element which contains the information.
    """
    new_lane_offset = RoadLanesLaneOffset(
        float(lane_offset.get("a")),
        float(lane_offset.get("b")),
        float(lane_offset.get("c")),
        float(lane_offset.get("d")),
        start_pos=float(lane_offset.get("s")),
    )

    new_road.lanes.laneOffsets.append(new_lane_offset)


def parse_opendrive_road_lane_section(new_road: Road, lane_section_id: int, lane_section: etree.ElementTree):
    """
    Parse OpenDRIVE road lane section and appends it to road object.

    :param new_road: Road to append the parsed road lane section.
    :param lane_section_id: ID which should be assigned to lane section.
    :param lane_section: XML element which contains the information.
    """

    new_lane_section = RoadLanesSection(road=new_road)

    # NOTE: Manually enumerate lane sections for referencing purposes
    new_lane_section.idx = lane_section_id

    new_lane_section.sPos = float(lane_section.get("s"))
    new_lane_section.singleSide = lane_section.get("singleSide")

    sides = dict(
        left=new_lane_section.leftLanes,
        center=new_lane_section.centerLanes,
        right=new_lane_section.rightLanes,
    )

    for sideTag, newSideLanes in sides.items():

        side = lane_section.find(sideTag)

        # It is possible one side is not present
        if side is None:
            continue

        for lane in side.findall("lane"):

            new_lane = RoadLaneSectionLane(
                parentRoad=new_road, lane_section=new_lane_section
            )
            new_lane.id = lane.get("id")
            new_lane.type = lane.get("type")

            # In some sample files the level is not specified according to the OpenDRIVE spec
            new_lane.level = (
                "true" if lane.get("level") in [1, "1", "true"] else "false"
            )

            # Lane Links
            if lane.find("link") is not None:

                if lane.find("link").find("predecessor") is not None:
                    new_lane.link.predecessorId = (
                        lane.find("link").find("predecessor").get("id")
                    )

                if lane.find("link").find("successor") is not None:
                    new_lane.link.successorId = (
                        lane.find("link").find("successor").get("id")
                    )

            # Width
            for widthIdx, width in enumerate(lane.findall("width")):
                new_width = RoadLaneSectionLaneWidth(
                    float(width.get("a")),
                    float(width.get("b")),
                    float(width.get("c")),
                    float(width.get("d")),
                    idx=widthIdx,
                    start_offset=float(width.get("sOffset")),
                )

                new_lane.widths.append(new_width)

            # Border
            for borderIdx, border in enumerate(lane.findall("border")):
                new_border = RoadLaneSectionLaneBorder(
                    float(border.get("a")),
                    float(border.get("b")),
                    float(border.get("c")),
                    float(border.get("d")),
                    idx=borderIdx,
                    start_offset=float(border.get("sOffset")),
                )

                new_lane.borders.append(new_border)

            if lane.find("width") is None and lane.find("border") is not None:
                new_lane.widths = new_lane.borders
                new_lane.has_border_record = True

            # Road Marks
            if lane.find("roadMark") is not None:
                mark = lane.find("roadMark")
                road_mark = RoadLaneRoadMark()

                road_mark.type = mark.get("type")
                road_mark.weight = mark.get("weight")
                road_mark.SOffset = mark.get("SOffset")

                new_lane.road_mark = road_mark

            # Material
            # TODO implementation

            # Visiblility
            # TODO implementation

            # Speed
            # TODO implementation

            # Access
            # TODO implementation

            # Lane Height
            # TODO implementation

            # Rules
            # TODO implementation

            newSideLanes.append(new_lane)

    new_road.lanes.lane_sections.append(new_lane_section)


def parse_opendrive_road_signal(new_road: Road, road_signal: etree.ElementTree):
    """
    Parse OpenDRIVE road signal and appends it to road object.

    :param new_road: Road to append the parsed road lane section.
    :param road_signal: XML element which contains the information.
    """
    new_signal = RoadSignal()
    new_signal.id = road_signal.get("id")
    new_signal.s = road_signal.get("s")  # position along the reference curve
    new_signal.t = road_signal.get("t")  # position away from the reference curve
    new_signal.name = road_signal.get("name")
    new_signal.country = road_signal.get("country")
    new_signal.type = road_signal.get("type")
    new_signal.subtype = road_signal.get("subtype")
    new_signal.orientation = road_signal.get("orientation")
    new_signal.dynamic = road_signal.get("dynamic")
    new_signal.signal_value = road_signal.get("value")
    new_signal.unit = road_signal.get("unit")
    new_signal.text = road_signal.get("text")

    new_road.addSignal(new_signal)


def parse_opendrive_road_signal_reference(new_road: Road, road_signal_reference: etree.ElementTree):
    """
    Parse OpenDRIVE road signal reference and appends it to road object.

    :param new_road: Road to append the parsed road signal reference.
    :param road_signal_reference: XML element which contains the information.
    """
    new_signal_reference = SignalReference()
    new_signal_reference.id = road_signal_reference.get("id")
    new_signal_reference.s = road_signal_reference.get("s")  # position along the reference curve
    new_signal_reference.t = road_signal_reference.get("t")  # position away from the reference curve
    new_signal_reference.orientation = road_signal_reference.get("orientation")

    new_road.addSignalReference(new_signal_reference)


def parse_opendrive_road(opendrive: OpenDrive, road: etree.ElementTree):
    """
    Parse OpenDRIVE road and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed road.
    :param road: XML element which contains the information.
    """

    new_road = Road()

    new_road.id = int(road.get("id"))
    new_road.name = road.get("name")

    junction_id = int(road.get("junction")) if road.get("junction") != "-1" else None

    if junction_id:
        new_road.junction = opendrive.getJunction(junction_id)

    # TODO verify road length
    new_road.length = float(road.get("length"))

    # Links
    opendrive_road_link = road.find("link")
    if opendrive_road_link is not None:
        parse_opendrive_road_link(new_road, opendrive_road_link)

    # Type
    for opendrive_xml_road_type in road.findall("type"):
        parse_opendrive_road_type(new_road, opendrive_xml_road_type)

    # Plan view
    for road_geometry in road.find("planView").findall("geometry"):
        parse_opendrive_road_geometry(new_road, road_geometry)
    # Elevation profile
    road_elevation_profile = road.find("elevationProfile")
    if road_elevation_profile is not None:
        parse_opendrive_road_elevation_profile(new_road, road_elevation_profile)

    # Lateral profile
    road_lateral_profile = road.find("lateralProfile")
    if road_lateral_profile is not None:
        parse_opendrive_road_lateral_profile(new_road, road_lateral_profile)

    # Lanes
    lanes = road.find("lanes")

    if lanes is None:
        raise Exception("Road must have lanes element")

    # Lane offset
    for lane_offset in lanes.findall("laneOffset"):
        parse_opendrive_road_lane_offset(new_road, lane_offset)

    # Lane sections
    for lane_section_id, lane_section in enumerate(
        road.find("lanes").findall("laneSection")
    ):
        parse_opendrive_road_lane_section(new_road, lane_section_id, lane_section)

    # Objects
    # TODO implementation

    # Signals
    if road.find("signals") is not None:
        for road_signal in road.find("signals").findall("signal"):
            if road_signal is not None:
                parse_opendrive_road_signal(new_road, road_signal)
        for road_signal_reference in road.find("signals").findall("signalReference"):
            # Parsing signal reference element
            if road_signal_reference is not None:
                parse_opendrive_road_signal_reference(new_road, road_signal_reference)
    else:
        pass

    calculate_lane_section_lengths(new_road)

    opendrive.roads.append(new_road)


def calculate_lane_section_lengths(new_road: Road):
    """
    Calculates lane section length for OpenDRIVE road.

    :param new_road: OpenDRIVE road for which lane section length should be calculated.
    """

    # OpenDRIVE does not provide lane section lengths by itself, calculate them by ourselves
    for lane_section in new_road.lanes.lane_sections:

        # Last lane section in road
        if lane_section.idx + 1 >= len(new_road.lanes.lane_sections):
            lane_section.length = new_road.planView.length - lane_section.sPos

        # All but the last lane section end at the succeeding one
        else:
            lane_section.length = (
                new_road.lanes.lane_sections[lane_section.idx + 1].sPos
                - lane_section.sPos
            )

    # OpenDRIVE does not provide lane width lengths by itself, calculate them by ourselves
    for lane_section in new_road.lanes.lane_sections:
        for lane in lane_section.allLanes:
            widths_poses = np.array(
                [x.start_offset for x in lane.widths] + [lane_section.length]
            )
            widths_lengths = widths_poses[1:] - widths_poses[:-1]

            for widthIdx, width in enumerate(lane.widths):
                width.length = widths_lengths[widthIdx]


def parse_opendrive_header(opendrive: OpenDrive, header: etree.ElementTree):
    """
    Parse OpenDRIVE header and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed header.
    :param header: XML element which contains the information.
    """

    # Generates object out of the attributes of the header
    parsed_header = Header(
        header.get("revMajor"),
        header.get("revMinor"),
        header.get("name"),
        header.get("version"),
        header.get("date"),
        header.get("north"),
        header.get("south"),
        header.get("west"),
        header.get("vendor"),
    )

    # Reference
    if header.find("geoReference") is not None:
        parsed_header.geo_reference = header.find("geoReference").text

    opendrive.header = parsed_header


def parse_opendrive_junction(opendrive: OpenDrive, junction: etree.ElementTree):
    """
    Parse OpenDRIVE junction and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed junction.
    :param junction: XML element which contains the information.
    """

    new_junction = Junction()

    new_junction.id = int(junction.get("id"))
    new_junction.name = str(junction.get("name"))

    for connection in junction.findall("connection"):

        new_connection = JunctionConnection()

        new_connection.id = connection.get("id")
        new_connection.incomingRoad = connection.get("incomingRoad")
        new_connection.connectingRoad = connection.get("connectingRoad")
        new_connection.contactPoint = connection.get("contactPoint")

        for laneLink in connection.findall("laneLink"):
            new_lane_link = JunctionConnectionLaneLink()

            new_lane_link.fromId = laneLink.get("from")
            new_lane_link.toId = laneLink.get("to")

            new_connection.addLaneLink(new_lane_link)

        new_junction.addConnection(new_connection)

    opendrive.junctions.append(new_junction)
