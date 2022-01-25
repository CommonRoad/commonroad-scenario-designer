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

Converting Lanelet/Lanelet2 to CommonRoad and vice versa
########################################################

Lanelet/Lanelet2 to CommonRoad
******************************
This conversion allows you to convert a road network description from the
`Lanelet/Lanelet2 format <https://github.com/fzi-forschungszentrum-informatik/Lanelet2>`_ to
the `CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-sc
enarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a).

Quick Start Guide
=================

Command Line Interface
----------------------

Want to quickly convert an Lanelet/Lanelet2 file to a CommonRoad map?

Use the command
``crdesigner osm -i input-file.osm -o output-file.xml``.

.. note::
   You have to activate the Python environment in which the CommonRoad Scenario Designer is
   installed before using the command line.

For example, ``crdesigner osm -i test.osm -o new_converted_file_name.xml``
produces a file called *new_converted_file_name.xml*

.. note::
   If no output file name is specified, the converted file will be called input-file.xml,
   e.g., ``crdesigner opendrive -i test.osm`` produces a file called *test.xml*.

You can also use the GUI to convert an OpenDRIVE file.
The GUI can be started from command line with ``crdesigner`` or ``crdesigner gui``.

Python APIs
-----------

.. code:: python

    from lxml import etree
    import os

    from commonroad.scenario.scenario import Tag
    from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
    from commonroad.planning.planning_problem import PlanningProblemSet

    from crdesigner.map_conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
    from crdesigner.map_conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser

    from crdesigner.map_conversion.map_conversion_interface import lanelet_to_commonroad

    input_path = ""  # replace empty string
    proj = ""  # replace empty string
    left_driving = False  # replace with favoured value
    adjacencies = False  # replace with favoured value

    # --------------------------------------- Option 1: General API --------------------------------------
    # load lanelet/lanelet2 file, parse it, and convert it to a CommonRoad scenario
    scenario = lanelet_to_commonroad(input_path, proj, left_driving, adjacencies)

    # store converted file as CommonRoad scenario
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=PlanningProblemSet(),
        author="Sebastian Maierhofer",
        affiliation="Technical University of Munich",
        source="CommonRoad Scenario Designer",
        tags={Tag.URBAN},
    )
    writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_Lanelet-1_1-T1.xml",
                         OverwriteExistingFile.ALWAYS)

    # ---------------------------------- Option 2: Lanelet conversion APIs -------------------------------
    # read and parse lanelet/lanelet2 file
    parser = Lanelet2Parser(etree.parse(input_path).getroot())
    lanelet2_content = parser.parse()

    # convert lanelet/lanelet2 map to CommonRoad
    lanelet2_converter = Lanelet2CRConverter(proj_string=proj)
    scenario = lanelet2_converter(lanelet2_content, detect_adjacencies=adjacencies, left_driving_system=left_driving)

    # store converted file as CommonRoad scenario
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=PlanningProblemSet(),
        author="Sebastian Maierhofer",
        affiliation="Technical University of Munich",
        source="CommonRoad Scenario Designer",
        tags={Tag.URBAN},
    )
    writer.write_to_file(os.path.dirname(os.path.realpath(__file__)) + "/" + "ZAM_Lanelet-1_1-T1.xml",
                         OverwriteExistingFile.ALWAYS)

Implementation Details
======================

As OSM lanelet boundaries are saved as geographic coordinates (lat, lon) and CommonRoad saves the
boundaries as cartesian (map projection) coordinates, a projection is needed for the conversion.
This projection is provided as a proj-string, as defined by the PROJ library (https://proj.org/index.html).
A proj-strings holds the parameters of a given coordinate transformation.

This project uses pyproj (https://pypi.org/project/pyproj/) which is a Python interface to the PROJ library.
The default proj-string defined here is "+proj=utm +zone=32 +ellps=WGS84", which describes
a Universal Transversal Mercator projection.

A few comments on the conversion:

- A lanelet and its successor share two nodes (last ones of the lanelet, first ones of the successor). Therefore, to detect this relation and save it in the CommonRoad file, dictionaries are used which save the node-lanelet relation, e.g., "Node is first left node of which lanelet" (first_left_nodes[node_id] = lanelet_id).
- Same for lanelet predecessor relationship.
- If lanelets in OSM share a common way, they are adjacent to each other. As a way can have only one direction, and if it is shared by lanelets having opposite driving directions, the vertices of one boundary of one of the two lanelet have to be reversed after conversion. This boundary is by default the left boundary considering the right-driving system in most of the world. You can set it to right by using the argument "left_driving_system=True" when calling the Converter.
- Lanelets can be adjacent without sharing a common way, because two ways can describe the same trajectory, but with a different number of nodes. This converter can still compare two vertices which resulted from converting two possible adjacent ways to the CommonRoad lanelet format and determine if the corresponding lanelets are adjacent. However, this is computationally quite intensive and is thus disabled by default (enable it with "--adjacencies" in the command line tool or setting "detect_adjacencies=True" when calling the converter.)

CommonRoad to Lanelet
*********************
This conversion allows you to convert a road network description from
the `CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-sc
enarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a) format to the
`Lanelet/Lanelet2 format <https://github.com/fzi-forschungszentrum-informatik/Lanelet2>`_ format.

Quick Start Guide
=================

Command Line Interface
----------------------

Want to quickly convert an CommonRoad map to a OSM lanelet map?

Use the command
``crdesigner osm -i input-file.xodr -o output-file.xml -c``.

.. note::
   You have to activate the Python environment in which the CommonRoad Scenario Designer is
   installed before using the command line.

For example, ``crdesigner osm -i test.xml -o new_converted_file_name.osm -c``
produces a file called *new_converted_file_name.osm*

.. note::
   If no output file name is specified, the converted file will be called input-file.xml,
   e.g., ``crdesigner osm -i test.osm -c`` produces a file called *test.osm*.

You can also use the GUI to convert an OpenDRIVE file.
The GUI can be started from command line with ``crdesigner`` or ``crdesigner gui``.


Python APIs
-----------

.. code:: python

    from lxml import etree
    from commonroad.common.file_reader import CommonRoadFileReader
    from crdesigner.map_conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter
    from crdesigner.input_output.api import commonroad_to_lanelet


    input_path = ""  # replace empty string
    output_name = ""  # replace empty string
    proj = ""  # replace empty string

    # ------------------------------------- Option 1: General API -----------------------------------------
    # load CommonRoad file and convert it to lanelet format
    commonroad_to_lanelet(input_path, output_name, proj)

    # ------------------------------- Option 2: Lanelet conversion APIs -----------------------------------
    try:
        commonroad_reader = CommonRoadFileReader(input_path)
        scenario, _ = commonroad_reader.open()
    except etree.XMLSyntaxError as xml_error:
        print(f"SyntaxError: {xml_error}")
        print(
            "There was an error during the loading of the selected CommonRoad file.\n"
        )
        scenario = None

    if scenario:
        l2osm = CR2LaneletConverter(proj)
        osm = l2osm(scenario)
        with open(f"{output_name}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
                )
            )


Implementation Details
======================

Converting back from cartesian to geographic coordinates requires, like mentioned in the above description of the
reverse conversion, a projection.

This code of this conversion take some points into account:

- If a lanelet has a successor, the converted nodes at the end of the lanelet have to be the same as the nodes of the converted successor.
- Same lanelet predecessor relationships.
- If a lanelet is adjacent to another lanelet, and the vertices of the shared border coincide, they can share a way in the converted OSM document.