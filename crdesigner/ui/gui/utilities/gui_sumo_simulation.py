import logging
import uuid

from commonroad.scenario.scenario import Scenario

from crdesigner.common.sumo_available import SUMO_AVAILABLE
from crdesigner.ui.gui.utilities.errors import error
from crdesigner.ui.gui.utilities.util import Observable

if SUMO_AVAILABLE:
    from sumocr.interface.sumo_simulation import SumoSimulation

    from crdesigner.map_conversion.sumo_map.config import SumoConfig
    from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter

from PyQt6 import QtWidgets
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QFrame, QMessageBox


class SimulationWorker(QThread):
    def __init__(self, scenario, config, output_folder):
        super(SimulationWorker, self).__init__()
        self.scenario: Scenario = scenario
        self.config: SumoConfig = config
        self.output_folder: str = output_folder
        self.simulated_scenario: Scenario = None
        self.error = None

    def run(self):
        try:
            # convert scenario to SUMO
            wrapper = CR2SumoMapConverter(self.scenario, self.config)
            wrapper.create_sumo_files(self.output_folder)

            simulation = SumoSimulation()
            simulation.initialize(self.config, wrapper)

            for _ in range(self.config.simulation_steps):
                simulation.simulate_step()
            simulation.stop()

            self.simulated_scenario = simulation.commonroad_scenarios_all_time_steps()
        except Exception as e:
            # log error and save it for display to the user
            logging.error(e)
            self.error = e


class ConversionWorker(QThread):
    def __init__(self, scenario, config, output_folder):
        super(ConversionWorker, self).__init__()
        self.scenario: Scenario = scenario
        self.config: SumoConfig = config
        self.output_folder: str = output_folder
        self.simulated_scenario: Scenario = None
        self.error = None

    def run(self):
        try:
            # convert scenario to SUMO
            wrapper = CR2SumoMapConverter(self.scenario, self.config)
            wrapper.create_sumo_files(self.output_folder)

        except Exception as e:
            # log error and save it for display to the user
            logging.error(e)
            self.error = e


class WaitingDialog(QtWidgets.QDialog):
    def __init__(self):
        super(WaitingDialog, self).__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.textBrowser = QtWidgets.QTextBrowser()
        self.setWindowTitle("Sumo Simulation")
        self.textBrowser.setText("Simulating, please wait ...")
        self.layout.addWidget(self.textBrowser)

        self.close_window = False

        def closeEvent(self, event):
            if self.close_window:
                super(WaitingDialog, self).closeEvent(event)
            else:
                event.ignore()


class SUMOSimulation(QFrame):
    def __init__(self, tmp_folder: str, parent=None):
        # set random uuid as name for the scenario files
        self._config = SumoConfig.from_scenario_name(str(uuid.uuid4()))
        self._config_obs = Observable(self._config)

        def set_config(config):
            self._config = config

        self._config_obs.subscribe(set_config)
        self._scenario: Scenario = None

        # observable giving the simulated scenario once done
        self.simulated_scenario = Observable(None)

        # set output_path to tmp_folder
        self._output_folder = tmp_folder

        super().__init__(parent)

    @property
    def config(self) -> Observable:
        return self._config_obs

    @property
    def scenario(self) -> Scenario:
        return self._scenario

    def set_simulation_length(self, steps: int):
        self._config.simulation_steps = steps

    @scenario.setter
    def scenario(self, scenario: Scenario):
        self._scenario = scenario

    def convert(self, output_folder) -> bool:
        """
        simulates the current scenario and returns the simulated version
        """
        if not self._scenario:
            error(self, "No Scenario loaded, load a valid CommonRoad scenario to simulate")
            return False

        self.waiting_msg = WaitingDialog()
        self.worker: ConversionWorker = ConversionWorker(
            self._scenario, self._config, output_folder
        )
        self.worker.finished.connect(self.simulation_done)
        self.worker.start()

        # show Info box, telling user to wait for the simulation to finish
        # self.waiting_msg.information(self, "SUMO Simulation", "Simulating...",
        #                              QMessageBox.StandardButton.Ok)
        self.waiting_msg.exec()

        return True

    def simulate(self) -> bool:
        """
        simulates the current scenario and returns the simulated version
        """
        if not self._scenario:
            error(self, "No Scenario loaded, load a valid CommonRoad scenario to simulate")
            return False

        self.waiting_msg = WaitingDialog()
        self.worker: SimulationWorker = SimulationWorker(
            self._scenario, self._config, self._output_folder
        )
        self.worker.finished.connect(self.simulation_done)
        self.worker.start()

        # show Info box, telling user to wait for the simulation to finish
        # self.waiting_msg.information(self, "SUMO Simulation", "Simulating...",
        #                             QMessageBox.StandardButton.Ok)
        self.waiting_msg.exec()

        return True

    def simulation_done(self):
        self.waiting_msg.close_window = True
        self.waiting_msg.close()
        if not self.worker.error:
            self.simulated_scenario.value = self.worker.simulated_scenario
        else:
            QMessageBox.critical(
                None,
                "SUMO Simulation",
                "The SUMO Simulation encountered an error:\n{}".format(self.worker.error),
                QMessageBox.StandardButton.Ok,
            )
