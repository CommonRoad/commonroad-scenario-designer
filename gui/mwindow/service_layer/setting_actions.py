from crdesigner.input_output.gui.toolboxes.gui_sumo_simulation import SUMO_AVAILABLE
if SUMO_AVAILABLE:
    from crdesigner.input_output.gui.settings.sumo_settings import SUMOSettings
from gui.mwindow.service_layer.general_services import create_action
from crdesigner.input_output.gui.converter_modules.osm_interface import OSMInterface
from crdesigner.input_output.gui.misc.gui_settings import GUISettings
from crdesigner.input_output.gui.converter_modules.opendrive_interface import OpenDRIVEInterface

"""
    File for providing functions for the settings.
"""


def create_setting_actions(mwindow) -> (any, any, any, any):
    """Function to create the export action in the menu bar."""
    osm_settings = create_action(mwindow=mwindow, text="OSM Settings", icon="", checkable=False, slot=_show_osm_settings,
            tip="Show settings for osm converter", shortcut=None)
    opendrive_settings = create_action(mwindow=mwindow, text="OpenDRIVE Settings", icon="", checkable=False,
            slot=_show_opendrive_settings, tip="Show settings for OpenDRIVE converter", shortcut=None)
    gui_settings = create_action(mwindow=mwindow, text="GUI Settings", icon="", checkable=False, slot=_show_gui_settings,
            tip="Show settings for the CR Scenario Designer", shortcut=None)
    sumo_settings = None
    if SUMO_AVAILABLE:
        sumo_settings = create_action(mwindow=mwindow, text="SUMO Settings", icon="", checkable=False, slot=_show_sumo_settings,
                tip="Show settings for the SUMO interface", shortcut=None)
    return osm_settings, opendrive_settings, gui_settings, sumo_settings


def _show_osm_settings(mwindow):
    """
        Showing the osm settings.
    """
    osm_interface = OSMInterface(mwindow)
    osm_interface.show_settings()


def _show_opendrive_settings(mwindow):
    """
        Show the opendrive settings.
    """
    opendrive_interface = OpenDRIVEInterface(mwindow)
    opendrive_interface.show_settings()


def _show_gui_settings(mwindow):
    """
        Show the gui settings.
    """
    mwindow.gui_settings = GUISettings(mwindow)


def _show_sumo_settings(mwindow):
    """
        Show the sumo settings.
    """
    mwindow.sumo_settings = SUMOSettings(mwindow, config=mwindow.obstacle_toolbox.sumo_simulation.config)
