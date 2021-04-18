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

This conversion allows you to convert a road network description from the
`OpenDRIVE format <http://www.opendrive.org/project.html>`_ to
the `CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-sc
enarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a).
Its theoretical background is detailed in the following paper
(https://mediatum.ub.tum.de/doc/1449005/1449005.pdf):
M. Althoff, S. Urban, and M. Koschi, "Automatic Conversion of Road Networks from OpenDRIVE to Lanelets,"
in Proc. of the IEEE International Conference on Service Operations and Logistics, and Informatics, 2018.

Since the release of the paper, various updates have been implemented in the code to enhance the converter.

Quick Start Guide
*****************

OpenDRIVE to CommonRoad
========================

Want to quickly convert an XODR file detailing a OpenDRIVE scenario
to a XML file with a CommonRoad scenario?

Use the command
``crdesigner opendrive -i input-file.xodr -o output-file.xml``.

For example ``crdesigner opendrive -i test.xodr -o new_converted_file_name.xml``
produces a file called *new_converted_file_name.xml*

.. note::
   If no output file name is specified, the converted file will be called input-file.xml,
   e.g. ``crdesigner opendrive -i test.xodr`` produces a file called *test.xml*.

Or use the GUI with the command
``crdesigner gui``.


Converting an OpenDRIVE file to CommonRoad
==========================================

.. code:: python

    from lxml import etree
    import os

    from commonroad.scenario.scenario import Tag
    from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
    from commonroad.planning.planning_problem import PlanningProblemSet

    from crdesigner.conversion.opendrive.opendriveparser.parser import parse_opendrive
    from crdesigner.conversion.opendrive.opendriveconversion.network import Network

    from crdesigner.io.api import opendrive_to_commonroad


    input_path = ""  # replace empty string

    # -------------------------------------- Option 1: General API --------------------------------------------
    # load OpenDRIVE file, parse it, and convert it to a CommonRoad scenario
    scenario = opendrive_to_commonroad(input_path)

    # store converted file as CommonRoad scenario
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=PlanningProblemSet(),
        author="Sebastian Maierhofer",
        affiliation="Technical University of Munich",
        source="CommonRoad Scenario Designer",
        tags={Tag.URBAN},
    )
    writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_OpenDRIVETest-1_1-T1.xml",
                         OverwriteExistingFile.ALWAYS)


    # ------------------------------- Option 2: OpenDRIVE conversion APIs ------------------------------------
    # OpenDRIVE parser to load file
    with open("{}".format(input_path), "r") as file_in:
        opendrive = parse_opendrive(etree.parse(file_in).getroot())

    # create OpenDRIVE intermediate network object
    road_network = Network()

    # convert OpenDRIVE file
    road_network.load_opendrive(opendrive)

    # export to CommonRoad scenario
    scenario = road_network.export_commonroad_scenario()

    # store converted file as CommonRoad scenario
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=PlanningProblemSet(),
        author="Sebastian Maierhofer",
        affiliation="Technical University of Munich",
        source="CommonRoad Scenario Designer",
        tags={Tag.URBAN},
    )
    writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_OpenDRIVETest-1_1-T1.xml",
                         OverwriteExistingFile.ALWAYS)


Implementation
**************

.. warning:
  **This work is still in progress.**

This part contains explanations of the rationales behind the implementation
of the opendrive2lanelet package.

In detail, the parsing of an OpenDrive file to a Python object,
the converting to a network of ``ParametricLane`` object and then the
conversion from parametric lanes to lanelets is explained.

Parsing OpenDRIVE
==================

Parsing the OpenDRIVE xodr file is pretty straightforward. We mirror the OpenDRIVE document
with a Python class in this package. The XML is parsed and from the results a OpenDRIVE object is created.


Converting to network of ParametricLanes
========================================
Every width section in OpenDRIVE gets converted into a ParametricLane and
in turn every lane section gets converted into a ParametricLaneGroup which consists of multiple ParametricLanes.
ParametricLanes have a ParametricLaneBorderGroup which has references to the left and right border of the
ParametricLane and to the offset of each borders, which indicate at which point of the border the ParametricLane
starts, as a Border can be used by multiple ParametricLanes.

Calculating cartesian coordinates at a position on a border works as follows:

- The border has a reference border which calculates its coordinates.
- The border has one or more tuples of width coefficients. With the width coefficients which apply at the position (determined by a width coefficients offset), it calculates the width of its reference border.
- The width is added to the coordinates of the reference border in orthogonal direction, which results in coordinates of the border at a specific position.

The position on a border is always specified in a curve parameter ds which follows the path of the border.
Each reference border is a border again, until the last reference border, which in turn is a reference path,
a PlaneView object. This PlaneView consists of the basic geometries which constitute the reference path.


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
the new width at the start is equal to the old width at the start and the new width at the end is equal to the
width of the lanelet it joins into at the end.

The difficulty in determining the parameters used to calculate the new border was amplified by following problems:

- Determining the position from where to calculate the new border. In general, this position is where the width of the joining/splitting lanelet has a zero derivative.
- The joining/splitting of a border could extend over multiple, successive lanelets.
- The joining/splitting lanelet has to be adjacent all the time to the lanelet it joins into or splits from, respectively.

Smaller issues
--------------

- If lanelets have zero width everywhere, they are discarded.
- If a lanelet has an adjacent neighbor, and the successor of this neighbor and the lanelets successor are adjacent too, the lanelets and their successors can be each merged into one lanelet in most circumstances.
