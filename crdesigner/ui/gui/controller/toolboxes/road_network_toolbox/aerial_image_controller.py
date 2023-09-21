from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from crdesigner.ui.gui.model.scenario_model import ScenarioModel
from crdesigner.ui.gui.view.toolboxes.road_network_toolbox.road_network_toolbox_ui.road_network_toolbox_ui import \
    RoadNetworkToolboxUI

from crdesigner.config.gui_config import gui_config as config_settings

class RequestRunnable(QRunnable):
    def __init__(self, fun, roadNetworkController):
        QRunnable.__init__(self)
        self.fun = fun
        self.roadNetworkController = roadNetworkController

    def run(self):
        self.fun()
        QMetaObject.invokeMethod(self.roadNetworkController, "stopSpinner", Qt.QueuedConnection,
                                Q_ARG(str, "Conversion Ended"))


class AddAerialImageController:

    def __init__(self, road_network_controller, scenario_model: ScenarioModel,
                 road_network_toolbox_ui: RoadNetworkToolboxUI):
        self.scenario_model = scenario_model
        self.road_network_toolbox_ui = road_network_toolbox_ui
        self.road_network_controller = road_network_controller
        
    def connect_gui_aerial_image(self):
        self.road_network_toolbox_ui.button_add_aerial_image.clicked.connect(lambda: self.show_aerial_image())
        self.road_network_toolbox_ui.button_remove_aerial_image.clicked.connect(lambda: self.remove_aerial_image())

    def show_aerial_image(self):
        if self.road_network_controller.mwindow.play_activated:
            self.road_network_controller.text_browser.append("Please stop the animation first.")
            return

        if not self.scenario_model.scenario_created():
            self.road_network_controller.text_browser.append("Please create first a new scenario.")
            return

        if float(self.road_network_toolbox_ui.northern_bound.text()) > 90 or float(
                self.road_network_toolbox_ui.northern_bound.text()) < -90:
            self.road_network_controller.text_browser.append("Invalid northern bound. Latitude has to be between -90 and 90.")
            return

        if float(self.road_network_toolbox_ui.southern_bound.text()) > 90 or float(
                self.road_network_toolbox_ui.southern_bound.text()) < -90:
            self.road_network_controller.text_browser.append("Invalid southern bound. Latitude has to be between -90 and 90.")
            return

        if float(self.road_network_toolbox_ui.western_bound.text()) > 180 or float(
                self.road_network_toolbox_ui.western_bound.text()) < -180:
            self.road_network_controller.text_browser.append("Invalid western bound. Longitude has to be between -180 and 180.")
            return

        if float(self.road_network_toolbox_ui.eastern_bound.text()) > 180 or float(
                self.road_network_toolbox_ui.eastern_bound.text()) < -180:
            self.road_network_controller.text_browser.append("Invalid eastern bound. Longitude has to be between -180 and 180.")
            return

        if float(self.road_network_toolbox_ui.southern_bound.text()) >= float(
                self.road_network_toolbox_ui.northern_bound.text()) or float(
                self.road_network_toolbox_ui.western_bound.text()) >= float(
                self.road_network_toolbox_ui.eastern_bound.text()):
            self.road_network_controller.text_browser.append("Invalid coordinate limits.")
            return

        if self.road_network_toolbox_ui.bing_selection.isChecked():
            if config_settings.BING_MAPS_KEY == "":
                print("_Warning__: No Bing Maps key specified. Go to settings and set password.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning", "No Bing Maps key specified. Go to settings and set password.",
                                       QMessageBox.Ok, QMessageBox.Ok)
                warning_dialog.close()
                return

        elif self.road_network_toolbox_ui.ldbv_selection.isChecked():
            if config_settings.LDBV_USERNAME == "" or config_settings.LDBV_PASSWORD == "":
                print("_Warning__: LDBV username and password not specified. Go to settings and set them.")
                warning_dialog = QMessageBox()
                warning_dialog.warning(None, "Warning",
                                       "LDBV username and password not specified. Go to settings and set them.",
                                       QMessageBox.Ok, QMessageBox.Ok)
                warning_dialog.close()
                return

            if float(self.road_network_toolbox_ui.southern_bound.text()) > 50.6 or float(
                    self.road_network_toolbox_ui.southern_bound.text()) < 47.2 or float(
                    self.road_network_toolbox_ui.northern_bound.text()) > 50.6 or float(
                    self.road_network_toolbox_ui.northern_bound.text()) < 47.2 or float(
                    self.road_network_toolbox_ui.western_bound.text()) > 13.9 or float(
                    self.road_network_toolbox_ui.western_bound.text()) < 8.9 or float(
                    self.road_network_toolbox_ui.eastern_bound.text()) > 13.9 or float(
                    self.road_network_toolbox_ui.eastern_bound.text()) < 8.9:
                self.road_network_controller.text_browser.append(
                    "Coordinates are outside Bavaria. This tool works only for coordinates inside Bavaria.")
                return

        self.road_network_controller.startSpinner(self.road_network_toolbox_ui.Spinner)
        runnable = RequestRunnable(self.activate_aerial_image, self.road_network_controller)
        QThreadPool.globalInstance().start(runnable)

    def remove_aerial_image(self):
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.deactivate_aerial_image()
        self.scenario_model.notify_all()

    def activate_aerial_image(self):
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.activate_aerial_image(
            self.road_network_toolbox_ui.bing_selection.isChecked(),
            float(self.road_network_toolbox_ui.northern_bound.text()),
            float(self.road_network_toolbox_ui.western_bound.text()),
            float(self.road_network_toolbox_ui.southern_bound.text()),
            float(self.road_network_toolbox_ui.eastern_bound.text()))
        self.road_network_controller.mwindow.animated_viewer_wrapper.cr_viewer.dynamic.show_aerial_image(True)

