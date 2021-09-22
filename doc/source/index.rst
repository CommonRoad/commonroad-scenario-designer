CommonRoad Scenario Designer
======================================

The CommonRoad Scenario Designer provides a toolbox for creating and manipulating CommonRoad maps
and scenarios as well as converting maps between different map formats.
The CommonRoad Scenario Designer can convert from the Lanelet/Lanelet2, OpenDRIVE, OpenStreetMap (OSM), and SUMO
formats to the CommonRoad format.
Additionally, we provide conversions from the CommonRoad map format to the SUMO and Lanelet format.
The toolbox includes a graphical user interface (GUI) for creating, editing, and visualizing CommonRoad maps
and scenarios, a command line interface, and different Python APIs.

.. note::
    This release (v0.2) is still a BETA version.
    In case you encounter errors or want to provide us feedback, please post them in our
    `forum <https://commonroad.in.tum.de/forum/c/scenario-designer/18>`_.

The software is written in Python 3.7/3.8/3.9 and tested on Linux. he usage of the Anaconda_ Python distribution
is strongly recommended.

.. _Anaconda: http://www.anaconda.com/download/#download

Documentation
=============

The full documentation of the API and introducing examples can be found under
`commonroad.in.tum.de <https://commonroad-scenario-designer.readthedocs.io/en/latest/>`__.

For getting started, we recommend our `tutorials <https://commonroad.in.tum.de/commonroad-io>`__.

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
* pytest>=5.3.2
* coverage
* parameterized>=0.7.4


Installation
============

For installing the CommonRoad Scenario Designer, clone from our gitlab repository::

	git clone https://gitlab.lrz.de/tum-cps/commonroad-scenario-designer.git

From the root directory of the corresponding repository run::

	pip install -e .

Alternatively, run::

	python setup.py install


Getting Started
===============

A tutorial on the main functionalities of the project is :ref:`available here<getting_started>`.

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
