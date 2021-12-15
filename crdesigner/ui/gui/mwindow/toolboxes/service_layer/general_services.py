"""Generic file to move complexity"""


def toolbox_callback(mwindow, scenario):
    """The callback when the user modifies the scenario via the toolboxes."""
    if scenario is not None:
        mwindow.animated_viewer_wrapper.cr_viewer.open_scenario(scenario)
        mwindow.animated_viewer_wrapper.update_view(focus_on_network=True)
        mwindow.update_max_step()
        mwindow.store_scenario()
