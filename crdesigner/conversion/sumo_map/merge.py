import os
from functools import reduce
from typing import *

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.scenario.lanelet import Lanelet
from commonroad.scenario.scenario import Scenario


def merge(to_merge: List[int], scenario: Scenario) -> Tuple[Scenario, int]:
    lanelet_network = scenario.lanelet_network
    lanelets = [lanelet_network.find_lanelet_by_id(lanelet_id) for lanelet_id in to_merge]

    merged_lanelet = reduce(Lanelet.merge_lanelets, lanelets)

    merged_lanelet._lanelet_type = {t for lanelet in lanelets for t in lanelet.lanelet_type}
    merged_lanelet._traffic_signs = {t for lanelet in lanelets for t in lanelet.traffic_signs}
    merged_lanelet._traffic_lights = {t for lanelet in lanelets for t in lanelet.traffic_lights}

    lanelet_network._lanelets = {l.lanelet_id: l for l in lanelet_network.lanelets + [merged_lanelet]
                                 if l.lanelet_id not in to_merge}
    to_merge = set(to_merge)
    update = lambda ids: list(set(ids) - to_merge | {merged_lanelet.lanelet_id})

    # update other lanelets
    for lanelet in lanelet_network.lanelets:
        if to_merge & set(lanelet.predecessor):
            lanelet._predecessor = update(lanelet.predecessor)
        if to_merge & set(lanelet.successor):
            lanelet._successor = update(lanelet.successor)
        if lanelet.adj_left in to_merge:
            lanelet._adj_left = merged_lanelet.lanelet_id
        if lanelet.adj_right in to_merge:
            lanelet._adj_right = merged_lanelet.lanelet_id

    # intersection handling
    for intersection in lanelet_network.intersections:
        for incoming in intersection.incomings:
            def update_incoming():
                if merged_lanelet.lanelet_id in incoming.incoming_lanelets:
                    incoming._incoming_lanelets = incoming.incoming_lanelets - {merged_lanelet.lanelet_id} | set(
                        merged_lanelet.predecessor)

            if to_merge & set(incoming.incoming_lanelets):
                incoming._incoming_lanelets = set(update(incoming.incoming_lanelets))
            if to_merge & set(incoming.successors_left):
                update_incoming()
                incoming._successors_left = set(update(incoming.successors_left))
            if to_merge & set(incoming.successors_right):
                update_incoming()
                incoming._successors_right = set(update(incoming.successors_right))
            if to_merge & set(incoming.successors_straight):
                update_incoming()
                incoming._successors_straight = set(update(incoming.successors_straight))

    scenario.lanelet_network = lanelet_network
    scenario.scenario_id = "DEU_test"
    return scenario, merged_lanelet.lanelet_id


base_path = os.path.abspath(os.path.join(__file__, "../..", "..", "..", "test", "sumo_xml_test_files"))
scenario_name = "garching"
scenario_path = os.path.join(base_path, scenario_name + ".xml")
scenario, planning_problem = CommonRoadFileReader(scenario_path).open()

scenario, lanelet_id = merge([266, 225], scenario)
scenario, lanelet_id = merge([lanelet_id, 228], scenario)
scenario, lanelet_id = merge([253, 226], scenario)
scenario, lanelet_id = merge([lanelet_id, 229], scenario)
scenario, lanelet_id = merge([222, 258], scenario)
scenario, lanelet_id = merge([223, 269], scenario)
scenario, lanelet_id = merge([207, 254], scenario)
scenario, lanelet_id = merge([208, 264], scenario)
scenario, lanelet_id = merge([210, 263], scenario)
scenario, lanelet_id = merge([211, 273], scenario)

new_scenario_path = os.path.join(base_path, f"{scenario_name}_merged.xml")
CommonRoadFileWriter(scenario,
                     planning_problem,
                     author=scenario.author,
                     affiliation=scenario.affiliation,
                     source=scenario.source,
                     tags=scenario.tags,
                     location=scenario.location) \
    .write_scenario_to_file(new_scenario_path, overwrite_existing_file=True)
