"""
CommonRoad to OpenStreetMap Converter

This module provides functionality to convert CommonRoad scenarios to OpenStreetMap (OSM) format.
"""

import logging
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.scenario import Location, Scenario
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from lxml import etree
from pyproj import CRS, Transformer

from crdesigner.common.config.general_config import GeneralConfig, general_config
from crdesigner.common.config.osm_config import OsmConfig, osm_config
from crdesigner.map_conversion.lanelet2.lanelet2 import Node, Way

logger = logging.getLogger(__name__)


class OSMDocument:
    """
    Container for OSM XML document with nodes, ways, and relations.
    """

    def __init__(self):
        self.nodes: List[Node] = []
        self.ways: List[Way] = []
        self.node_id_map: Dict[int, int] = {}  # Maps internal IDs to OSM IDs

    def add_node(self, node: Node):
        """Add a node to the OSM document."""
        self.nodes.append(node)

    def add_way(self, way: Way):
        """Add a way to the OSM document."""
        self.ways.append(way)

    def find_node_by_id(self, node_id: str) -> Optional[Node]:
        """Find a node by its ID."""
        for node in self.nodes:
            if node.id_ == str(node_id):
                return node
        return None

    def serialize_to_xml(self) -> bytes:
        """
        Serialize the OSM document to XML format.

        :return: XML bytes
        """
        osm = etree.Element("osm")
        osm.set("version", "0.6")
        osm.set("generator", "CommonRoad Scenario Designer")

        # Add all nodes
        for node in self.nodes:
            osm.append(node.serialize_to_xml())

        # Add all ways
        for way in self.ways:
            osm.append(way.serialize_to_xml())

        return etree.tostring(osm, pretty_print=True, xml_declaration=True, encoding="UTF-8")


