from typing import Tuple

from commonroad.scenario.scenario import GeoTransformation, Location, Scenario, Tag

from crdesigner.common.config.general_config import general_config
from crdesigner.common.config.osm_config import osm_config
from crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.cleanup import (
    sanitize,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._graph import (
    Graph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.graph_operations.road_graph._sublayered_graph import (
    SublayeredGraph,
)
from crdesigner.map_conversion.osm2cr.converter_modules.intermediate_operations.intermediate_format._intermediate_format import (
    IntermediateFormat,
)
from crdesigner.map_conversion.osm2cr.converter_modules.utility.geonamesID import (
    get_geonamesID,
)


def create_scenario_intermediate(graph) -> Tuple[Scenario, IntermediateFormat]:
    """Convert Scenario from RoadGraph via IntermediateFormat"""
    interm = IntermediateFormat.extract_from_road_graph(graph)
    if isinstance(graph, SublayeredGraph):
        interm_sublayer = IntermediateFormat.extract_from_road_graph(graph.sublayer_graph)
        crossings = IntermediateFormat.get_lanelet_intersections(interm_sublayer, interm)
        interm_sublayer.intersections = list()
        interm_sublayer.traffic_signs = list()
        interm_sublayer.traffic_lights = list()
        interm_sublayer.remove_invalid_references()
        print("removed intersections, traffic lights, traffic signs from sublayer")
        interm.merge(interm_sublayer)
        interm.add_crossing_information(crossings)
    scenario = interm.to_commonroad_scenario()
    return scenario, interm


def convert_to_scenario(graph: Graph) -> Scenario:
    # scenario = create_scenario(graph)
    scenario, intermediate_format = create_scenario_intermediate(graph)

    scenario.author = general_config.author
    scenario.affiliation = general_config.affiliation
    source = general_config.source
    if osm_config.MAPILLARY_CLIENT_ID != "demo":
        source += ", Mapillary"
    scenario.source = source
    scenario.tags = create_tags(general_config.tags)

    # create location tag automatically. Retreive geonamesID from the Internet.
    scenario.location = Location(
        gps_latitude=graph.center_point[0],
        gps_longitude=graph.center_point[1],
        geo_name_id=get_geonamesID(graph.center_point[0], graph.center_point[1]),
        geo_transformation=GeoTransformation(geo_reference=general_config.proj_string_cr),
    )

    # removing converting errors before writing to xml
    sanitize(scenario)
    return scenario


def create_tags(tags: str):
    """
    creates tags out of a space separated string

    :param tags: string of tags
    :return: list of tags
    """
    splits = tags.split()
    tags = set()
    for tag in splits:
        tags.add(Tag(tag))
    return tags
