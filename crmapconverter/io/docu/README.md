# Welcome to GUI 3.0 - CommonRoad Scenario Designer

## Overview of the architecture of CR Scenario Designer
The unified GUI structure of our design is composed of three modules:
+ Scenario Viewer module
+ Converter Interface
+ SUMO Tool

The Viewer module is responsible for the visualization of a loaded scenario. 
The Converter Interface is designed to convert different map types to CommonRoad. 
The Sumo Tool is in charge of traffic generation and simulation.

This GUI is designed to be able to import different types of map files and automatically convert them into CR files, 
to display them in the central area of the window and to provide functions such as manual lanelet creation and editing, 
adding of traffic signs and obstacles, as well as traffic simulation through SUMO tools. The layout of the GUI is illustrated in the following.

![Layout](crmapconverter/io/V3_0/Layout_cr_designer.png)

## Usage
Please see [the Usage of CR Scenario Designer](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/README.md)

## Overview of Code

| Python File or Folder | Functionalities |
| ------ | ------ |
| [main_cr_designer.py](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/main_cr_designer.py) | The class MWindow is the main GUI window based on PyQt |
| [gui_cr_viewer.py](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/gui_cr_viewer.py) | The class AnimatedViewer manages the functionalities of animation|
| [gui_toolbox.py](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/gui_toolbox.py) | The class UpperToolbox corresponds to Qt Widgets and manages Toolbox|
| [gui_settings.py](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/gui_settings.py) | This class manages the setting panel for GUI|
| [Converter_modules](https://gitlab.lrz.de/cps/commonroad-map-tool/-/tree/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/converter_modules) | This folder contains converter modules - OSM and OpenDrive|
| [SUMO_module](https://gitlab.lrz.de/cps/commonroad-map-tool/-/tree/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/SUMO_modules) | This folder contains python files for sumo tools and sumo settings|
| [GUI_resources](https://gitlab.lrz.de/cps/commonroad-map-tool/-/tree/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/GUI_resources) | This folder contains the Ui files generated from Qt Designer and the converted python files for GUI design|
| [GUI_src](https://gitlab.lrz.de/cps/commonroad-map-tool/-/tree/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/GUI_src) | This folder contains the icons and images used in GUI|