from crdesigner.common.config.config_base import Attribute, BaseConfig


class OsmConfig(BaseConfig):
    """
    This class contains all settings for the OSM import.
    """

    GEONAMES_USERNAME = Attribute("demo", "Geonames Username")
    # Mapillary Client ID which can be set to extract additional traffic signs. If set to "demo",
    # mapillary signs will be disabled
    MAPILLARY_CLIENT_ID = Attribute("demo", "Mapillary Client ID")

    # Proj string used by OSM; should not be changed in general.
    # See: https://osmdata.openstreetmap.de/info/projections.html
    PROJ_STRING_FROM = Attribute(
        "EPSG:4326",
        "Projection string",
        "String describing the projection of the OSM map",
    )

    # Lanelet type each lanelet should have
    LANELETTYPE = Attribute("urban", "Lanelet Type")

    # Aerial Image Settings
    # Path to save downloaded aerial images
    IMAGE_SAVE_PATH = Attribute("files/imagery/", "Image Save Path")
    # aerial image area threshold limiting the user input for the coordinates
    AERIAL_IMAGE_THRESHOLD = Attribute(0.01, "Aerial Image Threshold")

    # Map download Settings
    # path to save downloaded files
    SAVE_PATH = Attribute("files/", "Save Path")
    # half width of area downloaded in meters
    DOWNLOAD_EDGE_LENGTH = Attribute(200, "Download Edge Length")
    # coordinates in latitude and longitude specifying the center of the downloaded area
    DOWNLOAD_COORDINATES = Attribute((48.262447, 11.657881), "Download Coordinates")

    # Scenario Settings
    # include tunnels in result
    LOAD_TUNNELS = Attribute(False, "Load Tunnels")
    # delete unconnected edges
    MAKE_CONTIGUOUS = Attribute(False, "Make Contiguous")
    # split edges at corners (~90° between two waypoint segments)
    # this can help to model the course of roads on parking lots better
    SPLIT_AT_CORNER = Attribute(True, "Split at Corner")
    # use OSM restrictions for linking process
    USE_RESTRICTIONS = Attribute(True, "Use Restrictions")
    # types of roads extracted from the OSM file
    # suitable types: 'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
    # 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street', 'service'
    ACCEPTED_HIGHWAYS_MAINLAYER = Attribute(
        {
            "motorway": True,
            "trunk": True,
            "primary": True,
            "secondary": True,
            "tertiary": True,
            "unclassified": False,
            "residential": True,
            "motorway_link": True,
            "trunk_link": True,
            "primary_link": True,
            "secondary_link": True,
            "tertiary_link": True,
            "living_street": True,
            "service": False,
            "path": False,
            "footway": False,
            "cycleway": False,
        },
        "Accepted Highways Mainlayer",
    )
    EXTRACT_SUBLAYER = Attribute(False, "Extract Sublayer")
    # types of highways extracted from the OSM file as sublayer
    # elements mustn't be in ACCEPTED_HIGHWAYS
    ACCEPTED_HIGHWAYS_SUBLAYER = Attribute(
        {
            "motorway": False,
            "trunk": False,
            "primary": False,
            "secondary": False,
            "tertiary": False,
            "unclassified": False,
            "residential": False,
            "motorway_link": False,
            "trunk_link": False,
            "primary_link": False,
            "secondary_link": False,
            "tertiary_link": False,
            "living_street": False,
            "service": False,
            "path": True,
            "footway": True,
            "cycleway": True,
        },
        "Accepted Highways Sublayer",
    )
    # Lanelet type of the sublayer lanelets
    SUBLAYER_LANELETTYPE = Attribute("sidewalk", "Sublayer Lanelet Type")
    # Lanelet type of the sublayer lanelets that cross the main layer
    # overwrites SUBLAYER_LANELETTYPE for lanelets applied on
    CROSSING_LANELETTYPE = Attribute("crosswalk", "Crossing Lanelet Type")
    # osm ways with these tags are not taken into account
    REJECTED_TAGS = Attribute({"area": "yes"}, "Rejected Tags")
    # number of lanes for each type of road should be >=1
    LANECOUNTS = Attribute(
        {
            "motorway": 6,
            "trunk": 4,
            "primary": 2,
            "secondary": 2,
            "tertiary": 2,
            "unclassified": 2,
            "residential": 2,
            "motorway_link": 2,
            "trunk_link": 2,
            "primary_link": 2,
            "secondary_link": 2,
            "tertiary_link": 2,
            "living_street": 2,
            "service": 2,
            "path": 1,
            "footway": 1,
            "cycleway": 1,
        },
        "Lane Counts",
    )
    # width of lanes for each type of road in meters
    LANEWIDTHS = Attribute(
        {
            "motorway": 3.5,
            "trunk": 3.5,
            "primary": 3.5,
            "secondary": 3.5,
            "tertiary": 3.5,
            "unclassified": 3.5,
            "residential": 3.5,
            "motorway_link": 3.5,
            "trunk_link": 3.5,
            "primary_link": 3.5,
            "secondary_link": 3.5,
            "tertiary_link": 3.5,
            "living_street": 3.5,
            "service": 3.5,
            "path": 2.0,
            "footway": 2.0,
            "cycleway": 2.0,
        },
        "Lane widths",
    )
    # default speed limit for each type of road in km/h
    SPEED_LIMITS = Attribute(
        {
            "motorway": 120,
            "trunk": 100,
            "primary": 100,
            "secondary": 100,
            "tertiary": 100,
            "unclassified": 80,
            "residential": 50,
            "motorway_link": 80,
            "trunk_link": 80,
            "primary_link": 80,
            "secondary_link": 80,
            "tertiary_link": 80,
            "living_street": 7,
            "service": 10,
            "path": 8,
            "footway": 8,
            "cycleway": 20,
        },
        "Speed limits",
    )

    # Export Settings
    # desired distance between interpolated waypoints in meters
    INTERPOLATION_DISTANCE = Attribute(0.5, "Interpolation Distance")
    # allowed inaccuracy of exported lines to reduce number of way points in meters
    COMPRESSION_THRESHOLD = Attribute(0.05, "Compression Threshold")
    # toggle filtering of negligible waypoints
    FILTER = Attribute(True, "Filter")
    # delete invalid lanes before export
    DELETE_INVALID_LANES = Attribute(True, "Delete Invalid Lanes")

    # Internal Settings (these can be used to improve the conversion process for individual scenarios)
    # radius of the earth used for calculation in meters
    EARTH_RADIUS = Attribute(6371000, "Earth Radius")
    # delete short edges after cropping
    DELETE_SHORT_EDGES = Attribute(False, "Delete Short Edges")
    # distance between waypoints used internally in meters
    INTERPOLATION_DISTANCE_INTERNAL = Attribute(0.5, "Interpolation Distance Internal")
    # bezier parameter for interpolation (should be within [0, 0.5])
    BEZIER_PARAMETER = Attribute(0.35, "Bezier Parameter")
    # distance between roads at intersection used for cropping in meters
    INTERSECTION_DISTANCE = Attribute(4.0, "Intersection Distance")
    # associated with pedestrian pathways by default
    INTERSECTION_DISTANCE_SUBLAYER = Attribute(1.0, "Intersection Distance Sublayer")
    # defines if the distance to other roads is used for cropping
    # if false the distance to the center of the intersection is used
    INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = Attribute(
        True, "Intersection Cropping with Respect to Roads"
    )
    # threshold above which angles are considered as soft in degrees
    SOFT_ANGLE_THRESHOLD = Attribute(55.0, "Soft Angle Threshold")
    # least angle for lane segment to be added to the graph in degrees.
    # if you edit the graph by hand, a value of 0 is recommended
    LANE_SEGMENT_ANGLE = Attribute(5.0, "Lane Segment Angle")
    # least distance between graph nodes to try clustering in meters
    CLUSTER_LENGTH = Attribute(10.0, "Cluster Length")
    # least length of cluster to be added in meters
    LEAST_CLUSTER_LENGTH = Attribute(10.0, "Least Cluster Length")
    # maximal distance between two intersections to which they are merged, if zero, no intersections are merged
    MERGE_DISTANCE = Attribute(3.5, "Merge Distance")
    # threshold which is used to determine if a successor of an incoming lane is considered as straight
    INTERSECTION_STRAIGHT_THRESHOLD = Attribute(35.0, "Intersection Straight Threshold")
    # option to clean up intersections and add new traffic lights to it, that are not part of the original OSM file
    INTERSECTION_ENHANCEMENT = Attribute(True, "Intersection Enhancement")
    # option to remove unconnected lanelets from the main lanelet scenario
    REMOVE_UNCONNECTED_LANELETS = Attribute(True, "Remove Unconnected Lanelets")
    # set of processed turn lanes
    # this should only be changed for further development
    RECOGNIZED_TURNLANES = [
        "left",
        "through",
        "right",
        "slight_right",
        "slight_left",
        "merge_to_left",
        "merge_to_right",
        "through;right",
        "left;through",
        "left;through;right",
        "left;right",
        "none",
    ]

    # Traffic Lights
    # cycle that will be applied to each traffic light. Values in seconds
    TRAFFIC_LIGHT_CYCLE = Attribute(
        {"red_phase": 57, "red_yellow_phase": 3, "green_phase": 37, "yellow_phase": 3},
        "Traffic Light Cycle",
    )

    # Traffic Signs
    # values to search for in OSM
    TRAFFIC_SIGN_VALUES = ["traffic_signals", "stop", "give_way", "city_limit"]
    # keys to search for in OSM
    TRAFFIC_SIGN_KEYS = ["traffic_sign", "overtaking", "traffic_signals:direction", "maxspeed"]
    # categories to include if mapillary is used for sign extraction
    MAPILLARY_CATEGORIES = ["warning", "regulatory", "information", "complementary"]
    # include traffic signs based on their id, e.g. "Max_SPEED". Keep "ALL" to accept all found traffic sings
    ACCEPTED_TRAFFIC_SIGNS = ["ALL"]
    # exclude traffic signs based on their id, e.g. "MAX_SPEED". "ALL" has to be set in ACCEPTED_TRAFFIC_SIGNS
    EXCLUDED_TRAFFIC_SIGNS = []

    LAYOUT = [
        [
            "Scenario Settings",
            LOAD_TUNNELS,
            MAKE_CONTIGUOUS,
            SPLIT_AT_CORNER,
            USE_RESTRICTIONS,
            ACCEPTED_HIGHWAYS_MAINLAYER,
            LANECOUNTS,
            LANECOUNTS,
            SPEED_LIMITS,
            "Export Settings",
            INTERPOLATION_DISTANCE,
            COMPRESSION_THRESHOLD,
            FILTER,
        ],
        [
            "Internal Settings",
            EARTH_RADIUS,
            DELETE_SHORT_EDGES,
            INTERPOLATION_DISTANCE_INTERNAL,
            BEZIER_PARAMETER,
            INTERSECTION_DISTANCE,
            INTERSECTION_DISTANCE_SUBLAYER,
            SOFT_ANGLE_THRESHOLD,
            LANE_SEGMENT_ANGLE,
            CLUSTER_LENGTH,
            LEAST_CLUSTER_LENGTH,
            MERGE_DISTANCE,
            "Crossing Sublayer Settings",
            EXTRACT_SUBLAYER,
            ACCEPTED_HIGHWAYS_SUBLAYER,
            INTERSECTION_DISTANCE_SUBLAYER,
        ],
    ]


osm_config = OsmConfig()
