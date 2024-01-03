from crdesigner.ui.gui.utilities.toolbox_ui import Toolbox
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.add_lanelet_widget import (
    AddLaneletWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.aerial_image_widget import (
    AerialImageWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.intersection_widget import (
    IntersectionsWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.lanelet_attributes_widget import (
    LaneletAttributesWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.lanelet_operations_widget import (
    LaneletOperationsWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.traffic_light_widget import (
    TrafficLightWidget,
)
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.traffic_sign_widget import (
    TrafficSignWidget,
)


class RoadNetworkToolboxUI(Toolbox):
    """a dialog to which collapsible sections can be added;
    reimplement define_sections() to define sections and
    add them as (title, widget) tuples to self.sections
    """

    def __init__(self, mwindow):
        self.add_lanelet_widget = AddLaneletWidget(self)
        self.lanelet_attributes_widget = LaneletAttributesWidget(self)
        self.lanelet_operations_widget = LaneletOperationsWidget(self)
        self.traffic_sign_widget = TrafficSignWidget(self)
        self.traffic_light_widget = TrafficLightWidget(self)
        self.intersections_widget = IntersectionsWidget(self)
        self.aerial_image_widget = AerialImageWidget(self)
        self.curved_check_button = None
        self.select_end_position = None
        self.end_position_method = None
        self.lanelet_width = None
        super().__init__(mwindow)

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        self.sections.append(self.add_lanelet_widget.create_add_lanelet_widget())
        self.sections.append(self.lanelet_attributes_widget.create_lanelet_attributes_widget())
        self.sections.append(self.lanelet_operations_widget.create_lanelet_operations_widget())
        self.sections.append(self.traffic_sign_widget.create_traffic_sign_widget())
        self.sections.append(self.traffic_light_widget.create_traffic_light_widget())
        self.sections.append(self.intersections_widget.create_intersection_widget())
        self.sections.append(self.aerial_image_widget.create_aerial_image_widget())

    def update(self) -> None:
        super(RoadNetworkToolboxUI, self).update()

    def update_window(self):
        super().update_window()
        if self.place_at_position.isChecked():
            if self.curved_check_button.isChecked():
                self.select_end_position.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().disabled
                )
            else:
                self.select_end_position.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().color
                )

            if self.select_end_position.isChecked():
                self.curved_check_button.button.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().disabled
                )
            else:
                self.curved_check_button.button.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().color
                )

        if (
            self.place_at_position.isChecked()
            or self.connect_to_previous_selection.isChecked()
            or self.connect_to_predecessors_selection.isChecked()
            or self.connect_to_successors_selection.isChecked()
        ):
            if not self.place_at_position.isChecked():
                self.lanelet_width.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().disabled
                )
            else:
                self.lanelet_width.setStyleSheet(
                    "background-color: "
                    + self.mwindow.mwindow_ui.colorscheme().second_background
                    + "; color: "
                    + self.mwindow.mwindow_ui.colorscheme().color
                )
