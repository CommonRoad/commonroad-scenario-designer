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

.. _installation:

Installation
############

Recommended Installation
************************

Prerequisites
*************
Install library commonroad-io: https://gitlab.lrz.de/cps/commonroad-io 

Install library Sumo-Interface: https://gitlab.lrz.de/cps/sumo-interface/-/tree/develop

Make sure to checkout the branch develop.

Manual Installation
*******************
When manually installing this tool, you need to install it's dependencies via you package manager. 
Currently we provide validated installation steps **only for Ubuntu >= 18.04**.

A fully working setup requires installation of all the following dependencies.

Partial Installation
====================
When you just want to try the map conversion, but **not** simulate traffic on the resulting scenarios,
it suffices to just install the following requirements:

You need to firstly install ``cartopy`` either using conda:

.. code-block:: bash

  conda install -c conda-forge cartopy

**or** install the required libs manually (tested only on ubuntu 18:04)

.. code-block:: bash

  apt-get install -y libproj-dev proj-data proj-bin libgeos++-dev gcc g++  # Cartopy dependencies
  apt-get install -y libgl1-mesa-glx # PyQt dependencies

Then install the python dependencies as usual:

.. code-block:: bash

  git clone https://gitlab.lrz.de/cps/commonroad-map-tool.git
  cd commonroad-map-tool
  # install the requirements
  pip install -r requirements.txt

However this also hides all SUMO related features from the GUI. For a full installation see the following section.

Full installation
=================
SUMO is required for simulating vehicle on a CommonRoad Scenario. Firstly it's dependencies need to be installed:


Activate your python environment (Version >= 3.6):

.. code-block:: bash

  conda activate commonroad

Install our patched SUMO Version from `GitHub <https://github.com/octavdragoi/sumo>`_.

.. code-block:: bash

  # install system requirements (ubuntu)
  sudo apt-get install ffmpeg
  # Install SUMO
  git clone https://github.com/octavdragoi/sumo
  cd sumo
  git checkout smooth-lane-change
  sudo apt-get install -y cmake python g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev swig
  export SUMO_HOME="$(pwd)"
  echo "export SUMO_HOME=$(pwd)" >> ~/.bashrc
  cd build
  cmake ..
  make -j8 # this will take some time
  cd $HOME

**OR** if you don't want the smooth lane change install the stable version of `SUMO <https://sumo.dlr.de/docs/Installing.html>`_:

.. code-block:: bash

  sudo add-apt-repository ppa:sumo/stable
  sudo apt-get update
  sudo apt-get install -y sumo sumo-tools sumo-doc
  export SUMO_HOME="/usr/share/sumo"
  # add $SUMO_HOME to .bashrc (change if you're not using bash)
  echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
  cd $HOME

Install `cartopy <https://scitools.org.uk/cartopy/docs/latest/installing.html>`_:

.. code-block:: bash

  conda install -c conda-forge cartopy

Install the python requirements at the root of the project:

.. code-block:: bash

  git clone https://gitlab.lrz.de/cps/commonroad-map-tool.git
  cd commonroad-map-tool
  # install the requirements
  pip install -r requirements.txt
