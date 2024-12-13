# Changelog

## [0.8.3]

### Added
- odr2cr: Left-hand drive consideration

### Changed
- map-conversion: Interfaces can consider string and Path objects
- mkdocs for docu
- ruff for formatting
- add pre-commit hook

### Fixed
- cr2sumo: Trajectory conversion assigned non-existent edges to routes
- osm2cr: Intersection incoming elements did not reference any incoming lanelets
- Command line interface: Providing no input path
- Scenario fails to be opened, if any of the dynamic obstacles does not contain a prediction
- GUI: wrong usage of button
- Check for qt6 so that map conversions work under Ubuntu 20.04
- GUI: Adding traffic signs to lanelet did not work due to changes in commonroad-io
- osm2cr: Lanelet line markings were always set to 'no_marking' although the line markings are unkown

## [0.8.2] - 2024-07-22

### Added
- lanelet2cr: Multipolygon and line marking conversion
- lanelet2cr: Traffic light conversion for Autoware (retain traffic light ids, set own Autoware default cycle, and set traffic light active status to false)
- cr2lanelet: Area conversion
- cr2lanelet: Lane change property tags
- odr2cr: Road speed limit conversion
- odr2cr: Option to neglect projection by setting `config.proj_string_odr = None`


### Changed
- odr2cr: Warning instead of failure in case of not supported road object type

### Fixed
- odr2cr: Missing crosswalk projection
- odr2cr: Traffic light assignment
- odr2cr: Self-intersecting lanelets in case of wrong predecessor/successor relationships in OpenDRIVE file

### Removed
- Support of Python 3.8
- GUI simulation from GUI (the complete SUMO conversion/interface will be moved to another repository in the future)

## [0.8.1] - 2024-03-28

### Added
- Test cases for GUI
- Logging actions of users
- Optional functionality to get geonamesID locally without API-call
- Test Case for local geonamesID functionality
- OpenDRIVE to CommonRoad conversion: considering line markings of inner shared lanelet boundaries and the center line marking
- Checkbox in the settings to enable the manipulation of curved lanelets in the GUI
- Optional MGRS tag for nodes in CR to Lanelet2 conversion (compatibility with Autoware)
- Functionality to edit vertices of a lanelet in the canvas
- Eclipse-SUMO Python package dependency for better integration of SUMO
- cr2lanelet: Option of local coordinates for traffic lights
- cr2lanelet: Static height for traffic lights (1.2m) until official height support in CommonRoad
- cr2lanelet: Regulatory element to corresponding way relation for lanes (required by autoware)
- Option to display the aerial image of the current position
- By default, if no lbdv creditials are stored, the open source credentials are used
- File reader that optionally verifies and repairs the road network
- Option for the scenario designer file reader and writer to project the scenario
- Possibility to change the geo reference and translate the scenario
- Integrated map verification/repairing error visualization
- Separate obstacle profile widget within obstacle toolbox
- Multiple obstacle profiles visualizable
- Direct conversion from OpenDRIVE to Lanelet2

### Changed
- Remove second conversion option for Lanelet2 and OpenDRIVE conversion example files
- osm2cr: virtual traffic sign have position assigned
- PyQt6 instead of PyQt5 as GUI backend
- Code formatting (flake8, black, isort)
- cr2lanelet: traffic light subtype
- cr2lanelet: traffic light includes only two nodes (in case of autoware)
- osm2cr: use pyproj for projection

### Fixed
- Adding existing obstacles again
- Selecting obstacles with set-based prediction
- Bug when editing curved lanelets in the canvas
- lanelet2cr wrong final vertices assignment
- Deleting unreferenced traffic signs/lights after deleting lanelet
- Map verification/repairing: Checking unique ID of traffic light cycle element
- Consider x-, y-translation for cr2lanelet conversion (and vice versa)
- osm2cr projection
- odr2cr object crosswalk conversion
- odr2cr neglect merging of lanelets with conflicting references
- odr2cr fix overlapping boundaries
- lanelet2cr: traffic sign (speed limit) conversion bug

### Removed
- Unused osm2cr functions, e.g., for plotting graphs

## [0.8.0] - 2023-10-31

### Added
- CommonRoad map verification and repairing
- Cropping of a map in the GUI
- Background saves with restore functionality
- Scenario toolbox to specify planning problems
- Widget to edit settings of scenario
- Editing and adding curved lanelet via matplotlib visualization
- Support for visualizing scenarios with 3D coordinates on 2D plane
- cr2lanelet line marking conversion
- cr2lanelet bidirectional users conversion
- Possibility to change look of the GUI into a more modern style

### Changed
- GUI backend using MVC pattern
- Config model
- Automated creation of settings windows
- Support for commonroad-io 2023.3
- Commandline interface to use typer

