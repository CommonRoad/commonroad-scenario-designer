# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_simulate.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt6 import QtCore, QtWidgets


class Ui_sumo_simulate(object):
    def setupUi(self, sumo_simulate):
        sumo_simulate.setObjectName("sumo_simulate")
        sumo_simulate.resize(291, 354)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(sumo_simulate.sizePolicy().hasHeightForWidth())
        sumo_simulate.setSizePolicy(sizePolicy)
        sumo_simulate.setMinimumSize(QtCore.QSize(0, 0))
        sumo_simulate.setMaximumSize(QtCore.QSize(16777215, 16777215))
        sumo_simulate.setWindowTitle("")
        sumo_simulate.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(sumo_simulate)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(sumo_simulate)
        self.frame.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setAutoFillBackground(False)
        self.frame.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.doubleSpinBox_dt = QtWidgets.QDoubleSpinBox(self.frame)
        self.doubleSpinBox_dt.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox_dt.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox_dt.setSizePolicy(sizePolicy)
        self.doubleSpinBox_dt.setBaseSize(QtCore.QSize(100, 0))
        self.doubleSpinBox_dt.setLocale(
            QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
        )
        self.doubleSpinBox_dt.setMaximum(9999999999999.0)
        self.doubleSpinBox_dt.setProperty("value", 0.1)
        self.doubleSpinBox_dt.setObjectName("doubleSpinBox_dt")
        self.gridLayout.addWidget(self.doubleSpinBox_dt, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.spinBox_presimulation_steps = QtWidgets.QSpinBox(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.spinBox_presimulation_steps.sizePolicy().hasHeightForWidth()
        )
        self.spinBox_presimulation_steps.setSizePolicy(sizePolicy)
        self.spinBox_presimulation_steps.setBaseSize(QtCore.QSize(100, 0))
        self.spinBox_presimulation_steps.setMaximum(999999)
        self.spinBox_presimulation_steps.setProperty("value", 30)
        self.spinBox_presimulation_steps.setObjectName("spinBox_presimulation_steps")
        self.gridLayout.addWidget(self.spinBox_presimulation_steps, 1, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.frame)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.spinBox_simulation_steps = QtWidgets.QSpinBox(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox_simulation_steps.sizePolicy().hasHeightForWidth())
        self.spinBox_simulation_steps.setSizePolicy(sizePolicy)
        self.spinBox_simulation_steps.setBaseSize(QtCore.QSize(100, 0))
        self.spinBox_simulation_steps.setMaximum(999999999)
        self.spinBox_simulation_steps.setProperty("value", 200)
        self.spinBox_simulation_steps.setObjectName("spinBox_simulation_steps")
        self.gridLayout.addWidget(self.spinBox_simulation_steps, 2, 1, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        spacerItem = QtWidgets.QSpacerItem(
            20, 180, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred
        )
        self.verticalLayout_2.addItem(spacerItem)
        self.pushButton_simulate = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_simulate.sizePolicy().hasHeightForWidth())
        self.pushButton_simulate.setSizePolicy(sizePolicy)
        self.pushButton_simulate.setObjectName("pushButton_simulate")
        self.verticalLayout_2.addWidget(self.pushButton_simulate)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(sumo_simulate)
        QtCore.QMetaObject.connectSlotsByName(sumo_simulate)

    def retranslateUi(self, sumo_simulate):
        _translate = QtCore.QCoreApplication.translate
        self.label.setToolTip(
            _translate("sumo_simulate", "length of simulation step of the interface")
        )
        self.label.setText(_translate("sumo_simulate", "dt"))
        self.label_2.setToolTip(
            _translate(
                "sumo_simulate", "number of time steps before simulation with ego vehicle starts"
            )
        )
        self.label_2.setText(_translate("sumo_simulate", "Presimulation_steps"))
        self.label_3.setToolTip(
            _translate("sumo_simulate", "number of simulated (and synchronized) time steps")
        )
        self.label_3.setText(_translate("sumo_simulate", "Simulation_steps"))
        self.pushButton_simulate.setText(_translate("sumo_simulate", "Simulate"))
