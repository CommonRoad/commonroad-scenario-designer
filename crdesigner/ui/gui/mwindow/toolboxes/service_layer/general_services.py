"""Generic file to move complexity"""
from commonroad.scenario.scenario import Scenario


def toolbox_callback(mwindow, scenario: Scenario, new_file_added: bool = False):
    """The callback when the user modifies the scenario via the toolboxes."""
    if scenario is not None:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(scenario, new_file_added=new_file_added)
        mwindow.update_max_step()
        mwindow.store_scenario()
