Implementation
**************

.. warning:
  **This work is still in progress.**

This part contains explanations of the rationales behind the implementation
of the opendrive2lanelet package.

In detail, the parsing of a OpenDrive file to a Python object,
the converting to a network of ParametricLane object and then the
conversion from Parametric Lanes to Lanelets is explained.

Parsing OpenDRIVE
==================


Converting to network of ParametricLanes
========================================


Converting ParametricLanes to Lanelets
======================================

Converting OSM Lanelets to CommonRoad Lanelets and vice versa
==============================================================

OSM to CommonRoad
------------------

As OSM lanelet boundaries are saved as geographic coordinates (lat, lon) and CommonRoad saves the
boundaries as cartesian (map projection) coordinates, a projection is needed for the conversion.
This projection is provided as a proj-string, as defined by the PROJ library (https://proj.org/index.html). A proj-strings holds the parameters of a given coordinate transformation.

This project uses pyproj (https://pypi.org/project/pyproj/) which is a Python interface to the PROJ library. The default proj-string defined here is "+proj=utm +zone=32 +ellps=WGS84", which describes a Universal Transversal Mercator projection.

A few comments on the conversion:

#. A lanelet and its successor share two nodes (last ones of the lanelet, first ones of the successor). Therefore, to detect this relation and save it in the CommonRoad file, exist dicts which save the node-lanelet relation, e.g. "Node is first left node of which lanelet" (first_left_nodes[node_id] = lanelet_id).
#. Same goes for a lanelet and its predecessor.
#. If lanelets in OSM share a common way, they are adjacent to each other. As a way can have only one direction, and if it is shared by lanelets having opposite driving directions, the vertices of one boundary of one of the two lanelet have to be reversed after conversion. This boundary is by default the left boundary considering the right-driving system in most of the world. You can set it to right by using the argument "left_driving_system=True" when calling the Converter.
#. Lanelets can be adjacent without sharing a common way, because two ways can describe the same trajectory, but with a different number of nodes. This converter can still compare two vertices which resulted from converting two possible adjacent ways to the CommonRoad lanelet format and determine if the corresponding lanelets are adjacent. However, this is computationally quite intensive and is thus disabled by default (enable it with "--adjacencies" in the command line tool or setting "detect_adjacencies=True" when calling the converter.)
