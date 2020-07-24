import uuid
import os
import pathlib
import logging

from commonroad.scenario.scenario import Scenario

from crmapconverter.io.V3_0.GUI_resources.Sumo_simulate import Ui_sumo_simulate
from crmapconverter.io.V3_0.errors import error, warning
from crmapconverter.io.V3_0.observable import Observable

from crmapconverter.sumo_map.config import SumoConfig
from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from sumocr.interface.sumo_simulation import SumoSimulation

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread


class SimulationWorker(QThread):
    def __init__(self, scenario, config, output_folder):
        super(SimulationWorker, self).__init__()
        self.scenario = scenario
        self.config = config
        self.output_folder = output_folder
        self.simulated_scenario = None
        self.error = None

    def run(self):
        try:
            # convert scenario to SUMO
            wrapper = CR2SumoMapConverter(self.scenario.lanelet_network,
                                          self.config)
            wrapper.convert_to_net_file(self.output_folder)

            simulation = SumoSimulation()
            simulation.initialize(self.config, wrapper)

            for _ in range(self.config.simulation_steps):
                simulation.simulate_step()
            simulation.stop()

            self.simulated_scenario = simulation.commonroad_scenarios_all_time_steps(
            )
        except Exception as e:
            # log error and save it for display to the user
            logging.error(e)
            self.error = e


class WaitingDialog(QtWidgets.QDialog):
    def __init__(self):
        super(WaitingDialog, self).__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.textBrowser = QtWidgets.QTextBrowser()
        self.textBrowser.setText("Simulating, plase wait ...")
        self.layout.addWidget(self.textBrowser)

        self.close_window = False

        def closeEvent(self, event):
            if self.close_window:
                super(WaitingDialog, self).closeEvent(event)
            else:
                event.ignore()


class SUMOSimulation(QWidget, Ui_sumo_simulate):
    def __init__(self):
        # set random uuid as name for the scneario files
        self._config = SumoConfig.from_scenario_name(str(uuid.uuid4()))
        self._config_obs = Observable(self._config)

        def set_config(config):
            self._config = config

        self._config_obs.subscribe(set_config)
        self._scenario: Scenario = None

        # observable giving the simulated scenario once done
        self.simulated_scenario = Observable(None)

        # set path to chache folder and creat it if not already existing
        self._output_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "tmp"))
        pathlib.Path(self._output_folder).mkdir(parents=True, exist_ok=True)

        super(SUMOSimulation, self).__init__()
        self.setupUi(self)
        self._connect_events()

    @property
    def config(self) -> Observable:
        return self._config_obs

    @property
    def scenario(self) -> Scenario:
        return self._scenario

    @scenario.setter
    def scenario(self, scenario: Scenario):
        self._scenario = scenario

    def _connect_events(self) -> None:
        """
        Connecting valueChanged events of the SpinBoxes to the SumoConfig
        """

        # window.btn_restore_defaults.clicked.connect(self.restore_default_button)
        # window.btn_close.clicked.connect(self.close_button)

        self._update_ui_values()

        def set_dt(value):
            self.config.dt = value
            self._config_obs.value = self._config

        def set_presimulation_steps(value):
            self.config.presimulation_steps = value
            self._config_obs.value = self._config

        def set_simulation_steps(value):
            self.config.simulation_steps = value
            self._config_obs.value = self._config

        self.doubleSpinBox_dt.valueChanged.connect(set_dt)
        self.spinBox_presimulation_steps.valueChanged.connect(
            set_presimulation_steps)
        self.spinBox_simulation_steps.valueChanged.connect(
            set_simulation_steps)
        self.pushButton_simulate.clicked.connect(self.simulate)

    def _update_ui_values(self) -> None:
        """
        sets the values of the settings window to the current values of the SumoConfig file

        :return: None
        """
        # example code:
        # window.le_benchmark_id.setText(config.BENCHMARK_ID)
        # window.sb_compression_threshold.setValue(config.COMPRESSION_THRESHOLD)
        # window.chk_delete_short_edges.setChecked(config.DELETE_SHORT_EDGES)

        # load values from config
        self.doubleSpinBox_dt.setValue(self._config.dt)
        self.spinBox_presimulation_steps.setValue(
            self._config.presimulation_steps)
        self.spinBox_simulation_steps.setValue(self._config.simulation_steps)

    def simulate(self) -> bool:
        """
        simulates the current scenario and returns the simulated version
        """
        if not self._scenario:
            error(
                self,
                "No Scenario loaded, load a valid commonroad scenario to simulate"
            )
            return False

        self.waiting_msg = WaitingDialog()
        self.worker: SimulationWorker = SimulationWorker(
            self._scenario, self._config, self._output_folder)
        self.worker.finished.connect(self.simulation_done)
        self.worker.start()

        # show Info box, telling user to wait for the simulation to finish
        # self.waiting_msg.information(self, "SUMO Simulation", "Simulating...",
        #                              QMessageBox.Ok)
        self.waiting_msg.exec_()

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
                "The SUMO Simulation encountered an error:\n{}".format(
                    self.worker.error),
                QMessageBox.Ok,
            )

    # def save_to_config(self) -> None:
    #     """
    #     saves the values in the settings window to config.py

    #     :return: None
    #     """
    #     # example code:
    #     # config.BENCHMARK_ID = window.le_benchmark_id.text()
    #     # config.AERIAL_IMAGES = swindow.chb_aerial.isChecked()
    #     # config.DOWNLOAD_EDGE_LENGTH = window.sb_donwload_radius.value()
    #     return

    def close_button(self) -> None:
        """
        closes settings without saving

        :return: None
        """
        # and close
