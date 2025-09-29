# CommonRoad Scenario Designer
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/commonroad-scenario-designer.svg)](https://pypi.python.org/pypi/commonroad-scenario-designer/)
[![PyPI version fury.io](https://badge.fury.io/py/commonroad-scenario-designer.svg)](https://pypi.python.org/pypi/commonroad-scenario-designer/)
[![PyPI download week](https://img.shields.io/pypi/dw/commonroad-scenario-designer.svg?label=PyPI%20downloads)](https://pypi.python.org/pypi/commonroad-scenario-designer/)
[![PyPI download month](https://img.shields.io/pypi/dm/commonroad-scenario-designer.svg?label=PyPI%20downloads)](https://pypi.python.org/pypi/commonroad-scenario-designer/)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
[![PyPI license](https://img.shields.io/pypi/l/commonroad-scenario-designer.svg)](https://pypi.python.org/pypi/commonroad-scenario-designer/)

This toolbox provides map converters for [OpenStreetMap](https://www.openstreetmap.de/karte.html) (OSM),
[Lanelet](https://www.mrt.kit.edu/software/libLanelet/libLanelet.html) / [Lanelet2](https://github.com/fzi-forschungszentrum-informatik/Lanelet2),
[OpenDRIVE](https://www.asam.net/standards/detail/opendrive/), and [SUMO](https://sumo.dlr.de/docs/index.html) to the [CommonRoad](https://commonroad.in.tum.de/)
(CR) format and for some formats vice versa.
Additionally, a graphical user interface (GUI) is included, which allows one to efficiently create and manipulate
CommonRoad maps and scenarios.

|              Tool              |                         Path                         |                                Functionality                                 |
|:------------------------------:|:----------------------------------------------------:|:----------------------------------------------------------------------------:|
|        OpenDRIVE <=> CR        |        `crdesigner/map_conversion/opendrive`         |           Conversion from OpenDRIVE to CommonRoad and vice versa.            |
|    Lanelet/Lanelet2 <=> CR     |         `crdesigner/map_conversion/lanelet2`         | Conversion from Lanelet2 to CommonRoad <br /> and from CommonRoad to Lanelet |
|           OSM => CR            |          `crdesigner/map_conversion/osm2cr`          |                      Conversion from OSM to CommonRoad.                      |
|          SUMO <=> CR           |         `crdesigner/map_conversion/sumo_map`         |              Conversion from SUMO to CommonRoad and vice versa.              |
| OpenDRIVE => Lanelet/Lanelet2  | `crdesigner/map_conversion/map_conversion_interface` |                    Conversion from OpenDRIVE to Lanelet2                     |
| Map Verification and Repairing |         `crdesigner/verification_repairing`          |                Verification and Repairing of CommonRoad maps.                |
|    CR Scenario Designer GUI    |                 `crdesigner/ui/gui`                  |    Multi-functional GUI for map conversion and scenario creation/editing.    |

## Prerequisites and Installation
We have tested the toolbox with Python 3.10, 3.11, 3.12, and 3.13.
The toolbox works under Linux.
Below we present two ways of installing the CommonRoad Scenario Designer:
- Only using the CommonRoad Scenario Designer, e.g.,the GUI or integrating the scenario designer APIs into your code
- Developing code for the CommonRoad Scenario Designer

### Using the CommonRoad Scenario Designer
The recommended way of installation if you only want to use the scenario designer (i.e., you do not want to work with the code directly) is to use the PyPI package:
```bash
pip install commonroad-scenario-designer
```

### Development
First, clone the repository.
The usage of [Poetry](https://python-poetry.org/) is recommended.
Poetry can be installed using:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Create a new Python environment:
```bash
poetry shell
poetry install --with tests,docs,tutorials
```
We recommend to use PyCharm (Professional) as IDE.

### Common Errors during installation

#### Ubuntu
- **Could not load the Qt platform plugin “xcb” in “” even though it was found:** Error seems to be a missing package - either libxkbcommon-x11 or libxcb-xinerama0 (both can be installed by ```sudo apt install [package_name]```). See for reference [here](https://discuss.pixls.us/t/solved-could-not-load-the-qt-platform-plugin-xcb-in-even-though-it-was-found/17677/9)


## Usage
We provide different types of usage for the _CommonRoad Scenario Designer_. Subsequently, we present for each component
the different usage methods.

### GUI

![GUI_Screenshot](docs/assets/gui_screenshot.png)

The recommended aspect ratio is 16:9 with a scaling of 100%.
Within the GUI, you can also execute the different converters.
The GUI can either be activated via a Python API, command line, or executing a Python script.

#### Python Script

First you need to activate your python environment with the installed dependencies.
Afterward, you can start the _CommonRoad Scenario Designer_ and the GUI will open:

```bash
$ python crdesigner/ui/gui/start_gui.py
```

#### Command Line
The GUI can be started from command line via the following two options:
```bash
$ crdesigner
$ crdesigner gui
```
Note that you have to activate first the Python environment in which the CommonRoad Scenario Designer is installed.
You can also execute a map conversion via the commandline interface, e.g.,
`crdesigner --input-file /input/path/l2file.osm  --output-file /output/path/crfile.xml lanelet2cr`.
The output of `crdesigner --help` looks as follows:
```bash
Usage: crdesigner [OPTIONS] COMMAND [ARGS]...

  Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles

Options:
  --input-file PATH               Path to OpenDRIVE map
  --output-file PATH              Path where CommonRoad map should be stored
  --force-overwrite / --no-force-overwrite
                                  Overwrite existing CommonRoad file
                                  [default: force-overwrite]
  --author TEXT                   Your name
  --affiliation TEXT              Your affiliation, e.g., university, research
                                  institute, company
  --tags TEXT                     Tags for the created map
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  crlanelet2
  crsumo
  gui
  lanelet2cr
  odrcr
  osmcr
  sumocr
  odrlanelet2`
```

### Map Converters
You can execute the different converters either via command line, calling them within your Python program via an API,
or the GUI.

#### API
The main APIs to execute the pure conversions are located under `crdesigner/map_conversion/map_conversion_interface.py`.
For many conversions we provide further APIs, e.g., for downloading a map from OSM.

#### GUI
The GUI provides a toolbox with which contains functionality to load maps given in formats other the CommonRoad format
and to convert CommonRoad maps to other formats or the other formats to the CommonRoad format.

#### Saving Video

Provides the functionality to save the animation of the scenario as a mp4 file.

For error: "MovieWriter ffmpeg unavailable; using Pillow instead." try to install ffmpeg. This should solve the problem.
```bash
sudo apt-install ffmpeg
```

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
mkdocs serve
```

The documentation can be accessed by opening `public/index.html`.
The titles of module pages have to be set manually!
The full documentation of the API and introducing examples can also be found [here](https://cps.pages.gitlab.lrz.de/commonroad/commonroad-scenario-designer/).

## Changelog
A detailed overview about the changes in each version is provided in the [Changelog](https://github.com/CommonRoad/commonroad-scenario-designer/blob/master/CHANGELOG.md).

## Bug and feature reporting
This release (v0.8.5) is still a BETA version.
In case you detect a bug or you want to suggest a new feature, please report it in our [forum](https://github.com/CommonRoad/commonroad-scenario-designer/discussions).
If you want to contribute to the toolbox, you can also post it in the [forum](https://github.com/CommonRoad/commonroad-scenario-designer/discussions).

## Authors
Responsible: Sebastian Maierhofer, Sebastian Mair
Contribution (in alphabetic order by last name): Daniel Asch, Hamza Begic, Mohamed Bouhali, Florian Braunmiller,
Tim Dang, Setenay Eryasar, Behtarin Ferdousi, Maximilian Fruehauf, Marcus Gabler, Fabian Hoeltke,
Julian Hohenadel, Tom Irion, Aaron Kaefer, Anton Kluge,
David Le, Gustaf Lindgren, Sarra Ben Mohamed, Benjamin Orthen, Luisa Ortner, Louis Pröbstle, Benedikt Reinhard,
Maximilian Rieger, Nikolaos Sotirakis, Til Stotz, Stefan Urban, Max Winklhofer

## Credits
We gratefully acknowledge partial financial support by
- DFG (German Research Foundation) Priority Program SPP 1835 Cooperative Interacting Automobiles
- BMW Group within the Car@TUM project
- Central Innovation Programme of the German Federal Government under grant no. ZF4086007BZ8

## Citation
**If you use our code for research, please consider to cite our papers:**
```
@inproceedings{Maierhofer2023,
	author = {Maierhofer, Sebastian and  Ballnath, Yannick and  Althoff, Matthias},
	title = {Map Verification and Repairing Using Formalized Map Specifications},
	booktitle = {2023 IEEE International Conference on Intelligent Transportation Systems (ITSC)},
	year = {2023},
	pages = {},
	abstract = {Autonomous vehicles benefit from correct maps to participate in traffic safely, but often maps are not verified before their usage.
                    We address this problem by providing an approach to verify and repair maps automatically based on a formalization of map specifications in higher-order logic.
                    Unlike previous work, we provide a collection of map specifications.
                    We can verify and repair all possible map parts, from geometric to semantic elements, e.g., adjacency relationships, lane types, road boundaries, traffic signs, and intersections.
                    Due to the modular design of our approach, one can integrate additional logics.
                    We compare ontologies, answer set programming, and satisfiability modulo theories with our higher-order logic verification algorithm.
                    Our evaluation shows that our approach can efficiently verify and repair maps from several data sources and of different map sizes.
                    We provide our tool as part of the CommonRoad Scenario Designer toolbox available at commonroad.in.tum.de.},
}
```
```
@inproceedings{Maierhofer2021,
	author = {Sebastian Maierhofer, Moritz Klischat, and Matthias Althoff},
	title = {CommonRoad Scenario Designer: An Open-Source Toolbox for Map Conversion and Scenario Creation for Autonomous Vehicles},
	booktitle = {Proc. of the IEEE Int. Conf. on Intelligent Transportation Systems },
	year = {2021},
	pages = {3176-3182},
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
**If you use the OpenDRIVE to CommonRoad conversion for your paper, please consider to additionally cite the corresponding paper:**
```
@inproceedings{Althoff2018b,
	author = {Matthias Althoff and Stefan Urban and Markus Koschi},
	title = {Automatic Conversion of Road Networks from OpenDRIVE to Lanelets},
	booktitle = {Proc. of the IEEE International Conference on Service Operations and Logistics, and Informatics},
	year = {2018},
	pages = {157--162},
	abstract = {Detailed road maps are an important building block for autonomous driving. They accelerate creating a
	            semantic environment model within the vehicle and serve as a backup solution when sensors are occluded
	            or otherwise impaired. Due to the required detail of maps for autonomous driving and virtual test
	            drives, creating such maps is quite labor-intensive. While some detailed maps for fairly large regions
	            already exist, they are often in different formats and thus cannot be exchanged between companies and
	            research institutions. To address this problem, we present the first publicly available converter from
	            the OpenDRIVE format to lanelets—both representations are among the most popular map formats.
	            We demonstrate the capabilities of the converter by using publicly available maps.},
}
```
