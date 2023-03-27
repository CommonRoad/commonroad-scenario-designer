"""
This module holds all parameters necessary for the conversion
"""
from commonroad.scenario.traffic_sign import TrafficSignIDGermany, TrafficSignIDZamunda, \
    TrafficSignIDUsa  # type: ignore

# value of the tolerance for which we mark ways as equal
WAYS_ARE_EQUAL_TOLERANCE = 0.001

# default proj coordinates of TUM MI building
TUM_MI_BUILDING_X = 11.66821
TUM_MI_BUILDING_Y = 48.26301

# supported countries for traffic sign cr2lanelet conversion:
CR2LANELET_SUPPORTED_COUNTRIES_LIST = [TrafficSignIDGermany, TrafficSignIDZamunda, TrafficSignIDUsa]

# prefix dictionary for supported countries for traffic sign cr2lanelet conversion
CR2LANELET_SUPPORTED_COUNTRIES_PREFIX_DICTIONARY = {"TrafficSignIDZamunda": "de", "TrafficSignIDGermany": "de",
                                                    "TrafficSignIDUsa": "us"}

# lanelet2 subtypes of lanelet that are availabe in commonroad
L2_LANELET_SUBTYPES = ["urban", "country", "highway", "busLane", "bicycleLane", "exitRamp", "sidewalk", "crosswalk"]

# value of the tolerance (in meters) for which we mark nodes as equal
NODE_DISTANCE_TOLERANCE = 0.01

# list of priority signs
PRIORITY_SIGNS = ["PRIORITY", "RIGHT_OF_WAY"]

ADJACENT_WAY_DISTANCE_TOLERANCE = 0.05

DEFAULT_SCENARIO_COUNTRY_ID = "ZAM"

DEFAULT_SCENARIO_MAP_NAME = "OpenDrive"

DEFAULT_SCENARIO_MAP_ID = 123

GLOBAL_TIMESTEP = 0.1

DEFAULT_START_NODE_VALUE = 10

DEFAULT_PROJ_STRING = "+proj=utm +zone=32 +ellps=WGS84"
