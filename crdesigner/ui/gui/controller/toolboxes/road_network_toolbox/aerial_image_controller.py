from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from commonroad.scenario.scenario import Scenario
from pyproj import CRS, Transformer
from PyQt6.QtCore import Q_ARG, QMetaObject, QRunnable, Qt, QThreadPool

try:
    # required for Ubuntu 20.04 since there a system library is too old for pyqt6 and the import fails
    # when not importing this, one can still use the map conversion
    from PyQt6.QtWidgets import QMessageBox

    pyqt_available = True
except (ImportError, RuntimeError):
    pyqt_available = False

from crdesigner.common.config.gui_config import gui_config as config_settings
from crdesigner.common.config.gui_config import lanelet2_default
from crdesigner.common.logging import logger
from crdesigner.ui.gui.controller.animated_viewer.animated_viewer_controller import (
    extract_plot_limits,
)
from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import (
    RoadNetworkToolboxUI,
)

if TYPE_CHECKING:
    from crdesigner.ui.gui.controller.toolboxes.road_network_toolbox.road_network_controller import (
        RoadNetworkController,
    )


class RequestRunnable(QRunnable):
    def __init__(self, fun, road_network_controller: RoadNetworkController):
        QRunnable.__init__(self)
        self.fun = fun
        self.roadNetworkController = road_network_controller

    def run(self):
        self.fun()
        QMetaObject.invokeMethod(
            self.roadNetworkController,
            "stopSpinner",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, "Conversion Ended"),
        )


