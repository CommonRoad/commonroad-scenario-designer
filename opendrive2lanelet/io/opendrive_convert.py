#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""This file is a simple script to convert a xodr file
to a lanelet .xml file."""

import os
import sys
import argparse

from lxml import etree
from commonroad.scenario.scenario import Scenario

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

from opendrive2lanelet.opendriveparser.elements.opendrive import OpenDrive
from opendrive2lanelet.opendriveparser.parser import parse_opendrive
from opendrive2lanelet.network import Network
from opendrive2lanelet.osm.lanelet2osm import L2OSMConverter

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "1.2.0"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Released"


def parse_arguments():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("xodr_file", help="xodr file")
    parser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        help="overwrite existing file if it has same name as converted file",
    )
    parser.add_argument("--osm", help="use proj-string to convert directly to osm")
    parser.add_argument("-o", "--output-name", help="specify name of outputed file")
    args = parser.parse_args()
    return args


def convert_opendrive(opendrive: OpenDrive) -> Scenario:
    """Convert an existing OpenDrive object to a CommonRoad Scenario.

    Args:
      opendrive: Parsed in OpenDrive map.
    Returns:
      A commonroad scenario with the map represented by lanelets.
    """
    road_network = Network()
    road_network.load_opendrive(opendrive)

    return road_network.export_commonroad_scenario()


def main():
    """Helper function to convert an xodr to a lanelet file

    """
    args = parse_arguments()

    if args.output_name:
        output_name = args.output_name
    else:
        output_name = args.xodr_file.rpartition(".")[0]
        output_name = (
            f"{output_name}.osm" if args.osm else f"{output_name}.xml"
        )  # only name of file

    if os.path.isfile(output_name) and not args.force_overwrite:
        print(
            "Not converting because file exists and option 'force-overwrite' not active",
            file=sys.stderr,
        )
        sys.exit(-1)

    with open("{}".format(args.xodr_file), "r") as file_in:
        opendrive = parse_opendrive(etree.parse(file_in).getroot())

    scenario = convert_opendrive(opendrive)

    if not args.osm:
        writer = CommonRoadFileWriter(
            scenario=scenario,
            planning_problem_set=PlanningProblemSet(),
            author="",
            affiliation="",
            source="OpenDRIVE 2 Lanelet Converter",
            tags={Tag.URBAN, Tag.HIGHWAY},
        )
        writer.write_to_file(output_name, OverwriteExistingFile.ALWAYS)
    else:
        l2osm = L2OSMConverter(args.osm)
        osm = l2osm(scenario)
        with open(f"{output_name}", "wb") as file_out:
            file_out.write(
                etree.tostring(
                    osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
                )
            )


if __name__ == "__main__":
    main()
