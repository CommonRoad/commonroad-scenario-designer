# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings_ui.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

from crdesigner.ui.gui.mwindow.service_layer.gui_resources.size_policies import create_size_policy_for_settings_elements


class Ui_OSMSettings():

    def __init__(self, h, c, wm, wf, f):
        self.columns = c
        self.height = h
        self.widthm = int(wm * f)
        self.widthf = int(wf * f)
        self.factor = int(f)
    
    def setupUi(self, tabWidget):
        self.scrollArea = QtWidgets.QScrollArea(tabWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaLayout = QtWidgets.QGridLayout(self.scrollArea)

        # single content widget for adding to the scrollArea
        # otherwise scrolling is disabled
        self.contentWrapper = QtWidgets.QWidget()
        self.contentWrapper.setObjectName("ContentWrapper")
        self.HBoxLayout = QtWidgets.QHBoxLayout(self.contentWrapper)
        self.HBoxLayout.setObjectName("gridLayout")
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.HBoxLayout.setAlignment(QtCore.Qt.AlignTop)

        # creating columns
        self.content = []
        self.formLayout = []
        for i in range(self.columns):
            self.content.append(QtWidgets.QWidget(self.contentWrapper))
            self.content[i].setObjectName("scrollAreaWidgetContents_" + str(i))
            self.formLayout.append(QtWidgets.QFormLayout(self.content[i]))
            self.formLayout[i].setObjectName("form_" + str(i))
            self.content[i].setMinimumSize(860 * self.factor, 820)
            self.content[i].setLayout(self.formLayout[i])

        column = 0

        #Benchmark
        self.label_benchmark = QtWidgets.QLabel(self.content[column])
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_benchmark.setFont(font)
        self.label_benchmark.setObjectName("label_10")
        self.formLayout[column].addRow(self.label_benchmark)

        #benchmark_id
        # horizontal layout for three widgets (always same structure)
        self.hL_0 = QtWidgets.QHBoxLayout()
        self.hL_0.setObjectName("hL_0")
        self.le_benchmark_id = QtWidgets.QLineEdit(self.content[column])
        self.le_benchmark_id.setObjectName("le_benchmark_id")
        self.le_benchmark_id.setMinimumSize(self.widthm, self.height)
        self.le_benchmark_id.setSizePolicy(create_size_policy_for_settings_elements())

        self.label_benchmark_id = QtWidgets.QLabel(self.content[column])
        self.label_benchmark_id.setObjectName("label_11")
        self.label_benchmark_id.setMinimumSize(self.widthf, self.height)
        self.hL_0.addWidget(self.label_benchmark_id)
        self.hL_0.addWidget(self.le_benchmark_id)
        # third widget to seperate columns
        self.hL_0.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_0)

        #author
        self.hL_1 = QtWidgets.QHBoxLayout()
        self.hL_1.setObjectName("hL_1")
        self.label_author = QtWidgets.QLabel(self.content[column])
        self.label_author.setObjectName("label_12")
        self.label_author.setMinimumSize(self.widthf, self.height)
        self.le_author = QtWidgets.QLineEdit(self.content[column])
        self.le_author.setObjectName("le_author")
        self.le_author.setMinimumSize(self.widthm, self.height)
        self.le_author.setSizePolicy(create_size_policy_for_settings_elements())

        self.hL_1.addWidget(self.label_author)
        self.hL_1.addWidget(self.le_author)
        self.hL_1.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_1)
        
        #affiliation
        self.hL_2 = QtWidgets.QHBoxLayout()
        self.hL_2.setObjectName("hL_2")
        self.label_affiliation = QtWidgets.QLabel(self.content[column])
        self.label_affiliation.setObjectName("label_13")
        self.label_affiliation.setMinimumSize(self.widthf, self.height)
        self.le_affiliation = QtWidgets.QLineEdit(self.content[column])
        self.le_affiliation.setObjectName("le_affiliation")
        self.le_affiliation.setMinimumSize(self.widthm, self.height)
        self.le_affiliation.setSizePolicy(create_size_policy_for_settings_elements())

        self.hL_2.addWidget(self.label_affiliation)
        self.hL_2.addWidget(self.le_affiliation)
        self.hL_2.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_2)

        #source
        self.hL_3 = QtWidgets.QHBoxLayout()
        self.hL_3.setObjectName("hL_3")
        self.le_source = QtWidgets.QLineEdit(self.content[column])
        self.le_source.setObjectName("le_source")
        self.le_source.setMinimumSize(self.widthm, self.height)
        self.le_source.setSizePolicy(create_size_policy_for_settings_elements())

        self.label_source = QtWidgets.QLabel(self.content[column])
        self.label_source.setObjectName("label_14")
        self.label_source.setMinimumSize(self.widthf, self.height)
        self.hL_3.addWidget(self.label_source)
        self.hL_3.addWidget(self.le_source)
        self.hL_3.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_3)

        #tags
        self.hL_4 = QtWidgets.QHBoxLayout()
        self.hL_4.setObjectName("hL_4")
        self.le_tags = QtWidgets.QLineEdit(self.content[column])
        self.le_tags.setObjectName("le_tags")
        self.le_tags.setMinimumSize(self.widthm, self.height)
        self.le_tags.setSizePolicy(create_size_policy_for_settings_elements())

        self.label_tags = QtWidgets.QLabel(self.content[column])
        self.label_tags.setObjectName("label_15")
        self.label_tags.setMinimumSize(self.widthf, self.height)
        self.hL_4.addWidget(self.label_tags)
        self.hL_4.addWidget(self.le_tags)
        self.hL_4.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_4)

        #timestep_size
        self.hL_5 = QtWidgets.QHBoxLayout()
        self.hL_5.setObjectName("hL_5")
        self.label_timestep_size = QtWidgets.QLabel(self.content[column])
        self.label_timestep_size.setObjectName("label_16")
        self.label_timestep_size.setMinimumSize(self.widthf, self.height)
        self.sb_timestep_size = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_timestep_size.setMaximum(1000.0)
        self.sb_timestep_size.setObjectName("sb_time_step_size")
        self.sb_timestep_size.setMinimumSize(self.widthm, self.height)
        self.hL_5.addWidget(self.label_timestep_size)
        self.hL_5.addWidget(self.sb_timestep_size)
        self.hL_5.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_5)


        #scenario_settings
        self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_scenario_settings = QtWidgets.QLabel(self.content[column])
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_scenario_settings.setFont(font)
        self.label_scenario_settings.setObjectName("label_17")
        self.formLayout[column].addRow(self.label_scenario_settings)

        #load_tunnels
        self.hL_13 = QtWidgets.QHBoxLayout()
        self.hL_13.setObjectName("hL_13")
        self.chk_load_tunnels = QtWidgets.QCheckBox(self.content[column])
        self.chk_load_tunnels.setText("")
        self.chk_load_tunnels.setObjectName("chk_load_tunnels")
        self.label_load_tunnels = QtWidgets.QLabel(self.content[column])
        self.label_load_tunnels.setObjectName("label_18")
        self.label_load_tunnels.setMinimumSize(self.widthf, self.height)
        self.hL_13.addWidget(self.label_load_tunnels)
        self.hL_13.addWidget(self.chk_load_tunnels)
        self.hL_13.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_13)

        #contiguous
        self.hL_14 = QtWidgets.QHBoxLayout()
        self.hL_14.setObjectName("hL_14")
        self.chk_make_contiguous = QtWidgets.QCheckBox(self.content[column])
        self.chk_make_contiguous.setText("")
        self.chk_make_contiguous.setObjectName("chk_make_contiguous")
        self.label_make_contiguous = QtWidgets.QLabel(self.content[column])
        self.label_make_contiguous.setObjectName("label_19")
        self.label_make_contiguous.setMinimumSize(self.widthf, self.height)
        self.hL_14.addWidget(self.label_make_contiguous)
        self.hL_14.addWidget(self.chk_make_contiguous)
        self.hL_14.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_14)
    
        #split_corners
        self.hL_15 = QtWidgets.QHBoxLayout()
        self.hL_15.setObjectName("hL_15")
        self.chk_split_corners = QtWidgets.QCheckBox(self.content[column])
        self.chk_split_corners.setText("")
        self.chk_split_corners.setObjectName("chk_split_corners")
        self.label_split_corners = QtWidgets.QLabel(self.content[column])
        self.label_split_corners.setObjectName("label_21")
        self.label_split_corners.setMinimumSize(self.widthf, self.height)
        self.hL_15.addWidget(self.label_split_corners)
        self.hL_15.addWidget(self.chk_split_corners)
        self.hL_15.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_15)

        #osm_restrictions
        self.hL_16 = QtWidgets.QHBoxLayout()
        self.hL_16.setObjectName("hL_16")
        self.label_osm_restrictions = QtWidgets.QLabel(self.content[column])
        self.label_osm_restrictions.setObjectName("label_22")
        self.label_osm_restrictions.setMinimumSize(self.widthf, self.height)
        self.chk_osm_restrictions = QtWidgets.QCheckBox(self.content[column])
        self.chk_osm_restrictions.setText("")
        self.chk_osm_restrictions.setObjectName("chk_osm_restrictions")
        self.hL_16.addWidget(self.label_osm_restrictions)
        self.hL_16.addWidget(self.chk_osm_restrictions)
        self.hL_16.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_16)

        #street_types
        self.hL_17 = QtWidgets.QHBoxLayout()
        self.hL_17.setObjectName("hL_17")
        self.label_conv_street_types = QtWidgets.QLabel(self.content[column])
        self.label_conv_street_types.setObjectName("label_23")
        self.label_conv_street_types.setMinimumSize(self.widthf, self.height)
        self.btn_edit_street_types = QtWidgets.QPushButton(self.content[column])
        self.btn_edit_street_types.setObjectName("btn_edit_street_types")
        self.btn_edit_street_types.setMinimumSize(self.widthm, self.height)
        self.hL_17.addWidget(self.label_conv_street_types)
        self.hL_17.addWidget(self.btn_edit_street_types)
        self.hL_17.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_17)
        
        #lane_counts
        self.hL_18 = QtWidgets.QHBoxLayout()
        self.hL_18.setObjectName("hL_18")
        self.btn_edit_lane_counts = QtWidgets.QPushButton(self.content[column])
        self.btn_edit_lane_counts.setObjectName("btn_edit_lane_counts")
        self.btn_edit_lane_counts.setMinimumSize(self.widthm, self.height)
        self.label_lane_counts = QtWidgets.QLabel(self.content[column])
        self.label_lane_counts.setObjectName("label_24")
        self.label_lane_counts.setMinimumSize(self.widthf, self.height)
        self.hL_18.addWidget(self.label_lane_counts)
        self.hL_18.addWidget(self.btn_edit_lane_counts)
        self.hL_18.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_18)
        
        #lane_width
        self.hL_19 = QtWidgets.QHBoxLayout()
        self.hL_19.setObjectName("hL_19")
        self.label_lane_width = QtWidgets.QLabel(self.content[column])
        self.label_lane_width.setObjectName("label_25")
        self.label_lane_width.setMinimumSize(self.widthf, self.height)
        self.btn_edit_lane_widths = QtWidgets.QPushButton(self.content[column])
        self.btn_edit_lane_widths.setObjectName("btn_edit_lane_widths")
        self.btn_edit_lane_widths.setMinimumSize(self.widthm, self.height)
        self.hL_19.addWidget(self.label_lane_width)
        self.hL_19.addWidget(self.btn_edit_lane_widths)
        self.hL_19.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_19)
        
        #speed_limits
        self.hL_20 = QtWidgets.QHBoxLayout()
        self.hL_20.setObjectName("hL_20")
        self.btn_edit_speed_limits = QtWidgets.QPushButton(self.content[column])
        self.btn_edit_speed_limits.setObjectName("btn_edit_speed_limits")
        self.btn_edit_speed_limits.setMinimumSize(self.widthm, self.height)
        self.label_speed_limits = QtWidgets.QLabel(self.content[column])
        self.label_speed_limits.setObjectName("label_26")
        self.label_speed_limits.setMinimumSize(self.widthf, self.height)
        self.hL_20.addWidget(self.label_speed_limits)
        self.hL_20.addWidget(self.btn_edit_speed_limits)
        self.hL_20.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_20)


        #export_settings
        self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_export_settings = QtWidgets.QLabel(self.content[column])
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_export_settings.setFont(font)
        self.label_export_settings.setObjectName("label_27")
        self.formLayout[column].addRow(self.label_export_settings)
        
        #interpolation_distance
        self.hL_21 = QtWidgets.QHBoxLayout()
        self.hL_21.setObjectName("hL_21")
        self.label_interpolation_distance = QtWidgets.QLabel(self.content[column])
        self.label_interpolation_distance.setObjectName("label_28")
        self.label_interpolation_distance.setMinimumSize(self.widthf, self.height)
        self.sb_interpolation_distance = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_interpolation_distance.setMinimum(0.01)
        self.sb_interpolation_distance.setMaximum(1000.0)
        self.sb_interpolation_distance.setObjectName("sb_interpolation_distance")#
        self.sb_interpolation_distance.setMinimumSize(self.widthm, self.height)
        self.hL_21.addWidget(self.label_interpolation_distance)
        self.hL_21.addWidget(self.sb_interpolation_distance)
        self.hL_21.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_21)


        #compression
        self.hL_22 = QtWidgets.QHBoxLayout()
        self.hL_22.setObjectName("hL_22")
        self.sb_compression_threshold = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_compression_threshold.setMaximum(1000.0)
        self.sb_compression_threshold.setObjectName("sb_compression_threshold")
        self.sb_compression_threshold.setMinimumSize(self.widthm, self.height)
        self.label_compression_threshold = QtWidgets.QLabel(self.content[column])
        self.label_compression_threshold.setObjectName("label_29")
        self.label_compression_threshold.setMinimumSize(self.widthf, self.height)
        self.hL_22.addWidget(self.label_compression_threshold)
        self.hL_22.addWidget(self.sb_compression_threshold)
        self.hL_22.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_22)
        
        #utm_coordinates
        self.hL_23 = QtWidgets.QHBoxLayout()
        self.hL_23.setObjectName("hL_23")
        self.chk_utm_coordinates = QtWidgets.QCheckBox(self.content[column])
        self.chk_utm_coordinates.setText("")
        self.chk_utm_coordinates.setObjectName("chk_utm_coordinates")
        self.label_utm_coordinates = QtWidgets.QLabel(self.content[column])
        self.label_utm_coordinates.setObjectName("label_30")
        self.label_utm_coordinates.setMinimumSize(self.widthf, self.height)
        self.hL_23.addWidget(self.label_utm_coordinates)
        self.hL_23.addWidget(self.chk_utm_coordinates)
        self.hL_23.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_23)
        
        #filter_points
        self.hL_24 = QtWidgets.QHBoxLayout()
        self.hL_24.setObjectName("hL_24")
        self.chk_filter_points = QtWidgets.QCheckBox(self.content[column])
        self.chk_filter_points.setText("")
        self.chk_filter_points.setObjectName("chk_filter_points")
        self.label_filter_points = QtWidgets.QLabel(self.content[column])
        self.label_filter_points.setObjectName("label_43")
        self.label_filter_points.setMinimumSize(self.widthf, self.height)
        self.hL_24.addWidget(self.label_filter_points)
        self.hL_24.addWidget(self.chk_filter_points)
        self.hL_24.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_24)

        column = 1
        #internal_settings
        #self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_internal_settings = QtWidgets.QLabel(self.content[column])
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_internal_settings.setFont(font)
        self.label_internal_settings.setObjectName("label_31")
        self.formLayout[column].addRow(self.label_internal_settings)

        #earth_radius
        self.hL_25 = QtWidgets.QHBoxLayout()
        self.hL_25.setObjectName("hL_25")
        self.label_earth_radius = QtWidgets.QLabel(self.content[column])
        self.label_earth_radius.setObjectName("label_32")
        self.label_earth_radius.setMinimumSize(self.widthf, self.height)
        self.sb_earth_radius = QtWidgets.QSpinBox(self.content[column])
        self.sb_earth_radius.setMaximum(100000000)
        self.sb_earth_radius.setProperty("value", 6371000)
        self.sb_earth_radius.setObjectName("sb_earth_radius")
        self.sb_earth_radius.setMinimumSize(self.widthm, self.height)
        self.hL_25.addWidget(self.label_earth_radius)
        self.hL_25.addWidget(self.sb_earth_radius)
        self.hL_25.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_25)
        
        #delete_short_edges
        self.hL_26 = QtWidgets.QHBoxLayout()
        self.hL_26.setObjectName("hL_26")
        self.chk_delete_short_edges = QtWidgets.QCheckBox(self.content[column])
        self.chk_delete_short_edges.setText("")
        self.chk_delete_short_edges.setObjectName("chk_delete_short_edges")
        self.label_delete_short_edge = QtWidgets.QLabel(self.content[column])
        self.label_delete_short_edge.setObjectName("label_41")
        self.label_delete_short_edge.setMinimumSize(self.widthf, self.height)
        self.hL_26.addWidget(self.label_delete_short_edge)
        self.hL_26.addWidget(self.chk_delete_short_edges)
        self.hL_26.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_26)
        
        #internal_interpolation_distance
        self.hL_27 = QtWidgets.QHBoxLayout()
        self.hL_27.setObjectName("hL_27")
        self.label_internal_interpol_dist = QtWidgets.QLabel(self.content[column])
        self.label_internal_interpol_dist.setObjectName("label_33")
        self.label_internal_interpol_dist.setMinimumSize(self.widthf, self.height)
        self.sb_internal_interpolation_distance = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_internal_interpolation_distance.setMinimum(0.01)
        self.sb_internal_interpolation_distance.setMaximum(1000.0)
        self.sb_internal_interpolation_distance.setObjectName("sb_internal_interpolation_distance")
        self.sb_internal_interpolation_distance.setMinimumSize(self.widthm, self.height)
        self.hL_27.addWidget(self.label_internal_interpol_dist)
        self.hL_27.addWidget(self.sb_internal_interpolation_distance)
        self.hL_27.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_27)
        
        #bezier_parameter
        self.hL_28 = QtWidgets.QHBoxLayout()
        self.hL_28.setObjectName("hL_28")
        self.sb_bezier_parameter = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_bezier_parameter.setMaximum(0.5)
        self.sb_bezier_parameter.setProperty("value", 0.35)
        self.sb_bezier_parameter.setObjectName("sb_bezier_parameter")
        self.sb_bezier_parameter.setMinimumSize(self.widthm, self.height)
        self.label_bezier_param = QtWidgets.QLabel(self.content[column])
        self.label_bezier_param.setObjectName("label_34")
        self.label_bezier_param.setMinimumSize(self.widthf, self.height)
        self.hL_28.addWidget(self.label_bezier_param)
        self.hL_28.addWidget(self.sb_bezier_parameter)
        self.hL_28.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_28)

        #intersection_distance
        self.hL_29 = QtWidgets.QHBoxLayout()
        self.hL_29.setObjectName("hL_29")
        self.label_intersec_dist = QtWidgets.QLabel(self.content[column])
        self.label_intersec_dist.setObjectName("label_35")
        self.label_intersec_dist.setMinimumSize(self.widthf, self.height)
        self.sb_intersection_distance = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_intersection_distance.setMaximum(1000.0)
        self.sb_intersection_distance.setObjectName("sb_intersection_distance")
        self.sb_intersection_distance.setMinimumSize(self.widthm, self.height)
        self.hL_29.addWidget(self.label_intersec_dist)
        self.hL_29.addWidget(self.sb_intersection_distance)
        self.hL_29.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_29)

        #intersection_distance_respect
        self.hL_30 = QtWidgets.QHBoxLayout()
        self.hL_30.setObjectName("hL_30")
        self.chk_intersection_distance_respect = QtWidgets.QCheckBox(self.content[column])
        self.chk_intersection_distance_respect.setText("")
        self.chk_intersection_distance_respect.setObjectName("chk_intersection_distance_respect")
        self.label_intersection_distance_respect = QtWidgets.QLabel(self.content[column])
        self.label_intersection_distance_respect.setObjectName("label_42")
        self.label_intersection_distance_respect.setMinimumSize(self.widthf, self.height)
        self.hL_30.addWidget(self.label_intersection_distance_respect)
        self.hL_30.addWidget(self.chk_intersection_distance_respect)
        self.hL_30.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_30)

        #soft_angle_treshold
        self.hL_31 = QtWidgets.QHBoxLayout()
        self.hL_31.setObjectName("hL_31")
        self.sb_soft_angle_treshold = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_soft_angle_treshold.setMaximum(180.0)
        self.sb_soft_angle_treshold.setObjectName("sb_soft_angle_treshold")
        self.sb_soft_angle_treshold.setMinimumSize(self.widthm, self.height)
        self.label_soft_angle_threshold = QtWidgets.QLabel(self.content[column])
        self.label_soft_angle_threshold.setObjectName("label_36")
        self.label_soft_angle_threshold.setMinimumSize(self.widthf, self.height)
        self.hL_31.addWidget(self.label_soft_angle_threshold)
        self.hL_31.addWidget(self.sb_soft_angle_treshold)
        self.hL_31.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_31)

        #lane_segment_angle_treshold
        self.hL_32 = QtWidgets.QHBoxLayout()
        self.hL_32.setObjectName("hL_32")
        self.label_lane_segment_angle_treshold = QtWidgets.QLabel(self.content[column])
        self.label_lane_segment_angle_treshold.setObjectName("label_37")
        self.label_lane_segment_angle_treshold.setMinimumSize(self.widthf, self.height)
        self.sb_lane_segment_angle_treshold = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_lane_segment_angle_treshold.setMaximum(180.0)
        self.sb_lane_segment_angle_treshold.setObjectName("sb_lane_segment_angle_treshold")
        self.sb_lane_segment_angle_treshold.setMinimumSize(self.widthm, self.height)
        self.hL_32.addWidget(self.label_lane_segment_angle_treshold)
        self.hL_32.addWidget(self.sb_lane_segment_angle_treshold)
        self.hL_32.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_32)
        
        #cluster_length
        self.hL_33 = QtWidgets.QHBoxLayout()
        self.hL_33.setObjectName("hL_33")
        self.sb_cluster_length = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_cluster_length.setMaximum(1000000.0)
        self.sb_cluster_length.setObjectName("sb_cluster_length")
        self.sb_cluster_length.setMinimumSize(self.widthm, self.height)
        self.label_cluster_length = QtWidgets.QLabel(self.content[column])
        self.label_cluster_length.setObjectName("label_38")
        self.label_cluster_length.setMinimumSize(self.widthf, self.height)
        self.hL_33.addWidget(self.label_cluster_length)
        self.hL_33.addWidget(self.sb_cluster_length)
        self.hL_33.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_33)
        
        #cluster_length_treshold
        self.hL_34 = QtWidgets.QHBoxLayout()
        self.hL_34.setObjectName("hL_34")
        self.label_cluster_length_treshold = QtWidgets.QLabel(self.content[column])
        self.label_cluster_length_treshold.setObjectName("label_39")
        self.label_cluster_length_treshold.setMinimumSize(self.widthf, self.height)
        self.sb_cluster_length_treshold = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_cluster_length_treshold.setMaximum(1000000.0)
        self.sb_cluster_length_treshold.setObjectName("sb_cluster_length_treshold")
        self.sb_cluster_length_treshold.setMinimumSize(self.widthm, self.height)
        self.hL_34.addWidget(self.label_cluster_length_treshold)
        self.hL_34.addWidget(self.sb_cluster_length_treshold)
        self.hL_34.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_34)

        #merge_distance
        self.hL_35 = QtWidgets.QHBoxLayout()
        self.hL_35.setObjectName("hL_35")
        self.sb_merge_distance = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_merge_distance.setMaximum(1000000.0)
        self.sb_merge_distance.setObjectName("sb_merge_distance")
        self.sb_merge_distance.setMinimumSize(self.widthm, self.height)
        self.label_merge_distance = QtWidgets.QLabel(self.content[column])
        self.label_merge_distance.setObjectName("label_40")
        self.label_merge_distance.setMinimumSize(self.widthf, self.height)
        self.hL_35.addWidget(self.label_merge_distance)
        self.hL_35.addWidget(self.sb_merge_distance)
        self.hL_35.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_35)

        #crossing_sublayer_settings
        self.formLayout[column].addRow(QtWidgets.QLabel(self.content[column]))
        self.label_crossing_sublayer_settings = QtWidgets.QLabel(self.content[column])
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_crossing_sublayer_settings.setFont(font)
        self.label_crossing_sublayer_settings.setObjectName("label_44")
        self.formLayout[column].addRow(self.label_crossing_sublayer_settings)

        #extract_sublayer
        self.hL_36 = QtWidgets.QHBoxLayout()
        self.hL_36.setObjectName("hL_36")
        self.label_extract_sublayer = QtWidgets.QLabel(self.content[column])
        self.label_extract_sublayer.setObjectName("label_45")
        self.label_extract_sublayer.setMinimumSize(self.widthf, self.height)
        self.chk_extract_sublayer = QtWidgets.QCheckBox(self.content[column])
        self.chk_extract_sublayer.setText("")
        self.chk_extract_sublayer.setObjectName("chk_extract_sublayer")
        self.hL_36.addWidget(self.label_extract_sublayer)
        self.hL_36.addWidget(self.chk_extract_sublayer)
        self.hL_36.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_36)
        
        #sublayer_way_types
        self.hL_37 = QtWidgets.QHBoxLayout()
        self.hL_37.setObjectName("hL_37")
        self.label_sublayer_way_types = QtWidgets.QLabel(self.content[column])
        self.label_sublayer_way_types.setObjectName("label_46")
        self.label_sublayer_way_types.setMinimumSize(self.widthf, self.height)
        self.btn_edit_sublayer_way_types = QtWidgets.QPushButton(self.content[column])
        self.btn_edit_sublayer_way_types.setObjectName("btn_edit_sublayer_way_types")
        self.btn_edit_sublayer_way_types.setMinimumSize(self.widthm, self.height)
        self.hL_37.addWidget(self.label_sublayer_way_types)
        self.hL_37.addWidget(self.btn_edit_sublayer_way_types)
        self.hL_37.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_37)
        
        #intersection_distance_sublayer
        self.hL_38 = QtWidgets.QHBoxLayout()
        self.hL_38.setObjectName("hL_38")
        self.label_intersection_distance_sublayer = QtWidgets.QLabel(self.content[column])
        self.label_intersection_distance_sublayer.setObjectName("label_47")
        self.label_intersection_distance_sublayer.setMinimumSize(self.widthf, self.height)
        self.sb_intersection_distance_sublayer = QtWidgets.QDoubleSpinBox(self.content[column])
        self.sb_intersection_distance_sublayer.setMaximum(1000.0)
        self.sb_intersection_distance_sublayer.setObjectName("sb_intersection_distance_sublayer")
        self.sb_intersection_distance_sublayer.setMinimumSize(self.widthm, self.height)
        self.hL_38.addWidget(self.label_intersection_distance_sublayer)
        self.hL_38.addWidget(self.sb_intersection_distance_sublayer)
        self.hL_38.addWidget(QtWidgets.QLabel(self.content[column]))
        self.formLayout[column].addRow(self.hL_38)

        
        for i in range(self.columns):
            self.HBoxLayout.addWidget(self.content[i])

        self.scrollArea.setWidget(self.contentWrapper)
        #self.retranslateUi(tabWidget)
        QtCore.QMetaObject.connectSlotsByName(tabWidget)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.label_benchmark.setText(_translate("MainWindow", "Benchmark"))
        self.label_author.setText(_translate("MainWindow", "Author"))
        self.label_benchmark_id.setText(_translate("MainWindow", "Benchmark ID"))
        self.label_affiliation.setText(_translate("MainWindow", "Affiliation"))
        self.label_source.setText(_translate("MainWindow", "Source"))
        self.label_tags.setText(_translate("MainWindow", "Tags"))
        self.label_timestep_size.setText(_translate("MainWindow", "Timestep Size"))
        self.label_scenario_settings.setText(_translate("MainWindow", "Scenario Settings"))
        self.label_load_tunnels.setText(_translate("MainWindow", "Load Tunnels"))
        self.label_make_contiguous.setText(_translate("MainWindow", "Make Contiguous"))
        self.label_split_corners.setText(_translate("MainWindow", "Split at Corners"))
        self.label_osm_restrictions.setText(_translate("MainWindow", "Use OSM Restrictions"))
        self.label_conv_street_types.setText(_translate("MainWindow", "Converted Street Types (Main)"))
        self.label_lane_counts.setText(_translate("MainWindow", "Lane Counts"))
        self.label_lane_width.setText(_translate("MainWindow", "Lane Widths"))
        self.label_speed_limits.setText(_translate("MainWindow", "Speed Limits"))
        self.label_export_settings.setText(_translate("MainWindow", "Export Settings"))
        self.label_interpolation_distance.setText(_translate("MainWindow", "Interpolation Distance"))
        self.label_compression_threshold.setText(_translate("MainWindow", "Compression Threshold"))
        self.label_utm_coordinates.setText(_translate("MainWindow", "UTM Coordinates"))
        self.label_internal_settings.setText(_translate("MainWindow", "Internal Settings"))
        self.label_earth_radius.setText(_translate("MainWindow", "Earth Radius"))
        self.label_internal_interpol_dist.setText(_translate("MainWindow", "Internal Interpolation Distance"))
        self.label_bezier_param.setText(_translate("MainWindow", "Bezier Parameter"))
        self.label_intersec_dist.setText(_translate("MainWindow", "Intersection Distance"))
        self.label_soft_angle_threshold.setText(_translate("MainWindow", "Soft Angle Threshold"))
        self.label_lane_segment_angle_treshold.setText(_translate("MainWindow", "Lane Segment Angle Threshold"))
        self.label_cluster_length.setText(_translate("MainWindow", "Cluster Length"))
        self.label_cluster_length_treshold.setText(_translate("MainWindow", "Cluster Length Treshold"))
        self.label_merge_distance.setText(_translate("MainWindow", "Merge Distance"))
        self.label_delete_short_edge.setText(_translate("MainWindow", "Delete Short Edges"))
        self.label_intersection_distance_respect.setText(_translate("MainWindow", "Intersection Distance with\n"
"respect to other roads"))
        self.label_filter_points.setText(_translate("MainWindow", "Filter Points"))
        self.label_crossing_sublayer_settings.setText(_translate("MainWindow", "Crossing Sublayer Settings"))
        self.label_extract_sublayer.setText(_translate("MainWindow", "Extract Sublayer"))
        self.label_sublayer_way_types.setText(_translate("MainWindow", "Converted Street Types (Sub)"))
        self.label_intersection_distance_sublayer.setText(_translate("MainWindow", "Intersection Distance Sublayer"))
        self.btn_edit_lane_counts.setText(_translate("MainWindow", "Show"))
        self.btn_edit_speed_limits.setText(_translate("MainWindow", "Show"))
        self.btn_edit_street_types.setText(_translate("MainWindow", "Show"))
        self.btn_edit_lane_widths.setText(_translate("MainWindow", "Show"))
        self.btn_edit_sublayer_way_types.setText(_translate("MainWindow", "Show"))












