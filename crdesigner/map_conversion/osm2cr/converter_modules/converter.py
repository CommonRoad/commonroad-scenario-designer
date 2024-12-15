import logging

from crdesigner.common.config.osm_config import osm_config as config
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations import (
    intersection_merger,
    lane_linker,
    mapillary,
    offsetter,
    segment_clusters,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._sublayered_graph import (
    SublayeredGraph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations import osm_parser


def step_collection_1(file: str) -> Graph:
    graph = osm_parser.create_graph(file)
    if config.MAKE_CONTIGUOUS:
        logging.info("making graph contiguously")
        graph.make_contiguous()
    logging.info("merging close intersections")
    intersection_merger.merge_close_intersections(graph)
    if isinstance(graph, SublayeredGraph):
        intersection_merger.merge_close_intersections(graph.sublayer_graph)
    graph.link_edges()
    return graph


def step_collection_2(graph: Graph) -> Graph:
    logging.info("linking lanes")
    lane_linker.link_graph(graph)
    if isinstance(graph, SublayeredGraph):
        lane_linker.link_graph(graph.sublayer_graph)
    logging.info("interpolating waypoints")
    graph.interpolate()
    logging.info("offsetting roads")
    offsetter.offset_graph(graph)
    if isinstance(graph, SublayeredGraph):
        offsetter.offset_graph(graph.sublayer_graph)
    logging.info("cropping roads at intersections")
    edges_to_delete = graph.crop_waypoints_at_intersections(config.INTERSECTION_DISTANCE)
    if config.DELETE_SHORT_EDGES:
        logging.info("deleting short edges")
        graph.delete_edges(edges_to_delete)
    if isinstance(graph, SublayeredGraph):
        edges_to_delete = graph.sublayer_graph.crop_waypoints_at_intersections(
            config.INTERSECTION_DISTANCE_SUBLAYER
        )
        if config.DELETE_SHORT_EDGES:
            graph.sublayer_graph.delete_edges(edges_to_delete)
    logging.info("applying traffic signs to edges and nodes")
    mapillary.add_mapillary_signs_to_graph(graph)
    graph.apply_traffic_signs()
    logging.info("applying traffic lights to edges")
    graph.apply_traffic_lights()
    logging.info("creating waypoints of lanes")
    graph.create_lane_waypoints()
    return graph


def step_collection_3(graph: Graph) -> Graph:
    logging.info("creating segments at intersections")
    graph.create_lane_link_segments()
    logging.info("clustering segments")
    segment_clusters.cluster_segments(graph)
    if isinstance(graph, SublayeredGraph):
        segment_clusters.cluster_segments(graph.sublayer_graph)
    logging.info("changing to desired interpolation distance and creating borders of lanes")
    graph.create_lane_bounds(config.INTERPOLATION_DISTANCE_INTERNAL / config.INTERPOLATION_DISTANCE)
    if config.DELETE_INVALID_LANES:
        logging.info("deleting invalid lanes")
        graph.delete_invalid_lanes()
    if isinstance(graph, SublayeredGraph):
        if config.DELETE_INVALID_LANES:
            graph.sublayer_graph.delete_invalid_lanes()
    logging.info("adjust common bound points")
    graph.correct_start_end_points()
    logging.info("done converting")
    return graph


class GraphScenario:
    """
    Class that represents a road network
    data is saved by a graph structure (RoadGraph)

    """

    def __init__(self, file: str):
        """
        loads an OSM file and converts it to a graph

        :param file: OSM file to be loaded
        """
        logging.info("reading File and creating graph")

        graph = step_collection_1(file)
        graph = step_collection_2(graph)

        graph = step_collection_3(graph)
        self.graph: Graph = graph
