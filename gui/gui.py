from crdesigner.input_output.gui.commonroad_scenario_designer_gui import start_gui as start_gui_old


def start_gui():
    """
    The main entry point to the gui. For now this is more of an adapter to redirect to the implementation.
    """
    start_gui_old()


if __name__ == '__main__':
    start_gui()
