from typing import Dict, List

from commonroad.scenario.intersection import IntersectionIncomingElement  # type: ignore
from commonroad.scenario.lanelet import LaneletNetwork  # type: ignore
from lxml import etree  # type: ignore
from lxml.etree import Element

from crdesigner.map_conversion.opendrive.cr2odr.elements.road import Road
from crdesigner.map_conversion.opendrive.cr2odr.utils import config


class Junction:
    """
    This class adds junction child element to OpenDRIVE root element and
    also converts the CommonRoad junctions to OpenDRIVE junctions.
    The intersection of lane net consists of intersection incoming elements.
    For every intersection incoming element, all successors are obtained.
    """

    counting = 0

    def __init__(
        self,
        incoming: List[IntersectionIncomingElement],
        id_to_road: Dict[int, int],
        lanelet_to_lane: Dict[int, int],
        root: Element,
        lane_network: LaneletNetwork,
        junction_id: int,
    ) -> None:
        """
        This function lets the Junction class initialize the object with attributes incoming, id_to_road, lane_to_lane,
        root, lane_network, id and converts scenario junctions to OpenDRIVE junction.

        :param incoming: list of incoming intersection
        :param id_to_road: dictionary with lanelet id as key and OpenDRIVE road id as value
        :param lanelet_to_lane: dictionary with lanelet id as key and lane id as value
        :param root: OpenDRIVE etree element
        :param lane_network: collection of lanelet network
        :param junction_id: counting of junction
        """
        self.incoming = incoming
        self.id = junction_id
        self.root = root

        junction = etree.SubElement(root, config.JUNCTION_TAG)
        junction.set(config.NAME_TAG, "")
        junction.set(config.ID_TAG, str.format(config.ID_FORMAT_PATTERN, self.id))
        junction.set(config.TYPE_TAG, config.DEFAULT)

        self.junction = junction
        connection_num = 1

        # Do this for every IntersectionIncomingElement
        for inter_incoming in incoming:
            all_incomings = list(inter_incoming.incoming_lanelets)
            if len(all_incomings) == 0:  # todo this should be covered in the map verification
                continue

            # get all successors of the IntersectionIncomingElement
            # inc_suc are all roads as successors with their OpenDrive ID
            inc_suc = set()
            map_road_to_lane_link: dict = {}

            # all_suc has all successors with the commonroad-id
            all_suc = inter_incoming.successors_right.union(
                inter_incoming.successors_straight, inter_incoming.successors_left
            )
            for suc in all_suc:
                road_id = id_to_road[suc]
                inc_suc.add(road_id)
                map_road_to_lane_link[road_id] = []

            # look if all incoming lanes are on the same road in OpenDRIVE
            road_number = id_to_road[all_incomings[0]]
            for num in all_incomings:
                if road_number != id_to_road[num]:
                    print("ERROR, lanes not on the same road")
                    return
                inc_lane = lane_network.find_lanelet_by_id(num)
                lane_offset = lanelet_to_lane[num]
                for lane_suc in inc_lane.successor:
                    if map_road_to_lane_link.get(id_to_road[lane_suc]) is None:
                        map_road_to_lane_link[id_to_road[lane_suc]] = [
                            (lane_offset, lanelet_to_lane[lane_suc])
                        ]
                    else:
                        map_road_to_lane_link[id_to_road[lane_suc]].append(
                            (lane_offset, lanelet_to_lane[lane_suc])
                        )

            # create connection element for every successor road
            for connect in inc_suc:
                connection = etree.SubElement(junction, config.JUNCTION_CONNECTION_TAG)
                connection.set(config.ID_TAG, str.format(config.ID_FORMAT_PATTERN, connection_num))
                connection_num += 1
                connection.set(
                    config.JUNCTION_INCOMING_ROAD_TAG,
                    str.format(config.ID_FORMAT_PATTERN, road_number),
                )
                connection.set(
                    config.JUNCTION_CONNECTING_ROAD_TAG,
                    str.format(config.ID_FORMAT_PATTERN, connect),
                )
                connection.set(config.CONTACT_POINT_TAG, config.START_TAG)  # todo?
                road = Road.roads[connect]
                road.road.set(config.JUNCTION_TAG, str.format(config.ID_FORMAT_PATTERN, self.id))

                # link them with laneLink, accordingly to OpenDrive
                for inc, out in map_road_to_lane_link[connect]:
                    lane_link = etree.SubElement(connection, config.JUNCTION_LANE_LINK_TAG)
                    lane_link.set(
                        config.JUNCTION_FROM_TAG, str.format(config.ID_FORMAT_PATTERN, inc)
                    )
                    lane_link.set(config.JUNCTION_TO_TAG, str.format(config.ID_FORMAT_PATTERN, out))
