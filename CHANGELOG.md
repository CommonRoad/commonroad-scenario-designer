# Changelog
## [0.8.1] - 2023-12-22

### Changed
- Removed unnecessary lanelet2 and opendrive 'api' in conversion example files


## [0.8.1] - 2023-12-XX

### Added
- Test cases for GUI

### Fixed
- Adding existing obstacles again

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
