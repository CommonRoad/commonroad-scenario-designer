from lxml import etree
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from commonroad.scenario.lanelet import LaneletNetwork


class Junction:
    """
    This class adds junction child element to OpenDRIVE root element and
    also converts the CommonRoad junctions to opendrive junctions.
    The intersection of lane net consists of intersection incoming elements.
    For every intersection incoming element, all successors are obtained.
    """
    counting = 0

    def __init__(self, incoming: list, id_to_road: dict, lane_to_lane: dict,
                 root: etree, lane_network: LaneletNetwork, id: int):
        self.incoming = incoming
        self.id = id
        self.root = root

        junction = etree.SubElement(root, "junction")
        junction.set("name", "")
        junction.set("id", str.format("{}", self.id))
        junction.set("type", "default")

        self.junction = junction
        self.ending_list = []
        connection_num = 1

        # Do this for every IntersectionIncomingElement
        for inter_incoming in incoming:
            all_incomings = list(inter_incoming.incoming_lanelets)

            # get all successors of the IntersectionIncomingElement
            # inc_suc are all roads as successors with their OpenDrive ID
            inc_suc = set()
            map_road_to_lane_link = {}

            # all_suc has all successors with the commonroad-id
            all_suc = inter_incoming.successors_right.union(
                inter_incoming.successors_straight, inter_incoming.successors_left
            )
            for suc in all_suc:
                road_id = id_to_road[suc]
                inc_suc.add(road_id)
                map_road_to_lane_link[road_id] = []

            # look if all incoming lanes are on the same road in opendrive
            road_number = id_to_road[all_incomings[0]]
            for num in all_incomings:
                if road_number != id_to_road[num]:
                    print("ERROR, lanes not on the same road")
                    return
                inc_lane = lane_network.find_lanelet_by_id(num)
                lane_offset = lane_to_lane[num]
                for lane_suc in inc_lane.successor:
                    map_road_to_lane_link[id_to_road[lane_suc]].append(
                        (lane_offset, lane_to_lane[lane_suc])
                    )

            # create connection element for every successor road
            for connect in inc_suc:
                connection = etree.SubElement(junction, "connection")
                connection.set("id", str.format("{}", connection_num))
                connection_num += 1
                connection.set("incomingRoad", str.format("{}", road_number))
                connection.set("connectingRoad", str.format("{}", connect))
                connection.set("contactPoint", "start")  # todo?
                road = Road.roads[connect]
                road.road.set("junction", str.format("{}", self.id))

                # link them with laneLink, accordingly to OpenDrive
                for (inc, out) in map_road_to_lane_link[connect]:
                    laneLink = etree.SubElement(connection, "laneLink")
                    laneLink.set("from", str.format("{}", inc))
                    laneLink.set("to", str.format("{}", out))
