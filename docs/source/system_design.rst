System Design
=============

Format differences
------------------

OpenStreetMap (OSM) files and CommonRoad (CR) scenarios are formats that can both represent road networks with additional elements. While they both use XML to be stored on disk the internal structure has many differences. 
We will only look at the ones important for the conversion.

Firstly the road network in OSM is basically a graph with nodes and edges. One edge represents a road. Compared to CR here we have lanelets and information about intersections.
The coordinates (GPS) in OSM are rough and the amount of points per road section is much smaller.
To accomplish the conversion we have to use heuristics and interpolation for guessing the reality behind the data.

OSM also contains other elements like traffic signs. All this information is stored in so called tags or relations. With the latest version of CR (2020.2) new elements are inserted into the scenario format: Traffic Signs and Traffic Lights.

Conversion Overview
-------------------

Extremely simplified the conversion process works as follows:

.. image::
 images/OSM_control_flow.png
 :width: 500

The program takes a OSM file as input and parses it into the internel representation (graph). The refine the coordinate the user can adjust the graph with the GUI tool **EdgeEdit**. 

.. image::
 images/example_edgeedit.png
 :width: 500

Afterwards the each edge that is representing a road with multiple lanes is split into these lane so that there is exactely one edge per lane. As intersection are only single points in OSM the lanes are cut of with a specific radius around the intersection and linked together again. This linking can be adjusted with the GUI tool **LaneLinkEdit**. 

.. image::
 images/example_lanelinkedit.png
 :width: 500

Detailed Conversion
-------------------

Please refer to the Bachelor's thesis of Maximilian Rieger at **doc/pdf/thesis_osm2cr.pdf**.