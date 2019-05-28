"""Module to convert a lanelet UTM representation to OSM."""

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.0.2"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


from pyproj import Proj
from opendrive2lanelet.osm.osm import OSM, Node, Way, WayRelation


class L2OSMConverter:
    """Class to convert Lanelet to OSM."""

    def __init__(self, proj_string):
        self.proj = Proj(proj_string)
        self.osm = None
        self._id_count = -1

    @property
    def id_count(self):
        """Internal counter for giving IDs to the members of the OSM."""
        tmp = self._id_count
        self._id_count -= 1
        return tmp

    def __call__(self, scenario):
        """Convert a scenario to an OSM xml document."""
        self.osm = OSM()
        for lanelet in scenario.lanelet_network.lanelets:
            self._convert_lanelet(lanelet)

        return self.osm.serialize_to_xml()

    def _convert_lanelet(self, lanelet):
        """Convert a lanelet to a way relation."""
        left_nodes, right_nodes = [], []
        for vertice in lanelet.left_vertices:
            lon, lat = self.proj(vertice[0], vertice[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            left_nodes.append(node.id_)
            self.osm.add_node(node)
        for vertice in lanelet.right_vertices:
            lon, lat = self.proj(vertice[0], vertice[1], inverse=True)
            node = Node(self.id_count, lat, lon)
            right_nodes.append(node.id_)
            self.osm.add_node(node)

        left_way = Way(self.id_count, *left_nodes)
        right_way = Way(self.id_count, *right_nodes)
        self.osm.add_way(left_way)
        self.osm.add_way(right_way)
        self.osm.add_way_relation(
            WayRelation(lanelet.lanelet_id, left_way.id_, right_way.id_)
        )
