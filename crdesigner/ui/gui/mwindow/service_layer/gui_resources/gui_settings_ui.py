# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Sumo_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets, QtGui
from crdesigner.ui.gui.mwindow.service_layer.gui_resources.size_policies import create_size_policy_for_settings_elements

class UIGUISettings:

    def __init__(self, h: int, c, wm, wf: int, f):
        self.columns = c
        self.height = int(h)
        self.widthm = int(wm * f)
        self.widthf = int(wf * f)
        self.factor = int(f)
    
    def setupUi(self, tabWidget, ):
        self.scrollArea = QtWidgets.QScrollArea(tabWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaLayout = QtWidgets.QGridLayout(self.scrollArea)

        #single content widget for adding to the scrollArea
        #otherwise scrolling is disabled
        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setObjectName("ContentWrapper")
        self.HBoxLayout = QtWidgets.QHBoxLayout(self.contentWrapper)
        self.HBoxLayout.setObjectName("gridLayout")
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignTop)

        #creating columns
        self.content = []
        self.formLayout = []
        for i in range(self.columns):
            self.content.append(QtWidgets.QWidget(self.contentWrapper))
            self.content[i].setObjectName("scrollAreaWidgetContents_" + str(i))
            self.formLayout.append(QtWidgets.QFormLayout(self.content[i]))
            self.formLayout[i].setObjectName("form_" + str(i))
            self.content[i].setMinimumSize(860 * self.factor, 820)
            self.content[i].setLayout(self.formLayout[i])
            self.HBoxLayout.addWidget(self.content[i])

        column = 0

        #appearance
        self.label_appearance = QtWidgets.QLabel(self.content[column])
        self.label_appearance.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_appearance.setObjectName("label_appearances")
        self.formLayout[column].addRow(self.label_appearance)
        

        #colorscheme
        self.hl_darkmode = QtWidgets.QHBoxLayout()
        self.hl_darkmode.setObjectName("hl_darkmode")
        self.label_darkmode = QtWidgets.QLabel(self.content[column])
        self.label_darkmode.setObjectName("label_colorscheme")
        self.label_darkmode.setMinimumSize(self.widthf, self.height)
        self.chk_darkmode = QtWidgets.QCheckBox(self.content[column])
        self.chk_darkmode.setText("")
        self.chk_darkmode.setObjectName("chk_darkmode")
        self.chk_darkmode.setMinimumSize(self.widthm, self.height)
        self.hl_darkmode.addWidget(self.label_darkmode)
        self.hl_darkmode.addWidget(self.chk_darkmode)
        self.hl_darkmode.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hl_darkmode)

        # axis_visible
        self.hL_axis_visible = QtWidgets.QHBoxLayout()
        self.hL_axis_visible.setObjectName("hL_axis_visible")
        self.label_axis_visible = QtWidgets.QLabel(self.content[column])
        self.label_axis_visible.setObjectName("label_axis_visible")
        self.label_axis_visible.setMinimumSize(self.widthf, self.height)
        self.cmb_axis_visible = QtWidgets.QComboBox(self.content[column])
        self.cmb_axis_visible.addItem('All')
        self.cmb_axis_visible.addItem('Left/ Bottom')
        self.cmb_axis_visible.addItem('None')
        self.cmb_axis_visible.setObjectName("cmb_axis_visible")
        self.cmb_axis_visible.setMinimumSize(self.widthm, self.height)
        self.cmb_axis_visible.setSizePolicy(create_size_policy_for_settings_elements())
        self.hL_axis_visible.addWidget(self.label_axis_visible)
        self.hL_axis_visible.addWidget(self.cmb_axis_visible)
        self.hL_axis_visible.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_axis_visible)

        #showing legend
        self.hl_legend = QtWidgets.QHBoxLayout()
        self.hl_legend.setObjectName("hl_legend")
        self.label_legend = QtWidgets.QLabel(self.content[column])
        self.label_legend.setObjectName("label_legend")
        self.label_legend.setMinimumSize(self.widthf, self.height)
        self.chk_legend = QtWidgets.QCheckBox(self.content[column])
        self.chk_legend.setText("")
        self.chk_legend.setObjectName("chk_legend")
        self.chk_legend.setMinimumSize(self.widthm, self.height)
        self.hl_legend.addWidget(self.label_legend)
        self.hl_legend.addWidget(self.chk_legend)
        self.hl_legend.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hl_legend)

        # obstacle options
        self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_obstacle = QtWidgets.QLabel(self.content[column])
        self.label_obstacle.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_obstacle.setObjectName("label_obstacles")
        self.formLayout[column].addRow(self.label_obstacle)

        # draw_trajectory
        self.hL_1 = QtWidgets.QHBoxLayout()
        self.hL_1.setObjectName("hL_1")
        self.label_draw_trajectory = QtWidgets.QLabel(self.content[column])
        self.label_draw_trajectory.setObjectName("label_draw_trajectory")
        self.label_draw_trajectory.setMinimumSize(self.widthf, self.height)
        self.chk_draw_trajectory = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_trajectory.setText("")
        self.chk_draw_trajectory.setObjectName("chk_draw_trajectory")
        self.chk_draw_trajectory.setMinimumSize(self.widthm, self.height)
        self.hL_1.addWidget(self.label_draw_trajectory)
        self.hL_1.addWidget(self.chk_draw_trajectory)
        self.hL_1.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_1)

        #draw_label
        self.hL_2 = QtWidgets.QHBoxLayout()
        self.hL_2.setObjectName("hL_2")
        self.label_draw_label = QtWidgets.QLabel(self.content[column])
        self.label_draw_label.setObjectName("label_draw_label")
        self.label_draw_label.setMinimumSize(self.widthf, self.height)
        self.chk_draw_label = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_label.setText("")
        self.chk_draw_label.setObjectName("chk_draw_label")
        self.chk_draw_label.setMinimumSize(self.widthm, self.height)
        self.hL_2.addWidget(self.label_draw_label)
        self.hL_2.addWidget(self.chk_draw_label)
        self.hL_2.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_2)

        #draw_obstacle_icon
        self.hL_3 = QtWidgets.QHBoxLayout()
        self.hL_3.setObjectName("hL_3")
        self.label_draw_obstacle_icon = QtWidgets.QLabel(self.content[column])
        self.label_draw_obstacle_icon.setObjectName("label_draw_obstacle_icon")
        self.label_draw_obstacle_icon.setMinimumSize(self.widthf, self.height)
        self.chk_draw_obstacle_icon = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_obstacle_icon.setText("")
        self.chk_draw_obstacle_icon.setObjectName("chk_draw_obstacle_icon")
        self.chk_draw_obstacle_icon.setMinimumSize(self.widthm, self.height)
        self.hL_3.addWidget(self.label_draw_obstacle_icon)
        self.hL_3.addWidget(self.chk_draw_obstacle_icon)
        self.hL_3.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_3)

        #draw_obstacle_direction
        self.hL_4 = QtWidgets.QHBoxLayout()
        self.hL_4.setObjectName("hL_4")
        self.label_draw_obstacle_direction = QtWidgets.QLabel(self.content[column])
        self.label_draw_obstacle_direction.setObjectName("label_draw_obstacle_direction")
        self.label_draw_obstacle_direction.setMinimumSize(self.widthf, self.height)
        self.chk_draw_obstacle_direction = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_obstacle_direction.setText("")
        self.chk_draw_obstacle_direction.setObjectName("chk_draw_obstacle_direction")
        self.chk_draw_obstacle_direction.setMinimumSize(self.widthm, self.height)
        self.hL_4.addWidget(self.label_draw_obstacle_direction)
        self.hL_4.addWidget(self.chk_draw_obstacle_direction)
        self.hL_4.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_4)

        # draw_obstacle_signal
        self.hL_5 = QtWidgets.QHBoxLayout()
        self.hL_5.setObjectName("hL_5")
        self.label_draw_obstacle_signal = QtWidgets.QLabel(self.content[column])
        self.label_draw_obstacle_signal.setObjectName("label_draw_obstacle_signal")
        self.label_draw_obstacle_signal.setMinimumSize(self.widthf, self.height)
        self.chk_draw_obstacle_signal = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_obstacle_signal.setText("")
        self.chk_draw_obstacle_signal.setObjectName("chk_draw_obstacle_signal")
        self.chk_draw_obstacle_signal.setMinimumSize(self.widthm, self.height)
        self.hL_5.addWidget(self.label_draw_obstacle_signal)
        self.hL_5.addWidget(self.chk_draw_obstacle_signal)
        self.hL_5.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_5)

        # intersection options
        self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_intersection = QtWidgets.QLabel(self.content[column])
        self.label_intersection.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_intersection.setObjectName("label_intersections")
        self.formLayout[column].addRow(self.label_intersection)

        # draw_intersection
        self.hL_6 = QtWidgets.QHBoxLayout()
        self.hL_6.setObjectName("hL_6")
        self.label_draw_intersection = QtWidgets.QLabel(self.content[column])
        self.label_draw_intersection.setObjectName("label_draw_intersection")
        self.label_draw_intersection.setMinimumSize(self.widthf, self.height)
        self.chk_draw_intersection = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_intersection.setText("")
        self.chk_draw_intersection.setObjectName("chk_dintersection")
        self.chk_draw_intersection.setMinimumSize(self.widthm, self.height)
        self.hL_6.addWidget(self.label_draw_intersection)
        self.hL_6.addWidget(self.chk_draw_intersection)
        self.hL_6.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_6)

        # draw_incoming_lanelet
        self.hL_7 = QtWidgets.QHBoxLayout()
        self.hL_7.setObjectName("hL_7")
        self.label_draw_incoming_lanelet = QtWidgets.QLabel(self.content[column])
        self.label_draw_incoming_lanelet.setObjectName("label_draw_incoming_lanelet")
        self.label_draw_incoming_lanelet.setMinimumSize(self.widthf, self.height)
        self.chk_draw_incoming_lanelet = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_incoming_lanelet.setText("")
        self.chk_draw_incoming_lanelet.setObjectName("chk_dincoming_lanelet")
        self.chk_draw_incoming_lanelet.setMinimumSize(self.widthm, self.height)
        self.hL_7.addWidget(self.label_draw_incoming_lanelet)
        self.hL_7.addWidget(self.chk_draw_incoming_lanelet)
        self.hL_7.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_7)

        # draw_successors
        self.hL_8 = QtWidgets.QHBoxLayout()
        self.hL_8.setObjectName("hL_8")
        self.label_draw_successors = QtWidgets.QLabel(self.content[column])
        self.label_draw_successors.setObjectName("label_draw_successors")
        self.label_draw_successors.setMinimumSize(self.widthf, self.height)
        self.chk_draw_successors = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_successors.setText("")
        self.chk_draw_successors.setObjectName("chk_dsuccessors")
        self.chk_draw_successors.setMinimumSize(self.widthm, self.height)
        self.hL_8.addWidget(self.label_draw_successors)
        self.hL_8.addWidget(self.chk_draw_successors)
        self.hL_8.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_8)

        # draw_intersection_label
        self.hL_9 = QtWidgets.QHBoxLayout()
        self.hL_9.setObjectName("hL_9")
        self.label_draw_intersection_label = QtWidgets.QLabel(self.content[column])
        self.label_draw_intersection_label.setObjectName("label_draw_intersection_label")
        self.label_draw_intersection_label.setMinimumSize(self.widthf, self.height)
        self.chk_draw_intersection_label = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_intersection_label.setText("")
        self.chk_draw_intersection_label.setObjectName("chk_dintersection_label")
        self.chk_draw_intersection_label.setMinimumSize(self.widthm, self.height)
        self.hL_9.addWidget(self.label_draw_intersection_label)
        self.hL_9.addWidget(self.chk_draw_intersection_label)
        self.hL_9.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_9)

        column = 1

        # other options
        #self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_other = QtWidgets.QLabel(self.content[column])
        self.label_other.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.label_other.setObjectName("label_other")
        self.formLayout[column].addRow(self.label_other)

        # autofocus
        # horizontal layout for three widgets (always same structure)
        self.hL_0 = QtWidgets.QHBoxLayout()
        self.hL_0.setObjectName("hL_0")
        self.label_autofocus = QtWidgets.QLabel(self.content[column])
        self.label_autofocus.setObjectName("label_autofocus")
        self.label_autofocus.setMinimumSize(self.widthf, self.height)
        self.chk_autofocus = QtWidgets.QCheckBox(self.content[column])
        self.chk_autofocus.setText("")
        self.chk_autofocus.setObjectName("chk_autofocus")
        self.chk_autofocus.setMinimumSize(self.widthm, self.height)
        self.hL_0.addWidget(self.label_autofocus)
        self.hL_0.addWidget(self.chk_autofocus)
        # third widget to seperate columns
        self.hL_0.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_0)

        # draw_occupancy
        self.hL_10 = QtWidgets.QHBoxLayout()
        self.hL_10.setObjectName("hL_10")
        self.label_draw_occupancy = QtWidgets.QLabel(self.content[column])
        self.label_draw_occupancy.setObjectName("label_draw_occupancy")
        self.label_draw_occupancy.setMinimumSize(self.widthf, self.height)
        self.chk_draw_occupancy = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_occupancy.setText("")
        self.chk_draw_occupancy.setObjectName("chk_occupancy")
        self.formLayout[column].addRow(self.label_draw_occupancy, self.chk_draw_occupancy)
        self.hL_10.addWidget(self.label_draw_occupancy)
        self.hL_10.addWidget(self.chk_draw_occupancy)
        self.hL_10.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_10)

        # draw_traffic_sign
        self.hL_11 = QtWidgets.QHBoxLayout()
        self.hL_11.setObjectName("hL_11")
        self.label_draw_traffic_sign = QtWidgets.QLabel(self.content[column])
        self.label_draw_traffic_sign.setObjectName("label_draw_traffic_sign")
        self.label_draw_traffic_sign.setMinimumSize(self.widthf, self.height)
        self.chk_draw_traffic_sign = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_traffic_sign.setText("")
        self.chk_draw_traffic_sign.setObjectName("chk_traffic_sign")
        self.formLayout[column].addRow(self.label_draw_traffic_sign, self.chk_draw_traffic_sign)
        self.hL_11.addWidget(self.label_draw_traffic_sign)
        self.hL_11.addWidget(self.chk_draw_traffic_sign)
        self.hL_11.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_11)
        
        # traffic light options
        # self.label_traffic_light = QtWidgets.QLabel(self.content[column])
        # self.label_traffic_light.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        # self.label_traffic_light.setObjectName("label_traffic_light")
        # self.formLayout[column].addRow(self.label_traffic_light)

        # draw_traffic_light
        self.hL_12 = QtWidgets.QHBoxLayout()
        self.hL_12.setObjectName("hL_12")
        self.label_draw_traffic_light = QtWidgets.QLabel(self.content[column])
        self.label_draw_traffic_light.setObjectName("label_draw_traffic_light")
        self.label_draw_traffic_light.setMinimumSize(self.widthf, self.height)
        self.chk_draw_traffic_light = QtWidgets.QCheckBox(self.content[column])
        self.chk_draw_traffic_light.setText("")
        self.chk_draw_traffic_light.setObjectName("chk_traffic_light")
        self.formLayout[column].addRow(self.label_draw_traffic_light, self.chk_draw_traffic_light)
        self.hL_12.addWidget(self.label_draw_traffic_light)
        self.hL_12.addWidget(self.chk_draw_traffic_light)
        self.hL_12.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_12)

        self.hL_13 = QtWidgets.QHBoxLayout()
        self.hL_13.setObjectName("hL_13")
        self.label_bing_maps_key = QtWidgets.QLabel(self.content[column])
        self.label_bing_maps_key.setObjectName("label_bing_maps_key")
        self.label_bing_maps_key.setMinimumSize(self.widthf, self.height)
        self.lineed_bing_maps_key = QtWidgets.QLineEdit(self.content[column])
        self.lineed_bing_maps_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineed_bing_maps_key.setSizePolicy(create_size_policy_for_settings_elements())
        self.lineed_bing_maps_key.setMinimumSize(self.widthm, self.height)
        self.lineed_bing_maps_key.setObjectName("lineed_bing_maps_key")
        self.formLayout[column].addRow(self.label_bing_maps_key, self.lineed_bing_maps_key)
        self.hL_13.addWidget(self.label_bing_maps_key)
        self.hL_13.addWidget(self.lineed_bing_maps_key)
        self.hL_13.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_13)

        self.hL_14 = QtWidgets.QHBoxLayout()
        self.hL_14.setObjectName("hL_14")
        self.label_ldbv_username = QtWidgets.QLabel(self.content[column])
        self.label_ldbv_username.setObjectName("label_ldbv_username")
        self.label_ldbv_username.setMinimumSize(self.widthf, self.height)
        self.lineed_ldbv_username = QtWidgets.QLineEdit(self.content[column])
        self.lineed_ldbv_username.setSizePolicy(create_size_policy_for_settings_elements())
        self.lineed_ldbv_username.setMinimumSize(self.widthm, self.height)
        self.lineed_ldbv_username.setObjectName("lineed_ldbv_username")
        self.formLayout[column].addRow(self.label_ldbv_username, self.lineed_ldbv_username)
        self.hL_14.addWidget(self.label_ldbv_username)
        self.hL_14.addWidget(self.lineed_ldbv_username)
        self.hL_14.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_14)

        self.hL_15 = QtWidgets.QHBoxLayout()
        self.hL_15.setObjectName("hL_15")
        self.label_ldbv_password = QtWidgets.QLabel(self.content[column])
        self.label_ldbv_password.setObjectName("label_ldbv_password")
        self.label_ldbv_password.setMinimumSize(self.widthf, self.height)
        self.lineed_ldbv_password = QtWidgets.QLineEdit(self.content[column])
        self.lineed_ldbv_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lineed_ldbv_password.setSizePolicy(create_size_policy_for_settings_elements())
        self.lineed_ldbv_password.setMinimumSize(self.widthm, self.height)
        self.lineed_ldbv_password.setObjectName("lineed_ldbv_password")
        self.formLayout[column].addRow(self.label_ldbv_password, self.lineed_ldbv_password)
        self.hL_15.addWidget(self.label_ldbv_password)
        self.hL_15.addWidget(self.lineed_ldbv_password)
        self.hL_15.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_15)

        for i in range(self.columns):
            pass

        self.scrollArea.setWidget(self.contentWrapper)

        #self.retranslateUi(tabWidget)
        #QtCore.QMetaObject.connectSlotsByName(tabWidget)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate

        self.label_appearance.setText(_translate("MainWindow", "Appearance"))
        self.label_autofocus.setText(_translate("MainWindow", "Autofocus"))
        self.label_draw_trajectory.setText(_translate("MainWindow", "Draw trajectory"))
        self.label_axis_visible.setText(_translate("MainWindow", "Axis visibility"))
        self.label_darkmode.setText(_translate('MainWindow', 'Darkmode'))
        self.label_legend.setText(_translate('MainWindow', 'Legend'))
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
        self.label_bing_maps_key.setText(_translate("MainWindow", "Bing maps key"))
        self.label_ldbv_username.setText(_translate("MainWindow", "LDBV username"))
        self.label_ldbv_password.setText(_translate("MainWindow", "LDBV password"))

        self.label_obstacle.setText(_translate("MainWindow", "Obstacle visualization"))
        self.label_intersection.setText(_translate("MainWindow", "Intersection visualization"))
        self.label_other.setText(_translate("MainWindow", "Other"))

        self.label_autofocus.setToolTip(
            _translate("MainWindow", "activate zoom reset when selecting an item from the list"))

