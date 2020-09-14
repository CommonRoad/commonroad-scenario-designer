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

OpenDRIVE to CommonRoad Conversion
##################################

``opendrive2lanelet`` is a tool which allows you to convert a road network description from the
`OpenDRIVE format <http://www.opendrive.org/project.html>`_ to the `CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-scenarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a).
Hereby, the roads of the OpenDRIVE format are converted to `Lanelets <https://www.mrt.kit.edu/software/libLanelet/libLanelet.html>`_, hence the name of the package.
Additionally, we provide a converter from CommonRoad lanelets to OSM lanelets and vice versa.

This tool is part of the `CommonRoad <https://commonroad.in.tum.de/>`_ project. 
Its theoretical background is detailed in the following paper (https://mediatum.ub.tum.de/doc/1449005/1449005.pdf): M. Althoff, S. Urban, and M. Koschi, "Automatic Conversion of Road Networks from OpenDRIVE to Lanelets," in Proc. of the IEEE International Conference on Service Operations and Logistics, and Informatics, 2018.

Since the release of the paper, various updates have been implemented in the code to enhance the ``opendrive2lanelet`` converter.

Quick Start Guide
*****************

OpenDRIVE to CommonRoad
========================

Want to quickly convert an XODR file detailing a OpenDRIVE scenario
to a XML file with a CommonRoad scenario?

Use the command
``opendrive2lanelet-convert input-file.xodr -o output-file.xml``.

For example ``opendrive2lanelet test.xodr -o new_converted_file_name.xml``
produces a file called *new_converted_file_name.xml*

.. note::
   If no output file name is specified, the converted file will be called input-file.xml,
   e.g. ``opendrive2lanelet test.xodr`` produces a file called *test.xml*.

Or use the gui with command
``opendrive2lanelet-gui``.

.. warning::
   Visualizing the results of the conversion using the GUI is only helpful with small files, because you can not zoom into the map.
   Otherwise better use the ``opendrive2lanelet-visualize`` command.

If you want to inspect the result, you can use the command
``opendrive2lanelet-visualize input-file.xml``
which in turn calls the :py:meth:`draw_object` function from :py:mod:`commonroad.visualization.draw_dispatch_cr` to open a matplotlib window.


CommonRoad lanelets to OSM lanelets and vice versa
==================================================

Converting a CommonRoad file which details a map to an equivalent OSM file can be done via the command line, e.g.,
``osm-convert inputfile.xml -o outputfile.osm``. Use ``osm-convert -h`` for an overview about all available parameters.

Usage in own code


Converting an OpenDRIVE file to CommonRoad
==========================================

.. code:: python

    from lxml import etree

    from crmapconverter.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendriveconversion.network import Network

    from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
    from commonroad.planning.planning_problem import PlanningProblemSet
    from commonroad.scenario.scenario import Tag

    # Import, parse and convert OpenDRIVE file
    with open("{}/opendrive.xodr".format(os.path.dirname(os.path.realpath(__file__))), "r") as fi:
        open_drive = parse_opendrive(etree.parse(fi).getroot())

    road_network = Network()
    road_network.load_opendrive(open_drive)

    scenario = road_network.export_commonroad_scenario()
    # Write CommonRoad scenario to file
    from commonroad.common.file_writer import CommonRoadFileWriter
    CommonRoadFileWriter(
        scenario=self.scenario,
        planning_problem_set=PlanningProblemSet(),
        author="",
        affiliation="",
        source="OpenDRIVE 2 Lanelet Converter",
        tags={Tag.URBAN, Tag.HIGHWAY},
    )
    writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "opendrive.xml",
        OverwriteExistingFile.ALWAYS)

Just parsing the OpenDrive .xodr file
=====================================

.. code:: python

	from lxml import etree
	from crmapconverter.opendriveparser.parser import parse_opendrive

	with open("input_opendrive.xodr", 'r') as fh:
		open_drive = parse_opendrive(etree.parse(fh).getroot())

	# Now do stuff with the data
	for road in open_drive.roads:
		print("Road ID: {}".format(road.id))

A good file to take inspiration from is :py:mod:`opendrive2lanelet.io.opendrive_convert` or :py:mod:`opendrive2lanelet.io.osm_convert`.


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