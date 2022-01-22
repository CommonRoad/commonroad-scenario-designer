from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.ui.gui.mwindow.toolboxes.service_layer.sumo_settings import SUMOSettings
from crdesigner.ui.gui.mwindow.top_bar_wrapper.service_layer.general_services import create_action
from crdesigner.ui.gui.mwindow.service_layer.converter_modules.osm_interface import OSMInterface
from crdesigner.ui.gui.mwindow.service_layer.gui_settings import GUISettings
from crdesigner.ui.gui.mwindow.service_layer.converter_modules.opendrive_interface import OpenDRIVEInterface

"""
    File for providing functions for the settings.
"""


def show_osm_settings(mwindow):
    """
        Showing the osm settings.
    """
    osm_interface = OSMInterface(mwindow)
    osm_interface.show_settings()


def show_opendrive_settings(mwindow):
    """
        Show the OpenDRIVE settings.
    """
    opendrive_interface = OpenDRIVEInterface(mwindow)
    opendrive_interface.show_settings()


def show_gui_settings(mwindow):
    """
        Show the gui settings.
    """
    mwindow.gui_settings = GUISettings(mwindow)


def show_sumo_settings(mwindow):
    """
        Show the sumo settings.
    """
    mwindow.sumo_settings = SUMOSettings(mwindow, config=mwindow.obstacle_toolbox.sumo_simulation.config)
