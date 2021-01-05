# node 	id (string) 	The name of the node at which this crossing is located
# edges 	ids (list of strings) 	The (road) edges which are crossed
# priority 	bool 	Whether the pedestrians have priority over the vehicles (automatically set to true at tls-controlled intersections).
# width 	real (m) 	The width of the crossings.
# shape 	List of positions; each position is encoded in x,y or x,y,z in meters (do not separate the numbers with a space!). 	specifies a custom shape for this crossing. By default it is straight.

# Caution: The shape must be defined in counter-clockwise direction around the intersection.
# linkIndex 	int 	specifies a custom index within the signal plan (for the forward direction)
# linkIndex2 	int 	specifies a custom index within the signal plan (for the backward direction)
# discard

from typing import List, Iterable
from xml.etree import cElementTree as ET
from crmapconverter.sumo_map.sumolib_net.edge import Edge
from crmapconverter.sumo_map.sumolib_net.node import Node


class Crossing:
    def __init__(self,
                 node: Node,
                 edges: Iterable[Edge],
                 priority: bool = None,
                 width: float = None,
                 shape = None,
                 linkIndex: int = None,
                 linkIndex2: int = None,
                 discard: bool = None):
        self.node = node
        self.edges = edges
        self.priority = priority
        self.width = width
        self.shape = shape
        self.linkIndex = linkIndex
        self.linkIndex2 = linkIndex2
        self.discard = discard

    def __str__(self) -> str:
        return self.toXML()

    def toXML(self) -> str:
        c = ET.Element("crossing")
        c.set("node", str(self.node.getID()))
        c.set("edges", " ".join(str(edge.getID()) for edge in self.edges))
        if self.priority:
            c.set("priority", str(self.priority))
        if self.width:
            c.set("width", str(self.width))
        if self.shape is not None:
            c.set(
                "shape",
                " ".join([",".join(str(coord) for coord in v) for v in self.shape]))
        if self.linkIndex:
            c.set("linkIndex", str(self.linkIndex))
        if self.linkIndex2:
            c.set("linkIndex2", str(self.linkIndex2))
        if self.discard:
            c.set("discard", str(self.discard))

        return ET.tostring(c)