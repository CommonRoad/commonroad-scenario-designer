from crdesigner.map_conversion.common import geometry
from crdesigner.map_conversion.osm2cr.converter_modules.intermediate_operations.traffic_light_generator import (
    TrafficLightGenerator,
)
from crdesigner.map_conversion.osm2cr.converter_modules.utility import idgenerator


def intersection_enhancement(intermediate_format):
    """
    Enhance intersections with traffic lights.
    Method will remove intersections found in osm and add its own instead.
    """

    def remove_non_intersection_lights(all_incoming_lanes_in_scenario):
        traffic_lights_on_intersections = []
        for incoming_lane in all_incoming_lanes_in_scenario:
            if incoming_lane.traffic_lights:
                traffic_lights_on_intersections.extend(incoming_lane.traffic_lights)
        intermediate_format.traffic_lights = list(
            filter(
                lambda x: x.traffic_light_id in traffic_lights_on_intersections,
                intermediate_format.traffic_lights,
            )
        )

    def remove_existing_traffic_lights(incoming_lanes):
        for lane in incoming_lanes:
            if lane.traffic_lights:
                for light_id in lane.traffic_lights:
                    light = intermediate_format.find_traffic_light_by_id(light_id)
                    if light is not None:
                        intermediate_format.traffic_lights.remove(light)
            lane.traffic_lights = set()

    def remove_innner_lights(intersection, incoming_lanes):
        # removes inner traffic lights in the middle of crossings
        # if lane is short and predecessor is other incoming's successor
        remove = False
        for lane in incoming_lanes:
            if geometry.distance(
                lane.center_points[0], [lane.center_points[-1]]
            ) < 2 and check_pre_incoming_lane(lane, intermediate_format):  # shorter than two meters
                remove = True
                indicating_lane = lane.id
        if remove:
            for incoming in intersection.incomings:
                for incoming_lane in incoming.incoming_lanelets:
                    if incoming_lane == indicating_lane:
                        for incoming_t in incoming.incoming_lanelets:
                            intermediate_format.find_edge_by_id(incoming_t).traffic_lights = set()

    def create_new_traffic_lights(intersection):
        # create traffic light generator for intersection based on number of incomings
        traffic_light_generator = TrafficLightGenerator(len(intersection.incomings))

        # begin with incoming that is not left of any other
        left_of_map = {}
        for incoming in intersection.incomings:
            left_of_map[incoming] = incoming.left_of

        incoming = None
        # try to find incoming that is not right of any other incoming (3 incomings)
        for key in left_of_map:
            if key.incoming_id not in left_of_map.values() and key.left_of is not None:
                incoming = key
                break
        # if unable to find any than begin with any other incoming (4 incomings)
        if incoming is None:
            incoming = intersection.incomings[0]
        processed_incomings = set()

        # loop over incomings
        while incoming is not None:
            if incoming in processed_incomings:
                break

            # postition of traffic light
            for lane_id in incoming.incoming_lanelets:
                edge = intermediate_format.find_edge_by_id(lane_id)
                if not edge.adjacent_right:
                    position_point = edge.right_bound[-1]
                    break

            # create new traffic light
            new_traffic_light = traffic_light_generator.generate_traffic_light(
                position=position_point, new_id=idgenerator.get_id()
            )
            intermediate_format.traffic_lights.append(new_traffic_light)

            # add reference to each incoming lane
            for lane_id in incoming.incoming_lanelets:
                lane = intermediate_format.find_edge_by_id(lane_id)
                lane.traffic_lights.add(new_traffic_light.traffic_light_id)

            # process next left of current incoming
            processed_incomings.add(incoming)
            # new incoming is incoming with left_of id of current incoming, else None
            incoming = next(
                (i for i in intersection.incomings if i.incoming_id == incoming.left_of), None
            )
            # edge case if only 2 incomings were found:
            if len(intersection.incomings) == 2:
                incoming = intersection.incomings[-1]

    # keep track of all incoming lanes in scenario
    all_incoming_lanes_in_scenario = []

    # iterate over all intersections in scenario
    for intersection in intermediate_format.intersections:
        has_traffic_lights = False
        incoming_lanes = []

        # find all incoming lanes in intersection and determine if they have traffic lights
        for incoming in intersection.incomings:
            for incoming_lane in incoming.incoming_lanelets:
                lane = intermediate_format.find_edge_by_id(incoming_lane)
                if lane.traffic_lights:
                    has_traffic_lights = True
                # also check up to 2 predecessors ahead of lane
                pre1 = (
                    intermediate_format.find_edge_by_id(lane.predecessors[0])
                    if len(lane.predecessors) == 1
                    else None
                )
                pre2 = (
                    intermediate_format.find_edge_by_id(pre1.predecessors[0])
                    if pre1 and len(pre1.predecessors) == 1
                    else None
                )
                if pre1 and pre1.traffic_lights:
                    has_traffic_lights = True
                if pre2 and pre2.traffic_lights:
                    has_traffic_lights = True

                incoming_lanes.append(lane)
        # extend all incoming lanes in scenario
        all_incoming_lanes_in_scenario.extend(incoming_lanes)

        # merge short incomings with predecessors
        remove_short_predeccesors(intermediate_format, intersection, all_incoming_lanes_in_scenario)

        # modify intersection if traffic lights where found, else skip to next intersection
        if has_traffic_lights:
            # remove existing traffic lights
            remove_existing_traffic_lights(incoming_lanes)
            # create new traffic lights
            create_new_traffic_lights(intersection)
            # remove inner traffic lights in the middle of bigger crossings
            remove_innner_lights(intersection, incoming_lanes)

    # remove traffic lights that are not part of any intersection
    remove_non_intersection_lights(all_incoming_lanes_in_scenario)
    # clean up and remove invalid references
    intermediate_format.remove_invalid_references()


