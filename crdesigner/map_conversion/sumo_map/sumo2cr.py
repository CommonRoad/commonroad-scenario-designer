import os
import subprocess

from commonroad.scenario.scenario import Scenario
from lxml import etree

try:
    # required for Ubuntu 20.04 since there a system library is too old for pyqt6 and the import fails
    # when not importing this, one can still use the map conversion
    from PyQt6.QtWidgets import QMessageBox

    pyqt_available = True
except (ImportError, RuntimeError):
    pyqt_available = False

from crdesigner.map_conversion.opendrive.odr2cr.opendrive_conversion.network import (
    Network,
)
from crdesigner.map_conversion.opendrive.odr2cr.opendrive_parser.parser import (
    parse_opendrive,
)


def convert_net_to_cr(net_file: str, verbose: bool = False) -> Scenario:
    """
    Converts .net file to CommonRoad xml using netconvert and OpenDRIVE 2 Lanelet Converter.

    :param net_file: path of .net.xml file
    :param verbose: Boolean indicating whether status should be printed to console

    :return: CommonRoad map file
    """
    if net_file is None and pyqt_available:
        QMessageBox.warning(None, "Warning", "No file selected.", QMessageBox.StandardButton.Ok)
        return
    assert isinstance(net_file, str)

    out_folder_tmp = os.path.dirname(net_file)

    # filenames
    scenario_name = _get_scenario_name_from_netfile(net_file)
    opendrive_file = os.path.join(out_folder_tmp, scenario_name + ".xodr")

    # convert to OpenDRIVE file using netconvert
    subprocess.check_output(
        [
            "netconvert",
            "-s",
            net_file,
            "--opendrive-output",
            opendrive_file,
            "--junctions.scurve-stretch",
            "1.0",
        ]
    )
    if verbose:
        print("converted to OpenDrive (.xodr)")

    # convert to CommonRoad using opendrive2lanelet
    # import, parse and convert OpenDRIVE file
    with open(opendrive_file, "r") as fi:
        open_drive = parse_opendrive(etree.parse(fi).getroot())

    road_network = Network()
    road_network.load_opendrive(open_drive)
    scenario = road_network.export_commonroad_scenario()
    if verbose:
        print("converted to Commonroad (.cr.xml)")

    return scenario


def _get_scenario_name_from_netfile(filepath: str) -> str:
    """
    Returns the scenario name specified in the net file.

    :param filepath: the path of the net file

    """
    scenario_name: str = (os.path.splitext(os.path.basename(filepath))[0]).split(".")[0]
    return scenario_name