class AddAerialImageController:
    def __init__(
        self,
        road_network_controller,
        scenario_model: ScenarioModel,
        road_network_toolbox_ui: RoadNetworkToolboxUI,
    ):
        self.scenario_model = scenario_model
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.road_network_controller = road_network_controller

    def connect_gui_aerial_image(self):
        self.road_network_toolbox_ui.button_add_aerial_image.clicked.connect(
            lambda: self.show_aerial_image()
        )
        self.road_network_toolbox_ui.button_remove_aerial_image.clicked.connect(
            lambda: self.remove_aerial_image()
        )
        self.road_network_toolbox_ui.current_position.clicked.connect(
            lambda: self.show_aerial_image(True)
        )

    @logger.log
    def show_aerial_image(self, current_position: bool = False):
        """
        Triggers the display of the aerial image

        @param current_position: if the current_position of the scenario should be displayed
        """
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("Please create first a new scenario.")
            return

        if current_position:
            if self.scenario_model.get_lanelets() == []:
                self.road_network_controller.text_browser.append(
                    "The current Position can't be displayed, " "please create lanelets first"
                )
                return
            bounds = extract_plot_limits(self.scenario_model.get_lanelet_network())
            if (
                self.scenario_model.get_current_scenario().location.geo_transformation is not None
                and self.scenario_model.get_current_scenario().location.geo_transformation.x_translation
                != 0.0
            ):
                max_x = (
                    bounds[1]
                    + self.scenario_model.get_current_scenario().location.geo_transformation.x_translation
                )
                min_x = (
                    bounds[0]
                    + self.scenario_model.get_current_scenario().location.geo_transformation.x_translation
                )
            else:
                max_x = bounds[1]
                min_x = bounds[0]
            if (
                self.scenario_model.get_current_scenario().location.geo_transformation is not None
                and self.scenario_model.get_current_scenario().location.geo_transformation.y_translation
                != 0.0
            ):
                min_y = (
                    bounds[2]
                    + self.scenario_model.get_current_scenario().location.geo_transformation.y_translation
                )
                max_y = (
                    bounds[3]
                    + self.scenario_model.get_current_scenario().location.geo_transformation.y_translation
                )
            else:
                min_y = bounds[2]
                max_y = bounds[3]
            transformer = self._create_transformer_aerial(
                self.scenario_model.get_current_scenario()
            )
            if transformer is None:
                self.road_network_controller.text_browser.append(
                    "The current Position cannot be displayed"
                )
                return
            north, west = transformer.transform(min_x, max_y)
            south, east = transformer.transform(max_x, min_y)
            self.road_network_toolbox_ui.northern_bound.setText(str(north))
            self.road_network_toolbox_ui.eastern_bound.setText(str(east))
            self.road_network_toolbox_ui.southern_bound.setText(str(south))
            self.road_network_toolbox_ui.western_bound.setText(str(west))

        if (
            float(self.road_network_toolbox_ui.northern_bound.text()) > 90
            or float(self.road_network_toolbox_ui.northern_bound.text()) < -90
        ):
            self.road_network_controller.text_browser.append(
                "Invalid northern bound. Latitude has to be between -90 and 90."
            )
            return

        if (
            float(self.road_network_toolbox_ui.southern_bound.text()) > 90
            or float(self.road_network_toolbox_ui.southern_bound.text()) < -90
        ):
            self.road_network_controller.text_browser.append(
                "Invalid southern bound. Latitude has to be between -90 and 90."
            )
            return

        if (
            float(self.road_network_toolbox_ui.western_bound.text()) > 180
            or float(self.road_network_toolbox_ui.western_bound.text()) < -180
        ):
            self.road_network_controller.text_browser.append(
                "Invalid western bound. Longitude has to be between -180 and 180."
            )
            return

        if (
            float(self.road_network_toolbox_ui.eastern_bound.text()) > 180
            or float(self.road_network_toolbox_ui.eastern_bound.text()) < -180
        ):
            self.road_network_controller.text_browser.append(
                "Invalid eastern bound. Longitude has to be between -180 and 180."
            )
            return

        if float(self.road_network_toolbox_ui.southern_bound.text()) >= float(
            self.road_network_toolbox_ui.northern_bound.text()
        ) or float(self.road_network_toolbox_ui.western_bound.text()) >= float(
            self.road_network_toolbox_ui.eastern_bound.text()
        ):
            self.road_network_controller.text_browser.append("Invalid coordinate limits.")
            return

        if self.road_network_toolbox_ui.bing_selection.isChecked():
            if config_settings.BING_MAPS_KEY == "" and pyqt_available:
                print("_Warning__: No Bing Maps key specified. Go to settings and set password.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(
                    None,
                    "Warning",
                    "No Bing Maps key specified. Go to settings and set password.",
                    QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Ok,
                )
                warning_dialog.close()
                return

        elif self.road_network_toolbox_ui.ldbv_selection.isChecked():
            if (
                float(self.road_network_toolbox_ui.southern_bound.text()) > 50.6
                or float(self.road_network_toolbox_ui.southern_bound.text()) < 47.2
                or float(self.road_network_toolbox_ui.northern_bound.text()) > 50.6
                or float(self.road_network_toolbox_ui.northern_bound.text()) < 47.2
                or float(self.road_network_toolbox_ui.western_bound.text()) > 13.9
                or float(self.road_network_toolbox_ui.western_bound.text()) < 8.9
                or float(self.road_network_toolbox_ui.eastern_bound.text()) > 13.9
                or float(self.road_network_toolbox_ui.eastern_bound.text()) < 8.9
            ):
                self.road_network_controller.text_browser.append(
                    "Coordinates are outside Bavaria. This tool works only for coordinates inside Bavaria."
                )
                return

        self.road_network_controller.startSpinner(self.road_network_toolbox_ui.Spinner)
        runnable = RequestRunnable(self.activate_aerial_image, self.road_network_controller)
        QThreadPool.globalInstance().start(runnable)

    @logger.log
    def remove_aerial_image(self):
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.deactivate_aerial_image()
        self.scenario_model.notify_all()

    def activate_aerial_image(self):
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_aerial_image(
            self.road_network_toolbox_ui.bing_selection.isChecked(),
            float(self.road_network_toolbox_ui.northern_bound.text()),
            float(self.road_network_toolbox_ui.western_bound.text()),
            float(self.road_network_toolbox_ui.southern_bound.text()),
            float(self.road_network_toolbox_ui.eastern_bound.text()),
        )
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.show_aerial_image(
            True
        )

    def _create_transformer_aerial(self, scenario: Scenario) -> Optional[Transformer]:
        """
        Creates a transformer to convert the cooordinates of the scenario to longitude and latitude

        @param scenario: current scenario
        @returns: Transformer
        """
        loc = scenario.location
        proj_string_from = None
        if loc is not None and loc.geo_transformation is not None:
            proj_string_from = loc.geo_transformation.geo_reference
        if proj_string_from is None:
            return None
        crs_from = CRS(proj_string_from)
        crs_to = CRS(lanelet2_default)
        return Transformer.from_proj(crs_from, crs_to)
