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

CommonRoad to OpenDRIVE Conversion
##################################

This conversion allows you to convert a road network description from the
`CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-sc
enarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a) 
to the `OpenDRIVE format <https://www.asam.net/standards/detail/opendrive/>`_


Quick Start Guide
*****************

Command Line Interface
========================

Want to quickly convert a XML file with a CommonRoad scenario
to an XODR file describing an OpenDRIVE scenario?

Use the command
``crdesigner map-convert-commonroad -i input-file.xml -o output-file.xodr``.

.. note::
   You have to activate the Python environment in which the CommonRoad Scenario Designer is
   installed before using the command line.

For example, ``crdesigner map-convert-commonroad -i test.xml -o new_converted_file_name.xodr``
produces a file called *new_converted_file_name.xodr*

.. note::
   If no output file name is specified, the converted file will be called input-file.xodr,
   e.g., ``crdesigner map-convert-opendrive -i test.xml`` produces a file called *test.xodr*.

You can also use the GUI to convert an OpenDRIVE file.
The GUI can be started from command line with ``crdesigner`` or ``crdesigner gui``.


Python APIs
==========================================

.. code:: python

	from crdesigner.map_conversion.map_conversion_interface import commonroad_to_opendrive
	from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
	from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter

	input_file = "" #path to CommonRoad file
	output_file = "" #path where OpenDRIVE file should be stored

	# -------------------------------------- Option 1: General API --------------------------------------------
	# load xml file, preprocess it, and convert it to a respective OpenDRIVE file
	commonroad_to_opendrive(input_file, output_file)

    # ------------------------------- Option 2: CommonRoad conversion APIs ------------------------------------
	# load the xml file and preprocess it
	data = DataLoader(input_file)

	scenario, successors, ids = data.initialize()
	converter = Converter(input_file, scenario, successors, ids)
	converter.convert(output_file) 


Implementation Details
**********************

Initially, the CommonRoad XML file is read to create the corresponding lanelet network along with necessary intersections and dictionary of converted roads.
Afterward, the scenario object is converted into corresponding OpenDRIVE xodr file.

Code Structure
==============
Here is a simplified overview about the code structure (the presented code
structure is not complete)::

    /map_conversion/opendrive
    │
    └── /cr_to_opendrive
        ├── /elements
        ├── /reference_maps
        ├── /utils
        ├── converter.py
        └── dataloader.py

- `/elements`: This directory contains various classes for OpenDRIVE objects and is used in various stages during the conversion.
- `/utils`: This directory contains two files in which one is used to preprocess the polyline for road elements and another is used to write the OpenDRIVE file using the OpenDRIVE tree element.
- `converter.py`: Main conversion file.
- `dataloader.py`: File to parse CommonRoad file which includes preparation of intersections and preparation of a dictionary with lanelet ids that keep track of converted lanelets.

.. _fig.layout-commonroad-to-opendrive:
.. figure:: images/commonroad_to_opendrive_flowchart.png
   :alt: Layout of the CommonRoad Scenario Designer.
   :name: fig:workflow
   :align: center

   CommonRoad to OpenDRIVE conversion flow chart.

Create Scenario Object  
======================
The CommonRoad xml file is passed to the Dataloader class
in which the file is read and converted to the corresponding scenario object
using the CommonRoadFileReader.
Additionally, the dataloader prepares intersections and creates a dictionary with lanelet IDs
that keep track of already converted lanelet.

Convert Scenario Object to OpenDRIVE File 
=========================================
In order to convert scenario object to OpenDRIVE file, various elements have to be created
and linked together which are explained below in detail:


Roads
---------
For a given lanelet, it is expanded left and right to construct the corresponding road.
Then, we continue to expand with its successor and predecessors.
The road network is explored in a breadth-first fashion.


Checking correctness of road construction
----------------------------------------------------
We need to check whether all lanelets have been added to the road network or not. 
If it is not added, an error is raised as this particular lanelet is not added to the road network and the user is informed to check algorithm or provided road network.


Create linkMap where all linkage information is stored
------------------------------------------------------
A linkmap consist of ids of a road and it links. For each road and its links,
a data structure is created to store its corresponding successor and predessor. 
Each link consist of ids of a lanelet and corresponding lane successor and lane predessor.
For each lanelet, a data structure is created to store its corresponding lane successor 
and lane predessor. Finally, all information are stored as merged linkage.
Also, the stored information are linked with the road ID and stored as road linkage.


Add junction and link road to junction
---------------------------------------
The intersection of lane net consists of intersection incoming elements. 
For every intersection incoming elment, all successors are obtained.  
Road id of successors with the CommonRoad id are transformed to successors 
with their OpenDrive id.
All incoming lanes should be on the same road in OpenDRIVE.
For every successor road, connection element are created and 
are linked with the lanelink accordingly to OpenDRIVE.


Add static obstacles and regulatroy elements
------------------------------
Static obstacles are added to the map. Obstacles can be in the shape of circles, rectangles, or polygons.
Traffic signs and lights are added to the map.


Convert to Opendrive file
-------------------------
After performing all these stages of preprocessing and conversion, the OpenDRIVE file is created.
Additionally, the converter is cleaned up which makes it possible to convert multiple files queued up.
