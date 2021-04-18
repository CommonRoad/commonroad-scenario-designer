.. 
  Normally, there are no heading levels assigned to certain characters as the structure is
  determined from the succession of headings. However, this convention is used in Python’s
  Style Guide for documenting which you may follow:

  # with overline, for parts
  * for chapters
  = for sections
  - for subsections
  ^ for subsubsections
  " for paragraphs

Converting OSM Lanelets to CommonRoad Lanelets and vice versa
==============================================================

OSM lanelet to CommonRoad
-------------------------

As OSM lanelet boundaries are saved as geographic coordinates (lat, lon) and CommonRoad saves the
boundaries as cartesian (map projection) coordinates, a projection is needed for the conversion.
This projection is provided as a proj-string, as defined by the PROJ library (https://proj.org/index.html).
A proj-strings holds the parameters of a given coordinate transformation.

This project uses pyproj (https://pypi.org/project/pyproj/) which is a Python interface to the PROJ library.
The default proj-string defined here is "+proj=utm +zone=32 +ellps=WGS84", which describes
a Universal Transversal Mercator projection.

A few comments on the conversion:

#. A lanelet and its successor share two nodes (last ones of the lanelet, first ones of the successor).
Therefore, to detect this relation and save it in the CommonRoad file, exist dicts which save the node-lanelet
relation, e.g. "Node is first left node of which lanelet" (first_left_nodes[node_id] = lanelet_id).
#. Same goes for a lanelet and its predecessor.
#. If lanelets in OSM share a common way, they are adjacent to each other. As a way can have only one direction,
and if it is shared by lanelets having opposite driving directions, the vertices of one boundary of one of the two
lanelet have to be reversed after conversion. This boundary is by default the left boundary considering the
right-driving system in most of the world. You can set it to right by using the argument "left_driving_system=True"
when calling the Converter.
#. Lanelets can be adjacent without sharing a common way, because two ways can describe the same trajectory,
but with a different number of nodes. This converter can still compare two vertices which resulted from
converting two possible adjacent ways to the CommonRoad lanelet format and determine if the corresponding
lanelets are adjacent. However, this is computationally quite intensive and is thus disabled by default
(enable it with "--adjacencies" in the command line tool or setting "detect_adjacencies=True" when calling the
converter.)

CommonRoad to OSM lanelet
-------------------------

Converting back from cartesian to geographic coordinates requires, like mentioned in the above description of the
reverse conversion, a projection.

This code of this conversion take some points into account:

#. If a lanelet has a successor, the converted nodes at the end of the lanelet have to be the same as the nodes of the
converted successor.
#. Same goes for a lanelet and its predecessor.
#. If a lanelet is adjacent to another lanelet, and the vertices of the shared border coincide, they can share a way
in the converted OSM document.