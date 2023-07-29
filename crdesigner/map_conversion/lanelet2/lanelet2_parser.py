from lxml import etree  # type: ignore
from crdesigner.map_conversion.lanelet2.lanelet2 import OSMLanelet, Node, Way, WayRelation, RegulatoryElement

from commonroad.scenario.traffic_sign import TrafficSignIDGermany  # type: ignore

ALLOWED_TAGS = {"type", "subtype", "one_way", "virtual", "location", "bicycle", 'highway', }


class Lanelet2Parser:
    """
    Parser for OSM documents.
    Only extracts relevant information for conversion to Lanelet.
    """

    def __init__(self, xml_doc: etree.Element):
        """
        Inits Lanelet2Parser
        """
        self.xml = xml_doc

    def parse(self):
        """
        Parses the nodes, way relations, reg_element relations
        """
        osm = OSMLanelet()
        for node in self.xml.xpath("//node[@lat and @lon and @id]"):
            for tag in node.findall("./tag"):
                if tag.attrib.get("k") == "ele":
                    osm.add_node(Node(node.get("id"), node.get("lat"), node.get("lon"), tag.attrib.get("v")))
                    break
            else:
                osm.add_node(Node(node.get("id"), node.get("lat"), node.get("lon")))

        for way in self.xml.xpath("//way[@id]"):
            node_ids = [nd.get("ref") for nd in way.xpath("./nd")]
            tag_dict = {tag.get("k"): tag.get("v") for tag in way.xpath("./tag[@k and @v]") if
                        tag.get("k") in ALLOWED_TAGS}

            osm.add_way(Way(way.get("id"), node_ids, tag_dict))

        for way_rel in self.xml.xpath("//relation/tag[@v='lanelet' and @k='type']/.."):
            try:
                left_way = way_rel.xpath("./member[@type='way' and @role='left']/@ref")[0]
                right_way = way_rel.xpath("./member[@type='way' and @role='right']/@ref")[0]
                tag_dict = {tag.get("k"): tag.get("v") for tag in way_rel.xpath("./tag[@k and @v]") if
                            tag.get("k") in ALLOWED_TAGS}
                regulatory_elements = list(way_rel.xpath("./member[@role='regulatory_element']/@ref"))
                osm.add_way_relation(WayRelation(way_rel.get("id"), left_way, right_way, tag_dict, regulatory_elements))
            except IndexError:
                print(f"Lanelet relation {way_rel.attrib.get('id')} has either no left or no right way! "
                      f"Please check your data! Discarding this lanelet relation.")

        for reg_element_rel in self.xml.xpath("//relation/tag[@v='regulatory_element' and @k='type']/.."):
            # returns the parent element if there is another tag inside that is the right of way tag
            for right_of_way_rel in reg_element_rel.xpath("./tag[@v='right_of_way' and @k='subtype']/.."):
                try:
                    yield_lanelets = right_of_way_rel.xpath("./member[@role='yield']/@ref")
                    right_of_way_lanelets = right_of_way_rel.xpath("./member[@role='right_of_way']/@ref")
                    traffic_signs = right_of_way_rel.xpath("./member[@role='refers']/@ref")
                    # Reference line is optional
                    # defaults to last line of yield lanelets
                    tag_dict = {tag.get("k"): tag.get("v") for tag in right_of_way_rel.xpath("./tag[@k and @v]") if
                                tag.get("k") in ALLOWED_TAGS}
                    ref_lines = right_of_way_rel.xpath("./member[@role='ref_line']/@ref")
                    osm.add_regulatory_element(
                            RegulatoryElement(right_of_way_rel.get("id"), traffic_signs, yield_lanelets,
                                              right_of_way_lanelets, tag_dict, ref_lines))
                except IndexError:
                    print(f"Right of way relation {right_of_way_rel.attrib.get('id')} has no traffic sign. "
                          f"Please check your data! Discarding.")

            for speed_limit in reg_element_rel.xpath("./tag[@v='speed_limit' and @k='subtype']/.."):
                speed = speed_limit.xpath("./tag[@k='sign_type']/@v")[0]  # [:-3]
                speed_limit_id = speed_limit.attrib['id']
                traffic_sign_id = TrafficSignIDGermany.MAX_SPEED
                osm.add_speed_limit_sign(speed_limit_id, speed, traffic_sign_id)

            for traffic_light in reg_element_rel.xpath("./tag[@v='traffic_light' and @k='subtype']/.."):
                traffic_lights = traffic_light.xpath("./member[@role='refers']/@ref")
                ref_lines = traffic_light.xpath("./member[@role='ref_line']/@ref")
                tag_dict = {tag.get("k"): tag.get("v") for tag in traffic_light.xpath("./tag[@k and @v]") if
                            tag.get("k") in ALLOWED_TAGS}
                    
                osm.add_regulatory_element(RegulatoryElement(traffic_light.get('id'), ref_line=ref_lines,
                                                             refers=traffic_lights, tag_dict=tag_dict))

        return osm
