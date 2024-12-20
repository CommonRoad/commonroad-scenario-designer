from abc import ABC

import numpy as np
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from matplotlib import pyplot as plt
from matplotlib.axes import Axes


class Drawer(ABC):
    """
    The class is responsible for visualizing some specific elements in a CommonRoad map.
    """

    def __init__(self, network: LaneletNetwork, scenario_id: ScenarioID = ScenarioID()):
        """
        Constructor.

        :param network: Lanelet network.
        :param scenario_id: Scenario ID.
        """
        self._complete_map_name = (
            str(scenario_id.country_id)
            + "_"
            + str(scenario_id.map_name)
            + "-"
            + str(scenario_id.map_id)
        )
        self._network = network

    def _get_traffic_sign_position(self, traffic_sign: TrafficSign) -> np.ndarray:
        position = traffic_sign.position
        if position is None and traffic_sign.first_occurrence:
            first_occurrence = list(traffic_sign.first_occurrence)[0]
            rightmost_lanelet = self._network.find_lanelet_by_id(first_occurrence)
            while rightmost_lanelet.adj_right is not None:
                rightmost_lanelet = self._network.find_lanelet_by_id(rightmost_lanelet.adj_right)
            position = rightmost_lanelet.right_vertices[0]

        return position

    def _get_traffic_light_position(self, traffic_light: TrafficLight) -> np.ndarray:
        position = traffic_light.position
        if position is None:
            occurrences = set()
            for lanelet in self._network.lanelets:
                if traffic_light.traffic_light_id in lanelet.traffic_lights:
                    occurrences.update({lanelet.lanelet_id})

            if occurrences:
                first_occurrence = list(occurrences)[0]
                rightmost_lanelet = self._network.find_lanelet_by_id(first_occurrence)
                while rightmost_lanelet.adj_right is not None:
                    rightmost_lanelet = self._network.find_lanelet_by_id(
                        rightmost_lanelet.adj_right
                    )
                position = rightmost_lanelet.right_vertices[0]
        return position

    @staticmethod
    def _plot_point(
        point: np.ndarray, ax: Axes, color: str = "r+", zorder: int = 50, marker: str = "o"
    ):
        """
        Plots a point in map.

        :param point: Point
        :param ax: Axes used by renderer
        """
        ax.plot(point[0], point[1], color, zorder=zorder, marker=marker)

    @staticmethod
    def _plot_arrow(
        start_point: np.ndarray,
        end_point: np.ndarray,
        ax: Axes,
        head_width: float = 0.75,
        width: float = 0.1,
        ec: str = "red",
        zorder: int = 50,
        facecolor: str = "red",
    ):
        """
        Plots an arrow in map.

        :param start_point: Starting point
        :param end_point: Ending point
        :param ax: Axes used by renderer
        """
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        arrow = plt.arrow(
            start_point[0],
            start_point[1],
            dx,
            dy,
            head_width=head_width,
            width=width,
            ec=ec,
            zorder=zorder,
            facecolor=facecolor,
        )
        ax.add_artist(arrow)

    @staticmethod
    def _plot_circle(
        point: np.ndarray,
        ax: Axes,
        radius: float = 3.5,
        ec: str = "red",
        fill: bool = False,
        zorder: int = 50,
        linewidth: float = 3.5,
    ):
        """
        Plots a circle in map.

        :param point: Point
        :param ax: Axes used by renderer
        """
        circle = plt.Circle(
            (point[0], point[1]), radius, ec=ec, fill=fill, zorder=zorder, linewidth=linewidth
        )
        ax.add_artist(circle)

    @staticmethod
    def _plot_text(
        txt: str,
        point: np.ndarray,
        ax: Axes,
        color: str = "black",
        facecolor: str = "lightgrey",
        edgecolor: str = "black",
        zorder: int = 80,
    ):
        """
        Plots a text block.

        :param txt: Text block
        :param point: Point
        :param ax: Axes uses by renderer
        """
        text = plt.text(
            point[0],
            point[1],
            txt,
            color=color,
            bbox=dict(facecolor=facecolor, edgecolor=edgecolor),
            zorder=zorder,
        )
        ax.add_artist(text)

    @staticmethod
    def _plot_legend(
        artists: list, ax: Axes, size: int = 15, loc: str = "lower left", zorder: int = 90
    ):
        """
        Draws a legend which contains information about the used special symbols
        indicating invalid states in the map.

        :param ax: Axes used by renderer
        """
        ax.legend(handles=artists, prop={"size": size}, loc=loc).set_zorder(zorder)

    @staticmethod
    def _plot_caption(caption: str, fontsize: int = 18):
        """
        Draws a caption for map.

        :param caption: Caption
        :param fontsize: Size of font
        """
        plt.xlabel(caption, fontsize=fontsize)
