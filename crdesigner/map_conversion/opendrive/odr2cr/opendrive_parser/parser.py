import logging
import warnings
from pathlib import Path
from typing import Dict, Optional

import numpy as np
from lxml import etree

from crdesigner.common.config.opendrive_config import open_drive_config
from crdesigner.map_conversion.common.utils import (
    clean_projection_string,
    generate_unique_id,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    Connection as JunctionConnection,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    Junction,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.junction import (
    LaneLink as JunctionConnectionLaneLink,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.opendrive import (
    Header,
    OpenDrive,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.road import (
    Road,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadElevationProfile import (
    ElevationRecord as RoadElevationProfile,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    Lane as RoadLaneSectionLane,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    LaneBorder as RoadLaneSectionLaneBorder,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    LaneOffset as RoadLanesLaneOffset,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    LaneSection as RoadLanesSection,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    LaneWidth as RoadLaneSectionLaneWidth,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLanes import (
    RoadMark as RoadLaneRoadMark,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLateralProfile import (
    Crossfall as RoadLateralProfileCrossfall,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLateralProfile import (
    Shape as RoadLateralProfileShape,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLateralProfile import (
    Superelevation as RoadLateralProfileSuperelevation,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLink import (
    Neighbor as RoadLinkNeighbor,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLink import (
    Predecessor as RoadLinkPredecessor,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadLink import (
    Successor as RoadLinkSuccessor,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadObject import (
    Object as RoadObject,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadObject import (
    ObjectOutlineCorner,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadSignal import (
    Signal as RoadSignal,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadSignal import (
    SignalReference,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadtype import (
    RoadType,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.elements.roadtype import (
    Speed as RoadTypeSpeed,
)


def parse_opendrive(file_path: Path, odr_conf: open_drive_config = open_drive_config) -> OpenDrive:
    """
    Tries to parse XML tree, returns OpenDRIVE object

    :param file_path: path to OpenDRIVE file
    :param odr_conf: OpenDRIVE configuration.
    :return: Object representing an OpenDrive specification
    """
    generate_unique_id(odr_conf.initial_cr_id)  # reset IDs

    with file_path.open("r") as file_in:
        root_node = etree.parse(file_in)

        for elem in root_node.getiterator():
            if not (
                isinstance(elem, etree._Comment) or isinstance(elem, etree._ProcessingInstruction)
            ):
                elem.tag = etree.QName(elem).localname
        etree.cleanup_namespaces(root_node)

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

    :param new_road: Road element where link should be added
    :param opendrive_road_link: Loaded OpenDRIVE link
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
    Parse OpenDRIVE road type and appends it to road object.

    :param road: Road to append the parsed road_type to types
    :param opendrive_xml_road_type: XML element which contains the information
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


def defaultval(val: Optional[str], name: str, default: str = "0") -> str:
    """
    Replace a given value with a default value should it not exist in the XML and print a warning.

    :param val: Value that is inspected to be None
    :param name: Name of the variable inspected
    :param default: Alternative value given a val is None
    """
    default = str(default)
    if val is None:
        warnings.warn(
            "Parser could not find value for " + name + ", " + default + " is used per default."
        )
        return default
    else:
        return val


def parse_opendrive_road_geometry(
    new_road: Road, road_geometry: etree.ElementTree, offset: Dict[str, str]
):
    """
    Parse OpenDRIVE road geometry and appends it to road object.

    :param new_road: Road to append the parsed road geometry
    :param road_geometry: XML element which contains the information
    :param offset: Offset defined in OpenDRIVE.
    """
    start_coord = np.array(
        [
            float(road_geometry.get("x")) - float(offset["x"]),
            float(road_geometry.get("y")) - float(offset["y"]),
        ]
    )

    if road_geometry.find("line") is not None:
        new_road.plan_view.add_line(
            start_coord,
            float(road_geometry.get("hdg")) - float(offset["hdg"]),
            float(road_geometry.get("length")),
        )

    elif road_geometry.find("spiral") is not None:
        curv_start = float(
            defaultval(road_geometry.find("spiral").get("curvStart"), "spiral.curvStart")
        )
        curv_end = float(defaultval(road_geometry.find("spiral").get("curvEnd"), "spiral.curvEnd"))
        if np.isclose(curv_start, curv_end):
            raise AttributeError(
                "Curvature at the start and at the end of a spiral must be different"
            )
        new_road.plan_view.add_spiral(
            start_coord,
            float(road_geometry.get("hdg")) - float(offset["hdg"]),
            float(road_geometry.get("length")),
            curv_start,
            curv_end,
        )
    elif road_geometry.find("arc") is not None:
        new_road.plan_view.add_arc(
            start_coord,
            float(road_geometry.get("hdg")) - float(offset["hdg"]),
            float(road_geometry.get("length")),
            float(road_geometry.find("arc").get("curvature")),
        )

    elif road_geometry.find("poly3") is not None:
        new_road.plan_view.add_poly3(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(defaultval(road_geometry.find("poly3").get("a"), "poly3.a")),
            float(defaultval(road_geometry.find("poly3").get("b"), "poly3.b")),
            float(defaultval(road_geometry.find("poly3").get("c"), "poly3.c")),
            float(defaultval(road_geometry.find("poly3").get("d"), "poly3.d")),
        )
        # NotImplementedError()

    elif road_geometry.find("paramPoly3") is not None:
        if road_geometry.find("paramPoly3").get("pRange"):
            if road_geometry.find("paramPoly3").get("pRange") == "arcLength":
                p_max = float(road_geometry.get("length"))
            else:
                p_max = None
        else:
            p_max = None

        new_road.plan_view.add_param_poly3(
            start_coord,
            float(road_geometry.get("hdg")),
            float(road_geometry.get("length")),
            float(defaultval(road_geometry.find("paramPoly3").get("aU"), "paramPoly3.aU")),
            float(defaultval(road_geometry.find("paramPoly3").get("bU"), "paramPoly3.bU", 1)),
            float(defaultval(road_geometry.find("paramPoly3").get("cU"), "paramPoly3.cU")),
            float(defaultval(road_geometry.find("paramPoly3").get("dU"), "paramPoly3.dU")),
            float(defaultval(road_geometry.find("paramPoly3").get("aV"), "paramPoly3.aV")),
            float(defaultval(road_geometry.find("paramPoly3").get("bV"), "paramPoly3.bV")),
            float(defaultval(road_geometry.find("paramPoly3").get("cV"), "paramPoly3.cV")),
            float(defaultval(road_geometry.find("paramPoly3").get("dV"), "paramPoly3.dV")),
            p_max,
        )

    else:
        raise Exception("invalid xml")


def parse_opendrive_road_elevation_profile(
    new_road: Road, road_elevation_profile: etree.ElementTree
):
    """
    Parse OpenDRIVE road elevation profile and appends it to road object.

    :param new_road: Road to append the parsed road elevation profile
    :param road_elevation_profile: XML element which contains the information
    """
    for elevation in road_elevation_profile.findall("elevation"):
        new_elevation = RoadElevationProfile(
            float(defaultval(elevation.get("a"), "elevation.a")),
            float(defaultval(elevation.get("b"), "elevation.b")),
            float(defaultval(elevation.get("c"), "elevation.c")),
            float(defaultval(elevation.get("d"), "elevation.d")),
            start_pos=float(defaultval(elevation.get("s"), "elevation.s")),
        )

        new_road.elevation_profile.elevations.append(new_elevation)


def parse_opendrive_road_lateral_profile(new_road: Road, road_lateral_profile: etree.ElementTree):
    """
    Parse OpenDRIVE road lateral profile and appends it to road object.

    :param new_road: Road to append the parsed road lateral profile
    :param road_lateral_profile: XML element which contains the information
    """
    for super_elevation in road_lateral_profile.findall("superelevation"):
        new_super_elevation = RoadLateralProfileSuperelevation(
            float(defaultval(super_elevation.get("a"), "super_elevation.a")),
            float(defaultval(super_elevation.get("b"), "super_elevation.b")),
            float(defaultval(super_elevation.get("c"), "super_elevation.c")),
            float(defaultval(super_elevation.get("d"), "super_elevation.d")),
            start_pos=float(defaultval(super_elevation.get("s"), "super_elevation.s")),
        )

        new_road.lateral_profile.superelevations.append(new_super_elevation)

    for crossfall in road_lateral_profile.findall("crossfall"):
        new_crossfall = RoadLateralProfileCrossfall(
            float(defaultval(crossfall.get("a"), "crossfall.a")),
            float(defaultval(crossfall.get("b"), "crossfall.b")),
            float(defaultval(crossfall.get("c"), "crossfall.c")),
            float(defaultval(crossfall.get("d"), "crossfall.d")),
            side=defaultval(crossfall.get("side"), "crossfall.side", "both"),
            start_pos=float(defaultval(crossfall.get("s"), "crossfall.s")),
        )

        new_road.lateral_profile.crossfalls.append(new_crossfall)

    for shape in road_lateral_profile.findall("shape"):
        new_shape = RoadLateralProfileShape(
            float(defaultval(shape.get("a"), "shape.a")),
            float(defaultval(shape.get("b"), "shape.b")),
            float(defaultval(shape.get("c"), "shape.c")),
            float(defaultval(shape.get("d"), "shape.d")),
            start_pos=float(defaultval(shape.get("s"), "shape.s")),
            start_pos_t=float(defaultval(shape.get("t"), "shape.t")),
        )

        new_road.lateral_profile.shapes.append(new_shape)


def parse_opendrive_road_lane_offset(new_road: Road, lane_offset: etree.ElementTree):
    """
    Parse OpenDRIVE road lane offset and appends it to road object.

    :param new_road: Road to append the parsed road lane offset
    :param lane_offset: XML element which contains the information
    """
    new_lane_offset = RoadLanesLaneOffset(
        float(defaultval(lane_offset.get("a"), "lane_offset.a")),
        float(defaultval(lane_offset.get("b"), "lane_offset.b")),
        float(defaultval(lane_offset.get("c"), "lane_offset.c")),
        float(defaultval(lane_offset.get("d"), "lane_offset.d")),
        start_pos=float(defaultval(lane_offset.get("s"), "lane_offset.s")),
    )

    new_road.lanes.lane_offsets.append(new_lane_offset)


def parse_opendrive_road_lane_section(
    new_road: Road, lane_section_id: int, lane_section: etree.ElementTree
):
    """
    Parse OpenDRIVE road lane section and appends it to road object.

    :param new_road: Road to append the parsed road lane section
    :param lane_section_id: ID which should be assigned to lane section
    :param lane_section: XML element which contains the information
    """

    new_lane_section = RoadLanesSection(road=new_road)

    # NOTE: Manually enumerate lane sections for referencing purposes
    new_lane_section.idx = lane_section_id

    new_lane_section.sPos = float(lane_section.get("s"))
    new_lane_section.single_side = lane_section.get("singleSide")

    sides = dict(
        left=new_lane_section.left_lanes,
        center=new_lane_section.center_lanes,
        right=new_lane_section.right_lanes,
    )

    for sideTag, newSideLanes in sides.items():
        side = lane_section.find(sideTag)

        # It is possible one side is not present
        if side is None:
            continue

        for lane in side.findall("lane"):
            new_lane = RoadLaneSectionLane(parentRoad=new_road, lane_section=new_lane_section)
            new_lane.id = lane.get("id")
            new_lane.type = lane.get("type")

            # In some sample files the level is not specified according to the OpenDRIVE spec
            new_lane.level = "true" if lane.get("level") in [1, "1", "true"] else "false"

            # Lane Links
            if lane.find("link") is not None:
                if lane.find("link").find("predecessor") is not None:
                    new_lane.link.predecessorId = lane.find("link").find("predecessor").get("id")

                if lane.find("link").find("successor") is not None:
                    new_lane.link.successorId = lane.find("link").find("successor").get("id")

            # Width
            for widthIdx, width in enumerate(lane.findall("width")):
                new_width = RoadLaneSectionLaneWidth(
                    float(defaultval(width.get("a"), "width.a")),
                    float(defaultval(width.get("b"), "width.b")),
                    float(defaultval(width.get("c"), "width.c")),
                    float(defaultval(width.get("d"), "width.d")),
                    idx=widthIdx,
                    start_offset=float(defaultval(width.get("sOffset"), "width.sOffset")),
                )

                new_lane.widths.append(new_width)

            # Border
            for borderIdx, border in enumerate(lane.findall("border")):
                new_border = RoadLaneSectionLaneBorder(
                    float(defaultval(border.get("a"), "border.a")),
                    float(defaultval(border.get("b"), "border.b")),
                    float(defaultval(border.get("c"), "border.c")),
                    float(defaultval(border.get("d"), "border.d")),
                    idx=borderIdx,
                    start_offset=float(defaultval(border.get("sOffset"), "border.sOffset")),
                )

                new_lane.borders.append(new_border)

            if lane.find("width") is None and lane.find("border") is not None:
                new_lane.widths = new_lane.borders
                new_lane.has_border_record = True

            # Road Marks
            for mark in lane.findall("roadMark"):
                road_mark = RoadLaneRoadMark()

                road_mark.type = mark.get("type")
                if mark.get("weight") is not None:
                    road_mark.weight = mark.get("weight")
                road_mark.SOffset = mark.get("sOffset")

                new_lane.road_mark.append(road_mark)

            # Material and Rules are not implemented in CommonRoad -> no need

            # Visiblility -> not part of ASAM OpenDRIVE 1.7.0 anymore
            # TODO implementation

            # Speed
            if lane.find("speed") is not None:
                # speed is always converted to m/s
                unit = lane.find("speed").get("unit")
                if unit == "km/h":
                    new_lane.speed = float(lane.find("speed").get("max")) / 3.6
                elif unit == "mph":
                    new_lane.speed = float(lane.find("speed").get("max")) / 2.237
            else:
                new_lane.speed = None

            # Access
            for _access in lane.findall("access"):
                new_lane.access += [
                    [
                        str(_access.get("restriction")),
                        str(_access.get("rule")),
                        float(_access.get("sOffset")),
                    ]
                ]
            # Lane Height
            # TODO implementation

            newSideLanes.append(new_lane)

    new_road.lanes.lane_sections.append(new_lane_section)


def parse_opendrive_road_signal(new_road: Road, road_signal: etree.ElementTree):
    """
    Parse OpenDRIVE road signal and appends it to road object.

    :param new_road: Road to append the parsed road lane section
    :param road_signal: XML element which contains the information
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
    if road_signal.find("validity") is not None:
        new_signal.validity_from = road_signal.find("validity").get("fromLane")
        new_signal.validity_to = road_signal.find("validity").get("toLane")
    if (
        road_signal.find("userData") is not None
        and road_signal.find("userData").find("vectorSignal") is not None
    ):
        new_signal.signal_id = road_signal.find("userData") is not None and road_signal.find(
            "userData"
        ).find("vectorSignal").get("signalId")

    new_road.add_signal(new_signal)


def parse_opendrive_road_signal_reference(new_road: Road, road_signal_reference: etree.ElementTree):
    """
    Parse OpenDRIVE road signal reference and appends it to road object.

    :param new_road: Road to append the parsed road signal reference
    :param road_signal_reference: XML element which contains the information
    """
    new_signal_reference = SignalReference()
    new_signal_reference.id = road_signal_reference.get("id")
    new_signal_reference.s = road_signal_reference.get("s")  # position along the reference curve
    new_signal_reference.t = road_signal_reference.get(
        "t"
    )  # position away from the reference curve
    new_signal_reference.orientation = road_signal_reference.get("orientation")
    if road_signal_reference.find("validity") is not None:
        new_signal_reference.validity_from = road_signal_reference.find("validity").get("fromLane")
        new_signal_reference.validity_to = road_signal_reference.find("validity").get("toLane")
    if (
        road_signal_reference.find("userData") is not None
        and road_signal_reference.find("userData").find("vectorSignal") is not None
    ):
        if road_signal_reference.find("userData").find("vectorSignal").get("signalId") is not None:
            new_signal_reference.signal_id = (
                road_signal_reference.find("userData").find("vectorSignal").get("signalId")
            )
        if (
            road_signal_reference.find("userData").find("vectorSignal").get("turnRelation")
            is not None
        ):
            new_signal_reference.turn_relation = (
                road_signal_reference.find("userData").find("vectorSignal").get("turnRelation")
            )

    new_road.add_signal_reference(new_signal_reference)


def parse_opendrive_road(opendrive: OpenDrive, road: etree.ElementTree):
    """
    Parse OpenDRIVE road and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed road
    :param road: XML element which contains the information
    """

    new_road = Road()

    new_road.id = int(road.get("id"))
    new_road.name = road.get("name")
    new_road.driving_direction = True  # RHT default
    driving_direction = road.get("rule")
    if driving_direction is not None:
        if driving_direction == "LHT":
            new_road.driving_direction = False

    junction_id = int(road.get("junction")) if road.get("junction") != "-1" else None

    if junction_id:
        new_road.junction = opendrive.getJunction(junction_id)

    # TODO verify road length
    # length had no getter/setter and attribute was therefore deleted in road.py
    # new_road.length = float(road.get("length"))

    # Links
    opendrive_road_link = road.find("link")
    if opendrive_road_link is not None:
        parse_opendrive_road_link(new_road, opendrive_road_link)

    # Type
    for opendrive_xml_road_type in road.findall("type"):
        parse_opendrive_road_type(new_road, opendrive_xml_road_type)

    # Plan view
    for road_geometry in road.find("planView").findall("geometry"):
        parse_opendrive_road_geometry(new_road, road_geometry, opendrive.header.offset)
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
    for lane_section_id, lane_section in enumerate(road.find("lanes").findall("laneSection")):
        parse_opendrive_road_lane_section(new_road, lane_section_id, lane_section)

    # Objects
    if road.find("objects") is not None:
        for obj in road.find("objects").findall("object"):
            if obj is not None:
                parse_opendrive_road_object(new_road, obj)

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


def parse_opendrive_road_object(new_road: Road, obj: etree.ElementTree):
    """Parses opendrive road object, creates roadObject from it and adds it to the road.

    :param new_road: The road to add the object to.
    :param obj: XML road element which is parsed.
    """
    corners = []
    if obj.find("outlines") is not None:
        outlines = obj.find("outlines").findall("outline")
    elif (
        obj.find("outline") is not None
    ):  # based on the OpenDRIVE specification outline should be within outlines;
        # probably a bug in a previous RoadRunner version
        outlines = [obj.find("outline")]
    else:
        outlines = []

    if len(outlines) > 0:
        if len(outlines) > 1:
            logging.warning(
                "We do not support outlines consisting of several shapes at the moment."
            )
        for corner_local in outlines[0].findall("cornerLocal"):
            if corner_local is not None:
                corner = ObjectOutlineCorner()
                corner.u = corner_local.get("u")
                corner.v = corner_local.get("v")
                corner.z = corner_local.get("z")
                corners.append(corner)

    road_object = RoadObject()
    try:
        if obj.get("type") is not None:
            road_object.type = obj.get("type")
        if obj.get("id") is not None:
            road_object.id = obj.get("id")
        if obj.get("s") is not None:
            road_object.s = obj.get("s")
        if obj.get("t") is not None:
            road_object.t = obj.get("t")
        if obj.get("name") is not None:
            road_object.name = obj.get("name")
        if obj.get("width") is not None:
            road_object.width = obj.get("width")
        if obj.get("height") is not None:
            road_object.height = obj.get("height")
        if obj.get("length") is not None:
            road_object.validLength = obj.get("length")
        if obj.get("zOffset") is not None:
            road_object.zOffset = obj.get("zOffset")
        if obj.get("validLength") is not None:
            road_object.validLength = obj.get("validLength")
        if obj.get("orientation") is not None:
            road_object.orientation = obj.get("orientation")
        if obj.get("hdg") is not None:
            road_object.hdg = obj.get("hdg")
        if obj.get("pitch") is not None:
            road_object.pitch = obj.get("pitch")
        if obj.get("roll") is not None:
            road_object.roll = obj.get("roll")

        road_object.outline = corners
    except KeyError:
        logging.error(
            "parse_opendrive_road_object: Error during parsing of road objects. "
            "Object id {}".format(obj.attrib.get("id"))
        )

    new_road.add_object(road_object)


def calculate_lane_section_lengths(new_road: Road):
    """
    Calculates lane section length for OpenDRIVE road.

    :param new_road: OpenDRIVE road for which lane section length should be calculated
    """

    # OpenDRIVE does not provide lane section lengths by itself, calculate them by ourselves
    for lane_section in new_road.lanes.lane_sections:
        # Last lane section in road
        if lane_section.idx + 1 >= len(new_road.lanes.lane_sections):
            lane_section.length = new_road.plan_view.length - lane_section.sPos

        # All but the last lane section end at the succeeding one
        else:
            lane_section.length = (
                new_road.lanes.lane_sections[lane_section.idx + 1].sPos - lane_section.sPos
            )

    # OpenDRIVE does not provide lane width lengths by itself, calculate them by ourselves
    for lane_section in new_road.lanes.lane_sections:
        for lane in lane_section.all_lanes:
            widths_poses = np.array([x.start_offset for x in lane.widths] + [lane_section.length])
            widths_lengths = widths_poses[1:] - widths_poses[:-1]

            for widthIdx, width in enumerate(lane.widths):
                width.length = widths_lengths[widthIdx]


def parse_opendrive_header(opendrive: OpenDrive, header: etree.ElementTree):
    """
    Parse OpenDRIVE header and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed header
    :param header: XML element which contains the information
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
        header.get("east"),
        header.get("west"),
        header.get("vendor"),
    )

    # Reference
    if header.find("geoReference") is not None:
        parsed_header.geo_reference = clean_projection_string(header.find("geoReference").text)

    # offset {x: , y: , z: , hdg:}
    if header.find("offset") is not None:
        parsed_header.offset = header.find("offset").attrib

    opendrive.header = parsed_header


def parse_opendrive_junction(opendrive: OpenDrive, junction: etree.ElementTree):
    """
    Parse OpenDRIVE junction and appends it to OpenDRIVE object.

    :param opendrive: OpenDRIVE object to append the parsed junction
    :param junction: XML element which contains the information
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
