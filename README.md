# CommonRoad Scenario Designer

This toolbox provides map converters for [OpenStreetMap](https://www.openstreetmap.de/karte.html) (OSM), 
[Lanelet](https://www.mrt.kit.edu/software/libLanelet/libLanelet.html) / [Lanelet2](https://github.com/fzi-forschungszentrum-informatik/Lanelet2), 
[OpenDRIVE](https://www.asam.net/standards/detail/opendrive/), and [SUMO](https://sumo.dlr.de/docs/index.html) to the [CommonRoad](https://commonroad.in.tum.de/) 
(CR) format and for some formats vice versa.  
Additionally, a graphical user interface (GUI) is included, which allows one to efficiently create and manipulate 
CommonRoad maps and scenarios.

|  Tool                               |Path                                       |Functionality                                                                        |
| :---------------------------------: |:----------------------------------------: |:----------------------------------------------------------------------------------: |
|OpenDRIVE => CR            |`crdesigner/map_converter/opendrive`           |Conversion from OpenDRIVE to CommonRoad.                                             |
|Lanelet/Lanelet2 <=> CR |`crdesigner/map_converter/lanelet_lanelet2`    |Conversion from Lanelet/Lanelet2 to CommonRoad <br /> and from CommonRoad to lanelet |
|OSM => CR                  |`crdesigner/map_converter/osm2cr`              |Conversion from OSM to CommonRoad.                                                   |
|SUMO <=> CR             |`crdesigner/map_converter/sumo_map`            |Conversion from SUMO to CommonRoad and vice versa.                                   |
|CR Scenario Designer GUI             |`crdesigner/input_output/gui`|Multi-functional GUI for map conversion and scenario creation/editing.                     |

## Prerequisites and Installation
The usage of the Anaconda Python distribution is recommended. We have tested the toolbox with Python 3.7, 3.8, and 3.9.
You need the following modules:
- commonroad_io >= 2021.4
- matplotlib >= 3.1.0
- numpy >= 1.16.4
- ordered-set >= 4.0.2
- lxml >= 4.3.4
- pyproj >= 2.2.0
- scipy >= 1.3.0
- mercantile >= 1.1.3
- utm >= 0.5.0
- cartopy >= 0.17.0
- PyQt5 >= 5.12.2
- shapely>=1.7.0
- sumocr>=2021.5
- ordered-set>=4.0.2
- enum34>=1.1.10
- iso3166>=1.0.1
- networkx>=2.5

Cartopy can be easily installed via
```bash
conda install -c conda-forge cartopy
```
from you Anaconda environment. For the other packages, we recommend to use the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```

If you want to use the SUMO conversion or to generate traffic using SUMO, please install 
[SUMO](https://sumo.dlr.de/docs/index.html):
```bash
sudo apt-get install sumo sumo-tools sumo-doc
echo "export SUMO_HOME=/usr/share/sumo" >> ~/.bashrc
echo 'export PYTHONPATH="$SUMO_HOME/tools:$PYTHONPATH"' >> ~/.bashrc
```
If you use zsh, replace `.bashrc` with `.zshrc`.

To install the _CommonRoad Scenario Designer_, please execute one of the following two commands:
```bash
pip install -e .
```
or
```bash
python setup.py install
```
We will soon publish the toolbox on PyPI.

## Usage
We provide different types of usage for the _CommonRoad Scenario Designer_. Subsequently, we present for each component 
the different usage methods.

### GUI

![GUI_Screenshot](docs/source/details/images/gui_screenshot.png)

Within the GUI, you can also execute the different converters.
The GUI can either be activated via a Python API, command line, or executing a Python script.

#### Python Script

First you need to activate your python environment with the installed dependencies (we assume the environment 
is called _commonroad_).  
Afterward, you can start the _CommonRoad Scenario Designer_ and the GUI will open:

```bash
$ conda activate commonroad
# Run CR Scenario designer
$ python crdesigner/input_output/gui/commonroad_scenario_designer_gui.py
```

#### Command Line
The GUI can be started from command line via the following two options:
```bash
$ crdesigner
$ crdesigner gui
```
Note that you have to activate first the Python environment in which the CommonRoad Scenario Designer is installed.

### Map Converters
You can execute the different converters either via command line, calling them within your Python program via an API, 
or the GUI.

#### API
The main APIs to execute the pure conversions are located under `crdesigner/input_output/api`. 
For many conversions we provide further APIs, e.g., for downloading a map from OSM.

#### Command Line
Note that you have to activate first the Python environment in which the CommonRoad Scenario Designer was installed.  
Converting a file from OpenDRIVE to CommonRoad with the command line:
```bash
crdesigner [mode] -i [input_file] -o [output_file] -c -f -t [tags] --proj [proj-string] --adjacencies --left-driving --author --affiliation
```
For a description of the command line arguments please execute 
```bash
crdesigner -h
```

#### GUI
The GUI provides a toolbox with which contains functionality to load maps given in formats other the CommonRoad format 
and to convert CommonRoad maps to other formats or the other formats to the CommonRoad format.

#### Important information

When converting OSM maps, missing information such as the course of individual lanes is estimated during the process.
These estimations are imperfect (the OSM maps as well) and often it is advisable to edit the 
scenarios by hand via the GUI.

#### Tutorials
We also provide tutorials demonstrating how the different map converter APIs can be used. 
The tutorials include a jupyter notebook and exemplary Python scripts for each conversion.

## Documentation
To generate the documentation from source, first install the necessary dependencies with pip:

```bash
pip install -r docs/doc_requirements.txt
```

Afterward run:

```bash
cd docs && ./docs_build_script.sh
```

The documentation can be accessed by opening `doc/_build/html/index.html`.
The titles of module pages have to be set manually!
The full documentation of the API and introducing examples can also be found [here](https://commonroad-scenario-designer.readthedocs.io/en/latest/).

## Changelog
Compared to version 0.1, the following features have been added or changed:

- Planning problem visualization in GUI
- Extension of readme and documentation

A detailed overview about the changes in each version is provided in the [Changelog](https://gitlab.lrz.de/tum-cps/commonroad-scenario-designer/-/blob/main/CHANGELOG.md).

## Bug and feature reporting
This release (v0.3) is still a BETA version.  
In case you detect a bug or you want to suggest a new feature, please report it in our [forum](https://commonroad.in.tum.de/forum/c/scenario-designer/18).   
If you want to contribute to the toolbox, you can also post it in the [forum](https://commonroad.in.tum.de/forum/c/scenario-designer/18) or contact [Sebastian Maierhofer](sebastian.maierhofer@tum.de).

## Authors

Responsible: Sebastian Maierhofer (maintainer), Moritz Klischat  
Contribution (in alphabetic order by last name): Maximilian Fruehauf, Marcus Gabler, Fabian Hoeltke, Aaron Kaefer, 
Benjamin Orthen, Maximilian Rieger, Stefan Urban

## Citation
**If you use our code for research, please consider citing our paper:**
```
@inproceedings{ ,
	author = {Sebastian Maierhofer, Moritz Klischat, and Matthias Althoff},
	title = {CommonRoad Scenario Designer: An Open-Source Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles},
	booktitle = {Proc. of the IEEE Int. Conf. on Intelligent Transportation Systems },
	year = {2021},
	abstract = {Maps are essential for testing autonomous driving functions. Several map and scenario formats are 
                    available. However, they are usually not compatible with each other, limiting their usability.  
                    In this paper, we address this problem using our open-source toolbox that provides map converters  
                    from different formats to the well-known CommonRoad format. Our toolbox provides converters for 
                    OpenStreetMap, Lanelet/Lanelet2, OpenDRIVE, and SUMO. Additionally, a graphical user interface is 
                    included, which allows one to efficiently create and manipulate CommonRoad maps and scenarios. 
                    We demonstrate the functionality of the toolbox by creating CommonRoad maps and scenarios based on 
                    other map formats and manually-created map data.},
}
```
