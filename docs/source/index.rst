CommonRoad Scenario Designer
======================================

The CommonRoad Scenario Designer provides a toolbox for creating and manipulating CommonRoad maps
and scenarios as well as converting maps between different map formats.
The CommonRoad Scenario Designer can convert maps from the Lanelet/Lanelet2, OpenDRIVE, OpenStreetMap (OSM), and SUMO
formats to the CommonRoad format.
Additionally, we provide conversions from the CommonRoad map format to the SUMO and Lanelet format.
The toolbox includes a graphical user interface (GUI) for creating, editing, and visualizing CommonRoad maps
and scenarios, a command line interface, and different Python APIs.

.. note::
    This release (v0.2) is still a BETA version.
    In case you encounter errors or want to provide us feedback, please post them in our
    `forum <https://commonroad.in.tum.de/forum/c/scenario-designer/18>`_.

The software is written in Python 3.7/3.8/3.9 and tested on Linux. The usage of the Anaconda_ Python distribution
is strongly recommended.

.. _Anaconda: http://www.anaconda.com/download/#download

Requirements
============

The required dependencies for running the CommonRoad Scenario Designer are:

* numpy>=1.16.4
* lxml>=4.3.4
* commonroad-io>=2021.3
* pyproj>=2.2.0
* scipy>=1.3.0
* Pillow>=7.1.1
* mercantile>=1.1.3
* utm>=0.5.0
* cartopy>=0.17.0
* PyQt5>=5.12.2
* matplotlib>=3.1.0
* shapely>=1.7.0
* ipython>=7.19.0
* sumocr>=2021.5
* ordered-set>=4.0.2
* enum34>=1.1.10
* iso3166>=1.0.1
* future>=0.17.1
* networkx>=2.5

Cartopy can be easily installed with::

   conda install -c conda-forge cartopy

from your Anaconda environment. For the other packages, we recommend to use the provided `requirements.txt`::

    pip install -r requirements.txt


If you want to use the SUMO conversion or to generate traffic using SUMO, please install `SUMO <https://sumo.dlr.de/docs/index.html>`_::

    sudo apt-get install sumo sumo-tools sumo-doc
    echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
    echo 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' >> ~/.bashrc

If you use zsh, replace `.bashrc` with `.zshrc`.

Installation
============

To install the *CommonRoad Scenario Designer*, please execute one of the following two commands: ::

    pip install -e .
or::

    python setup.py install

We will soon publish the toolbox on PyPI.

Getting Started
===============

A tutorial on the Python APIs can be found in the form of jupyter notebooks in the tutorials folder.
We also provide exemplary Python scripts for each conversion within the same folder.

Subsequently, we briefly explain how to use the command line interface.
Note that you have to activate first the Python environment in which the CommonRoad Scenario Designer was installed.
Converting a file from OpenDRIVE to CommonRoad with the command line::

    crdesigner [mode] -i [input_file] -o [output_file] -c -f -t [tags] --proj [proj-string] --adjacencies --left-driving --author --affiliation

For a description of the command line arguments please execute::

    crdesigner -h

The GUI can be started from command line via the following two options::

    crdesigner

or::

    crdesigner gui



We provide more detailed information and examples under the following links, e.g., information about implementation details, API usage, or limitations:

.. toctree::
    :maxdepth: 2

    open_drive
    osm
    lanelet2
    sumo
    commonroad_scenario_designer

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contact information
===================

:Website: `http://commonroad.in.tum.de <https://commonroad.in.tum.de/>`_
:Email: `commonroad@lists.lrz.de <commonroad@lists.lrz.de>`_
