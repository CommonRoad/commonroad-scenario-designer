"""
This module holds all parameters necessary for the conversion
"""

# Benchmark Settings
# name of the benchmark
BENCHMARK_ID = "ZAM_Test-1_1_T-1"
# author of the benchmark
AUTHOR = "Automated converter by Maximilian Rieger"
# affiliation of the benchmark
AFFILIATION = "Technical University of Munich, Germany"
# source of the benchmark
SOURCE = "OpenStreetMaps (OSM)"
# additional tags for the benchmark
TAGS = "urban"
# Geonames username to retrieve geonamesID for created scenarios
GEONAMES_USERNAME = "demo"
# Mapillary Client ID which can be set to extract additional traffic signs. If set to "demo",
# mapillary signs will be disabled
MAPILLARY_CLIENT_ID = "demo"
# time step size for the benchmark in seconds
TIMESTEPSIZE = 0.1

# Lanelet type each lanelet should have
LANELETTYPE = "urban"

# Aerial Image Settings
# Use aerial images for edit
AERIAL_IMAGES = False
# Path to save downloaded aerial images
IMAGE_SAVE_PATH = "files/imagery/"
# The zoom level of Bing Maps tiles
ZOOM_LEVEL = 19
# aerial image area threshold limiting the user input for the coordinates
AERIAL_IMAGE_THRESHOLD = 0.01

# Map download Settings
# path to save downloaded files
SAVE_PATH = "files/"
# half width of area downloaded in meters
DOWNLOAD_EDGE_LENGTH = 200
# coordinates in latitude and longitude specifying the center of the downloaded area
DOWNLOAD_COORDINATES = (48.262447, 11.657881)

# Scenario Settings
# include tunnels in result
LOAD_TUNNELS = False
# delete unconnected edges
MAKE_CONTIGUOUS = False
# split edges at corners (~90° between two waypoint segments)
# this can help to model the course of roads on parking lots better
SPLIT_AT_CORNER = True
# use OSM restrictions for linking process
USE_RESTRICTIONS = True
# types of roads extracted from the OSM file
# suitable types: 'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
# 'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street', 'service'
ACCEPTED_HIGHWAYS_MAINLAYER = [
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    # "unclassified",
    "residential",
    "motorway_link",
    "trunk_link",
    "primary_link",
    "secondary_link",
    "tertiary_link",
    "living_street",
    # "service"
]
EXTRACT_SUBLAYER = False
# types of highways extracted from the OSM file as sublayer
# elements mustn't be in ACCEPTED_HIGHWAYS
ACCEPTED_HIGHWAYS_SUBLAYER = [
    "path",
    "footway",
    "cycleway"
]
# Lanelet type of the sublayer lanelets
SUBLAYER_LANELETTYPE = 'sidewalk'
# Lanelet type of the sublayer lanelets that cross the main layer
# overwrites SUBLAYER_LANELETTYPE for lanelets applied on
CROSSING_LANELETTYPE = 'crosswalk'
# osm ways with these tags are not taken into account
REJECTED_TAGS = {
    "area": "yes"
}
# number of lanes for each type of road should be >=1
LANECOUNTS = {
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
    "cycleway": 1
}
# width of lanes for each type of road in meters
LANEWIDTHS = {
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
    "cycleway": 2.0
}
# default speed limit for each type of road in km/h
SPEED_LIMITS = {
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
    "cycleway": 20
}

# Export Settings
# desired distance between interpolated waypoints in meters
INTERPOLATION_DISTANCE = 0.5
# allowed inaccuracy of exported lines to reduce number of way points in meters
COMPRESSION_THRESHOLD = 0.05
# export the scenario in UTM coordinates
EXPORT_IN_UTM = False
# toggle filtering of negligible waypoints
FILTER = True
# delete invalid lanes before export
DELETE_INVALID_LANES = True

# Internal Settings (these can be used to improve the conversion process for individual scenarios)
# radius of the earth used for calculation in meters
EARTH_RADIUS = 6371000
# delete short edges after cropping
DELETE_SHORT_EDGES = False
# distance between waypoints used internally in meters
INTERPOLATION_DISTANCE_INTERNAL = 0.5
# bezier parameter for interpolation (should be within [0, 0.5])
BEZIER_PARAMETER = 0.35
# distance between roads at intersection used for cropping in meters
INTERSECTION_DISTANCE = 4.0
# associated with pedestrian pathways by default
INTERSECTION_DISTANCE_SUBLAYER = 1.0
# defines if the distance to other roads is used for cropping
# if false the distance to the center of the intersection is used
INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = True
# threshold above which angles are considered as soft in degrees
SOFT_ANGLE_THRESHOLD = 55.0
# least angle for lane segment to be added to the graph in degrees.
# if you edit the graph by hand, a value of 0 is recommended
LANE_SEGMENT_ANGLE = 5.0
# least distance between graph nodes to try clustering in meters
CLUSTER_LENGTH = 10.0
# least length of cluster to be added in meters
LEAST_CLUSTER_LENGTH = 10.0
# maximal distance between two intersections to which they are merged, if zero, no intersections are merged
MERGE_DISTANCE = 3.5
# threshold which is used to determine if a successor of an incoming lane is considered as straight
INTERSECTION_STRAIGHT_THRESHOLD = 35.0
# option to clean up intersections and add new traffic lights to it, that are not part of the original OSM file
INTERSECTION_ENHANCEMENT = True
# option to remove unconnected lanelets from the main lanelet scenario
REMOVE_UNCONNECTED_LANELETS = True
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
TRAFFIC_LIGHT_CYCLE = {
    "red_phase": 57,
    "red_yellow_phase": 3,
    "green_phase": 37,
    "yellow_phase": 3
}

# Traffic Signs
# values to search for in OSM
TRAFFIC_SIGN_VALUES = [
    "traffic_signals",
    "stop",
    "give_way",
    "city_limit",
]
# keys to search for in OSM
TRAFFIC_SIGN_KEYS = [
    "traffic_sign",
    "overtaking",
    "traffic_signals:direction",
    "maxspeed",
]
# categories to include if mapillary is used for sign extraction
MAPILLARY_CATEGORIES = [
    "warning",
    "regulatory",
    "information",
    "complementary"
]
# include traffic signs based on their id, e.g. "Max_SPEED". Keep "ALL" to accept all found traffic sings
ACCEPTED_TRAFFIC_SIGNS = ["ALL"]
# exclude traffic signs based on their id, e.g. "MAX_SPEED". "ALL" has to be set in ACCEPTED_TRAFFIC_SIGNS
EXCLUDED_TRAFFIC_SIGNS = []

# User edit activation
# Toggle edit for user
USER_EDIT = False
