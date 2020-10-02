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
  pip install -r test_requirements.txt
  # run tests in current environment
  tox --current-env -e $PY_VERSION -- test/

Where you will need to replace ``$PY_VERSION`` with your current python version (e.g ``py36``, ``py37`` or ``py38``).
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

  # this will take some time (45 min)
  docker build -t commonroad ci/Dockerfile 
  docker run -it commonroad
  # activate python 3.6
  (commonroad-py38) cruser@70474a0ef635: conda activate commonroad-py36
  # activate python 3.7
  (commonroad-py38) cruser@70474a0ef635: conda activate commonroad-py37
  # activate python 3.8
  (commonroad-py38) cruser@70474a0ef635: conda activate commonroad-py38



However each of the python environments only has the bare minimum dependencies installed.
From then you can install clone / mount the commonroad-map-tool repo and install the missing dependencies with:

.. code-block:: bash

  (commonroad-py38) cruser@70474a0ef635:~/commonroad-map-tool$ pip install -r requirements.txt


Prebuild Images
---------------

We also provide a prebuild version of the aforementioned docker image `here <https://hub.docker.com/repository/docker/rasaford/commonroad-map-tool>`_.
You can run it with:

.. code-block:: bash

    docker run -it rasaford/commonroad-map-tool:VERSION

Replacing ``VERSION`` with the latest version of the docker image.