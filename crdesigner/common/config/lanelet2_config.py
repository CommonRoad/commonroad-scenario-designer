from commonroad.scenario.traffic_sign import (
    TrafficSignIDGermany,
    TrafficSignIDUsa,
    TrafficSignIDZamunda,
)

from crdesigner.common.config.config_base import Attribute, BaseConfig


class Lanelet2Config(BaseConfig):
    """
    Lanelet2Config contains all the configuration parameters for the conversion from lanelet2 to CommonRoad.
    """

    # cr2lanelet
    ways_are_equal_tolerance = Attribute(
        0.001, "Ways are equal tolerance", "Value of the tolerance for which we mark ways as equal"
    )

    autoware = Attribute(
        False,
        "Autoware",
        "Boolean indicating whether the conversion " "should be autoware compatible",
    )

    use_local_coordinates = Attribute(
        False,
        "Use local coordinates",
        "Boolean indicating whether local coordinates should be added",
    )

    supported_countries = [TrafficSignIDGermany, TrafficSignIDZamunda, TrafficSignIDUsa]

    supported_countries_prefixes = {
        "TrafficSignIDZamunda": "de",
        "TrafficSignIDGermany": "de",
        "TrafficSignIDUsa": "us",
    }

    supported_lanelet2_subtypes = Attribute(
        [
            "urban",
            "country",
            "highway",
            "interstate",
            "busLane",
            "bicycleLane",
            "exitRamp",
            "sidewalk",
            "crosswalk",
        ],
        "Supported lanelet2 subtypes",
        "Lanelet2 subtypes that are available in commonroad",
    )

    supported_lanelet2_vehicles = ["car", "truck", "bus", "emergency", "motorcycle", "taxi"]

    # lanelet2cr
    node_distance_tolerance = Attribute(
        0.01,
        "Node distance tolerance",
        "Value of the tolerance (in meters) for which we mark nodes as equal",
    )

    priority_signs = Attribute(
        ["PRIORITY", "RIGHT_OF_WAY"], "Priority signs", "List of priority signs"
    )

    adjacent_way_distance_tolerance = Attribute(
        0.05, "Adjacent way distance tolerance", "Threshold indicating adjacent way"
    )

    start_node_id_value = Attribute(10, "Start Node ID", "Initial node ID")

    left_driving = Attribute(False, "Left Driving", "Map describes left driving system")

    adjacencies = Attribute(
        True,
        "Adjacencies",
        "Detect left and right adjacencies of lanelets if they do not share a common way",
    )

    translate = Attribute(
        False,
        "Translate",
        "Boolean indicating whether map should be translated by the location coordinate specified "
        "in the CommonRoad map",
    )

    allowed_tags = Attribute(
        ["type", "subtype", "one_way", "virtual", "location", "bicycle", "highway"],
        "Allowed Tags",
        "Lanelet tags which are considered for conversion. "
        "Lanelets with other tags are not converted.",
    )

    eps2_values = Attribute(
        [1, 5, 10, 20, 50],
        "CCS Eps2 Values",
        "Possible values for length of additional segments of curvilinear coordinate system.",
    )

    max_polyline_resampling_step_values = Attribute(
        [2, 0.25, 0.5, 1, 5, 10, 20, 25],
        "Max. Polyline Resampling Step Values",
        "Possible values for resampling step size of reference for curvilinear coordinate system.",
    )

    chaikins_initial_refinements = Attribute(
        5,
        "Initial CCS Refinements",
        "Number of initial refinements of chaikins corner cutting algorithms "
        "for curvilinear coordinate system.",
    )

    chaikins_repeated_refinements = Attribute(
        10,
        "Max. Polyline Resampling Step",
        "Number of repeated refinements of chaikins corner cutting algorithms "
        "for curvilinear coordinate system.",
    )

    resampling_initial_step = Attribute(
        5,
        "Initial Max. Polyline Resampling Step",
        "Initial value for resampling step size of reference for curvilinear coordinate system.",
    )

    resampling_repeated_step = Attribute(
        5,
        "Repeated Max. Polyline Resampling Step",
        "Repeated value for resampling step size of reference for curvilinear coordinate system.",
    )

    perc_vert_wrong_side = Attribute(
        0.6,
        "Percentage Vertices Correct Direction",
        "Min. percentage of correctly assigned vertices to each polyline of lanelet.",
    )

    LAYOUT = [
        [
            "CommonRoad To Lanelet2",
            ways_are_equal_tolerance,
            autoware,
            use_local_coordinates,
            supported_lanelet2_subtypes,
            "General",
            translate,
            left_driving,
        ],
        [
            "Lanelet2 To CommonRoad",
            node_distance_tolerance,
            adjacent_way_distance_tolerance,
            start_node_id_value,
            priority_signs,
            adjacencies,
            allowed_tags,
        ],
    ]


lanelet2_config = Lanelet2Config()
