from crdesigner.common.config.config_base import Attribute, BaseConfig
from crdesigner.common.config.gui_config import pseudo_mercator


class OpenDriveConfig(BaseConfig):
    """
    This config holds all configs for the Open Drive conversion.
    """

    initial_cr_id = Attribute(1, "Initial CommonRoad element ID", "Initial CommonRoad element ID")

    error_tolerance = Attribute(
        0.15, "Error tolerance", "Max. error between reference geometry and polyline of vertices"
    )

    min_delta_s = Attribute(
        0.5,
        "Min. delta s",
        "Min. step length between two sampling positions on the reference geometry",
    )

    precision = Attribute(
        0.5, "Precision", "Precision with which to convert plane group to lanelet"
    )

    driving_default_lanelet_type = Attribute(
        "urban",
        "Driving default lanelet type",
        "Mapping of OpenDRIVE driveway lane type to a CommonRoad lanelet type",
    )

    general_lanelet_type_activ = Attribute(
        True,
        "General lanelet type active",
        "Activates whether certain lanelet type should be added to all lanelets",
    )

    general_lanelet_type = Attribute(
        "urban",
        "General lanelet type",
        "Lanelet type which is added to every lanelet (if activated)",
    )

    lanelet_types_backwards_compatible = Attribute(
        False,
        "Lanelet types backwards compatible",
        "If active, converts OpenDRIVE lane types only to CommonRoad "
        "lanelet types "
        " with commonroad-io==2022.1 (probably also even older ones)",
    )

    intersection_straight_threshold = Attribute(
        35.0,
        "Intersection straight threshold",
        "Threshold which is used to determine if a successor of an incoming " "lane is ",
    )

    lane_segment_angle = Attribute(
        5.0,
        "Lane segment angle",
        "Least angle for lane segment to be added to the "
        "graph in degrees. If you edit the graph by hand, "
        "a value of 0 is recommended",
    )

    proj_string_odr = Attribute(
        pseudo_mercator, "Proj string", "String used for the " "initialization of projection"
    )

    filter_types = Attribute(
        [
            "driving",
            "restricted",
            "onRamp",
            "offRamp",
            "exit",
            "entry",
            "sidewalk",
            "shoulder",
            "crosswalk",
            "bidirectional",
        ],
        "Filter types",
        "OpenDRIVE lane types which are considered for conversion",
    )

    # cr2odr config parameters
    initial_road_counting = Attribute(20, "Initial road ID", "Initial counting for road ID")

    # 0.0174533 == 1deg
    heading_threshold = Attribute(
        0.00174533,
        "Heading threshold",
        "Threshold influencing selection of line (constant heading)",
    )

    # 0.01 == 0.5729578deg
    curvature_threshold = Attribute(
        0.01, "Curvature threshold", "Threshold influencing selection of arc (constant curvature)"
    )

    # 0.01 == 0.5729578deg
    curvature_dif_threshold = Attribute(
        0.01,
        "Curvature difference threshold",
        "Threshold influencing selection of clothoid (constant curvature difference)",
    )
    # Constant for lane parameters evaluation
    lane_evaluation_step = Attribute(
        50, "Curvature threshold clothoid", "Constant for lane parameters evaluation"
    )

    LAYOUT = [
        [
            "Conversion Parameters odr2cr",
            initial_cr_id,
            error_tolerance,
            min_delta_s,
            precision,
            proj_string_odr,
            "Intersection and Lane Segment Parameters",
            intersection_straight_threshold,
            lane_segment_angle,
        ],
        [
            "Lanelet Type Configuration odr2cr",
            driving_default_lanelet_type,
            general_lanelet_type_activ,
            general_lanelet_type,
            lanelet_types_backwards_compatible,
            filter_types,
        ],
        [
            "Conversion Parameters cr2odr",
            initial_road_counting,
            heading_threshold,
            curvature_threshold,
            curvature_dif_threshold,
            lane_evaluation_step,
        ],
    ]


open_drive_config = OpenDriveConfig()
