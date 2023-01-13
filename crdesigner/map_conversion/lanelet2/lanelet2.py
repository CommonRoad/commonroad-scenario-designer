from typing import Optional
from lxml import etree  # type: ignore
from typing import List

DEFAULT_PROJ_STRING = "+proj=utm +zone=32 +ellps=WGS84"


class Node:
    """
    OSM Node.
    """

    def __init__(self, id_, lat, lon):
        """
        Initialization of Node
        
        :param lat: Latitude geo position information
        :param lon: Longitutde geo position information
        """
        self.id_ = str(id_)
        self.lat = str(lat)
        self.lon = str(lon)

    def serialize_to_xml(self) -> etree:
        """
        Serializes the Node object to the xml format
        """
        node = etree.Element("node")
        node.set("id", self.id_)
        node.set("action", "modify")
        node.set("visible", "true")
        node.set("lat", self.lat)
        node.set("lon", self.lon)
        return node


class Way:
    """
    OSM Way
    """

    def __init__(self, id_, nodes: list, tag_dict: Optional[dict] = None):
        """
        Initiialization of Way

        :param id_: ID of the way
        :param nodes: list of the way node IDs
        :param tag_dict: tag dictionary of the way
        """
        self.id_ = str(id_)
        self.nodes = [str(node) for node in nodes]
        self.tag_dict = tag_dict if tag_dict is not None else {}

    def serialize_to_xml(self):
        """
        Serializes the Way object to the xml format
        """
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
    """
    Relation for a lanelet with a left and a right way
    """

    def __init__(self, id_, left_way, right_way, tag_dict: Optional[dict] = None,
                 regulatory_elements: Optional[List[str]] = None):
        """
        Initialization of WayRelation
        
        :param id_: ID of the WayRelation
        :param left_way: ID of the left_way of WayRelation
        :param right_way: ID of the right_way of WayRelation
        :param tag_dict: tag dictionary of WayRelation
        :param regulatory_elements: regulatory elements of WayRelation
        """
        #  add a spot for traffic signs especially speed limit
        self.id_ = str(id_)
        self.left_way = str(left_way)
        self.right_way = str(right_way)
        self.tag_dict = tag_dict if tag_dict is not None else {}
        self.regulatory_elements = regulatory_elements if regulatory_elements is not None else []

    def serialize_to_xml(self) -> etree.Element:
        """
        Serializes the WayRelation object to the xml format
        """
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
    """
    Relation for a right of way relation with yield and right of way lines.
    """

    def __init__(self, id_, refers: list, yield_ways: list, right_of_ways: list, tag_dict: Optional[dict] = None,
                 ref_line: Optional[list] = None):
        """
        Initialization of RightOfWayRelation
        
        :param id_: ID of the RightOfWayRelation
        :param refers: list of the way IDs that the relation refers to
        :param yield_ways: list of the yield way IDs that the relation contains
        :param right_of_ways: list of the right of way IDs that the relation contains
        :param tag_dict: tag dictionary of the RightOfWayRelation
        :param ref_line: list of the ref line IDs of the RightOfWayRelation
        """
        self.id_ = str(id_)
        self.refers = [str(i) for i in refers]
        self.yield_ways = [str(i) for i in yield_ways]
        self.right_of_ways = [str(i) for i in right_of_ways]
        self.ref_line = [str(i) for i in ref_line] if ref_line is not None else []
        self.tag_dict = tag_dict if tag_dict is not None else {}

    def serialize_to_xml(self) -> etree.Element:
        """
        Serializes the RightOfWayRelation object to the xml format
        """
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


class OSMLanelet:
    """
    Basic OSM representation.
    """

    def __init__(self):
        """
        Initalization of the OSMLanelet
        """
        self.nodes = {}
        self._ways = {}
        self.way_relations = {}
        self.right_of_way_relations = {}
        self.speed_limit_signs = {}

    def add_node(self, node: Node):
        """
        Add a new node to the OSM.

        :param node: Node to be added.
        """
        self.nodes[node.id_] = node

    def add_way(self, way: Way):
        """
        Maps a way id with the way object and inserts it into the OSM object.

        :param way: Way that will be added to the OSM object
        """
        self._ways[way.id_] = way

    def add_way_relation(self, way_relation: WayRelation):
        """
        Maps a way relation id with the way relation object and inserts it into the OSM object.

        :param way_relation: WayRelation that will be added to the OSM object
        """
        self.way_relations[way_relation.id_] = way_relation

    def add_right_of_way_relation(self, right_of_way_relation: RightOfWayRelation):
        """
        Maps a right of way relation id with the right of way relation object and inserts it into the OSM object.

        :param right_of_way_relation: RightOfWayRelation that will be added to the OSM object
        """
        self.right_of_way_relations[right_of_way_relation.id_] = right_of_way_relation

    def add_speed_limit_sign(self, speed_limit_id: str, speed_limit_speed: str, traffic_sign_id):
        """
        Maps a speed limit id with the speed limit speed and the traffic sign id and inserts it into the OSM object.

        :param right_of_way_relation: RightOfWayRelation that will be added to the OSM object
        """
        self.speed_limit_signs[speed_limit_id] = (speed_limit_speed, traffic_sign_id)

    def find_way_by_id(self, way_id: str) -> Optional[Way]:
        """
        Finds a way corresponding to its id.

        :param way_id: id of the way
        :return: Way with the corresponding id
        """
        return self._ways.get(way_id)

    def find_right_of_way_by_id(self, right_id: str) -> Optional[RightOfWayRelation]:
        """
        Finds a right of way relation corresponding to its id.
        
        :param right_id: id of the right of way relation
        :return: RightOfWayRelation with the corresponding id
        """
        return self.right_of_way_relations.get(right_id)

    def find_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        Finds a node corresponding to its id.
        
        :param node_id: id of the node
        :return: Node with the corresponding id
        """
        return self.nodes.get(node_id)

    def find_way_rel_by_id(self, way_rel_id: str) -> Optional[WayRelation]:
        """
        Finds a way relation corresponding to its id

        :param way_rel_id: Id to the way relation
        :return: WayRelation with the corresponding id
        """
        return self.way_relations.get(way_rel_id)

    def serialize_to_xml(self) -> etree.Element:
        """
        Serialize the OSM to an XML document.
        """
        osm = etree.Element("osm")
        osm.set("version", "0.6")
        osm.set("upload", "true")
        osm.set("generator", "commonroad-scenario-designer")

        for node in self.nodes.values():
            osm.append(node.serialize_to_xml())

        for way in self._ways.values():
            osm.append(way.serialize_to_xml())

        for way_relation in self.way_relations.values():
            osm.append(way_relation.serialize_to_xml())

        for right_of_way_relation in self.right_of_way_relations.values():
            osm.append(right_of_way_relation.serialize_to_xml())

        return osm
