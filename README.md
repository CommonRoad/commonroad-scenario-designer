# CommonRoad Scenario Designer

This toolbox provides map converters for OpenStreetMap (OSM), Lanelet/Lanelet2, OpenDRIVE, and SUMO to the CommonRoad 
(CR) format and for some formats vice versa.  
Additionally, a graphical user interface (GUI) is included, which allows one to efficiently create and manipulate 
CommonRoad maps and scenarios.

|  Tool                           |Path                             |Functionality                                                    |
| :-----------------------------: |:------------------------------: |:--------------------------------------------------------------: |
|OpenDRIVE &rightarrow; CR        |`crdesigner/opendrive`           |Conversion from OpenDRIVE to CommonRoad.                         |
|Lanelet/Lanelet2 &rightarrow; CR |`crdesigner/lanelet_lanelet2`    |Conversion from Lanelet/Lanelet2 to CommonRoad.                  |
|CR &rightarrow; Lanelet          |`crdesigner/lanelet_lanelet2`    |Conversion from CommonRoad to the original lanelet format.       |
|OSM &rightarrow; CR              |`crdesigner/osm2cr`              |Conversion from OSM to CommonRoad.                               |
|SUMO &rightarrow; CR             |`crdesigner/sumo_map`            |Conversion from SUMO to CommonRoad.                              |
|CR &rightarrow; SUMO             |`crdesigner/sumo_map`            |Conversion from CommonRoad to SUMO.                              |
|CR Scenario Designer GUI         |`crdesigner/io/scenario_designer`|Multi-functional GUI for map conversion and scenario generation. |

## Prerequisites and Installation
For the execution of the _CommonRoad Scenario Designer_ you need at least Python 3.7 and the following modules:
- commonroad_io >= 2021.1
- matplotlib >= 3.1.0
- numpy >= 1.16.4
- ordered-set > =4.0.2
- lxml >= 4.3.4
- pyproj >= 2.2.0
- scipy >= 1.3.0
- Pillow >= 7.1.1
- mercantile >= 1.1.3
- utm >= 0.5.0
- cartopy >= 0.17.0
- PyQt5 >= 5.12.2

If you want to use the SUMO conversion or to generate traffic using SUMO, please install 
[SUMO](https://sumo.dlr.de/docs/index.html) 
and our [SUMO-Interface](https://gitlab.lrz.de/tum-cps/commonroad-sumo-interface).

The usage of the Anaconda Python distribution is recommended.  
To install the _CommonRoad Scenario Designer_, please execute one of the following two commands:
```bash
python setup.py install
pip install -e .
```

## Usage
We provide different types of usage for the _CommonRoad Scenario Designer_. Subsequently, we present for each component 
the different usage methods.

### GUI

![GUI_Screenshot](./docs/source/images/gui/GUI_screenshot.png)

The GUI can either activated via a Python API, command line, or executing a Python script.
First you need to activate your python environment with the installed dependencies.
Then you can start _CommonRoad Scenario Designer_:

```bash
$ conda activate commonroad
# Run CR Scenario designer
$ python crdesigner/io/scenario_designer/main_cr_designer.py
```

Within the GUI, you can also execute the different converters.

### Map Converters
You can execute the different converters either via command line, calling them within your Python program via an API, 
or the GUI.

Converting a file from OpenDRIVE to CommonRoad with the command line:

```bash
opendrive2lanelet-convert input_file.xodr -o output_file.xml
```

Opening OpenDRIVE to CommonRoad converter GUI:

```bash
opendrive2lanelet-gui
```

Visualizing the results of the conversion from OpenDrive to CommonRoad:

```bash
opendrive2lanelet-visualize input-file.xml
```

Converting a file from the Lanelet/Lanelet2 format to CommonRoad lanelets with the command line (for description of input parameters see documentation):

```bash
osm-convert inputfile.osm --reverse -o outputfile.xml --adjencies --proj "+proj=etmerc +lat_0=38 +lon_0=125 +ellps=bessel"
```

For the conversion of CommonRoad lanelets to OSM lanelets change the input and output file accordingly.

For the conversion of a [OpenStreetMap](https://www.openstreetmap.de/karte.html) to CommonRoad you can
open the GUI and start from there the conversion.
Missing information such as the course of individual lanes is estimated during the process.
These estimations are imperfect (the OSM maps as well) and often it is advisable to edit the scenarios by hand via the GUI.
Converting a file from the [OpenStreetMap](https://www.openstreetmap.de/karte.html) format to CommonRoad with the command line:
```bash
osm2cr inputfile.osm outputfile.xml"
```

## Documentation

To generate the documentation from source, first install the necessary dependencies with pip:

```bash
pip install -r docs_requirements.txt
```

Afterward run:

```bash
cd docs && make html
```

The documentation can be accessed by opening `docs/_build/html/index.html`.

## Bug and feature reporting

In case you detect a bug or you want to suggest a new feature, please create an issue in the repository (if you are TUM member) or report them in our forum (https://commonroad.in.tum.de/forum/c/map-tool/11). 

## Authors

Responsible: Sebastian Maierhofer (maintainer), Moritz Klischat  
Contribution (in alphabetic order of last name): Maximilian Fruehauf, Marcus Gabler, Fabian Hoeltke, Aaron Kaefer, 
Benjamin Orthen, Maximilian Rieger, Stefan Urban
