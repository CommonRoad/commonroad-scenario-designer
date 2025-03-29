from typing import Any, Dict

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.visualization.draw_params import (
    IntersectionParams,
    LaneletNetworkParams,
    LaneletParams,
    TrafficLightParams,
    TrafficSignParams,
)
from commonroad.visualization.mp_renderer import MPRenderer
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from crdesigner.verification_repairing.drawing.drawer import Drawer
from crdesigner.verification_repairing.drawing.invalid_states.element_draw_params import (
    IntersectionDrawParams,
    LaneletDrawParams,
    TrafficLightDrawParams,
    TrafficSignDrawParams,
)
from crdesigner.verification_repairing.verification.satisfaction import InvalidStates


class InvalidStatesDrawer(Drawer):
    """
    The class is responsible for visualizing the invalid states in a CommonRoad map.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: Scenario ID.
        """
        super().__init__(network, scenario_id)

    def save_invalid_states_drawing(
        self, invalid_states: InvalidStates, file_dir: str, file_name: str, file_format: str
    ):
        """
        Saves the visualizing of the invalid states in a map.

        :param invalid_states: Invalid states.
        :param file_dir: Directory for drawn plots.
        :param file_name: Name of file.
        :param file_format: Format which should be used, e.g., png and svg.
        """
        self._draw_invalid_states(invalid_states)
        plt.savefig(file_dir + "/" + file_name + f".{file_format}", format=file_format, dpi=300)
        plt.close()

    def _draw_invalid_states(self, invalid_states: InvalidStates):
        """
        Builds the visualizing of the invalid states in a map. Supported parameters of MPRenderer and
        own customized parameters are used for this purpose.

        :param invalid_states: Invalid states.
        """
        ax = plt.gca()
        rnd = MPRenderer(figsize=(25, 25), ax=ax)

        parameterizings = [
            parameterizing(self._network)
            for parameterizing in [
                LaneletDrawParams,
                TrafficSignDrawParams,
                TrafficLightDrawParams,
                IntersectionDrawParams,
            ]
        ]

        custom_draw_params = {}
        for parameterizing in parameterizings:
            func_names = [
                func for func in dir(parameterizing) if callable(getattr(parameterizing, func))
            ]

            for invalid_state_id, locations in invalid_states.items():
                for func_name in func_names:
                    if "param_" + str(invalid_state_id.value) == func_name:
                        for location in locations:
                            func = getattr(parameterizing, func_name)
                            func(location)

            if isinstance(parameterizing, LaneletDrawParams):
                self._draw_lanelet_supported_params(parameterizing.draw_params, rnd)
            elif isinstance(parameterizing, TrafficSignDrawParams):
                self._draw_traffic_sign_supported_params(parameterizing.draw_params, rnd)
            elif isinstance(parameterizing, TrafficLightDrawParams):
                self._draw_traffic_light_supported_params(parameterizing.draw_params, rnd)
            elif isinstance(parameterizing, IntersectionDrawParams):
                self._draw_intersection_supported_params(parameterizing.draw_params, rnd)
            custom_draw_params.update({type(parameterizing): parameterizing.custom_draw_params})

        rnd.render()

        for parameterizing, params in custom_draw_params.items():
            if parameterizing == LaneletDrawParams:
                self._draw_lanelet_custom_params(params, ax)
            if parameterizing == TrafficSignDrawParams:
                self._draw_traffic_sign_custom_params(params, ax)
            if parameterizing == TrafficLightDrawParams:
                self._draw_traffic_light_custom_params(params, ax)
            if parameterizing == IntersectionDrawParams:
                self._draw_intersection_custom_params(params, ax)

        self._draw_information(ax)

    def _draw_lanelet_supported_params(
        self, invalid_state_params: Dict[int, LaneletParams], rnd: MPRenderer
    ):
        """
        Draws the lanelets. For drawing the parameters supported by the renderer are used to
        indicate some invalid states in a lanelet.

        :param invalid_state_params: Supported parameters.
        :param rnd: Renderer.
        """
        valid_lanelets = []
        for lanelet in self._network.lanelets:
            if lanelet.lanelet_id not in invalid_state_params.keys():
                valid_lanelets.append(lanelet.lanelet_id)
        lanelet_params = LaneletParams(draw_linewidth=1.5)
        traffic_light_params = TrafficLightParams(draw_traffic_lights=False)
        lanelet_network_params = LaneletNetworkParams(
            draw_ids=valid_lanelets, lanelet=lanelet_params, traffic_light=traffic_light_params
        )
        self._network.draw(rnd, lanelet_network_params)

        for lanelet_id, lanelet_params in invalid_state_params.items():
            lanelet_params.show_label = True
            lanelet_params.draw_linewidth = 1.5
            traffic_light_params = TrafficLightParams(draw_traffic_lights=False)
            lanelet_network_params = LaneletNetworkParams(
                draw_ids=[lanelet_id], lanelet=lanelet_params, traffic_light=traffic_light_params
            )
            self._network.draw(rnd, draw_params=lanelet_network_params)

    def _draw_traffic_sign_supported_params(
        self, invalid_state_params: Dict[int, TrafficSignParams], rnd: MPRenderer
    ):
        """
        Draws the traffic signs. For drawing the parameters supported by the renderer are used to
        indicate some invalid states in a traffic sign.

        :param invalid_state_params: Invalid state parameters.
        :param rnd: Renderer.
        """
        for traffic_sign in self._network.traffic_signs:
            if traffic_sign.traffic_sign_id in invalid_state_params.keys():
                traffic_sign.draw(rnd, invalid_state_params[traffic_sign.traffic_sign_id])
            else:
                traffic_sign.draw(rnd, TrafficSignParams(show_label=False))

    def _draw_traffic_light_supported_params(
        self, traffic_light_params: Dict[int, TrafficLightParams], rnd: MPRenderer
    ):
        """
        Draws the traffic lights. For drawing the parameters supported by the renderer are used to
        indicate some invalid states in a traffic light.

        :param traffic_light_params: Supported parameters.
        :param rnd: Renderer.
        """
        for traffic_light in self._network.traffic_lights:
            if traffic_light.traffic_light_id in traffic_light_params.keys():
                traffic_light.draw(rnd, traffic_light_params[traffic_light.traffic_light_id])
            else:
                traffic_light.draw(rnd, TrafficLightParams(show_label=False))

    def _draw_intersection_supported_params(
        self, intersection_params: Dict[int, IntersectionParams], rnd: MPRenderer
    ):
        """
        Draws the intersections. For drawing the parameters supported by the renderer are used to
        indicate some invalid states in an intersection.

        :param intersection_params: Supported parameters.
        :param rnd: Renderer.
        """
        for intersection in self._network.intersections:
            if intersection.intersection_id in intersection_params.keys():
                pass
            else:
                pass

    def _draw_lanelet_custom_params(self, invalid_state_params: Dict[int, Any], ax: Axes):
        """
        Draws the symbols indicating the invalid states in a lanelet. The symbol depend on
        the used custom parameters.

        :param invalid_state_params: Custom parameters.
        :param ax: Axes used by renderer.
        """
        for lanelet_id, invalid_state_params in invalid_state_params.items():
            for param, value in invalid_state_params.copy().items():
                lanelet = self._network.find_lanelet_by_id(lanelet_id)
                if lanelet is None:
                    continue

                left_vertices = lanelet.left_vertices
                size = len(left_vertices)
                if param == "mark_left_start_vertex" and value:
                    self._plot_point(left_vertices[0], ax)
                if param == "mark_left_end_vertex" and value:
                    self._plot_point(left_vertices[size - 1], ax)

                right_vertices = lanelet.right_vertices
                size = len(right_vertices)
                if param == "mark_right_start_vertex" and value:
                    self._plot_point(right_vertices[0], ax)
                if param == "mark_right_end_vertex" and value:
                    self._plot_point(right_vertices[size - 1], ax)

                if param == "show_vector":
                    self._plot_arrow(value[0], value[1], ax)

    def _draw_traffic_sign_custom_params(self, invalid_state_params: Dict[int, Any], ax: Axes):
        """
        Draws the symbols indicating the invalid states in a traffic sign. The symbol depend on
        the used custom parameters.

        :param invalid_state_params: Custom parameters.
        :param ax: Axes used by renderer.
        """
        for traffic_sign_id, invalid_state_params in invalid_state_params.items():
            traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)
            if traffic_sign is None:
                continue

            for param, value in invalid_state_params.copy().items():
                if (param == "mark_traffic_sign" or param == "show_traffic_sign_id") and value:
                    position = self._get_traffic_sign_position(traffic_sign)

                    if position is None:
                        continue

                    if param == "mark_traffic_sign":
                        self._plot_circle(position, ax)
                    elif param == "show_traffic_sign_id":
                        position = np.array([position[0] + 1.5, position[1] + 1.5])
                        self._plot_text(str(traffic_sign_id), position, ax)

    def _draw_traffic_light_custom_params(self, invalid_state_params: Dict[int, Any], ax: Axes):
        """
        Draws the symbols indicating the invalid states in a traffic light. The symbol depend on
        the used custom parameters.

        :param invalid_state_params: Custom parameters.
        :param ax: Axes used by renderer.
        """
        for traffic_light_id, invalid_state_params in invalid_state_params.items():
            traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)
            if traffic_light is None:
                continue

            for param, value in invalid_state_params.copy().items():
                if (param == "mark_traffic_light" or param == "show_traffic_light_id") and value:
                    position = self._get_traffic_light_position(traffic_light)

                    if position is None:
                        continue

                    if param == "mark_traffic_light":
                        self._plot_circle(position, ax)
                    elif param == "show_traffic_light_id":
                        position = np.array([position[0] + 1.5, position[1] + 1.5])
                        self._plot_text(str(traffic_light_id), position, ax)

    def _draw_intersection_custom_params(self, invalid_state_params: Dict[int, Any], ax: Axes):
        """
        Draws the symbols indicating the invalid states in an intersection. The symbols depend on
        the used custom parameters.

        :param invalid_state_params: Custom parameters.
        :param ax: Axes used by renderer.
        """
        for intersection_id, invalid_state_params in invalid_state_params.items():
            intersection = self._network.find_intersection_by_id(intersection_id)
            if intersection is None:
                continue
            pass  # TODO: Implement

    def _draw_information(self, ax: Axes):
        """
        Draws a legend which contains information about the used special symbols
        indicating invalid states in the map.

        :param ax: Axes used by renderer.
        """
        self._plot_caption("Invalid States in Map " + str(self._complete_map_name))

        invalid_lanelet = mpatches.Patch(color="lightcoral", label="Invalid lanelet")
        connection_point = mlines.Line2D(
            [],
            [],
            marker="o",
            color="red",
            label="Inaccurate connection",
            linestyle="None",
            markerfacecolor="r",
            markersize=7,
        )
        border_line = mlines.Line2D([], [], color="red", label="Inaccurate border")
        reference_arrow = mlines.Line2D(
            [],
            [],
            marker=">",
            color="red",
            label="Non-referenced",
            linestyle="None",
            markerfacecolor="r",
            markersize=10,
        )
        invalid_sign_light = mlines.Line2D(
            [],
            [],
            marker="o",
            markerfacecolor="white",
            label="Invalid traffic sign/light",
            linestyle="None",
            color="red",
            markersize=18,
            fillstyle="none",
            markeredgewidth=1.5,
            markeredgecolor="red",
        )
        self._plot_legend(
            [invalid_lanelet, connection_point, border_line, reference_arrow, invalid_sign_light],
            ax,
        )
