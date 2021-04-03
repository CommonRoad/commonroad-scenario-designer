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


Development
###########

Unit Testing
************

Unit tests for testing expected behaviour are found in ``/tests``. To execute them locally run the following commands:


.. code-block:: bash

  # install test dependencies
  pip install -r requirements.txt -r test_requirements.txt
  # run tests in current environment
  tox --current-env -e <PY_VERSION> -- test/

Where you will need to replace ``<PY_VERSION>`` with your current python version (e.g ``py37``, ``py38``, ``py39``).
This will install all the required dependencies for testing, assuming you already have installed the tool as described in :ref:`installation`
and run the full test suite on you current code base.

Continuous Integration
**********************

Continuous Integration is handled for the project using `GitLab runners <https://docs.gitlab.com/runner/>`_.
All configuration for which is in ``.gitlab-ci.yml`` found in the project root. Here all stages of the build
and test process can be changed according to the `GitLab CI Syntax <https://docs.gitlab.com/ee/ci/yaml/README.html>`_.

Docker Image
=============

As a base image for the build process we use the docker image found in ``ci/Dockerfile`` which contains a full
installation of the project. It includes multiple conda environments with python versions installed ranging from python 3.6 to 3.8.
You can run the docker container as follows:

.. code-block:: bash

  # this will take some time (20 min)
  docker build -t commonroad ci/Dockerfile
  ci/run_tests.sh

**Caution** This will expose you ssh private key to the docker container to install updated dependencies.
Use with caution.

Prebuild Images
---------------

We also provide a prebuild version of the aforementioned docker image `here <https://gitlab.lrz.de/cps/commonroad-map-tool/container_registry/757>`_.
You can run it with:

.. code-block:: bash

    docker run -it gitlab.lrz.de:5005/cps/commonroad-map-tool/ci:VERSION

Replacing ``VERSION`` with the latest version of the docker image.


CR to SUMO Converter
********************
The main module of the converter is in ``crdesiger/sumo_map/cr2sumo/converter.py``. Here, a
CommonRoad Scenario is converted to it's representation as a SUMO Net. This SUMO Net is then
used as the specification for simulating vehicles with SUMO.

In detail, conversion follows roughly the following steps, which are successively called in
``_convert_map()``:

1. Find lanes from lanelets
2. Initialize SUMO Nodes
3. Create Lanes and Edges from Lanelets
4. Initialize Connections between Lanes
5. Merge overlapping lanelets into a single junction
6. Remove merged edges
7. Create Lane based connections
8. Create pedestrian crossings
9. Encode Traffic Signs from CR file
10. Encode Traffic Lights from CR file


Add a new GUI element
*********************

Button
======
- QPushButton (https://doc.qt.io/qt-5/qpushbutton.html)
- Example: add button to toolbox
  1. define layout
  2. create button:
  .. code-block:: bash

    button_forwards = QPushButton()

    button_forwards.setText("forwards")

    button_forwards.setIcon(QIcon("PATH"))

    layoutlanelets.addWidget(button_forwards, 1, 0)

    button_forwards.clicked.connect("METHOD")

Replacing ``PATH`` with the path to the icon and ``METHOD`` with an corresponding method




