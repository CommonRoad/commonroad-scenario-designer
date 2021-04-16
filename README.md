# CommonRoad Scenario Designer

This toolbox provides map converters for [OpenStreetMap](https://www.openstreetmap.de/karte.html) (OSM), 
[Lanelet](https://www.mrt.kit.edu/software/libLanelet/libLanelet.html) / [Lanelet2](https://github.com/fzi-forschungszentrum-informatik/Lanelet2), 
[OpenDRIVE](https://www.asam.net/standards/detail/opendrive/), and [SUMO](https://sumo.dlr.de/docs/index.html) to the [CommonRoad](https://commonroad.in.tum.de/) 
(CR) format and for some formats vice versa.  
Additionally, a graphical user interface (GUI) is included, which allows one to efficiently create and manipulate 
CommonRoad maps and scenarios.

|  Tool                               |Path                                       |Functionality                                                                        |
| :---------------------------------: |:----------------------------------------: |:----------------------------------------------------------------------------------: |
|OpenDRIVE &rightarrow; CR            |`crdesigner/converter/opendrive`           |Conversion from OpenDRIVE to CommonRoad.                                             |
|Lanelet/Lanelet2 &leftrightarrow; CR |`crdesigner/converter/lanelet_lanelet2`    |Conversion from Lanelet/Lanelet2 to CommonRoad <br /> and from CommonRoad to lanelet |
|OSM &rightarrow; CR                  |`crdesigner/converter/osm2cr`              |Conversion from OSM to CommonRoad.                                                   |
|SUMO &leftrightarrow; CR             |`crdesigner/converter/sumo_map`            |Conversion from SUMO to CommonRoad and vice versa.                                   |
|CR Scenario Designer GUI             |`crdesigner/io/gui                        `|Multi-functional GUI for map conversion and scenario generation.                     |

## Prerequisites and Installation
For the execution of the _CommonRoad Scenario Designer_ you need at least Python 3.7 and the following modules:
- commonroad_io >= 2021.1
- matplotlib >= 3.1.0
- numpy >= 1.16.4
- ordered-set >= 4.0.2
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

![GUI_Screenshot](./docs/source/images/gui/gui_screenshot.png)

Within the GUI, you can also execute the different converters.
The GUI can either be activated via a Python API, command line, or executing a Python script.

#### Python Script

First you need to activate your python environment with the installed dependencies (we assume the environment 
is called _commonroad_).  
Afterward, you can start the _CommonRoad Scenario Designer_ and the GUI will open:

```bash
$ conda activate commonroad
# Run CR Scenario designer
$ python crdesigner/io/scenario_designer/main_cr_designer.py
```

#### API

#### Command Line
The GUI can be started from command line via the following two options.
```bash
$ crdesigner
$ crdesigner gui
```

### Map Converters
You can execute the different converters either via command line, calling them within your Python program via an API, 
or the GUI.

#### API
The main APIs to execute the pure conversions are located under `crdesigner/io/api`. 
For many conversions we provide further APIs, e.g., for downloading a map from OSM.

#### Command Line

Converting a file from OpenDRIVE to CommonRoad with the command line:

```bash
crdesigner [mode] -i [input_file] -o [output_file] ~~~~
```

Converting a file from the Lanelet/Lanelet2 format to CommonRoad lanelets with the command line:
```bash
lanelet2cr-convert inputfile.osm --reverse -o outputfile.xml --adjencies --proj "+proj=etmerc +lat_0=38 +lon_0=125 +ellps=bessel"
```

For the conversion of CommonRoad maps to the original lanelet format change the input and output file accordingly:
```bash
lanelet2cr-convert inputfile.xml -o outputfile.osm
```

Missing information such as the course of individual lanes is estimated during the process.
These estimations are imperfect (the OSM maps as well) and often it is advisable to edit the 
scenarios by hand via the GUI.
Converting a file from the OSM format to CommonRoad  with the command line:
```bash
osm2cr-convert inputfile.osm outputfile.xml"
```

#### GUI
The GUI provides a toolbox with which contains functionality to load maps given in formats other the CommonRoad format 
and to convert CommonRoad maps to other formats or the other formats to the CommonRoad format.

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

In case you detect a bug or you want to suggest a new feature, please create an issue in the repository 
(if you are TUM member) or report them in our forum (https://commonroad.in.tum.de/forum/c/map-tool/11). 

## Authors

Responsible: Sebastian Maierhofer (maintainer), Moritz Klischat  
Contribution (in alphabetic order by last name): Maximilian Fruehauf, Marcus Gabler, Fabian Hoeltke, Aaron Kaefer, 
Benjamin Orthen, Maximilian Rieger, Stefan Urban
