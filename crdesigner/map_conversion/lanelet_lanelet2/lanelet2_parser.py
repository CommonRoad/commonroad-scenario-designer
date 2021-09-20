# -*- coding: utf-8 -*-

"""Module to parse OSM document."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

from lxml import etree
from crdesigner.map_conversion.lanelet_lanelet2.lanelet2 import OSMLanelet, Node, Way, WayRelation, RightOfWayRelation

from commonroad.scenario.traffic_sign import TrafficSignIDGermany

ALLOWED_TAGS = {
    "type",
    "subtype",
    "one_way",
    "virtual",
    "location",
    "bicycle",
    'highway',
}


class Lanelet2Parser:
    """Parser for OSM documents.

    Only extracts relevant information for conversion to Lanelet.
    """

    def __init__(self, xml_doc: etree.Element):
        self.xml = xml_doc

    def parse(self):
        osm = OSMLanelet()
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
                regulatory_elements = [ref for ref in way_rel.xpath("./member[@role='regulatory_element']/@ref")]
                osm.add_way_relation(
                    WayRelation(way_rel.get("id"), left_way, right_way, tag_dict, regulatory_elements)
                )
            except IndexError:
                print(
                    f"Lanelet relation {way_rel.attrib.get('id')} has either no left or no right way! "
                    f"Please check your data! Discarding this lanelet relation."
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
                        RightOfWayRelation(right_of_way_rel.get("id"), traffic_signs, yield_lanelets,
                                           right_of_way_lanelets, tag_dict, ref_lines)
                    )
                except IndexError:
                    print(
                        f"Right of way relation {right_of_way_rel.attrib.get('id')} has no traffic sign. "
                        f"Please check your data! Discarding."
                    )

            for speed_limit in reg_element_rel.xpath("./tag[@v='speed_limit' and @k='subtype']/.."):
                '''
                TODO 
                create a traffic sign 
                commonroad.scenario.traffic_sign
                
                TrafficSignElement with speed limit as additional value
                
                wrap in a traffic sign or later wrap all sign in a Traffic Sign 
                
                each lanelet with a relation to this speed limit needs a reference
                '''
                # TODO find out if required to remove kmh or mph
                speed = speed_limit.xpath("./tag[@k='sign_type']/@v")[0] #[:-3]
                speed_limit_id = speed_limit.attrib['id']
                traffic_sign_id = TrafficSignIDGermany.MAX_SPEED
                osm.add_speed_limit_sign(speed_limit_id, speed, traffic_sign_id)

        return osm
