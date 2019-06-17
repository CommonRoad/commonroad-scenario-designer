osm2cr Documentation
====================

How to Install the Tool
-----------------------

To run this Tool, please make sure, you have installed all dependencies:

 * cartopy		
 * matplotlib
 * mercantile
 * numpy
 * pillow
 * scipy
 * utm
 * commonroad-io

If you want to use aerial images in the GUI you also need to get a
`Bing Maps key <https://docs.microsoft.com/en-us/bingmaps/getting-started/bing-maps-dev-center-help/getting-a-bing-maps-key>`_
and insert it in **config.py**.

How to Start the Tool
---------------------

To start a conversion with osm2cr run **main.py** with either of the following arguments:

* **o** **filename** to open a osm file and convert it
* **d** to download a area specified in **config.py**
* **g** to open the gui

Valid calls would for example be::

    $ python main.py o map.osm

Or::

    $ pyton main.py d

Or::

    $ python main.py g

A further description is given in **Usage Example**.

This Documentation
------------------

You can find a possiblilty to use the methods of this package without **main.py** in the **Usage Example**.
A description of the capabilities of the automated conversion is given in **When does the automated conversion work?**.
**How to use the GUI** is a guide for the GUI.
The documentation of the converter module providing the main functionality can be found in **The Converter Module**.
A description of all parameters is provided in **Parameters**.
The full documentation of the package is visible in **converter package**.

.. toctree::
   :maxdepth: 1
   
   usage/example
   automation
   gui_guide
   converter
   config
   converter-package
   
Further reading
---------------

If you need further information about the conversion process, you can read `my Bachelors Thesis <../../thesis.pdf>`_ on this project.
Please note, that it is not up to date, but wide aspects of the conversion stayed the same.