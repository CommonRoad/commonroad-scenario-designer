#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to call from commandline to convert OSM to a CommonRoad file."""

import os
import sys
import argparse

from pyproj import Proj
from lxml import etree
from commonroad.common.file_writer import CommonRoadFileWriter

from opendrive2lanelet.osm.osm2lanelet import OSM2LConverter
from opendrive2lanelet.osm.parser import OSMParser

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.0.2"
__maintainer__ = "Benjamin Orthen"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


def parse_arguments():
    """Parse command line arguemts.

    Returns:
      args object
    """
    parser = argparse.ArgumentParser(description="Provide ls")
    parser.add_argument("input_file", help="file to be converted")
    parser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        help="overwrite existing file if it has same name as converted file",
    )
    parser.add_argument("-o", "--output-name", help="specify name of outputed file")
    parser.add_argument("--proj", help="proj-string to specify conversion")
    args = parser.parse_args()
    return args


def main():
    """Run script to convert file."""
    args = parse_arguments()
    partition = args.input_file.rpartition(".")

    if args.output_name:
        output_name = args.output_name
    else:
        output_name = f"{partition[0]}.xml"  # only name of file

    if os.path.isfile(output_name) and not args.force_overwrite:
        print(
            "Not converting because file exists and option 'force-overwrite' not active",
            file=sys.stderr,
        )
        sys.exit(-1)

    with open("{}".format(args.input_file), "r") as file_in:
        parser = OSMParser(etree.parse(file_in).getroot())
        osm = parser.parse()

    osm2l = OSM2LConverter(args.proj)
    scenario = osm2l(osm)
    writer = CommonRoadFileWriter(
        scenario=scenario,
        planning_problem_set=None,
        author="",
        affiliation="",
        source="OpenDRIVE 2 Lanelet Converter",
        tags="",
    )

    with open(f"{output_name}", "w") as file_out:
        writer.write_scenario_to_file_io(file_out)
