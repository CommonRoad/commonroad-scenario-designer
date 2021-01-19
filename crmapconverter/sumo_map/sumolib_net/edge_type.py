from xml.etree import ElementTree as ET
from typing import List, Dict, Union, TypeVar, Callable
from .constants import SUMO_VEHICLE_CLASSES
from copy import deepcopy


def bool_to_str(b: bool) -> str:
    return "true" if b else "false"


def str_to_bool(s: str) -> bool:
    return s == "true"


# generic type
_T = TypeVar("_T")


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

        assert not (allow and disallow and set(allow) & set(disallow)), \
            f"allow and disallow contain common elements {set(allow) & set(disallow)}"
        if allow:
            assert set(allow).issubset(SUMO_VEHICLE_CLASSES), \
                f"allow contains invalid classes {set(allow) - set(SUMO_VEHICLE_CLASSES)}"
            self.allow = allow
        else:
            self.allow = []
        if disallow:
            assert set(disallow).issubset(SUMO_VEHICLE_CLASSES), \
                f"disallow contains invalid classes {set(disallow) - set(SUMO_VEHICLE_CLASSES)}"
            self.disallow = disallow
        else:
            self.disallow = []

        self.discard = discard
        self.num_lanes = num_lanes
        self.oneway = oneway
        self.priority = priority
        self.speed = speed
        self.sidewalk_width = sidewalk_width

    @classmethod
    def from_XML(cls, xml: str) -> 'EdgeType':
        """
        Creates an instance of this class from the given xml representation
        :param xml:
        :return:
        """
        root = ET.fromstring(xml)

        def get_map(key: str, map: Callable[[str], _T], default: _T) -> _T:
            value = root.get(key)
            return map(value) if value else default

        return cls(id=root.get("id"),
                   allow=get_map("allow", lambda s: s.split(" "), []),
                   disallow=get_map("disallow", lambda s: s.split(" "), []),
                   discard=get_map("discard", str_to_bool, False),
                   num_lanes=get_map("numLanes", int, -1),
                   oneway=get_map("oneway", str_to_bool, False),
                   priority=get_map("priority", int, 0),
                   speed=get_map("speed", float, 13.89),
                   sidewalk_width=get_map("sidewalkWidth", int, -1))

    def to_XML(self) -> str:
        """
        Converts this node to it's xml representation
        :return: xml representation of this EdgeType
        """
        node = ET.Element("type")
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
        return str(ET.tostring(node), encoding="utf-8")

    def __str__(self):
        return self.to_XML()


class EdgeTypes:
    def __init__(self, types: Dict[str, EdgeType] = None):
        self.types: Dict[str, EdgeType] = types if types else dict()

    @classmethod
    def from_XML(cls, xml: str) -> 'EdgeTypes':
        root = ET.fromstring(xml)
        types: Dict[str, EdgeType] = {}
        for edge_type in root.iter("type"):
            types[edge_type.get("id")] = EdgeType.from_XML(str(ET.tostring(edge_type), encoding="utf-8"))
        return cls(types)

    def to_XML(self) -> str:
        types = ET.Element("types")
        types.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        types.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/types_file.xsd")
        for type_id, type in self.types.items():
            types.append(ET.fromstring(type.to_XML()))
        return str(ET.tostring(types), encoding="utf-8")

    def _create_from_update(self, old_id: str, attr: str, value: any) -> Union[EdgeType, None]:
        if old_id not in self.types:
            return None
        edge_type = self.types[old_id]
        new_id = f"{edge_type.id}_{attr}_{value}"
        if new_id in self.types:
            return self.types[new_id]

        new_type = deepcopy(edge_type)
        new_type.id = new_id
        setattr(new_type, attr, value)
        self.types[new_type.id] = new_type
        return new_type

    def create_from_update_priority(self, old_id: str, priority: int) -> Union[EdgeType, None]:
        return self._create_from_update(old_id, "priority", priority)

    def create_from_update_speed(self, old_id: str, speed: float) -> Union[EdgeType, None]:
        return self._create_from_update(old_id, "speed", round(speed, 2))

    def create_from_update_oneway(self, old_id: str, oneway: bool) -> Union[EdgeType, None]:
        return self._create_from_update(old_id, "oneway", oneway)

    def create_from_update_allow(self, old_id: str, allow: List[str]) -> Union[EdgeType, None]:
        return self._create_from_update(old_id, "allow", allow)

    def create_from_update_disallow(self, old_id: str, disallow: List[str]) -> Union[EdgeType, None]:
        return self._create_from_update(old_id, "allow", disallow)
