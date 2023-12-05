import warnings
import os

# third party
from lxml import etree  # type: ignore
from shapely import Polygon as ShapelyPolygon
from shapely import MultiPoint as ShapelyMultiPoint
from ruamel.yaml import YAML
import mgrs
import utm

# commonroad
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile  # type: ignore
from commonroad.planning.planning_problem import PlanningProblemSet  # type: ignore
from commonroad.scenario.scenario import Tag, Scenario  # type: ignore
from commonroad.common.file_reader import CommonRoadFileReader  # type: ignore

# cr-designer
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.config.lanelet2_config import lanelet2_config
from crdesigner.config.general_config import general_config



# own code base
from crdesigner.comparison_visualization.Lanelet2NodeVisualization import Lanelet2VisNode
from crdesigner.comparison_visualization.visualization import plot_comparison


# typing
from typing import List
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crdesigner.map_conversion.lanelet2.lanelet2 import OSMLanelet
    from commonroad.scenario.scenario import Scenario


class Commonroad2Lanelet2Comparison:
    """
    Utility Class for debugging Lanelet2 to CommonRoad conversions.
    """

    def __init__(self, lanelet2_path: str, commonroad_xml_path:str):
        self.lanelet2_path: str = lanelet2_path
        self.cr_path: str = commonroad_xml_path

        # Loaded from scenario
        self.l2_parsing: "OSMLanelet" = None
        self.cr_scenario: "Scenario" = None
        self._load_scenario()

        # set in visualize_comparison
        self.l2_vis_nodes: List["Lanelet2VisNode"] = None


    def _load_scenario(self) -> None:
        """
        Loads osm and xml files and saves them in member.
        """
        with open(lanelet2_path, "r", ) as fh:
            self.l2_parsing: "OSMLanelet" = Lanelet2Parser(etree.parse(fh).getroot()).parse()

        commonroad_reader = CommonRoadFileReader(xml_path)
        self.cr_scenario, _ = commonroad_reader.open()


    def visualize_comparison(self) -> None:
        """
        Visualizes both a lanelet2 map and its converted commonroad map into on figure.
        """

        self.l2_vis_nodes: List[Lanelet2VisNode] = list()
        # Compute plot limits and create L2visnodes
        for id, node in self.l2_parsing.nodes.items():
            if(node.local_x is not None):
                x: float = float(node.local_x)
                y: float = float(node.local_y)
                l2_node: Lanelet2VisNode = Lanelet2VisNode(x, y)
                self.l2_vis_nodes.append(l2_node)

        if(len(self.l2_vis_nodes) < 100):
            warnings.warn(f'Could only find {len(self.l2_vis_nodes)}. That seems a bit too few')
        plot_comparison(lanelet2_nodes=self.l2_vis_nodes, cr_scenario=self.cr_scenario)


    def check_intersection(self) :
        """
        Checks whether the convex hull of l2_nodes and cr_lanelet network intersect,
        """

        raise NotImplementedError(f'Currently shapely bug')

        # FIXME: Currently shapely bug

        cr_road_network: ShapelyPolygon = None
        for lanelet_polygon in self.cr_scenario.lanelet_network.lanelet_polygons:
            if(cr_road_network is None):
                cr_road_network = lanelet_polygon.shapely_object
            else:
                try:
                    cr_road_network.union(lanelet_polygon.shapely_object)
                except:
                    warnings.warn(f"problems when trying to access the polygon")

        points: List[List[float]] = list()
        for node in self.l2_nodes:
            p = [node.x, node.y]
            points.append(p)

        l2_road_network: ShapelyPolygon = ShapelyMultiPoint(points).convex_hull


        if(not cr_road_network.intersects(l2_road_network)):
            warnings.warn(f'Commonroad road network and lanelet2 road network do not intersect')

        else:
            cr_area: float = cr_road_network.area
            l2_area: float = l2_road_network.area
            intersection_area: float = cr_road_network.intersection(l2_road_network).area

            percentage_intersection_cr: float = intersection_area / cr_area
            percentage_intersection_l2: float = intersection_area / l2_area

            print(f'cr-intersection: {percentage_intersection_cr}%  --  l2-intersection: {percentage_intersection_l2}')





if __name__ == "__main__":
    root_dir: str = "/home/tmasc/mapconversion/example_files"
    lanelet2_path = root_dir + "/campus.osm"
    xml_path = root_dir + "/campus.xml"

    comp_helper = Commonroad2Lanelet2Comparison(lanelet2_path, xml_path)
    comp_helper.visualize_comparison()








