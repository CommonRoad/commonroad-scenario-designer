from crmapconverter.io.scenario_designer.GUI_resources.Setting import Ui_SettingUi
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class Setting(Ui_SettingUi):
    """The Setting UI of CR Scenario Designer."""

    def __init__(self):
        """

        :param:
        """

        self.window = QDialog()
        self.ui = Ui_SettingUi()
        self.ui.setupUi(self.window )
        self.window.show()

