#!/bin/bash

make clean
sphinx-apidoc -o source/api/map_conversion/opendrive ../crdesigner/map_conversion/opendrive -f
sphinx-apidoc -o source/api/map_conversion/sumo ../crdesigner/map_conversion/sumo_map -f
sphinx-apidoc -o source/api/map_conversion/osm ../crdesigner/map_conversion/osm2cr -f
sphinx-apidoc -o source/api/map_conversion/lanelet ../crdesigner/map_conversion/lanelet2 -f
sphinx-apidoc -o source/api/ui/ ../crdesigner/ui/ -d 1 -f
make html

# Titles of module pages have to be set manually!