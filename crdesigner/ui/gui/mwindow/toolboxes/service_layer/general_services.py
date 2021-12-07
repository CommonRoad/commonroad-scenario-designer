"""Generic file to move complexity"""
from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.gui_sumo_simulation import SUMO_AVAILABLE


def toolbox_callback(mwindow, scenario):
    """The callback when the user modifies the scenario via the toolboxes."""
    if scenario is not None:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(scenario)
        mwindow.animated_viewer_wrapper.update_view(focus_on_network=True)
        mwindow.update_max_step()
        mwindow.store_scenario()
