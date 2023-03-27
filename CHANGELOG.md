# Changelog

## [0.7.0] - 2023-0X-XX

### Added
- Possibility to load aerial image from Bing in the background
- Possibility to load aerial image from LDBV in the background
- CommonRoad to Lanelet2 conversion: Conversion of regulatory elements
- CommonRoad to Lanelet2 conversion: Conversion of lanelet types

### Changed
- Default matplotlib area
- Generalized traffic sign conversion 
- Lanelet2 to CommonRoad conversion: Generalize traffic sign conversion

### Fixed
- Persisting zoomed scale
- Connect to predecessor, previously added, and successor
- Adding rotated lanelet (>360°)
- Lanelet selection after translating a lanelet in the GUI
- Blue position waypoint in GUI is removed when new scenario is created

### Removed

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