def check_pre_incoming_lane(lane, intermediate_format):
    """
    Determines if any predecessor of a lane is part of another intersection as successor
    """
    for intersection in intermediate_format.intersections:
        all_succesors = set()
        for incoming in intersection.incomings:
            all_succesors.update(incoming.successors_left)
            all_succesors.update(incoming.successors_right)
            all_succesors.update(incoming.successors_straight)
        for pre in lane.predecessors:
            if pre in all_succesors:
                return True
    return False


def merge_incoming(incoming, intermediate_format, all_incoming_lanes_in_scenario):
    """
    Merge incomings of intersection with predecessor edge
    """
    for incoming_id in incoming.incoming_lanelets:
        edge = intermediate_format.find_edge_by_id(incoming_id)

        # only one predecessor edge is allowed
        if not len(edge.predecessors) == 1:
            return

        pre = intermediate_format.find_edge_by_id(edge.predecessors[0])

        # predecessor is not allowed to be another incoming lane
        if pre in all_incoming_lanes_in_scenario:
            return

        assert len(pre.left_bound) == len(pre.right_bound) == len(pre.center_points)
        assert len(edge.left_bound) == len(edge.right_bound) == len(edge.center_points)

        shared_node = None
        # find shared node
        if edge.node1.id == pre.node2.id:
            shared_node = edge.node1
        elif edge.node2.id == pre.node1.id:
            shared_node = edge.node2
        else:
            raise ValueError
        assert shared_node is not None

        if shared_node.id == edge.node1.id:
            edge.node1 = pre.node1
        elif shared_node.id == edge.node2:
            edge.node2 = pre.node2
        else:
            raise ValueError

        edge.right_bound = pre.right_bound + edge.right_bound
        edge.left_bound = pre.left_bound + edge.left_bound
        edge.center_points = pre.center_points + edge.center_points
        assert len(edge.left_bound) == len(edge.right_bound) == len(edge.center_points)

        # traffic lights and signs
        edge.traffic_signs.union(pre.traffic_signs)
        edge.traffic_lights.union(pre.traffic_lights)

        # update predeccessors
        edge.predecessors = pre.predecessors
        for pre_pre in pre.predecessors:
            pre_pre_edge = intermediate_format.find_edge_by_id(pre_pre)

            pre_pre_edge.successors.remove(pre.id)
            pre_pre_edge.successors.append(edge.id)

        # remove pre from edge list
        intermediate_format.edges.remove(pre)

        # update adajcent opposite direction
        if edge.adjacent_left and not edge.adjacent_left_direction_equal:
            merge_outgoing(
                intermediate_format.find_edge_by_id(edge.adjacent_left),
                intermediate_format,
                all_incoming_lanes_in_scenario,
            )


