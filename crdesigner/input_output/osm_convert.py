#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to call from commandline to convert OSM to a CommonRoad file."""

import os
import sys
import argparse
from lxml import etree

from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag
from commonroad.common.file_reader import CommonRoadFileReader

from crdesigner.map_conversion.lanelet_lanelet2.lanelet2cr import Lanelet2CRConverter
from crdesigner.map_conversion.lanelet_lanelet2.lanelet2_parser import Lanelet2Parser
from crdesigner.map_conversion.lanelet_lanelet2.cr2lanelet import CR2LaneletConverter

__author__ = "Benjamin Orthen"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


def parse_arguments():
    """Parse command line arguemts.

    Returns:
      args object
    """
    parser = argparse.ArgumentParser(
        description="Parse an OSM file containing lanelets and convert it to a CommonRoad scenario file or vice versa."
    )
    parser.add_argument("input_file", help="file to be converted")
    parser.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        help="overwrite existing file if it has same name as converted file",
    )
    parser.add_argument("-o", "--output-name", help="specify name of outputed file")
    parser.add_argument("-t", "--tags", nargs="+", type=Tag, help="tags of the created scenarios", default=set())
    parser.add_argument("--proj", help="proj-string to specify conversion")
    parser.add_argument(
        "-a",
        "--adjacencies",
        action="store_true",
        help="detect left and right adjacencies of lanelets if they do not share a common way",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="convert in the reverse direction, i.e. from CommonRoad to OSM lanelets.",
    )
    parser.add_argument(
        "--left-driving",
        action="store_true",
        help="set to true if map describes a left driving system (e.g. in Great Britain)",
    )
    args = parser.parse_args()
    return args


def main():
    """Run script to convert file."""
    args = parse_arguments()
    partition = args.input_file.rpartition(".")

    file_ending = "osm" if args.reverse else "xml"

    if args.output_name:
        output_name = args.output_name
    else:
        output_name = f"{partition[0]}.{file_ending}"  # only name of file

    if os.path.isfile(output_name) and not args.force_overwrite:
        print(
            "Not converting because file exists and option 'force-overwrite' not active",
            file=sys.stderr,
        )
        sys.exit(-1)

    if args.reverse:
        commonroad_to_osm(args, output_name)
    else:
        osm_to_commonroad(args, output_name)


def osm_to_commonroad(args, output_name: str):
    """Convert from OSM to CommonRoad.
    Args:
      args: Object containing parsed arguments.
      output_name: Name of file where result should be written to.
    """
    parser = Lanelet2Parser(etree.parse(args.input_file).getroot())
    osm = parser.parse()

    osm2l = Lanelet2CRConverter(proj_string=args.proj)
    scenario = osm2l(
        osm, detect_adjacencies=args.adjacencies, left_driving_system=args.left_driving
    )
    if scenario:
        writer = CommonRoadFileWriter(
            scenario=scenario,
            planning_problem_set=PlanningProblemSet(),
            author="",
            affiliation="",
            source="OpenDRIVE 2 Lanelet Converter",
            tags=set(args.tags),
        )
        writer.write_to_file(output_name, OverwriteExistingFile.ALWAYS)
    else:
        print("Could not convert from OSM to CommonRoad format!")


def commonroad_to_osm(args, output_name: str):
    """Convert from CommonRoad to OSM.

    Args:
      args: Object containing parsed arguments.
      output_name: Name of file where result should be written to.
    """
    try:
        commonroad_reader = CommonRoadFileReader(args.input_file)
        scenario, _ = commonroad_reader.open()

    except etree.XMLSyntaxError as xml_error:
        print(f"SyntaxERror: {xml_error}")
        print(
            "There was an error during the loading of the selected CommonRoad file.\n"
        )
    l2osm = CR2LaneletConverter(args.proj)
    osm = l2osm(scenario)
    with open(f"{output_name}", "wb") as file_out:
        file_out.write(
            etree.tostring(
                osm, xml_declaration=True, encoding="UTF-8", pretty_print=True
            )
        )


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


if __name__ == '__main__':
    main()