### Fixed
- Handling of projection strings which contain elements which third-party tool does not support
- Issue when creating adjacent lanelets through *lanelet operations*
- No recognition of the selected lanelet by the *lanelet operations* widget
- Changes to some lanelets messing up the lanelet
- KeyError when yield sign has no stop line in cr2lanelet2 conversion
- Adaption of commonroad-io traffic light color usage in CommonRoad to lanelet2 conversion
- Add default traffic light cycle for OpenDRIVE conversion to support 2020a format
- Rotating lanelet cannot be selected through canvas anymore
- OpenDRIVE/Lanelet2 conversion intersection incoming lanelets as set instead of list/tuple
- Relationship of predecessor/successor when creating adjacent lanelets
- Obstacle information no longer crashes when selecting static obstacle or required state value is missing
- Visualization of obstacle colors
- Obstacles are not shown after time step 200

## [0.7.2] - 2023-07-29

### Added
- Lanelet2 conversion considers z-coordinate/elevation

### Fixed
- ID assignment lanelet2cr conversion
- lanelet2cr stop line projection

### Changed
- minimum cr-io version: 2023.2

## [0.7.1] - 2023-06-21

### Added
- Creation of autoware-compatible lanelet2 maps
- Set custom plot limits when adding scenario or aerial image
- Map German traffic sign 252 to sign to 260
- Consider OpenDRIVE offset

### Changed
- Versions of third-party packages
- Use positive IDs for the cr2lanelet conversion
- Structure for config parameters (similar as in commonroad-io)
- Add version to lanelet2 xml elements

### Fixed
- Lanelet2 projection
- Visualization of aerial images

### Removed
- GUI button to center aerial image at origin

## [0.7.0] - 2023-03-28

### Added
- Possibility to load aerial image from Bing in the background
- Possibility to load aerial image from LDBV in the background
- CommonRoad to Lanelet2 conversion: Conversion of regulatory elements
- CommonRoad to Lanelet2 conversion: Conversion of lanelet types
- Visualized scenario time step can be set manually (no need to use slider anymore)

### Changed
- Default matplotlib area
- Generalized traffic sign conversion
- Lanelet2 to CommonRoad conversion: Generalize traffic sign conversion
- Packaging using poetry

### Fixed
- Persisting zoomed scale
- Connect to predecessor, previously added, and successor
- Adding rotated lanelet (>360°)
- Lanelet selection after translating a lanelet in the GUI
- Blue position waypoint in GUI is removed when new scenario is created
- Video and matplotlib figure saving not working

## [0.6.1] - 2023-02-09

### Fixed
- GUI setting for axis visibility not changeable
- OpenDRIVE conversion endless loop speed limit mapping
- Yaml configuration loading under Windows

## [0.6.0] - 2023-01-31

### Added
- New test cases for the OpenDRIVE to CommonRoad conversion
- New shortcut buttons for lanelet adding, merging, splitting, creating adjacent
- Function to convert OSM to CommonRoad using SUMO
- Convert lane speed limits in OpenDRIVE
- Convert OpenDRIVE stop lines represented as object
- Reading of protobuf CommonRoad scenarios
- Support for commonroad-io 2022.3
- Unit test cases for Lanelet2 conversion
- Removing lanelets via "entf", "back", and "del" keys
- Removing lanelets via right click on lanelet
- Open edit section of lanelet via right click on lanelet
- Support for Python 3.10
- Preserving of settings

### Changed
- User interface for adding and updating lanelets

### Fixed
- Preventing GUI crash when adding obstacle without existing scenario
- Conversion of straight euler spiral
- Floating point error in computation of Cartesian points of lane border in OpenDRIVE2CR conversion
- Various small bug fixes

### Removed
- Support for Python 3.7

## [0.5.1] - 2022-05-20

### Fixed
- Switching shape of dynamic obstacle
- Adding adjacent lanelet which already exists
- Lanelet translation with missing x- or y-coordinate
- Missing location information when storing a scenario
- Various small bug fixes

## [0.5] - 2022-03-06

### Added
- Dynamic loading of large maps
- Adding of static obstacles
- Individual colors for obstacles
- Obstacle states can be changed by moving profiles in obstacle toolbox

### Fixed
- System crash if SUMO is available
- Undo button works again
- Various small bug fixes

## [0.4] - 2022-01-06

### Added
- Adding/Updating of static obstacles with circle, polygon, and rectangle shape in GUI

### Changed
- New GUI software architecture

### Fixed
- Various small bug fixes

## [0.3] - 2021-12-02

### Changed
- Solved deprecated warnings related to commonroad-io version 2021.3

### Fixed
- Various small bug fixes

## [0.2] - 2021-09-22

### Added
- Planning problem visualization in GUI

### Changed
- Extension of readme and documentation

### Fixed
- Various small bug fixes

## [0.1] - 2021-04-01
### Added
- graphical user interface for creating and manipulating CommonRoad maps and scenarios
- converts between different map formats: OpenStreetMap, SUMO, Lanelet/Lanelet2, OpenDRIVE, CommonRoad
- test cases for different converters
- tutorials for different converters
- readme and documentation
