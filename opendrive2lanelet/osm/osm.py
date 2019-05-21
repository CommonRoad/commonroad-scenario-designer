"""Module for OSM representation in python."""

from lxml import etree


class Node:
    """OSM Node."""

    def __init__(self, id_, lat, lon):
        self.id_ = str(id_)
        self.lat = str(lat)
        self.lon = str(lon)

    def serialize_to_xml(self):
        node = etree.Element("node")
        node.set("id", self.id_)
        node.set("action", "modify")
        node.set("visible", "true")
        node.set("lat", self.lat)
        node.set("lon", self.lon)

        return node


class Way:
    """OSM Way."""

    def __init__(self, id_: str, *nodes):
        self.id_ = str(id_)
        self.nodes = []
        for node in nodes:
            self.nodes.append(node)

    def serialize_to_xml(self):
        way = etree.Element("way")
        way.set("id", self.id_)
        way.set("action", "modify")
        way.set("visible", "true")
        for node in self.nodes:
            xml_node = etree.SubElement(way, "nd")
            xml_node.set("ref", node.id_)

        return way


class WayRelation:
    """Relation for a lanelet with a left and a right way."""

    def __init__(self, id_: str, left_way: Way, right_way: Way):
        self.id_ = str(id_)
        self.left_way = left_way
        self.right_way = right_way

    def serialize_to_xml(self):
        rel = etree.Element("relation")
        rel.set("id", self.id_)
        rel.set("action", "modify")
        rel.set("visible", "true")
        right_way = etree.SubElement(rel, "member")
        right_way.set("type", "way")
        right_way.set("ref", self.right_way.id_)
        right_way.set("role", "right")
        left_way = etree.SubElement(rel, "member")
        left_way.set("type", "way")
        left_way.set("ref", self.left_way.id_)
        left_way.set("role", "left")
        tag = etree.SubElement(rel, "tag")
        tag.set("k", "type")
        tag.set("v", "lanelet")

        return rel


class OSM:
    """Basic OSM representation."""

    def __init__(self):
        self.nodes = []
        self._ways = []
        self.way_relations = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_way(self, way: Way):
        self._ways.append(way)

    def add_way_relation(self, way_relation: WayRelation):
        self.way_relations.append(way_relation)

    def find_way_by_id(self, way_id: str):
        for way in self._ways:
            if way.id_ == way_id:
                return way
        return None

    def find_node_by_id(self, node_id: str) -> Node:
        for nd in self.nodes:
            if nd.id_ == node_id:
                return nd

        return None

    def serialize_to_xml(self):
        osm = etree.Element("osm")
        osm.set("version", "0.6")
        osm.set("upload", "true")
        osm.set("generator", "opendrive2lanelet")

        for node in self.nodes:
            osm.append(node.serialize_to_xml())

        for way in self._ways:
            osm.append(way.serialize_to_xml())

        for way_relation in self.way_relations:
            osm.append(way_relation.serialize_to_xml())

        return osm
