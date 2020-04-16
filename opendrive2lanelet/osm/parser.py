# -*- coding: utf-8 -*-

"""Module to parse OSM document."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"

from lxml import etree
from opendrive2lanelet.osm.osm import OSM, Node, Way, WayRelation


class OSMParser:
    """Parser for OSM documents.

    Only extracts relevant information for conversion to Lanelet.
    """

    def __init__(self, xml_doc: etree.Element):
        self.xml = xml_doc

    def parse(self):
        osm = OSM()
        for node in self.xml.xpath("//node[@lat and @lon and @id]"):
            osm.add_node(Node(node.get("id"), node.get("lat"), node.get("lon")))

        for way in self.xml.xpath("//way[@id]"):
            node_ids = []
            for nd in way.xpath("./nd"):
                node_ids.append(nd.get("ref"))

            osm.add_way(Way(way.get("id"), *node_ids))

        for way_rel in self.xml.xpath("//relation/tag[@v='lanelet' and @k='type']/.."):
            try:
                left_way = way_rel.xpath("./member[@type='way' and @role='left']/@ref")[
                    0
                ]
                right_way = way_rel.xpath(
                    "./member[@type='way' and @role='right']/@ref"
                )[0]
                osm.add_way_relation(
                    WayRelation(way_rel.get("id"), left_way, right_way)
                )
            except IndexError:
                print(
                    f"Lanelet relation {way_rel.attrib.get('id')} has either no left or no right way! Please check your data! Discarding this lanelet relation."
                )

        return osm
