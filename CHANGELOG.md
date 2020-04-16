# Changelog

## [1.2.0] - 2020-04-14
### Changed
- Update to CommonRoad-io 2020.2

## [1.1.2] - 2020-02-10
### Changed
- Renamed lanelet.py and lanelet_network.py to conversion_lanelet.py and conversion_lanelet_network.py

## [1.1.0] - 2019-06-12
### Added
- Conversion from OSM lanelets to CommonRoad lanelets
- Conversion from CommonRoad lanelets to OSM lanelets
- New command for OSM<->CommonRoad lanelets conversion

### Changed
- Update dependencies

### Fixed
- Slight changes to algorithm which removes lanes with zero width

## [1.0.3] - 2019-05-28
## Changed
- Updated dependencies
- As commonroad-io has now better support for writing files, use CommonRoadFileWriter instead of ExtendedCommonRoadFileWriter

### Added
- First support for OSM-Lanelet to CommonRoad-Lanelet Conversion
- Plot center as command line argument to visualize CommonRoad files

## [1.0.2] - 2019-05-07
### Fixed
- Support for Poly3 was not fully implemented

## [1.0.1] - 2019-03-13
### Added
- Command line options for opendrive2lanelet-visualize

### Changed
- Slight adjustment of algorithm that determines new border points
when lanelets join into or split from other lanelets
- Minimum of 3 points per lanelet border are required

### Fixed
- Issue with selecting the proper width coefficients when calculating points on lanelet borders

## [1.0.0] - 2019-01-28
### Added
- Algorithm to generate proper lanelet borders for splitting or joining lanelets
- Command line tools to convert xodr files and visualize the results
- More inline code documentation
- Unit tests for xodr files where edge cases appear
- Sphinx documentation in docs/
- Support for Jenkins and Gitlab-CI

### Fixed
- Bugs in reading in the xodr file
- Bugs in renaming lanelet ids while converting
- Various other bugs
- Variable naming to adhere to python snake_case standard

### Removed
- Python properties which did not provide better functionality in comparison to normal attributes
