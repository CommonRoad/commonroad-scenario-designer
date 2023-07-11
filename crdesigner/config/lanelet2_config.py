from commonroad.scenario.traffic_sign import TrafficSignIDGermany, TrafficSignIDZamunda, TrafficSignIDUsa

from crdesigner.config.config_base import BaseConfig, Attribute
from crdesigner.config.gui_config import gui_config


class Lanelet2Config(BaseConfig):
    """
    Lanelet2Config contains all the configuration parameters for the conversion from lanelet2 to CommonRoad.
    """

    ways_are_equal_tolerance = Attribute(0.001, "Ways are equal tolerance",
                                         "Value of the tolerance for which we mark ways as equal")

    default_lon_coordinate = Attribute(11.66821, "Default longitude coordinate",
                                       "Default longitude coordinate (TUM MI building)")

    default_lat_coordinate = Attribute(48.26301, "Default latitude coordinate",
                                       "Default latitude coordinate (TUM MI building)")

    supported_countries = Attribute([TrafficSignIDGermany, TrafficSignIDZamunda, TrafficSignIDUsa],
                                    "Supported countries", "Supported countries for traffic sign cr2lanelet conversion")

    supported_countries_prefixes = Attribute(
            {"TrafficSignIDZamunda": "de", "TrafficSignIDGermany": "de", "TrafficSignIDUsa": "us"},
            "Supported countries prefixes",
            "Prefix dictionary for supported countries for traffic sign cr2lanelet conversion")

    supported_lanelet2_subtypes = Attribute(
            ["urban", "country", "highway", "busLane", "bicycleLane", "exitRamp", "sidewalk", "crosswalk"],
            "Supported lanelet2 subtypes", "Lanelet2 subtypes that are available in commonroad")

    node_distance_tolerance = Attribute(0.01, "Node distance tolerance",
                                        "Value of the tolerance (in meters) for which we mark nodes as equal")

    priority_signs = Attribute(["PRIORITY", "RIGHT_OF_WAY"], "Priority signs", "List of priority signs")

    adjacent_way_distance_tolerance = Attribute(0.05, "Adjacent way distance tolerance",
                                                "Threshold indicating adjacent way")

    start_node_id_value = Attribute(10, "Start node ID", "Initial node ID")

    proj_string = Attribute(gui_config.pseudo_mercator, "Projection string",
                            "String used for the initialization of projection")

    autoware = Attribute(False, "Autoware", "Boolean indicating whether the conversion should be autoware compatible")

    use_local_coordinates = Attribute(False, "Use local coordinates",
                                      "Boolean indicating whether local coordinates should be added")

    translate = Attribute(False, "Translate",
                          "Boolean indicating whether map should be translated by the location coordinate specified "
                          "in the CommonRoad map")

    left_driving = Attribute(False, "Left driving", "Map describes left driving system")

    adjacencies = Attribute(True, "Adjacencies",
                            "Detect left and right adjacencies of lanelets if they do not share a common way")

    LAYOUT = [["Coordinates and Tolerances", ways_are_equal_tolerance, default_lon_coordinate, default_lat_coordinate,
               node_distance_tolerance, adjacent_way_distance_tolerance, "Country and Type Information",
               supported_countries_prefixes, supported_lanelet2_subtypes],
              ["Node and Way Info", start_node_id_value, priority_signs, adjacencies, "Map Settings", proj_string,
               autoware, use_local_coordinates, translate, left_driving]]


lanelet2_config = Lanelet2Config()
