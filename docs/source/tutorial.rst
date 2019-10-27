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

Converting a CommonRoad file which details a map to an equivalent OSM file can be done via the command line.

For example
``osm-convert inputfile.xml --reverse -o outputfile.osm --adjencies --proj "+proj=etmerc +lat_0=38 +lon_0=125 +ellps=bessel"``


Usage in own code
===================

Converting an OpenDRIVE file to CommonRoad
-------------------------------------------

.. code:: python

	from lxml import etree
	from crmapconverter.opendriveparser.parser import parse_opendrive
	from crmapconverter.opendriveconversion.network import Network
	from from commonroad.common.file_writer import CommonRoadFileWriter

	# Import, parse and convert OpenDRIVE file
	with open("{}/opendrive-1.xodr".format(os.path.dirname(os.path.realpath(__file__))), "r") as fi:
		open_drive = parse_opendrive(etree.parse(fi).getroot())

	road_network = Network()
	road_network.load_opendrive(open_drive)

	scenario = road_network.export_commonroad_scenario()
	# Write CommonRoad scenario to file
	from commonroad.common.file_writer import CommonRoadFileWriter
	commonroad_writer = CommonRoadFileWriter(
				scenario=scenario,
				planning_problem_set=None,
				author="",
				affiliation="",
				source="OpenDRIVE 2 Lanelet Converter",
				tags="",
			)
	with open("{}/opendrive-1.xml".format(os.path.dirname(os.path.realpath(__file__))), "w") as fh:
		commonroad_writer.write_scenario_to_file_io(file_io=fh)

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
