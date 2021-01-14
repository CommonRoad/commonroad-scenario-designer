from xml.etree import ElementTree as ET
from typing import List, Dict


def bool_to_str(b: bool) -> str:
    return "true" if b else "false"


def str_to_bool(s: str) -> bool:
    return s == "true"


class EdgeType:
    def __init__(self, id: str,
                 allow: List[str] = None,
                 disallow: List[str] = None,
                 discard: bool = False,
                 num_lanes: int = -1,
                 oneway=False,
                 priority: int = 0,
                 speed: float = 13.89,
                 sidewalk_width: float = -1):
        """
        Constructs a SUMO Edge Type
        Documentation from: https://sumo.dlr.de/docs/SUMO_edge_type_file.html
        :param id: The name of the road type. This is the only mandatory attribute. For OpenStreetMap data, the name could, for example, be highway.trunk or highway.residential. For ArcView data, the name of the road type is a number.
        :param allow: List of allowed vehicle classes
        :param disallow: List of not allowed vehicle classes
        :param discard: If "yes", edges of that type are not imported. This parameter is optional and defaults to false.
        :param num_lanes: The number of lanes on an edge. This is the default number of lanes per direction.
        :param oneway: If "yes", only the edge for one direction is created during the import. (This attribute makes no sense for SUMO XML descriptions but, for example, for OpenStreetMap files.)
        :param priority: A number, which determines the priority between different road types. netconvert derives the right-of-way rules at junctions from the priority. The number starts with one; higher numbers represent more important roads.
        :param speed: The default (implicit) speed limit in m/s.
        :param sidewalk_width: The default width for added sidewalks (defaults to -1 which disables extra sidewalks).
        """
        self.id = id
        self.allow = allow if allow else []
        self.disallow = disallow if disallow else []
        self.discard = discard
        self.num_lanes = num_lanes
        self.oneway = oneway
        self.priority = priority
        self.speed = speed
        self.sidewalk_width = sidewalk_width

    @classmethod
    def from_XML(cls, xml: bytes) -> 'EdgeType':
        """
        Creates an instance of this class from the given xml representation
        :param xml:
        :return:
        """
        root = ET.parse(xml).getroot()
        return cls(id=root.get("id"),
                   allow=root.get("allow", "").split(" "),
                   disallow=root.get("disallow", "").split(" "),
                   discard=str_to_bool(root.get("discard")),
                   num_lanes=int(root.get("numLanes", "-1")),
                   oneway=str_to_bool(root.get("oneway")),
                   priority=int(root.get("priority", "0")),
                   speed=float(root.get("speed", "13.89")),
                   sidewalk_width=float(root.get("sidewalkWidth", "-1")))

    def to_XML(self) -> bytes:
        """
        Converts this node to it's xml representation
        :return: xml representation of this EdgeType
        """
        node = ET.Element("node")
        node.set("id", str(self.id))
        if self.allow:
            node.set("allow", str(' '.join(self.allow)))
        if self.disallow:
            node.set("disallow", str(' '.join(self.disallow)))
        if self.discard:
            node.set("discard", bool_to_str(self.discard))
        if self.num_lanes != -1:
            node.set("numLanes", str(self.num_lanes))
        if self.oneway:
            node.set("oneway", bool_to_str(self.oneway))
        if self.priority:
            node.set("priority", str(self.priority))
        if self.speed:
            node.set("speed", f"{self.speed:.2f}")
        if self.sidewalk_width > 0:
            node.set("sidewalkWidth", f"{self.sidewalk_width:.2f}")
        return ET.tostring(node)


class EdgeTypes:
    def __init__(self):
        self.types: Dict[str, EdgeType] = dict()
