"""Module for OSM representation in python."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

from typing import Optional, Union

from lxml import etree
from typing import List

DEFAULT_PROJ_STRING = "+proj=utm +zone=32 +ellps=WGS84"


class Node:
    """OSM Node."""

    def __init__(self, id_, lat, lon):
        self.id_ = str(id_)
        self.lat = str(lat)
        self.lon = str(lon)

    def serialize_to_xml(self) -> etree:
        node = etree.Element("node")
        node.set("id", self.id_)
        node.set("action", "modify")
        node.set("visible", "true")
        node.set("lat", self.lat)
        node.set("lon", self.lon)

        return node


class Way:
    """OSM Way."""

    def __init__(self, id_, nodes: list, tag_dict: Optional[dict] = None):
        self.id_ = str(id_)
        self.nodes = [str(node) for node in nodes]
        self.tag_dict = tag_dict if tag_dict is not None else {}

    def serialize_to_xml(self):
        way = etree.Element("way")
        way.set("id", self.id_)
        way.set("action", "modify")
        way.set("visible", "true")
        for node in self.nodes:
            xml_node = etree.SubElement(way, "nd")
            xml_node.set("ref", node)
        for tag_key, tag_value in self.tag_dict.items():
            xml_node = etree.SubElement(way, "tag")
            xml_node.set("k", tag_key)
            xml_node.set("v", tag_value)

        return way


class WayRelation:
    """Relation for a lanelet with a left and a right way."""

    def __init__(self, id_, left_way, right_way, tag_dict: Optional[dict] = None, regulatory_elements: List[str] = []): #add a spot for traffic signs especially speed limit
        self.id_ = str(id_)
        self.left_way = str(left_way)
        self.right_way = str(right_way)
        self.tag_dict = tag_dict if tag_dict is not None else {}
        self.regulatory_elements = regulatory_elements

    def serialize_to_xml(self) -> etree.Element:
        rel = etree.Element("relation")
        rel.set("id", self.id_)
        rel.set("action", "modify")
        rel.set("visible", "true")
        right_way = etree.SubElement(rel, "member")
        right_way.set("type", "way")
        right_way.set("ref", self.right_way)
        right_way.set("role", "right")
        left_way = etree.SubElement(rel, "member")
        left_way.set("type", "way")
        left_way.set("ref", self.left_way)
        left_way.set("role", "left")
        for tag_key, tag_value in self.tag_dict.items():
            xml_node = etree.SubElement(rel, "tag")
            xml_node.set("k", tag_key)
            xml_node.set("v", tag_value)

        return rel


class RightOfWayRelation:
    """Relation for a right of way relation with yield and right of way lines."""

    def __init__(self, id_, refers: list, yield_ways: list, right_of_ways: list, tag_dict: Optional[dict] = None, ref_line: Optional[list] = None):
        self.id_ = str(id_)
        self.refers = [str(i) for i in refers]
        self.yield_ways = [str(i) for i in yield_ways]
        self.right_of_ways = [str(i) for i in right_of_ways]
        self.ref_line = [str(i) for i in ref_line] if ref_line is not None else []
        self.tag_dict = tag_dict if tag_dict is not None else {}

    def serialize_to_xml(self) -> etree.Element:
        rel = etree.Element("relation")
        rel.set("id", self.id_)
        rel.set("action", "modify")
        rel.set("visible", "true")
        for r in self.refers:
            right_way = etree.SubElement(rel, "member")
            right_way.set("type", "way")
            right_way.set("ref", r)
            right_way.set("role", "refers")
        for y in self.yield_ways:
            right_way = etree.SubElement(rel, "member")
            right_way.set("type", "relation")
            right_way.set("ref", y)
            right_way.set("role", "yield")
        for r in self.right_of_ways:
            right_way = etree.SubElement(rel, "member")
            right_way.set("type", "relation")
            right_way.set("ref", r)
            right_way.set("role", "right_of_way")
        for r in self.ref_line:
            right_way = etree.SubElement(rel, "member")
            right_way.set("type", "way")
            right_way.set("ref", r)
            right_way.set("role", "ref_line")
        for tag_key, tag_value in self.tag_dict.items():
            xml_node = etree.SubElement(rel, "tag")
            xml_node.set("k", tag_key)
            xml_node.set("v", tag_value)

        return rel


class OSM:
    """Basic OSM representation."""

    def __init__(self):
        self.nodes = {}
        self._ways = {}
        self.way_relations = {}
        self.right_of_way_relations = {}
        self.speed_limit_signs = {}

    def add_node(self, node: Node):
        """Add a new node to the OSM.

        Args:
          node: Node to be added.
        """
        self.nodes[node.id_] = node

    def add_way(self, way: Way):
        self._ways[way.id_] = way

    def add_way_relation(self, way_relation: WayRelation):
        self.way_relations[way_relation.id_] = way_relation

    def add_right_of_way_relation(self, right_of_way_relation: RightOfWayRelation):
        self.right_of_way_relations[right_of_way_relation.id_] = right_of_way_relation

    def add_speed_limit_sign(self, speed_limit_id: str, speed_limit_speed: str, traffic_sign_id):
        self.speed_limit_signs[speed_limit_id] = (speed_limit_speed, traffic_sign_id)

    def find_way_by_id(self, way_id: str) -> Optional[Way]:
        return self._ways.get(way_id)

    def find_right_of_way_by_id(self, right_id: str) -> Optional[RightOfWayRelation]:
        return self.right_of_way_relations.get(right_id)

    def find_node_by_id(self, node_id: str) -> Optional[Node]:
        return self.nodes.get(node_id)

    def find_way_rel_by_id(self, way_rel_id: str) -> Optional[WayRelation]:
        """Find and return the WayRelation of the OSM if it matches the id.

        Args:
          way_rel_id: Id to be matched.
        """
        return self.way_relations.get(way_rel_id)

    def serialize_to_xml(self) -> etree.Element:
        """Serialize the OSM to an XML document."""
        osm = etree.Element("osm")
        osm.set("version", "0.6")
        osm.set("upload", "true")
        osm.set("generator", "opendrive2lanelet")

        for node in self.nodes.values():
            osm.append(node.serialize_to_xml())

        for way in self._ways.values():
            osm.append(way.serialize_to_xml())

        for way_relation in self.way_relations.values():
            osm.append(way_relation.serialize_to_xml())

        for right_of_way_relation in self.right_of_way_relations.values():
            osm.append(right_of_way_relation.serialize_to_xml())

        return osm
