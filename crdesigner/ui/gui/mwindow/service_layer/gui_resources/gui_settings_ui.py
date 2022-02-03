# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(300, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 956, 1182))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        #self.gridLayout_2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        #self.gridLayout_2.setObjectName("gridLayout_2")

        self.formLayout_2 = QtWidgets.QFormLayout(self.scrollAreaWidgetContents)
        self.formLayout_2.setObjectName("form_2")

        self.label_autofocus = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_autofocus.setObjectName("label_autofocus")
        
        self.chk_autofocus = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_autofocus.setText("")
        self.chk_autofocus.setObjectName("chk_autofocus")
        self.formLayout_2.addRow(self.label_autofocus, self.chk_autofocus)
        # obstacle options
        self.label_obstacle = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_obstacle.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_obstacle.setObjectName("label_obstacles")
        self.formLayout_2.addRow(self.label_obstacle)

        self.label_draw_trajectory = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_trajectory.setObjectName("label_draw_trajectory")
        
        self.chk_draw_trajectory = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_trajectory.setText("")
        self.chk_draw_trajectory.setObjectName("chk_draw_trajectory")
        self.formLayout_2.addRow(self.label_draw_trajectory, self.chk_draw_trajectory)

        self.label_draw_label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_label.setObjectName("label_draw_label")
        
        self.chk_draw_label = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_label.setText("")
        self.chk_draw_label.setObjectName("chk_draw_label")
        self.formLayout_2.addRow(self.label_draw_label, self.chk_draw_label)

        self.label_draw_obstacle_icon = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_obstacle_icon.setObjectName("label_draw_obstacle_icon")
        
        self.chk_draw_obstacle_icon = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_obstacle_icon.setText("")
        self.chk_draw_obstacle_icon.setObjectName("chk_draw_obstacle_icon")
        self.formLayout_2.addRow(self.label_draw_obstacle_icon, self.chk_draw_obstacle_icon)

        self.label_draw_obstacle_direction = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_obstacle_direction.setObjectName("label_draw_obstacle_direction")
        
        self.chk_draw_obstacle_direction = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_obstacle_direction.setText("")
        self.chk_draw_obstacle_direction.setObjectName("chk_draw_obstacle_direction")
        self.formLayout_2.addRow(self.label_draw_obstacle_direction, self.chk_draw_obstacle_direction)

        self.label_draw_obstacle_signal = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_obstacle_signal.setObjectName("label_draw_obstacle_signal")
        
        self.chk_draw_obstacle_signal = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_obstacle_signal.setText("")
        self.chk_draw_obstacle_signal.setObjectName("chk_draw_obstacle_signal")
        self.formLayout_2.addRow(self.label_draw_obstacle_signal, self.chk_draw_obstacle_signal)
        # intersection options
        self.label_intersection = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_intersection.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_intersection.setObjectName("label_intersections")
        self.formLayout_2.addRow(self.label_intersection)

        self.label_draw_intersection = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_intersection.setObjectName("label_draw_intersection")
        
        self.chk_draw_intersection = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_intersection.setText("")
        self.chk_draw_intersection.setObjectName("chk_dintersection")
        self.formLayout_2.addRow(self.label_draw_intersection, self.chk_draw_intersection)

        self.label_draw_incoming_lanelet = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_incoming_lanelet.setObjectName("label_draw_incoming_lanelet")
        
        self.chk_draw_incoming_lanelet = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_incoming_lanelet.setText("")
        self.chk_draw_incoming_lanelet.setObjectName("chk_dincoming_lanelet")
        self.formLayout_2.addRow(self.label_draw_incoming_lanelet, self.chk_draw_incoming_lanelet)

        self.label_draw_successors = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_successors.setObjectName("label_draw_successors")
        
        self.chk_draw_successors = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_successors.setText("")
        self.chk_draw_successors.setObjectName("chk_dsuccessors")
        self.formLayout_2.addRow(self.label_draw_successors, self.chk_draw_successors)

        self.label_draw_intersection_label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_intersection_label.setObjectName("label_draw_intersection_label")
        
        self.chk_draw_intersection_label = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_intersection_label.setText("")
        self.chk_draw_intersection_label.setObjectName("chk_dintersection_label")
        self.formLayout_2.addRow(self.label_draw_intersection_label, self.chk_draw_intersection_label)
       
        # occupancy options
        self.label_occupancy = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_occupancy.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_occupancy.setObjectName("label_occupancy")
        self.formLayout_2.addRow(self.label_occupancy)

        self.label_draw_occupancy = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_occupancy.setObjectName("label_draw_occupancy")
        
        self.chk_draw_occupancy = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_occupancy.setText("")
        self.chk_draw_occupancy.setObjectName("chk_occupancy")
        self.formLayout_2.addRow(self.label_draw_occupancy, self.chk_draw_occupancy)
        # traffic sign options
        self.label_traffic_sign = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_traffic_sign.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_traffic_sign.setObjectName("label_traffic_sign")
        self.formLayout_2.addRow(self.label_traffic_sign)

        self.label_draw_traffic_sign = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_traffic_sign.setObjectName("label_draw_traffic_sign")
        
        self.chk_draw_traffic_sign = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_traffic_sign.setText("")
        self.chk_draw_traffic_sign.setObjectName("chk_traffic_sign")
        self.formLayout_2.addRow(self.label_draw_traffic_sign, self.chk_draw_traffic_sign)
        # traffic light options
        self.label_traffic_light = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_traffic_light.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_traffic_light.setObjectName("label_traffic_light")
        self.formLayout_2.addRow(self.label_traffic_light)

        self.label_draw_traffic_light = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_draw_traffic_light.setObjectName("label_draw_traffic_light")
        
        self.chk_draw_traffic_light = QtWidgets.QCheckBox(self.scrollAreaWidgetContents)
        self.chk_draw_traffic_light.setText("")
        self.chk_draw_traffic_light.setObjectName("chk_traffic_light")
        self.formLayout_2.addRow(self.label_draw_traffic_light, self.chk_draw_traffic_light)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_3.setObjectName("gridLayout_3")
        # self.botton_restore_defaults = QtWidgets.QPushButton(self.frame)
        # self.botton_restore_defaults.setObjectName("botton_restore_defaults")
        # self.gridLayout_3.addWidget(self.botton_restore_defaults, 0, 0, 1, 1)
        self.botton_close = QtWidgets.QPushButton(self.frame)
        self.botton_close.setObjectName("botton_close")
        self.gridLayout_3.addWidget(self.botton_close, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.frame)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 990, 23))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "GUI Settings"))

        self.label_autofocus.setText(_translate("MainWindow", "Autofocus"))
        self.label_draw_trajectory.setText(_translate("MainWindow", "Draw trajectory"))
        self.label_draw_intersection.setText(_translate("MainWindow", "Draw intersections"))
        self.label_draw_label.setText(_translate("MainWindow", "Draw obstacle labels"))
        self.label_draw_obstacle_icon.setText(_translate("MainWindow", "Draw obstacle icons"))
        self.label_draw_obstacle_direction.setText(_translate("MainWindow", "Draw obstacle direction"))
        self.label_draw_obstacle_signal.setText(_translate("MainWindow", "Draw obstacle signals"))
        self.label_draw_occupancy.setText(_translate("MainWindow", "Draw occupancy"))
        self.label_draw_traffic_sign.setText(_translate("MainWindow", "Draw traffic signs"))
        self.label_draw_traffic_light.setText(_translate("MainWindow", "Draw traffic lights"))
        self.label_draw_incoming_lanelet.setText(_translate("MainWindow", "Draw incoming lanelets"))
        self.label_draw_successors.setText(_translate("MainWindow", "Draw successor lanelets"))
        self.label_draw_intersection_label.setText(_translate("MainWindow", "Draw intersection labels"))
        

        self.label_obstacle.setText(_translate("MainWindow", "Obstacle visualization"))
        self.label_intersection.setText(_translate("MainWindow", "Intersection visualization"))
        self.label_occupancy.setText(_translate("MainWindow", "Occupancy visualization"))
        self.label_traffic_sign.setText(_translate("MainWindow", "Traffic sign visualization"))
        self.label_traffic_light.setText(_translate("MainWindow", "Traffic light visualization"))

        self.label_autofocus.setToolTip(_translate("MainWindow", 
            "activate zoom reset when selecting an item from the list"))
        
        # self.botton_restore_defaults.setText(_translate("MainWindow", "Restore Defaults"))
        self.botton_close.setText(_translate("MainWindow", "Appy and close"))

