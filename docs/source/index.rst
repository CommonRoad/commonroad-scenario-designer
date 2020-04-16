.. opendrive2lanelet documentation master file, created by
   sphinx-quickstart on Fri Dec  7 23:04:03 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to opendrive2lanelet's documentation!
=============================================

**opendrive2lanelet** is a tool which allows you to convert a road network description from the
`OpenDRIVE format <http://www.opendrive.org/project.html>`_ to the `CommonRoad format <https://gitlab.lrz.de/tum-cps/commonroad-scenarios/blob/master/documentation/XML_commonRoad_2020a.pdf>`_ (Version 2020a).
Hereby, the roads of the OpenDRIVE format are converted to `Lanelets <https://www.mrt.kit.edu/software/libLanelet/libLanelet.html>`_, hence the name of the package.
Additionally, we provide a converter from CommonRoad lanelets to OSM lanelets and vice versa.
We currently do not support the conversion of traffic signs and traffic lights.

This tool is part of the `CommonRoad <https://commonroad.in.tum.de/>`_ project. Its theoretical background is detailed in the following paper (https://mediatum.ub.tum.de/doc/1449005/1449005.pdf): M. Althoff, S. Urban, and M. Koschi, "Automatic Conversion of Road Networks from OpenDRIVE to Lanelets," in Proc. of the IEEE International Conference on Service Operations and Logistics, and Informatics, 2018.

Since the release of the paper, various updates have been implemented in the code to enhance the opendrive2lanelet converter.


.. toctree::
   :maxdepth: 2
   :caption: Contents
   :glob:

   OpenDRIVE Tutorial <tutorial>
   Implementation explained <implementation>
   API <api/opendrive2lanelet>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
