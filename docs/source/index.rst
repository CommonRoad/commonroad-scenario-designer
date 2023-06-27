****************************
CommonRoad Scenario Designer
****************************

The CommonRoad Scenario Designer provides a toolbox for creating and manipulating CommonRoad maps
and scenarios as well as converting maps between different map formats.
The CommonRoad Scenario Designer can convert maps from the Lanelet/Lanelet2, OpenDRIVE, OpenStreetMap (OSM), and SUMO
formats to the CommonRoad format.
Additionally, we provide conversions from the CommonRoad map format to the SUMO and Lanelet format.
The toolbox includes a graphical user interface (GUI) for creating, editing, and visualizing CommonRoad maps
and scenarios, a command line interface, and different Python APIs.

.. note::
    This release (v0.7.1) is still a BETA version.
    In case you encounter errors or want to provide us feedback, please post them in our
    `forum <https://commonroad.in.tum.de/forum/c/scenario-designer/18>`_.

We have tested the toolbox with Python 3.8, 3.9, 3.10, and 3.11.
The toolbox should work under Linux, macOS, and Windows.

Prerequisites and Installation
==============================
We have tested the toolbox with Python 3.8, 3.9, 3.10, and 3.11.
The toolbox should work under Linux, macOS, and Windows.
Below we present two ways of installing the CommonRoad Scenario Designer:

- Only using the CommonRoad Scenario Designer, e.g.,the GUI or integrating the scenario designer APIs into your code
- Developing code for the CommonRoad Scenario Designer

If you want to use the SUMO conversion or to generate traffic using SUMO, please install
`SUMO <https://sumo.dlr.de/docs/index.html>`_::
    sudo apt-get update
    sudo apt-get install sumo sumo-tools sumo-doc
    echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
    echo 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' >> ~/.bashrc

If you use zsh, replace `.bashrc` with `.zshrc`.

Using the CommonRoad Scenario Designer
**************************************
The recommended way of installation if you only want to use the scenario designer (i.e., you do not want to work with the code directly) is to use the PyPI package::

    pip install commonroad-scenario-designer


Development
**********
First, clone the repository.
The usage of `Poetry <https://python-poetry.org/>`_ is recommended.
Poetry can be installed using::

    curl -sSL https://install.python-poetry.org | python3 -

Create a new Python environment::

    poetry shell
    poetry install --with tests,docs,tutorials

We recommend to use PyCharm (Professional) as IDE.


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

    details/opendrive_to_commonroad
    details/commonroad_to_opendrive
    details/osm_to_commonroad
    details/lanelet2
    details/sumo
    details/commonroad_scenario_designer

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contact information
===================

:Website: `http://commonroad.in.tum.de <https://commonroad.in.tum.de/>`_
:Email: `commonroad@lists.lrz.de <commonroad@lists.lrz.de>`_
