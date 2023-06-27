"""
This model holds all default parameters necessary for the conversion
"""


class ConfigDefaultModel:

    def __init__(self):
        super().__init__()

        # Benchmark settings
        # name of the benchmark
        self.BENCHMARK_ID = "DEU_test"
        # author of the benchmark
        self.AUTHOR = "Automated converter by Maximilian Rieger"
        # affiliation of the benchmark
        self.AFFILIATION = "Technical University of Munich, Germany"
        # source of the benchmark
        self.SOURCE = "OpenStreetMaps (OSM)"
        # additional tags for the benchmark
        self.TAGS = "urban"
        # GeonameID
        self.GEONAME_ID = -999
        # GPS latitude
        self.GPS_LATITUDE = "123.45"
        # GPS longitude
        self.GPS_LONGITUDE = "123.45"
        # time step size for the benchmark in seconds
        self.TIMESTEPSIZE = 0.1

        # Lanelet type each lanelet should have
        self.LANELETTYPE = 'urban'

        # Aerial Image Settings
        # Use aerial images for edit
        self.AERIAL_IMAGES = False
        # Path to save downloaded aerial images
        self.IMAGE_SAVE_PATH = "files/imagery/"
        # The zoom level of Bing Maps tiles
        self.ZOOM_LEVEL = 19

        # Map download Settings
        # path to save downloaded files
        self.SAVE_PATH = "files/"
        # half width of area downloaded in meters
        self.DOWNLOAD_EDGE_LENGTH = 200
        # coordinates in latitude and longitude specifying the center of the downloaded area
        self.DOWNLOAD_COORDINATES = (48.262447, 11.657881)

        # Scenario Settings
        # include tunnels in result
        self.LOAD_TUNNELS = False
        # delete unconnected edges
        self.MAKE_CONTIGUOUS = False
        # split edges at corners (~90° between two waypoint segments)
        # this can help to model the course of roads on parking lots better
        self.SPLIT_AT_CORNER = True
        # use OSM restrictions for linking process
        self.USE_RESTRICTIONS = True
        # types of roads extracted from the OSM file
        # suitable types: 'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
        # 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street', 'service'
        self.ACCEPTED_HIGHWAYS_MAINLAYER = ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
                                            "residential", "motorway_link", "trunk_link", "primary_link",
                                            "secondary_link", "tertiary_link", "living_street", "service"]
        self.EXTRACT_SUBLAYER = True
        # types of highways extracted from the OSM file as sublayer
        # elements mustn't be in ACCEPTED_HIGHWAYS
        self.ACCEPTED_HIGHWAYS_SUBLAYER = ["path", "footway", "cycleway"]
        # Lanelet type of the sublayer lanelets
        self.SUBLAYER_LANELETTYPE = 'sidewalk'
        # Lanelet type of the sublayer lanelets that cross the main layer
        # overwrites SUBLAYER_LANELETTYPE for lanelets applied on
        self.CROSSING_LANELETTYPE = 'crosswalk'
        # osm ways with these tags are not taken into account
        self.REJECTED_TAGS = {"area": "yes"}
        # number of lanes for each type of road should be >=1
        self.LANECOUNTS = {"motorway": 6, "trunk": 4, "primary": 2, "secondary": 2, "tertiary": 2, "unclassified": 2,
                           "residential": 2, "motorway_link": 2, "trunk_link": 2, "primary_link": 2,
                           "secondary_link": 2, "tertiary_link": 2, "living_street": 2, "service": 2, "path": 1,
                           "footway": 1, "cycleway": 1}
        # width of lanes for each type of road in meters
        self.LANEWIDTHS = {"motorway": 3.5, "trunk": 3.5, "primary": 3.5, "secondary": 3.5, "tertiary": 3.5,
                           "unclassified": 3.5, "residential": 3.5, "motorway_link": 3.5, "trunk_link": 3.5,
                           "primary_link": 3.5, "secondary_link": 3.5, "tertiary_link": 3.5, "living_street": 3.5,
                           "service": 3.5, "path": 2.0, "footway": 2.0, "cycleway": 2.0}
        # default speed limit for each type of road in km/h
        self.SPEED_LIMITS = {"motorway": 120, "trunk": 100, "primary": 100, "secondary": 100, "tertiary": 100,
                             "unclassified": 80, "residential": 50, "motorway_link": 80, "trunk_link": 80,
                             "primary_link": 80, "secondary_link": 80, "tertiary_link": 80, "living_street": 7,
                             "service": 10, "path": 8, "footway": 8, "cycleway": 20}

        # Export Settings
        # desired distance between interpolated waypoints in meters
        self.INTERPOLATION_DISTANCE = 0.5
        # allowed inaccuracy of exported lines to reduce number of way points in meters
        self.COMPRESSION_THRESHOLD = 0.05
        # export the scenario in UTM coordinates
        self.EXPORT_IN_UTM = False
        # toggle filtering of negligible waypoints
        self.FILTER = True

        # Internal settings (these can be used to improve the conversion process for individual scenarios)
        # radius of the earth used for calculation in meters
        self.EARTH_RADIUS = 6371000
        # delete short edges after cropping
        self.DELETE_SHORT_EDGES = False
        # distance between waypoints used internally in meters
        self.INTERPOLATION_DISTANCE_INTERNAL = 0.25
        # bezier parameter for interpolation (should be within [0, 0.5])
        self.BEZIER_PARAMETER = 0.35
        # distance between roads at intersection used for cropping in meters
        self.INTERSECTION_DISTANCE = 20.0
        # associated with pedestrian pathways by default
        self.INTERSECTION_DISTANCE_SUBLAYER = 1.0
        # defines if the distance to other roads is used for cropping
        # if false the distance to the center of the intersection is used
        self.INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = True
        # threshold above which angles are considered as soft in degrees
        self.SOFT_ANGLE_THRESHOLD = 55.0
        # least angle for lane segment to be added to the graph in degrees.
        # if you edit the graph by hand, a value of 0 is recommended
        self.LANE_SEGMENT_ANGLE = 5.0
        # least distance between graph nodes to try clustering in meters
        self.CLUSTER_LENGTH = 10.0
        # least length of cluster to be added in meters
        self.LEAST_CLUSTER_LENGTH = 10.0
        # maximal distance between two intersections to which they are merged, if zero, no intersections are merged
        self.MERGE_DISTANCE = 3.5
        # threshold which is used to determine if a successor of an incoming lane is considered as straight
        self.INTERSECTION_STRAIGHT_THRESHOLD = 35.0

        # Toggle edit for user
        self.USER_EDIT = False

        # set of processed turn lanes
        # this should only be changed for further development
        self.RECOGNIZED_TURNLANES = ["left", "through", "right", "merge_to_left", "merge_to_right", "through;right",
                                     "left;through", "left;through;right", "left;right", "none", ]

        # values to search for in OSM
        self.TRAFFIC_SIGN_VALUES = ["traffic_signals", "stop", "give_way", "city_limit", ]
        # keys to search for in OSM
        self.TRAFFIC_SIGN_KEYS = ["traffic_sign", "overtaking", "traffic_signals:direction", "maxspeed", ]


config_default_model = ConfigDefaultModel()
