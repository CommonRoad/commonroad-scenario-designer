Tutorial for opendrive2lanelet
*******************************

Quick start
===========

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


Usage in own code
===================

Please refer to `README.md` where this is stated.

A good file to take inspiration from is :py:mod:`opendrive2lanelet.io.opendrive_convert` or :py:mod:`opendrive2lanelet.io.osm_convert`.
