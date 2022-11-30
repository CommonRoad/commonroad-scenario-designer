"""
This file is just a helper to start the GUI easily.
"""
import yaml
from crdesigner.ui.gui.mwindow.service_layer import config
from crdesigner.ui.gui.gui import start_gui_new


if __name__ == '__main__':
    with open('crdesigner/configurations/custom_settings.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    if data.get("Autofocus"):
        config.AUTOFOCUS = data.get("Autofocus")
    if data.get("Axis") == 'Left/ Bottom' or data.get("Axis") == 'None':
        config.AXIS_VISIBLE = data.get("Axis")
    if data.get("Darkmode"):
        config.DARKMODE = data.get("Darkmode")
    if not data.get("Draw_incoming_lanelets"):
        config.DRAW_INCOMING_LANELETS = data.get("Draw_incoming_lanelets")
    if data.get("Draw_intersection_labels"):
        config.DRAW_INTERSECTION_LABELS = data.get("Draw_intersection_labels")
    if data.get("Draw_intersections"):
        config.DRAW_INTERSECTIONS = data.get("Draw_intersections")
    if data.get("Draw_obstacle_direction"):
        config.DRAW_OBSTACLE_DIRECTION = data.get("Draw_obstacle_direction")
    if data.get("Draw_obstacle_icons"):
        config.DRAW_OBSTACLE_ICONS = data.get("Draw_obstacle_icons")
    if not data.get("Draw_obstacle_labels"):
        config.DRAW_OBSTACLE_LABELS = data.get("Draw_obstacle_labels")
    if not data.get("Draw_obstacle_signals"):
        config.DRAW_OBSTACLE_SIGNALS = data.get("Draw_obstacle_signals")
    if data.get("Draw_occupancy"):
        config.DRAW_OCCUPANCY = data.get("Draw_occupancy")
    if not data.get("Draw_successors"):
        config.DRAW_SUCCESSORS = data.get("Draw_successors")
    if not data.get("Draw_traffic_lights"):
        config.DRAW_TRAFFIC_LIGHTS = data.get("Draw_traffic_lights")
    if data.get("Draw_traffic_signs"):
        config.DRAW_TRAFFIC_SIGNS = data.get("Draw_traffic_signs")
    if data.get("Draw_trajectory"):
        config.DRAW_TRAJECTORY = data.get("Draw_trajectory")
    if not data.get("Legend"):
        config.LEGEND = data.get("Legend")
    start_gui_new()
