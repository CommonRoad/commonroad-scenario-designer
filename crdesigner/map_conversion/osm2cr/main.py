"""
This module can be executed to perform a conversion.
"""
import argparse
import os

import matplotlib
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Tag

import crdesigner.map_conversion.osm2cr.converter_modules.converter as converter
import crdesigner.map_conversion.osm2cr.converter_modules.cr_operations.export as ex
from crdesigner.map_conversion.osm2cr import config
from crdesigner.map_conversion.osm2cr.converter_modules.intermediate_operations.intermediate_format import \
    IntermediateFormat
from crdesigner.map_conversion.osm2cr.converter_modules.osm_operations.downloader import download_around_map

matplotlib.use("Qt5Agg")


def convert(filename_open, filename_store=None):
    """
    opens and converts a map

    :param filename_open: the file to open
    :type filename_open: str
    :param filename_store: the file to open
    :type filename_store: str
    :return: None
    """
    scenario = converter.GraphScenario(filename_open)
    #scenario.save_as_cr(filename_store)

    interm_format = IntermediateFormat.extract_from_road_graph(scenario.graph)
    scenario_cr = interm_format.to_commonroad_scenario()
    problemset = PlanningProblemSet(None)
    author = config.AUTHOR
    affiliation = config.AFFILIATION
    source = config.SOURCE
    tags_str = config.TAGS
    tags = []
    for tag_str in tags_str.split():
        tags.append(Tag[tag_str.upper()])
    file_path = config.SAVE_PATH + config.BENCHMARK_ID + ".xml"
    # in the current commonroad version the following line works
    file_writer = CommonRoadFileWriter(
        scenario_cr, problemset, author, affiliation, source, tags, decimal_precision=16
    )
    # file_writer = CommonRoadFileWriter(scenario, problemset, author, affiliation, source, tags)
    file_writer.write_scenario_to_file(file_path, OverwriteExistingFile.ALWAYS)


def download_and_convert():
    """
    downloads and converts a map

    :return: None
    """
    x, y = config.DOWNLOAD_COORDINATES
    if not os.path.exists(config.SAVE_PATH):
        os.makedirs(config.SAVE_PATH)
    download_around_map(
        config.SAVE_PATH + config.BENCHMARK_ID + "_downloaded.osm",
        x,
        y,
        config.DOWNLOAD_EDGE_LENGTH,
    )
    scenario = converter.GraphScenario(
        config.SAVE_PATH + config.BENCHMARK_ID + "_downloaded.osm"
    )
    scenario.save_as_cr(None)


def main():
    parser = argparse.ArgumentParser(
        description="download or open an OSM file and convert it to CR or use GUI"
    )
    parser.add_argument("action",
                        choices=["g", "gui", "d","download", "o", "open"],
                        help="g or gui for starting the gui, d or download to "
                            + "download a OSM file, o or open to convert files")
    parser.add_argument("file", nargs="?", help="file input for the converter")
    args = parser.parse_args()
    if args.action == "d" or args.action == "download":
        download_and_convert()
        ex.view_xml(config.SAVE_PATH + config.BENCHMARK_ID + ".xml")
    elif args.action == "o" or args.action == "open":
        if args.file is not None:
            convert(args.file)
            ex.view_xml(config.SAVE_PATH + config.BENCHMARK_ID + ".xml")
        else:
            print("please provide a file to open")
            return
    else:
        print("invalid arguments")
        return


if __name__ == "__main__":
    main()
