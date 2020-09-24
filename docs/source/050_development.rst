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

Continuous Integration
**********************

Continuous Integration is handled for the project using `GitLab runners <https://docs.gitlab.com/runner/>`_. 
All configuration for which is in ``.gitlab-ci.yml`` found in the project root. Here all stages of the build
and test process can be changed according to the `GitLab CI Syntax <https://docs.gitlab.com/ee/ci/yaml/README.html>`_.

Docker Images
=============

As a base image for the build process we use one docker image found in ``CI/Dockerfile`` which contains a full
installation of the project. Additionally you can specify the python version to use, when building 
the image like so:

.. code-block:: bash

    docker build --build-arg PYTHON_VERSION=3.7 -t commonroad-map-tool .

Using the above command, a build environment will be created with the Python version specified in ``PYTHON_VERSION``.
But beware building the environment might take quite some time. 
Therefore we also provide pre-built versions at:

- https://hub.docker.com/repository/docker/rasaford/commonroad-map-tool-py36
- https://hub.docker.com/repository/docker/rasaford/commonroad-map-tool-py37

You can run any of the versions above with:

.. code-block:: bash

    docker run -it rasaford/commonroad-map-tool-PY_VERSION:VERSION

Replacing ``PYVERSION`` with the desired python version, e.g. ``py37`` and replacing ``VERSION`` with the latest version of the docker image.