def merge_outgoing(outgoing, intermediate_format, all_incoming_lanes_in_scenario):
    """
    Merge outgoings of intersection with sucessor edge
    """
    if not (
        geometry.distance(outgoing.center_points[0], [outgoing.center_points[-1]]) < 2
        and len(outgoing.successors) == 1  # shorter than 2 meters
    ):
        return

    suc = intermediate_format.find_edge_by_id(outgoing.successors[0])

    # successor is not allowed to be an incoming
    if suc in all_incoming_lanes_in_scenario:
        return

    assert len(suc.left_bound) == len(suc.right_bound) == len(suc.center_points)
    assert len(outgoing.left_bound) == len(outgoing.right_bound) == len(outgoing.center_points)

    shared_node = None
    # find shared node
    if outgoing.node1.id == suc.node2.id:
        shared_node = outgoing.node1
    elif outgoing.node2.id == suc.node1.id:
        shared_node = outgoing.node2
    else:
        raise ValueError

    assert shared_node is not None

    if shared_node.id == outgoing.node1.id:
        outgoing.node1 = suc.node1
    elif shared_node.id == outgoing.node2.id:
        outgoing.node2 = suc.node2
    else:
        raise ValueError

    outgoing.right_bound = outgoing.right_bound + suc.right_bound
    outgoing.left_bound = outgoing.left_bound + suc.left_bound
    outgoing.center_points = outgoing.center_points + suc.center_points
    assert len(outgoing.left_bound) == len(outgoing.right_bound) == len(outgoing.center_points)

    # traffic lights and signs
    outgoing.traffic_signs.union(suc.traffic_signs)
    outgoing.traffic_lights.union(suc.traffic_lights)

    # update successors
    outgoing.successors = suc.successors
    for suc_suc in suc.successors:
        suc_suc_edge = intermediate_format.find_edge_by_id(suc_suc)

        suc_suc_edge.predecessors.remove(suc.id)
        suc_suc_edge.predecessors.append(outgoing.id)

    # remove suc from edge list
    intermediate_format.edges.remove(suc)

    # update adjacent same direction
    if outgoing.adjacent_right and outgoing.adjacent_left_direction_equal:
        merge_outgoing(
            intermediate_format.find_edge_by_id(outgoing.adjacent_right),
            intermediate_format,
            all_incoming_lanes_in_scenario,
        )


def remove_short_predeccesors(intermediate_format, intersection, all_incoming_lanes_in_scenario):
    """
    Merge very short incomings with predecessors
    """
    for incoming in intersection.incomings:
        merge = True
        for incoming_lane in incoming.incoming_lanelets:
            edge = intermediate_format.find_edge_by_id(incoming_lane)
            if (
                geometry.distance(edge.center_points[0], [edge.center_points[-1]]) < 2
                and len(edge.predecessors) == 1  # shorter than 2 meters
                and not check_pre_incoming_lane(edge, intermediate_format)
                and edge.adjacent_right is None
            ):
                merge = True
                break
            merge = False
        if merge:
            merge_incoming(incoming, intermediate_format, all_incoming_lanes_in_scenario)
