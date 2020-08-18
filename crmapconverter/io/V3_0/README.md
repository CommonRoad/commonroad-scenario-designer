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
![image](https://gitlab.lrz.de/cps/commonroad-map-tool/-/blob/GUI_CR_Scenario_Designer/crmapconverter/io/V3_0/Layout_cr_designer.png)