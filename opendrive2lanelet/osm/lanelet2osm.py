"""Module to convert a lanelet UTM representation to OSM and vice versa."""

from pyproj import Proj
from opendrive2lanelet.osm.osm import OSM, Node, Way, WayRelation
import ipdb


class OSMConverter:
    """Class to convert Lanelet to OSM."""

    def __init__(self, proj_string):
        self.proj = Proj(proj_string)
        self.osm = OSM()
        self._id_count = -2

    @property
    def id_count(self):
        tmp = self._id_count
        self._id_count -= 2
        return tmp

    def __call__(self, scenario):
        """Convert a scenario to an OSM xml document."""
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        return self.osm.serialize_to_xml()

    def _convert_lanelet(self, lanelet):
        """Convert a lanelet to a way relation."""
        left_nodes, right_nodes = [], []
        for vertice in lanelet.left_vertices:
            lat, lon = self.proj(vertice[0], vertice[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            left_nodes.append(node)
            self.osm.add_node(node)
        for vertice in lanelet.right_vertices:
            lat, lon = self.proj(vertice[0], vertice[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            right_nodes.append(node)
            self.osm.add_node(node)

        left_way = Way(self.id_count, *left_nodes)
        right_way = Way(self.id_count, *right_nodes)
        self.osm.add_way(left_way)
        self.osm.add_way(right_way)
        self.osm.add_way_relation(WayRelation(self.id_count, left_way, right_way))
