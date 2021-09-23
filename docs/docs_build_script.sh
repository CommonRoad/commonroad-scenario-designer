#!/bin/bash

make clean
sphinx-apidoc -o source/api/map_conversion/opendrive ../crdesigner/map_conversion/opendrive -f
sphinx-apidoc -o source/api/map_conversion/sumo ../crdesigner/map_conversion/sumo_map -f
sphinx-apidoc -o source/api/map_conversion/osm ../crdesigner/map_conversion/osm2cr -f
sphinx-apidoc -o source/api/map_conversion/lanelet ../crdesigner/map_conversion/lanelet_lanelet2 -f
sphinx-apidoc -o source/api/input_output/ ../crdesigner/input_output/ -d 1 -f
make html

