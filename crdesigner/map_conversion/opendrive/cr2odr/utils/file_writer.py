from datetime import datetime

import numpy as np
from lxml import etree

from crdesigner.map_conversion.opendrive.cr2odr.utils import config


class Writer:
    """
    This class creates a OpenDRIVE file. The xml etree element is written as OpenDRIVE file.
    """

    def __init__(self, file_path_out: str, geo_reference: str) -> None:
        """
        This function let class Write to initialize the object with path for storing converted
        OpenDRIVE file and initialize the instance variables and creates header child elements
        with different attributes.

        :param file_path_out: path of converted OpenDRIVE file to be stored
        :geo_reference: Geo-reference of map.
        """
        self.file_path_out = file_path_out
        self.root = etree.Element(config.OPENDRIVE)
        etree.indent(self.root, space="    ")
        self.write_header(geo_reference)
        self.tree = etree.ElementTree(self.root)

    def save(self) -> None:
        """
        This function writes the OpenDRIVE file.
        """
        etree.indent(self.root, space="    ")
        self.tree.write(
            self.file_path_out,
            xml_declaration=True,
            method="xml",
            encoding="UTF-8",
            pretty_print=True,
        )

    # TODO: does this need to be <header></header> or is <header/> fine?
    def write_header(self, geo_reference: str) -> None:
        """
        This function creates header child element with various attributes and add it to OpenDrive root element.

        :param geo_reference: Geo-reference of the map.
        """
        name = self.file_path_out.split("/")[-1].split(".")[0]
        self.header = etree.SubElement(self.root, config.HEADER_TAG)
        self.header.set(config.HEADER_REV_MAJOR_TAG, "1")
        self.header.set(config.HEADER_REV_MINOR_TAG, "6")
        self.header.set(config.HEADER_VERSION_TAG, "1.0")
        self.header.set(config.NAME_TAG, name)
        mydate = datetime.now()
        self.header.set(config.HEADER_DATE_TAG, mydate.isoformat())
        val = 0
        self.header.set(config.NORTH, str.format(config.DOUBLE_FORMAT_PATTERN, val))
        self.header.set(config.SOUTH, str.format(config.DOUBLE_FORMAT_PATTERN, val))
        self.header.set(config.EAST, str.format(config.DOUBLE_FORMAT_PATTERN, val))
        self.header.set(config.WEST, str.format(config.DOUBLE_FORMAT_PATTERN, val))
        if geo_reference != "":
            self.geo_reference = etree.SubElement(self.header, config.GEO_REFFERENCE_TAG)
            self.geo_reference.text = f"<![CDATA[{geo_reference}]]>"

    def set_child_of_road(self, name: str) -> etree:
        """
        This function add sub-element to road parent element

        :param name: name of sub-element to be added
        :return: road element xml with specific sub element
        """
        return etree.SubElement(self.road, name)

    def create_road_childs(self) -> None:
        """
        This function creates child elements for road parent element.
        """
        # sub-element link - TODO
        self.link = self.set_child_of_road(config.LINK_TAG)

        # sub-element type - TODO
        self.type = self.set_child_of_road(config.TYPE_TAG)

        # sub-element planeview - TODO
        self.plane_view = self.set_child_of_road(config.PLAN_VIEW_TAG)

        # sub-element elevationProfile - TODO
        self.elevation_profile = self.set_child_of_road(config.ELEVATION_PROFILE_TAG)

        # sub-element lateralProfile - TODO
        self.lateral_profile = self.set_child_of_road(config.LATERAL_PROFILE_TAG)

        # sub-element lanes - TODO
        self.lanes = self.set_child_of_road(config.LANES_TAG)

        # sub-element objects - TODO
        self.objects = self.set_child_of_road(config.OBJECTS_TAG)

        # sub-element signals - TODO
        self.signals = self.set_child_of_road(config.SIGNALS_TAG)

    # this will later take a road element
    def write_road(self) -> None:
        """
        This function add road child element with various attributes to Opendrive root element.
        """
        # sub-element road
        # set self.road for every road so that we do not overwrite existing roads
        self.road = etree.SubElement(self.root, config.ROAD_TAG)
        self.create_road_childs()

        # Write type - TODO
        self.type.set(config.GEOMETRY_S_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, 0))
        self.type.set(config.TYPE_TAG, config.TOWN_TAG)

        # road name - TODO
        self.road.set(config.NAME_TAG, "")

        # road length - TODO this needs to be stored in the road object
        self.road.set(
            config.LENGTH_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, 10)
        )  # road.length))

        # road id - TODO this needs to be stored in the road object
        self.road.set(config.ID_TAG, str.format(config.ID_FORMAT_PATTERN, 100))  # road.counting))

        # road junction - TODO this needs to be stored in the road object
        self.road.set(
            config.JUNCTION_TAG, str.format(config.ID_FORMAT_PATTERN, -1)
        )  # road.junction))

    def print_line(
        self, s: np.float64, x: np.float64, y: np.float64, hdg: np.float64, length: np.float64
    ) -> None:
        """
        This function add geometry child element with various attribute to planView parent element and
        then add line child element to geometry parent element

        :param s: s-coordinate of start position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param length: Length of the element’s reference line
        """
        geometry = etree.SubElement(self.plane_view, config.GEOMETRY_TAG)
        geometry.set(config.GEOMETRY_S_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, s))
        geometry.set(config.GEOMETRY_X_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, x))
        geometry.set(config.GEOMETRY_Y_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, y))
        geometry.set(config.GEOMETRY_HEADING_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, hdg))
        geometry.set(config.LENGTH_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, length))

        # line = etree.SubElement(geometry, config.LINE_TAG)

    def print_spiral(
        self,
        s: np.float64,
        x: np.float64,
        y: np.float64,
        hdg: np.float64,
        length: np.float64,
        curv_start: np.float64,
        curv_end: np.float64,
    ):
        """
        This function add geometry child element with various attribute to planView parent element and
        then add spiral child element to geometry parent element

        :param s: s-coordinate of start-position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param length: Length of the element’s reference line
        """
        geometry = etree.SubElement(self.plane_view, config.GEOMETRY_TAG)
        geometry.set(config.GEOMETRY_S_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, s))
        geometry.set(config.GEOMETRY_X_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, x))
        geometry.set(config.GEOMETRY_Y_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, y))
        geometry.set(config.GEOMETRY_HEADING_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, hdg))
        geometry.set(config.LENGTH_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, length))

        spiral = etree.SubElement(geometry, config.SPIRAL_TAG)
        spiral.set(
            config.GEOMETRY_CURV_START_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, curv_start)
        )
        spiral.set(config.GEOMETRY_CURV_END_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, curv_end))

    def print_arc(
        self,
        s: np.float64,
        x: np.float64,
        y: np.float64,
        hdg: np.float64,
        length: np.float64,
        curvature: np.float64,
    ) -> None:
        """
        This function add geometry child element with various attribute to planView parent element and
        then add arc child element to geometry parent element

        :param s: s-coordinate of start-position
        :param x: Start position (x inertial)
        :param y: Start position (y inertial)
        :param hdg: Start orientation (inertial heading)
        :param length: Length of the element’s reference line
        :param curvature: Constant curvature throughout the element
        """
        geometry = etree.SubElement(self.plane_view, config.GEOMETRY_TAG)
        geometry.set(config.GEOMETRY_S_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, s))
        geometry.set(config.GEOMETRY_X_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, x))
        geometry.set(config.GEOMETRY_Y_COORDINATE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, y))
        geometry.set(config.GEOMETRY_HEADING_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, hdg))
        geometry.set(config.LENGTH_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, length))

        arc = etree.SubElement(geometry, config.ARC_TAG)
        arc.set(config.GEOMETRY_CURVATURE_TAG, str.format(config.DOUBLE_FORMAT_PATTERN, curvature))
