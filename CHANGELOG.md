## [Unreleased]
### Added
- Command line options for opendrive2lanelet-visualize

### Changed
- Slight adjustment of algorithm for join/split border movement

## [1.0.0] - 2018-01-28
### Added
- Algorithm to generate proper lanelet borders for splitting or joining lanelets.
- Command line tools to convert xodr files and visualize the results.
- More inline code documentation.
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