class CR2OSMConverter:
    """
    Converter from CommonRoad format to OpenStreetMap format.

    This converter creates OSM ways representing road centerlines from CommonRoad lanelets.
    It preserves elevation data if present in 3D vertices.
    """

    def __init__(
        self, osm_config: OsmConfig = osm_config, cr_config: GeneralConfig = general_config
    ):
        """
        Initialize the CR2OSMConverter.

        :param osm_config: OSM configuration parameters
        :param cr_config: CommonRoad configuration parameters
        """
        self._osm_config = osm_config
        self._cr_config = cr_config
        self.transformer: Optional[Transformer] = None
        self.osm: Optional[OSMDocument] = None
        self._id_count = 1
        self.lanelet_network = None
        self.scenario_translation = (0, 0)

    def _create_transformer(self, scenario: Scenario):
        """
        Create a coordinate transformer from CommonRoad to WGS84 (lat/lon).

        The input projection is determined from the scenario's geo transformation if available,
        otherwise the default projection from config is used.
        """
        loc: Location = scenario.location
        proj_string_from = None

        if loc is not None and loc.geo_transformation is not None:
            geo_trans = loc.geo_transformation
            proj_string_from = geo_trans.geo_reference
            self.scenario_translation = (geo_trans.x_translation, geo_trans.y_translation)

            if geo_trans.z_rotation != 0.0 or geo_trans.scaling != 1.0:
                warnings.warn(
                    "<CR2OSMConverter>: z_rotation and scaling are not fully supported during transformation"
                )

        if proj_string_from is None:
            proj_string_from = self._cr_config.proj_string_cr

        crs_from = CRS(proj_string_from)
        crs_to = CRS("EPSG:4326")  # WGS84 for OSM
        self.transformer = Transformer.from_proj(crs_from, crs_to)

    @property
    def id_count(self) -> int:
        """
        Get the next available ID and increment the counter.

        :return: Next available ID
        """
        tmp = self._id_count
        self._id_count += 1
        return tmp

    def __call__(self, scenario: Scenario) -> bytes:
        """
        Convert a CommonRoad scenario to OSM XML format.

        :param scenario: CommonRoad scenario to convert
        :return: OSM XML as bytes
        """
        logger.info("Starting CommonRoad to OSM conversion")

        self._create_transformer(scenario)
        self.osm = OSMDocument()
        self.lanelet_network = scenario.lanelet_network

        # Convert lanelets to OSM ways
        logger.info(f"Converting {len(scenario.lanelet_network.lanelets)} lanelets")
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        # Convert traffic signs
        logger.info(f"Converting {len(scenario.lanelet_network.traffic_signs)} traffic signs")
        for traffic_sign in scenario.lanelet_network.traffic_signs:
            self._convert_traffic_sign(traffic_sign)

        # Convert traffic lights
        logger.info(f"Converting {len(scenario.lanelet_network.traffic_lights)} traffic lights")
        for traffic_light in scenario.lanelet_network.traffic_lights:
            self._convert_traffic_light(traffic_light)

        logger.info("Conversion completed successfully")
        return self.osm.serialize_to_xml()

    def _convert_lanelet(self, lanelet: Lanelet):
        """
        Convert a CommonRoad lanelet to OSM way(s).

        Creates a centerline way from the lanelet's left and right boundaries.
        Preserves elevation data if vertices are 3D.

        :param lanelet: CommonRoad lanelet to convert
        """
        # Calculate centerline from left and right vertices
        left_vertices = lanelet.left_vertices
        right_vertices = lanelet.right_vertices

        # Ensure both have the same number of points
        if len(left_vertices) != len(right_vertices):
            # Resample to match lengths
            logger.warning(
                f"Lanelet {lanelet.lanelet_id}: left and right boundaries have different lengths"
            )
            # Use the shorter length
            min_len = min(len(left_vertices), len(right_vertices))
            left_vertices = left_vertices[:min_len]
            right_vertices = right_vertices[:min_len]

        # Calculate centerline
        centerline = (left_vertices + right_vertices) / 2.0

        # Create nodes for centerline
        node_ids = []
        for i, point in enumerate(centerline):
            x, y = point[0], point[1]
            z = point[2] if point.shape[0] > 2 else 0.0  # Extract elevation if 3D

            # Apply translation
            x += self.scenario_translation[0]
            y += self.scenario_translation[1]

            # Transform to lat/lon
            lat, lon = self.transformer.transform(x, y)

            # Create node
            node_id = self.id_count
            node = Node(node_id, lat, lon, ele=z)
            self.osm.add_node(node)
            node_ids.append(node_id)

        # Create way from nodes
        way_id = self.id_count

        # Determine OSM highway tag based on lanelet type
        highway_type = self._get_highway_type(lanelet)

        # Determine oneway status
        oneway = "yes"  # CommonRoad lanelets are typically directional
        if lanelet.adj_left_same_direction or lanelet.adj_right_same_direction:
            # If adjacent lanelets in same direction exist, might be multi-lane road
            oneway = "yes"
        if lanelet.predecessor is not None and len(lanelet.predecessor) == 0:
            # Dead end
            pass

        # Create tag dictionary
        tags = {
            "highway": highway_type,
            "oneway": oneway,
            "cr:lanelet_id": str(lanelet.lanelet_id),
        }

        # Add speed limit if available
        if hasattr(lanelet, "speed_limit") and lanelet.speed_limit is not None:
            tags["maxspeed"] = str(int(lanelet.speed_limit * 3.6))  # m/s to km/h

        # Add lanes information
        tags["lanes"] = "1"  # Each CR lanelet is one lane

        # Add surface type if available
        if hasattr(lanelet, "lanelet_type"):
            # Map CommonRoad lanelet types to OSM surface types
            type_str = str(lanelet.lanelet_type)
            if "URBAN" in type_str:
                tags["area"] = "urban"
            elif "HIGHWAY" in type_str:
                tags["highway"] = "motorway"
            elif "BICYCLE" in type_str:
                tags["highway"] = "cycleway"

        way = Way(way_id, node_ids, tags)
        self.osm.add_way(way)

    def _get_highway_type(self, lanelet: Lanelet) -> str:
        """
        Determine appropriate OSM highway type from CommonRoad lanelet.

        :param lanelet: CommonRoad lanelet
        :return: OSM highway type string
        """
        # Default to unclassified
        highway_type = "unclassified"

        # Try to infer from lanelet type or other attributes
        if hasattr(lanelet, "lanelet_type"):
            type_str = str(lanelet.lanelet_type)
            if "HIGHWAY" in type_str:
                highway_type = "motorway"
            elif "MAIN" in type_str or "PRIMARY" in type_str:
                highway_type = "primary"
            elif "URBAN" in type_str:
                highway_type = "residential"
            elif "BICYCLE" in type_str:
                highway_type = "cycleway"
            elif "PEDESTRIAN" in type_str or "SIDEWALK" in type_str:
                highway_type = "footway"

        return highway_type

    def _convert_traffic_sign(self, traffic_sign: TrafficSign):
        """
        Convert a CommonRoad traffic sign to OSM node with tags.

        :param traffic_sign: CommonRoad traffic sign
        """
        # Extract position
        position = traffic_sign.position
        x, y = position[0], position[1]
        z = position[2] if len(position) > 2 else 0.0

        # Apply translation
        x += self.scenario_translation[0]
        y += self.scenario_translation[1]

        # Transform to lat/lon
        lat, lon = self.transformer.transform(x, y)

        # Create node
        node_id = self.id_count
        node = Node(node_id, lat, lon, ele=z)
        self.osm.add_node(node)

        # Create way with single node to hold traffic sign tags
        way_id = self.id_count
        tags = {
            "traffic_sign": "yes",
            "cr:sign_id": str(traffic_sign.traffic_sign_id),
        }

        # Add traffic sign elements
        if traffic_sign.traffic_sign_elements:
            sign_types = [str(elem.traffic_sign_element_id) for elem in traffic_sign.traffic_sign_elements]
            tags["traffic_sign:type"] = ";".join(sign_types)

        way = Way(way_id, [node_id], tags)
        self.osm.add_way(way)

    def _convert_traffic_light(self, traffic_light: TrafficLight):
        """
        Convert a CommonRoad traffic light to OSM node with tags.

        :param traffic_light: CommonRoad traffic light
        """
        # Extract position
        position = traffic_light.position
        x, y = position[0], position[1]
        z = position[2] if len(position) > 2 else 0.0

        # Apply translation
        x += self.scenario_translation[0]
        y += self.scenario_translation[1]

        # Transform to lat/lon
        lat, lon = self.transformer.transform(x, y)

        # Create node
        node_id = self.id_count
        node = Node(node_id, lat, lon, ele=z)
        self.osm.add_node(node)

        # Create way with single node to hold traffic light tags
        way_id = self.id_count
        tags = {
            "highway": "traffic_signals",
            "cr:light_id": str(traffic_light.traffic_light_id),
        }

        way = Way(way_id, [node_id], tags)
        self.osm.add_way(way)


def commonroad_to_osm(
    scenario: Scenario,
    osm_config: OsmConfig = osm_config,
    cr_config: GeneralConfig = general_config,
) -> bytes:
    """
    Convert a CommonRoad scenario to OpenStreetMap XML format.

    :param scenario: CommonRoad scenario to convert
    :param osm_config: OSM configuration (optional)
    :param cr_config: CommonRoad configuration (optional)
    :return: OSM XML as bytes
    """
    converter = CR2OSMConverter(osm_config, cr_config)
    return converter(scenario)
