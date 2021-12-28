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
to an XODR file detailing a OpenDRIVE scenario?

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

from crdesigner.map_conversion.opendrive.cr_to_opendrive.dataloader import DataLoader
from crdesigner.map_conversion.opendrive.cr_to_opendrive.converter import Converter

# load the xml file and preprocess it
data = DataLoader(input_file)

scenario, successors, ids = data.initialize()
converter = Converter(input_file, scenario, successors, ids)
converter.convert(output_file) 
