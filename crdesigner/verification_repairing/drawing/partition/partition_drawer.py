import random

from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.visualization.draw_params import (
    LaneletNetworkParams,
    LaneletParams,
    TrafficLightParams,
)
from commonroad.visualization.mp_renderer import MPRenderer
from crmapver.drawing.drawer import Drawer
from crmapver.partitioning.map_partition import (
    IntersectionBlock,
    LaneletBlock,
    Partition,
    TrafficLightBlock,
    TrafficSignBlock,
)
from matplotlib import pyplot as plt


class PartitionDrawer(Drawer):
    """
    The class is responsible for visualizing the partition of a CommonRoad map.
    """

    def __init__(self, network: LaneletNetwork):
        """
        Constructor.

        :param network: Lanelet network.
        """
        super().__init__(network)

    def save_partition_drawing(self, partition: Partition, file_dir: str, file_name: str):
        """
        Saves the visualizing of the partition of a map.

        :param partition: Partition
        :param file_dir: Directory for drawn plots
        :param file_name: Name of file
        """
        self._draw_partition(partition)
        plt.savefig(file_dir + "/" + file_name + ".png", format="png")
        plt.close()

    def _draw_partition(self, partition: Partition):
        """
        Draws the partition.

        :param partition: Partition
        """
        ax = plt.gca()
        rnd = MPRenderer(figsize=(25, 25), ax=ax)

        colors = []

        def new_color() -> str:
            while True:
                rgba = "%06x" % random.randint(0, 0xFFFFFF)
                if rgba not in colors:
                    return "#" + rgba + "A0"

        for _ in range(len(partition)):
            colors.append(new_color())

        lanelet_in_blocks = set()
        for i, block in enumerate(partition):
            lanelet_block = block[0]
            for lanelet_id in lanelet_block:
                lanelet_in_blocks.add(lanelet_id)

            self._draw_lanelet_block(lanelet_block, colors[i], rnd)

        lanelet_not_in_blocks = []
        for lanelet in self._network.lanelets:
            if lanelet.lanelet_id not in lanelet_in_blocks:
                lanelet_not_in_blocks.append(lanelet.lanelet_id)
        self._draw_lanelet_block(lanelet_not_in_blocks, "#c7c7c7", rnd)

        for traffic_sign in self._network.traffic_signs:
            traffic_sign.draw(rnd)
        for traffic_light in self._network.traffic_lights:
            traffic_light.draw(rnd)

        rnd.render()

        for i, block in enumerate(partition):
            traffic_sign_block = block[1]
            traffic_light_block = block[2]
            intersection_block = block[3]

            self._draw_traffic_sign_block(traffic_sign_block, colors[i], rnd)
            self._draw_traffic_light_block(traffic_light_block, colors[i], rnd)
            self._draw_intersection_block(intersection_block, colors[i], rnd)

        self._draw_information()

    def _draw_lanelet_block(self, block: LaneletBlock, color: str, rnd: MPRenderer):
        """
        Draws the lanelet block of partition

        :param block: Lanelet block of partition
        :param color: Color
        :param rnd: Renderer
        """
        lanelet_params = LaneletParams(facecolor=color, show_label=False)
        traffic_light_params = TrafficLightParams(draw_traffic_lights=False)
        lanelet_network_params = LaneletNetworkParams(
            draw_ids=block, lanelet=lanelet_params, traffic_light=traffic_light_params
        )
        self._network.draw(rnd, lanelet_network_params)

    def _draw_traffic_sign_block(self, block: TrafficSignBlock, color: str, rnd: MPRenderer):
        """
        Draws the traffic sign block of partition

        :param block: Traffic sign block of partition
        :param color: Color
        :param rnd: Renderer
        """
        for traffic_sign in self._network.traffic_signs:
            if traffic_sign.traffic_sign_id in block:
                position = self._get_traffic_sign_position(traffic_sign)

                if position is None:
                    continue

                self._plot_circle(position, rnd.ax, ec=color)

    def _draw_traffic_light_block(self, block: TrafficLightBlock, color: str, rnd: MPRenderer):
        """
        Draws the traffic light block of partition

        :param block: Traffic light block of partition
        :param color: Color
        :param rnd: Renderer
        """
        for traffic_light in self._network.traffic_lights:
            if traffic_light.traffic_light_id in block:
                position = self._get_traffic_light_position(traffic_light)

                if position is None:
                    continue

                self._plot_circle(position, rnd.ax, ec=color)

    def _draw_intersection_block(self, block: IntersectionBlock, color: str, rnd: MPRenderer):
        """
        Draws the intersection block of partition

        :param block: Intersection block of partition
        :param color: Color
        :param rnd: Renderer
        """
        pass

    def _draw_information(self):
        """
        Draws the caption.

        """
        self._plot_caption("Partitioned Map " + str(self._complete_map_name))
