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

Parsing the OpenDRIVE xodr file is pretty straightforward. We mirror the OpenDRIVE document
with a Python class in this package. The XML is parsed and from the results a OpenDRIVE object is created.


Converting to network of ParametricLanes
========================================
Every width section in OpenDRIVE gets converted into a ParametricLane and
in turn every lane section gets converted into a ParametricLaneGroup which consists of multiple ParametricLanes. ParametricLanes have a ParametricLaneBorderGroup which has references to the left and right border of the ParametricLane and to the offset of each borders, which indicate at which point of the border the ParametricLane starts, as a Border can be used by multiple ParametricLanes.

Calculating cartesian coordinates at a position on a border works as follows:
#. The border has a reference border which calculates its coordinates.
#. The border has one or more tuples of width coefficients. With the width coefficients which apply at the position (determined by a width coefficients offset), it calculates the width of its reference border.
#. The width is added to the coordinates of the reference border in orthogonal direction, which results in coordinates of the border at a specific position.

The position on a border is always specified in a curve parameter ds which follows the path of the border. Each reference border is a border again, until the last reference border, which in turn is a reference path, a PlaneView object. This PlaneView consists of the basic geometries which constitute the reference path.




Converting ParametricLanes to Lanelets
======================================

Challenge: Splitting and joining lanelets
------------------------------------------

As detailed in Figure 6 of the accompanying paper, if a lanelet splits from
another lanelet (merge in the paper) or joins into another lanelet, an additional
border has to be created, because the end points of the splitting or joining lanelet
have to coincide with the the lanelet it splits from or joins into, respectively.
Creating the new border works by offsetting the other, not to be recreated border of the lanelet
by a linear varying distance, such that for e.g. a lanelet which joins into another lanelet,
the new width at the start is equal to the old width at the start and the new width at the end is equal to the width of the lanelet it joins into at the end.

The difficulty in determining the parameters used to calculate the new border was amplified by following problems:
* Determining the position from where to calculate the new border. In general, this position is where the width of the joining/splitting lanelet has a zero derivative.
* The joining/splitting of a border could extend over multiple, successive lanelets.
* The joining/splitting lanelet has to be adjacent all the time to the lanelet it joins into or splits from, respectively.

Smaller issues
--------------

#. If lanelets have zero width everywhere, they are discarded.
#. If a lanelet has an adjacent neighbor, and the successor of this neighbor and the lanelets successor are adjacent too, the lanelets and their successors can be each merged into one lanelet in most circumstances.


Converting OSM Lanelets to CommonRoad Lanelets and vice versa
==============================================================

OSM lanelet to CommonRoad
-------------------------

As OSM lanelet boundaries are saved as geographic coordinates (lat, lon) and CommonRoad saves the
boundaries as cartesian (map projection) coordinates, a projection is needed for the conversion.
This projection is provided as a proj-string, as defined by the PROJ library (https://proj.org/index.html). A proj-strings holds the parameters of a given coordinate transformation.

This project uses pyproj (https://pypi.org/project/pyproj/) which is a Python interface to the PROJ library. The default proj-string defined here is "+proj=utm +zone=32 +ellps=WGS84", which describes a Universal Transversal Mercator projection.

A few comments on the conversion:

#. A lanelet and its successor share two nodes (last ones of the lanelet, first ones of the successor). Therefore, to detect this relation and save it in the CommonRoad file, exist dicts which save the node-lanelet relation, e.g. "Node is first left node of which lanelet" (first_left_nodes[node_id] = lanelet_id).
#. Same goes for a lanelet and its predecessor.
#. If lanelets in OSM share a common way, they are adjacent to each other. As a way can have only one direction, and if it is shared by lanelets having opposite driving directions, the vertices of one boundary of one of the two lanelet have to be reversed after conversion. This boundary is by default the left boundary considering the right-driving system in most of the world. You can set it to right by using the argument "left_driving_system=True" when calling the Converter.
#. Lanelets can be adjacent without sharing a common way, because two ways can describe the same trajectory, but with a different number of nodes. This converter can still compare two vertices which resulted from converting two possible adjacent ways to the CommonRoad lanelet format and determine if the corresponding lanelets are adjacent. However, this is computationally quite intensive and is thus disabled by default (enable it with "--adjacencies" in the command line tool or setting "detect_adjacencies=True" when calling the converter.)

CommonRoad to OSM lanelet
-------------------------

Converting back from cartesian to geographic coordinates requires, like mentioned in the above description of the reverse conversion, a projection.

This code of this conversion take some points into account:

#. If a lanelet has a successor, the converted nodes at the end of the lanelet have to be the same as the nodes of the converted successor.
#. Same goes for a lanelet and its predecessor.
#. If a lanelet is adjacent to another lanelet, and the vertices of the shared border coincide, they can share a way in the converted OSM document.
