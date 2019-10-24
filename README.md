# CommonRoad Map Converter

This software provides multiple converters from other map formats to the CommonRoad map, which is based on lanelets.

| Tool | Functionality |
|:----:|:------------:|
| [opendrive2lanelet](##opendrive2lanelet) | Convert OpenDRIVE files to Lanelet maps |
| [osm-convert](##osm-convert) | Convert lanelet maps between the OSM and the CommonRoad format |
| [osm2cr](##osm2cr) | Convert general OSM maps to CommonRoad Lanelet maps |

## opendrive2lanelet

We provide the code for an OpenDRIVE ([www.opendrive.org](http://www.opendrive.org)) to lanelets ([www.mrt.kit.edu/software/liblanelet](https://www.mrt.kit.edu/software/libLanelet/libLanelet.html)) converter, which has been introduced in our [paper](https://mediatum.ub.tum.de/doc/1449005/1449005.pdf): M. Althoff, S. Urban, and M. Koschi, "Automatic Conversion of Road Networks from OpenDRIVE to Lanelets," in Proc. of the IEEE International Conference on Service Operations and Logistics, and Informatics, 2018.

[![Documentation Status](https://readthedocs.org/projects/opendrive2lanelet/badge/?version=latest)](https://opendrive2lanelet.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/opendrive2lanelet.svg)](https://badge.fury.io/py/opendrive2lanelet)
[![Supported python versions](https://img.shields.io/pypi/pyversions/opendrive2lanelet.svg)](https://pypi.org/project/opendrive2lanelet/)
[![License](https://img.shields.io/pypi/l/opendrive2lanelet.svg)](https://www.gnu.org/licenses/gpl-3.0.de.html)

### Installation

#### Installing from source

```bash
git clone https://gitlab.lrz.de/cps/opendrive2lanelet.git
cd opendrive2lanelet
python setup.py install
```

Public source (only released versions): https://gitlab.lrz.de/tum-cps/opendrive2lanelet.git



#### Using pip:

```bash
pip install opendrive2lanelet
```

Optionally, for using the gui packages:

```bash
pip install opendrive2lanelet[GUI]
```

### Example OpenDRIVE Files

Download example files from: http://opendrive.org/download.html

### Usage

#### Using our provided GUI

Start the GUI with ```opendrive2lanelet-gui```

![GUI screenshot](gui_screenshot.png "Screenshot of converter GUI")

#### Converting a file from OpenDRIVE with the command line

Execute ```opendrive2lanelet-convert input_file.xodr -o output_file.xml```

If you want to visualize the Commonroad file, use the ```opendrive2lanelet-visualize``` command.


### Documentation

The documentation is published on [Read the Docs](https://opendrive2lanelet.readthedocs.io/en/latest/).


To generate the documentation from source, first install the necessary dependencies with pip:
```bash
pip install -r docs_requirements.txt
```

Then you can run
```bash
cd docs && make html
```
for example.



### Known Problems

- When trying to use the gui.py under Wayland, the following error occurs:
  ```
  This application failed to start because it could not find or load the Qt platform plugin "wayland" in "".
  Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, xcb.
  Reinstalling the application may fix this problem.
  ```
  Set the platform to *xcb* using this command: ```export QT_QPA_PLATFORM="xcb"```



## osm-convert

This tool can be used to convert from CommonRoad lanelets to OSM lanelets and vice versa.

Use the command ```osm-convert --help``` to see what is possible.

## osm2cr

For the documentation of osm2cr, see the [README](./crmapconverter/osm2cr/readme.rst).

### Authors

Sebastian Maierhofer (current maintainer)  
Benjamin Orthen 
Stefan Urban
