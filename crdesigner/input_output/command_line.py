__author__ = "Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["BMW Car@TUM"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

import os
import argparse
import sys

from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import Tag

from crdesigner.input_output.gui.commonroad_scenario_designer_gui import start_gui
from crdesigner.input_output.api import commonroad_to_lanelet, lanelet_to_commonroad, opendrive_to_commonroad, \
    osm_to_commonroad, commonroad_to_sumo, sumo_to_commonroad


def get_args() -> argparse.Namespace:
    """
    Specifies and reads command line arguments

    :return: command line arguments
    """
    parser = argparse.ArgumentParser(description="Toolbox for Map Conversion and Scenario Creation for "
                                                 "Autonomous Vehicles")
    parser.add_argument('mode', type=str, const='all', nargs='?', choices=["gui", "map-convert-osm",
                                                                           "map-convert-sumo",
                                                                           "map-convert-lanelet",
                                                                           "map-convert-opendrive"],
                        help='specification of operation mode', default="gui")
    parser.add_argument('-i', '--input_file', type=str, help='Path to input file', default=None)
    parser.add_argument('-o', '--output_file', type=str, help='Path for output file')
    parser.add_argument('-c', '--source_commonroad', default=False, action='store_true',
                        help='indicator whether a conversion from CommonRoad to the other format should be performed, '
                             'default=False')
    parser.add_argument("-f", "--force-overwrite", action="store_true", help="overwrite existing file if it has same "
                                                                             "name as converted file")
    parser.add_argument("-t", "--tags", nargs="+", help="tags for the created scenario", default=set())
    parser.add_argument("--proj", help="proj-string to specify conversion for lanelet/lanelet2 format")
    parser.add_argument("--adjacencies", action="store_true", help="detect left and right adjacencies of "
                                                                   "lanelets if they do not share a common way "
                                                                   "(this is only used for lanelet/lanelet2 "
                                                                   "conversion)")
    parser.add_argument("--left-driving", action="store_true", help="set to true if map describes a left driving "
                                                                    "system, e.g., in Great Britain "
                                                                    "(this is only used for lanelet/lanelet2 "
                                                                    "conversion)")
    parser.add_argument("--author", help="comma-separated list of scenario/map author names", default="")
    parser.add_argument("--affiliation", help="your affiliation, e.g., university, research institute, company",
                        default="")

    return parser.parse_args()


def main():
    """
    Processes command line input and executes necessary action
    """
    args = get_args()

    input_file = args.input_file
    if args.mode == "gui":
        start_gui(input_file)
    else:
        partition = args.input_file.rpartition(".")

        file_ending = "xml"
        if args.source_commonroad:
            if args.mode == "map-convert-osm":
                print(
                    "Not converting: The CommonRoad to OpenStreetMap conversion is currently not supported.",
                    file=sys.stderr,
                )
            elif args.mode == "map-convert-opendrive":
                print(
                    "Not converting: The CommonRoad to OpenDRIVE conversion is currently not supported.",
                    file=sys.stderr,
                )
            elif args.mode == "map-convert-sumo":
                file_ending = "net"
            elif args.mode == "map-convert-lanelet":
                file_ending = "osm"

        if args.output_file:
            output_file = args.output_file
        else:
            output_file = f"{partition[0]}.{file_ending}"  # only name of file

        if os.path.isfile(output_file) and not args.force_overwrite:
            print(
                "Not converting because file exists and option 'force-overwrite' not active",
                file=sys.stderr,
            )
            sys.exit(-1)

        if args.source_commonroad:
            if args.mode == "map-convert-lanelet":
                commonroad_to_lanelet(input_file, output_file, args.proj)
            if args.mode == "map-convert-sumo":
                commonroad_to_sumo(input_file, output_file)
        else:
            if args.mode == "map-convert-osm":
                scenario = osm_to_commonroad(input_file)
            elif args.mode == "map-convert-opendrive":
                scenario = opendrive_to_commonroad(input_file)
            elif args.mode == "map-convert-sumo":
                scenario = sumo_to_commonroad(input_file)
            elif args.mode == "map-convert-lanelet":
                scenario = lanelet_to_commonroad(input_file, args.proj, args.left_driving, args.adjacencies)
            else:
                return
            tags = set([Tag(t) for t in args.tags])
            writer = CommonRoadFileWriter(
                scenario=scenario,
                planning_problem_set=PlanningProblemSet(),
                author=args.author,
                affiliation=args.affiliation,
                source="CommonRoad Scenario Designer",
                tags=tags,
            )
            if args.force_overwrite:
                writer.write_to_file(output_file, OverwriteExistingFile.ALWAYS)
            else:
                writer.write_to_file(output_file, OverwriteExistingFile.SKIP)
