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
from crmapconverter.osm.osm import OSM, Node, Way, WayRelation, RightOfWayRelation

ALLOWED_TAGS = {
    "type",
    "subtype",
    "one_way",
    "virtual",
    "location",
}

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
            node_ids = [nd.get("ref") for nd in way.xpath("./nd")]
            tag_dict = {tag.get("k"): tag.get("v") for tag in way.xpath("./tag[@k and @v]")
                        if tag.get("k") in ALLOWED_TAGS}

            osm.add_way(Way(way.get("id"), node_ids, tag_dict))

        for way_rel in self.xml.xpath("//relation/tag[@v='lanelet' and @k='type']/.."):
            try:
                left_way = way_rel.xpath("./member[@type='way' and @role='left']/@ref")[
                    0
                ]
                right_way = way_rel.xpath(
                    "./member[@type='way' and @role='right']/@ref"
                )[0]
                tag_dict = {tag.get("k"): tag.get("v") for tag in way_rel.xpath("./tag[@k and @v]")
                            if tag.get("k") in ALLOWED_TAGS}
                osm.add_way_relation(
                    WayRelation(way_rel.get("id"), left_way, right_way, tag_dict)
                )
            except IndexError:
                print(
                    f"Lanelet relation {way_rel.attrib.get('id')} has either no left or no right way! Please check your data! Discarding this lanelet relation."
                )

        for reg_element_rel in self.xml.xpath("//relation/tag[@v='regulatory_element' and @k='type']/.."):
            # returns the parent element if there is another tag inside that is the right of way tag
            for right_of_way_rel in reg_element_rel.xpath("./tag[@v='right_of_way' and @k='subtype']/.."):
                try:
                    yield_lanelets = right_of_way_rel.xpath("./member[@role='yield']/@ref")
                    right_of_way_lanelets = right_of_way_rel.xpath("./member[@role='right_of_way']/@ref")
                    traffic_signs = right_of_way_rel.xpath("./member[@role='refers']/@ref")
                    # Reference line is optional
                    # defaults to last line of yield lanelets
                    tag_dict = {tag.get("k"): tag.get("v") for tag in right_of_way_rel.xpath("./tag[@k and @v]")
                                if tag.get("k") in ALLOWED_TAGS}
                    ref_lines = right_of_way_rel.xpath("./member[@role='ref_line']/@ref")
                    osm.add_right_of_way_relation(
                        RightOfWayRelation(right_of_way_rel.get("id"), traffic_signs, yield_lanelets, right_of_way_lanelets, tag_dict, ref_lines)
                    )
                except IndexError:
                    print(
                        f"Right of way relation {right_of_way_rel.attrib.get('id')} has no traffic sign. Please check your data! Discarding."
                    )

        return osm
