import warnings
import numpy as np

# third party
from lxml import etree  # type: ignore
from shapely import Polygon as ShapelyPolygon
from shapely import Point as ShapelyPoint
from shapely import MultiPoint as ShapelyMultiPoint

# commonroad
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile  # type: ignore
from commonroad.planning.planning_problem import PlanningProblemSet  # type: ignore
from commonroad.scenario.scenario import Tag, Scenario  # type: ignore
from commonroad.common.file_reader import CommonRoadFileReader  # type: ignore

# cr-designer
from crdesigner.map_conversion.lanelet2.lanelet2_parser import Lanelet2Parser


# own code base
from crdesigner.comparison_visualization.Lanelet2NodeVisualization import Lanelet2VisNode
from crdesigner.comparison_visualization.visualization import plot_comparison


# typing
from typing import List, Dict, Tuple
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from crdesigner.map_conversion.lanelet2.lanelet2 import OSMLanelet
    from commonroad.scenario.scenario import Scenario




def check_intersection(l2_nodes: List[Lanelet2VisNode], cr_scenario: "Scenario") -> None:
    """
    Checks whether the convex hull of l2_nodes and cr_lanelet network intersect
    """

    cr_road_network: ShapelyPolygon = None
    for lanelet_polygon in cr_scenario.lanelet_network.lanelet_polygons:
        if(cr_road_network is None):
            cr_road_network = lanelet_polygon.shapely_object
        else:
            cr_road_network.union(lanelet_polygon.shapely_object)

    points: List[List[float]] = list()
    for node in l2_nodes:
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




def visualize_comparison(lanelet2_path: str, xml_path: str) -> None:
    """
    Visualizes both a lanelet2 map and its converted commonroad map into on figure.
    """

    with open(lanelet2_path, "r", ) as fh:
        l2_parsing: "OSMLanelet" = Lanelet2Parser(etree.parse(fh).getroot()).parse()

    l2_vis_nodes: List[Lanelet2VisNode] = list()

    commonroad_reader = CommonRoadFileReader(xml_path)
    cr_scenario, _ = commonroad_reader.open()
    cr_scenario: Scenario = cr_scenario

    # get min, max x and y values

    min_x: float = np.inf
    min_y: float = np.inf
    max_x: float = -np.inf
    max_y: float = -np.inf


    # Compute plot limits and create L2visnodes
    for id, node in l2_parsing.nodes.items():
        x: float = float(node.lon)
        y: float = float(node.lat)


        l2_node: Lanelet2VisNode = Lanelet2VisNode(x, y)
        l2_vis_nodes.append(l2_node)

        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)



    for lanelet_polygon in cr_scenario.lanelet_network.lanelet_polygons:
        for idx in range(lanelet_polygon.vertices.shape[0]):
            x: float = lanelet_polygon.vertices[idx, 0]
            y: float = lanelet_polygon.vertices[idx, 1]

            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)


    check_intersection(l2_vis_nodes, cr_scenario)

    plot_comparison(l2_vis_nodes, None, [min_x, max_x, min_y, max_y])


    x = 3



if __name__ == "__main__":
    root_dir: str = "/home/tmasc/mapconversion/example_files"
    lanelet2_path = root_dir + "/planning_sim.osm"
    xml_path = root_dir + "/planning_sim.xml"
    visualize_comparison(lanelet2_path, xml_path)








