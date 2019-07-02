"""
This module can be executed to perform a conversion.
"""
import argparse
import os

import matplotlib

import crmapconverter.osm2cr.converter_modules.converter as converter
import crmapconverter.osm2cr.converter_modules.cr_operations.export as ex
from crmapconverter.osm2cr import config
from crmapconverter.osm2cr.converter_modules.osm_operations.downloader import (
    download_around_map,
)
from crmapconverter.osm2cr.converter_modules.gui_modules.gui_embedding import MainApp

matplotlib.use("Qt5Agg")


def convert(filename):
    """
    opens and converts a map

    :param filename: the file to open
    :type filename: str
    :return: None
    """
    scenario = converter.Scenario(filename)
    scenario.save_as_cr()


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
    scenario = converter.Scenario(
        config.SAVE_PATH + config.BENCHMARK_ID + "_downloaded.osm"
    )
    scenario.save_as_cr()


def start_gui(parent=None):
    app = MainApp(parent)
    app.start()


def main():
    parser = argparse.ArgumentParser(
        description="download or open an OSM file and convert it to CR or use GUI"
    )
    parser.add_argument("action", type=str)
    parser.add_argument("file", nargs="?")
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
    elif args.action == "g" or args.action == "gui":
        start_gui()
    else:
        print("invalid arguments")
        return


if __name__ == "__main__":
    main()
