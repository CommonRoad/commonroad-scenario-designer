""" window with settings for the Scenario Designer """

import yaml

from crdesigner.ui.gui.mwindow.animated_viewer_wrapper.commonroad_viewer.service_layer.draw_params_updater import \
    set_draw_params
from crdesigner.ui.gui.mwindow.service_layer import config


class GUISettings:
    
    def __init__(self, parent):
        self.darkmode = config.DARKMODE
        self.parent = parent
        self.window = self.parent.window.gui_settings


    def connect_events(self):
        """ connect buttons to callables """
        self.window.chk_darkmode.stateChanged.connect(self.update_window)

    def update_ui_values(self):
        """
        sets the values of the settings window to the current values of config
        """
        self.window.chk_autofocus.setChecked(config.AUTOFOCUS)
        self.window.chk_draw_trajectory.setChecked(config.DRAW_TRAJECTORY)
        self.window.chk_draw_intersection.setChecked(config.DRAW_INTERSECTIONS)
        self.window.chk_draw_label.setChecked(config.DRAW_OBSTACLE_LABELS)
        self.window.chk_draw_obstacle_icon.setChecked(config.DRAW_OBSTACLE_ICONS)
        self.window.chk_draw_obstacle_direction.setChecked(config.DRAW_OBSTACLE_DIRECTION)
        self.window.chk_draw_obstacle_signal.setChecked(config.DRAW_OBSTACLE_SIGNALS)
        self.window.chk_draw_occupancy.setChecked(config.DRAW_OCCUPANCY)
        self.window.chk_draw_traffic_sign.setChecked(config.DRAW_TRAFFIC_SIGNS)
        self.window.chk_draw_traffic_light.setChecked(config.DRAW_TRAFFIC_LIGHTS)
        self.window.chk_draw_incoming_lanelet.setChecked(config.DRAW_INCOMING_LANELETS)
        self.window.chk_draw_successors.setChecked(config.DRAW_SUCCESSORS)
        self.window.chk_draw_intersection_label.setChecked(config.DRAW_INTERSECTION_LABELS)
        self.window.cmb_axis_visible.setCurrentText(config.AXIS_VISIBLE)
        self.window.chk_darkmode.setChecked(config.DARKMODE)
        self.window.chk_legend.setChecked(config.LEGEND)
        return

    def save_to_config(self):
        """
        saves the values in the settings window to config.py
        """
        config.AUTOFOCUS = self.window.chk_autofocus.isChecked()
        config.DRAW_TRAJECTORY = self.window.chk_draw_trajectory.isChecked()
        config.DRAW_INTERSECTIONS = self.window.chk_draw_intersection.isChecked()
        config.DRAW_OBSTACLE_LABELS = self.window.chk_draw_label.isChecked()
        config.DRAW_OBSTACLE_ICONS = self.window.chk_draw_obstacle_icon.isChecked()
        config.DRAW_OBSTACLE_DIRECTION = self.window.chk_draw_obstacle_direction.isChecked()
        config.DRAW_OBSTACLE_SIGNALS = self.window.chk_draw_obstacle_signal.isChecked()
        config.DRAW_OCCUPANCY = self.window.chk_draw_occupancy.isChecked()
        config.DRAW_TRAFFIC_SIGNS = self.window.chk_draw_traffic_sign.isChecked()
        config.DRAW_TRAFFIC_LIGHTS = self.window.chk_draw_traffic_light.isChecked()
        config.DRAW_INCOMING_LANELETS = self.window.chk_draw_incoming_lanelet.isChecked()
        config.DRAW_SUCCESSORS = self.window.chk_draw_successors.isChecked()
        config.DRAW_INTERSECTION_LABELS = self.window.chk_draw_intersection_label.isChecked()
        config.AXIS_VISIBLE = str(self.window.cmb_axis_visible.currentText())
        config.DARKMODE = self.window.chk_darkmode.isChecked()
        config.LEGEND = self.window.chk_legend.isChecked()

    def has_valid_entries(self) -> bool:
        """
        Check if the user input is valid. Otherwise warn the user.

        :return: bool wether the input is valid
        """
        # use if settings get extended
        return True

    def apply_close(self) -> None:
        """
        closes settings if settings could be saved to config
        """
        if self.has_valid_entries():
            self.save_to_config()
            self.darkmode= config.DARKMODE

            set_draw_params(trajectory=self.window.chk_draw_trajectory.isChecked(),
                            intersection=self.window.chk_draw_intersection.isChecked(),
                            obstacle_label=self.window.chk_draw_label.isChecked(),
                            obstacle_icon=self.window.chk_draw_obstacle_icon.isChecked(),
                            obstacle_direction=self.window.chk_draw_obstacle_direction.isChecked(),
                            obstacle_signal=self.window.chk_draw_obstacle_signal.isChecked(),
                            occupancy=self.window.chk_draw_occupancy.isChecked(),
                            traffic_signs=self.window.chk_draw_traffic_sign.isChecked(),
                            traffic_lights=self.window.chk_draw_traffic_light.isChecked(),
                            incoming_lanelets=self.window.chk_draw_incoming_lanelet.isChecked(),
                            successors=self.window.chk_draw_successors.isChecked(),
                            intersection_labels=self.window.chk_draw_intersection_label.isChecked(),
                            colorscheme=self.parent.cr_designer.colorscheme(),
                            )
        else:
            print("invalid settings")

    def update_window(self):
        config.DARKMODE = self.window.chk_darkmode.isChecked()
        set_draw_params(trajectory=config.DRAW_TRAJECTORY,
                        intersection=config.DRAW_INTERSECTIONS,
                        obstacle_label=config.DRAW_OBSTACLE_LABELS,
                        obstacle_icon=config.DRAW_OBSTACLE_ICONS,
                        obstacle_direction=config.DRAW_OBSTACLE_DIRECTION,
                        obstacle_signal=config.DRAW_OBSTACLE_SIGNALS,
                        occupancy=config.DRAW_OCCUPANCY,
                        traffic_signs=config.DRAW_TRAFFIC_SIGNS,
                        traffic_lights=config.DRAW_TRAFFIC_LIGHTS,
                        incoming_lanelets=config.DRAW_INCOMING_LANELETS,
                        successors=config.DRAW_SUCCESSORS,
                        intersection_labels=config.DRAW_INTERSECTION_LABELS,
                        colorscheme=self.parent.cr_designer.colorscheme(), )
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()

    def close(self):
        config.DARKMODE = self.darkmode
        set_draw_params(trajectory=config.DRAW_TRAJECTORY,
                        intersection=config.DRAW_INTERSECTIONS,
                        obstacle_label=config.DRAW_OBSTACLE_LABELS,
                        obstacle_icon=config.DRAW_OBSTACLE_ICONS,
                        obstacle_direction=config.DRAW_OBSTACLE_DIRECTION,
                        obstacle_signal=config.DRAW_OBSTACLE_SIGNALS,
                        occupancy=config.DRAW_OCCUPANCY,
                        traffic_signs=config.DRAW_TRAFFIC_SIGNS,
                        traffic_lights=config.DRAW_TRAFFIC_LIGHTS,
                        incoming_lanelets=config.DRAW_INCOMING_LANELETS,
                        successors=config.DRAW_SUCCESSORS,
                        intersection_labels=config.DRAW_INTERSECTION_LABELS,
                        colorscheme=self.parent.cr_designer.colorscheme(), )
        self.parent.canvas.update_obstacle_trajectory_params()
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()

    def apply_set_to_default(self):

        with open('crdesigner/configurations/default_settings.yaml') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        config.AUTOFOCUS = data.get("Autofocus")
        config.DRAW_TRAJECTORY = data.get("Draw_trajectory")
        config.DRAW_INTERSECTIONS = data.get("Draw_intersections")
        config.DRAW_OBSTACLE_LABELS = data.get("Draw_obstacle_labels")
        config.DRAW_OBSTACLE_ICONS = data.get("Draw_obstacle_icons")
        config.DRAW_OBSTACLE_DIRECTION = data.get("Draw_obstacle_direction")
        config.DRAW_OBSTACLE_SIGNALS = data.get("Draw_obstacle_signals")
        config.DRAW_OCCUPANCY = data.get("Draw_occupancy")
        config.DRAW_TRAFFIC_SIGNS = data.get("Draw_traffic_signs")
        config.DRAW_TRAFFIC_LIGHTS = data.get("Draw_traffic_lights")
        config.DRAW_INCOMING_LANELETS = data.get("Draw_incoming_lanelets")
        config.DRAW_SUCCESSORS = data.get("Draw_successors")
        config.DRAW_INTERSECTION_LABELS = data.get("Draw_intersection_labels")
        config.AXIS_VISIBLE = data.get("Axis")
        config.DARKMODE = data.get("Darkmode")
        config.LEGEND = data.get("Legend")
        set_draw_params(trajectory=data.get("Draw_trajectory"), intersection=data.get("Draw_intersections"),
                        obstacle_label=data.get("Draw_obstacle_labels"),
                        obstacle_icon=data.get("Draw_obstacle_icons"), obstacle_direction=data.get("Draw_obstacle_direction"),
                        obstacle_signal=data.get("Draw_obstacle_signals"),
                        occupancy=data.get("Draw_occupancy"), traffic_signs=data.get("Draw_traffic_signs"),
                        traffic_lights=data.get("Draw_traffic_lights"),
                        incoming_lanelets=data.get("Draw_incoming_lanelets"), successors=data.get("Draw_successors"),
                        intersection_labels=data.get("Draw_intersection_labels"),
                        colorscheme=self.parent.cr_designer.colorscheme(),)
        self.parent.canvas.update_obstacle_trajectory_params()
        if self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.current_scenario != None:
            self.parent.cr_designer.animated_viewer_wrapper.cr_viewer.update_plot()
        self.parent.cr_designer.update_window()
        self.parent.window.update_window()




