from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)


class AddAerialImageUI:
    def __init__(
        self, scenario_model: ScenarioModel, road_network_toolbox_ui: RoadNetworkToolboxUI
    ):
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.scenario_model = scenario_model
