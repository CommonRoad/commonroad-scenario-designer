Tutorial for opendrive2lanelet
*******************************

Quick start
===========

OpenDRIVE to CommonRoad
-------------------------

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
-----------------------------------------------------

Converting a CommonRoad file which details a map to an equivalent OSM file can be done via the command line, e.g.,
``osm-convert inputfile.xml -o outputfile.osm``. Use ``osm-convert -h`` for an overview about all available parameters.

Usage in own code
===================

Converting an OpenDRIVE file to CommonRoad
-------------------------------------------

.. code:: python

    from lxml import etree

    from crmapconverter.opendriveparser.parser import parse_opendrive
    from crmapconverter.opendriveconversion.network import Network

    from from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
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
---------------------------------------------
.. code:: python

	from lxml import etree
	from crmapconverter.opendriveparser.parser import parse_opendrive

	with open("input_opendrive.xodr", 'r') as fh:
		open_drive = parse_opendrive(etree.parse(fh).getroot())

	# Now do stuff with the data
	for road in open_drive.roads:
		print("Road ID: {}".format(road.id))

A good file to take inspiration from is :py:mod:`opendrive2lanelet.io.opendrive_convert` or :py:mod:`opendrive2lanelet.io.osm_convert`.
