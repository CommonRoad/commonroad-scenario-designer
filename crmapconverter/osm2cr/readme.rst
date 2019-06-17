OSM2CR
======

This repository allows to convert OpenStreetMap maps to the Commonroad format.
Missing information such as the course of individual lanes is estimated during the process.
These estimations are imperfect (the OSM maps as well) and often it is advisable to edit the scenarios by hand.
This tool also provides a simple GUI, to edit scenarios by hand.

Installation
------------
* install requirements (see requirements.txt)
* if you want to use aerial images in the GUI, get a
  `Bing Maps key <https://docs.microsoft.com/en-us/bingmaps/getting-started/bing-maps-dev-center-help/getting-a-bing-maps-key>`_
  and set it in config.py
* execute main.py with ``python main.py g``

Documentation
-------------
A detailed Documentation and usage description can be found `here <documentation/build/html/index.html>`_.
If you cannot render html files on gitlab, clone the repository and open *documentation/readme.html* directly.