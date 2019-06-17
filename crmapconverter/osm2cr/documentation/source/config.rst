Parameters
==========

There are several parameters which can be edited in **config.py**.
These Parameters can also be set in the GUI via **edit settings**.

Benchmark settings
------------------
* **BENCHMARK_ID**: name of the benchmark::

	BENCHMARK_ID = "test_bench"

* **AUTHOR**: author of the benchmark::

	AUTHOR = "Automated converter by Maximilian Rieger"

* **AFFILIATION**: affiliation of the benchmark::

	AFFILIATION = "Technical University of Munich, Germany"

* **SOURCE**: source of the benchmark::

	SOURCE = "OpenStreetMaps (OSM)"

* **TAGS**: additional tags for the benchmark::

	TAGS = "..."

* **TIMESTEPSIZE**: time step size for the benchmark in seconds::

	TIMESTEPSIZE = 0.1

Aerial Image Settings
---------------------
* **AERIAL_IMAGES** Use aerial images for edit::

	AERIAL_IMAGES = True

* **IMAGE_SAVE_PATH**: Path to save downloaded aerial images::

	IMAGE_SAVE_PATH = "files/imagery/"

* **ZOOM_LEVEL**: The zoom level of Bing Maps tiles::

	ZOOM_LEVEL = 19

* **BING_MAPS_KEY**: The key to access bing maps::

	BING_MAPS_KEY = "key"

Map download Settings
---------------------
* **SAVE_PATH** path to save downloaded files::

	SAVE_PATH = "files/"

* **DOWNLOAD_EDGE_LENGTH**: half width of area downloaded in meters::

	DOWNLOAD_EDGE_LENGTH = 200

* **DOWNLOAD_COORDINATES**: coordinates in latitude and longitude specifying the center of the downloaded area::

	DOWNLOAD_COORDINATES = (48.262447, 11.657881)

Scenario Settings
-----------------
* **LOAD_TUNNELS**: include tunnels in result::

	LOAD_TUNNELS = False

* **MAKE_CONTIGUOUS**: delete unconnected edges::

	MAKE_CONTIGUOUS = False

* **SPLIT_AT_CORNER**: split edges at corners (~90° between two waypoint segments)
  this can help to model the course of roads on parking lots better::

	SPLIT_AT_CORNER = True

* **USE_RESTRICTIONS**: use OSM restrictions for linking process::

	USE_RESTRICTIONS = True

* **ACCEPTED_HIGHWAYS**: types of roads extracted from the OSM file
  suitable types: 'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified', 'residential',
  'motorway_link', 'trunk_link', 'primary_link', 'secondary_link', 'tertiary_link', 'living_street', 'service'::

	ACCEPTED_HIGHWAYS = ['motorway',
                     'trunk',
                     'primary',
                     'secondary',
                     'tertiary',
                     'unclassified',
                     'residential',
                     'motorway_link',
                     'trunk_link',
                     'primary_link',
                     'secondary_link',
                     'tertiary_link',
                     'living_street',
                     'service']

* **LANECOUNTS**: number of lanes for each type of road should be >=1::

	LANECOUNTS = {'motorway': 6,
              'trunk': 4,
              'primary': 2,
              'secondary': 2,
              'tertiary': 2,
              'unclassified': 2,
              'residential': 2,
              'motorway_link': 2,
              'trunk_link': 2,
              'primary_link': 2,
              'secondary_link': 2,
              'tertiary_link': 2,
              'living_street': 2,
              'service': 2}

* **LANEWIDTHS**: width of lanes for each type of road in meters::

	LANEWIDTHS = {'motorway': 2.5,
              'trunk': 2.5,
              'primary': 2.5,
              'secondary': 2.5,
              'tertiary': 2.5,
              'unclassified': 2.5,
              'residential': 2.5,
              'motorway_link': 2.5,
              'trunk_link': 2.5,
              'primary_link': 2.5,
              'secondary_link': 2.5,
              'tertiary_link': 2.5,
              'living_street': 2.5,
              'service': 2.5}

* **SPEED_LIMITS**: default speed limit for each type of road in km/h::

	SPEED_LIMITS = {'motorway': 120,
                'trunk': 100,
                'primary': 100,
                'secondary': 100,
                'tertiary': 100,
                'unclassified': 80,
                'residential': 50,
                'motorway_link': 80,
                'trunk_link': 80,
                'primary_link': 80,
                'secondary_link': 80,
                'tertiary_link': 80,
                'living_street': 7,
                'service': 10}

Export Settings
---------------
* **INTERPOLATION_DISTANCE**: desired distance between interpolated waypoints in meters::

	INTERPOLATION_DISTANCE = 0.5

* **COMPRESSION_THRESHOLD**: allowed inaccuracy of exported lines to reduce number of way points in meters::

	COMPRESSION_THRESHOLD = 0.05

* **EXPORT_IN_UTM**: export the scenario in UTM coordinates::

	EXPORT_IN_UTM = True

* **FILTER**: toggle filtering of negligible waypoints::

	FILTER = True

Internal settings
-----------------
these can be used to improve the conversion process for individual scenarios

* **EARTH_RADIUS**: radius of the earth used for calculation in meters::

	EARTH_RADIUS = 6371000

* **DELETE_SHORT_EDGES**: delete short edges after cropping::

	DELETE_SHORT_EDGES = False

* **INTERPOLATION_DISTANCE_INTERNAL**: distance between waypoints used internally in meters::

	INTERPOLATION_DISTANCE_INTERNAL = 0.25

* **BEZIER_PARAMETER**: bezier parameter for interpolation (should be within [0, 0.5])::

	BEZIER_PARAMETER = 0.35

* **INTERSECTION_DISTANCE**: distance between roads at intersection used for cropping in meters::

	INTERSECTION_DISTANCE = 5.0

* **INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS**: defines if the distance to other roads is used for cropping
  if false the distance to the center of the intersection is used::

	INTERSECTION_CROPPING_WITH_RESPECT_TO_ROADS = True

* **SOFT_ANGLE_THRESHOLD**: threshold above which angles are considered as soft in degrees::

	SOFT_ANGLE_THRESHOLD = 55.0

* **LANE_SEGMENT_ANGLE**: least angle for lane segment to be added to the graph in degrees.
  if you edit the graph by hand, a value of 0 is recommended::

	LANE_SEGMENT_ANGLE = 5.0

* **CLUSTER_LENGTH**: least distance between graph nodes to try clustering in meters::

	CLUSTER_LENGTH = 10.0

* **LEAST_CLUSTER_LENGTH**: least length of cluster to be added in meters::

	LEAST_CLUSTER_LENGTH = 10.0

* **MERGE_DISTANCE**: maximal distance between two intersections to which they are merged, if zero, no intersections are merged::

	MERGE_DISTANCE = 0.0

User edit activation
--------------------

* **USER_EDIT**: Toggle edit for user::

	USER_EDIT = False
