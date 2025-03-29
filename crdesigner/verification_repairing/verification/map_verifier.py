import copy
import enum
import logging
import multiprocessing
from multiprocessing import Process
from typing import List, Tuple

from commonroad.scenario.lanelet import LaneletNetwork

from crdesigner.verification_repairing.config import MapVerParams
from crdesigner.verification_repairing.partitioning.map_partition import (
    IntersectionBlock,
    LaneletBlock,
    LaneletPartitioning,
    Partition,
    TrafficLightBlock,
    TrafficLightPartitioning,
    TrafficSignBlock,
    TrafficSignPartitioning,
    pymetis_imported,
)
from crdesigner.verification_repairing.verification.formula_ids import (
    FormulaID,
    FormulaTypes,
    LaneletFormulaID,
    TrafficLightFormulaID,
    TrafficSignFormulaID,
    extract_formula_ids_by_type,
    filter_formula_ids_by_type,
)
from crdesigner.verification_repairing.verification.hol.mapping import HOLMapping
from crdesigner.verification_repairing.verification.hol.satisfaction import (
    HOLVerificationChecker,
)
from crdesigner.verification_repairing.verification.satisfaction import InvalidStates


class MapVerifier:
    def __init__(self, network: LaneletNetwork, config: MapVerParams):
        """
        Constructor.

        :param network: Lanelet network.
        :param config: Configuration.
        """
        # self._complete_map_name = network.meta_information.complete_map_name
        self._network = network
        self._config = config

    def verify(self) -> InvalidStates:
        """
        Verifies and detects the invalid states in the map.

        :return: Invalid states.
        """
        if self._config.evaluation.partitioned and pymetis_imported:
            if not pymetis_imported:
                logging.error(
                    "MapVerifier::verify: pymetis could not be imported for partitioning."
                )
            invalid_states = self._partitioned_verify()
        else:
            invalid_states = self._unpartitioned_verify()

        return invalid_states

    def _unpartitioned_verify(self) -> InvalidStates:
        """
        Verifies and detects the invalid states in the map.

        :return: Invalid states.
        """
        mapping = self._create_mapping(self._network, self._config)

        mapping.map_verification_paras()
        mapping.map_lanelet_network()

        formula_ids = [
            formula
            for formula in self._config.verification.formulas
            if formula not in self._config.verification.excluded_formulas
        ]
        valid_checker = self._create_verifier(mapping, formula_ids)

        results = []
        valid_checker.check_validity(self._config.verification, results)

        return results[0]

    def _partitioned_verify(self) -> InvalidStates:
        """
        Verifies and detects the invalid states in all blocks of maps partition.

        :return: Invalid states.
        """
        processes = []

        manager = multiprocessing.Manager()
        results = manager.list()

        for formula_type in FormulaTypes:
            if self._config.verification.formulas is None:
                formula_ids = extract_formula_ids_by_type(formula_type)
            else:
                formula_ids = filter_formula_ids_by_type(
                    self._config.verification.formulas, formula_type
                )
            formula_ids = [
                formula
                for formula in formula_ids
                if formula not in self._config.verification.excluded_formulas
            ]

            if not formula_ids:
                continue

            partition, draw_file_name = MapVerifier._create_partitioning(
                formula_type, self._network, self._config
            )

            # if self._config.evaluation.partition_draw_dir is not None:
            #     drawer = PartitionDrawer(self._network)
            #     drawer.save_partition_drawing(partition, self._config.evaluation.partition_draw_dir,
            #                                   f'{draw_file_name}-{self._complete_map_name}')

            mappings = []
            for block in partition:
                network = self._reduce_network(block)

                mapping = MapVerifier._create_mapping(network, self._config)
                mappings.append(mapping)

            for mapping in mappings:
                mapping.map_verification_paras()
                mapping.map_lanelet_network()

                valid_checker = MapVerifier._create_verifier(mapping, formula_ids)

                if len(processes) >= self._config.verification.num_threads:
                    for p in processes:
                        p.join()
                    processes.clear()

                p = Process(
                    target=valid_checker.check_validity, args=(self._config.verification, results)
                )
                processes.append(p)
                p.start()

        for p in processes:
            p.join()

        invalid_states = {}
        for result in results:
            for invalid_state_id, locations in result.items():
                if invalid_state_id in invalid_states.keys():
                    for location in locations:
                        if location not in invalid_states[invalid_state_id]:
                            invalid_states[invalid_state_id].append(location)
                else:
                    invalid_states.update({invalid_state_id: locations})

        return invalid_states

    def _reduce_network(
        self, block: Tuple[LaneletBlock, TrafficSignBlock, TrafficLightBlock, IntersectionBlock]
    ) -> LaneletNetwork:
        """
        Reduces network to a smaller network which includes all lanelets, traffic signs, traffic lights, and
        intersections contained by the block of partition.

        :return: Reduced lanelet network
        """
        lanelet_block, traffic_sign_block, traffic_light_block, intersection_block = block

        network = LaneletNetwork()

        # Construct the smaller network
        for lanelet_id in lanelet_block:
            lanelet = self._network.find_lanelet_by_id(lanelet_id)
            network.add_lanelet(copy.deepcopy(lanelet))

        for traffic_sign_id in traffic_sign_block:
            traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)
            network.add_traffic_sign(copy.deepcopy(traffic_sign), set())

        for traffic_light_id in traffic_light_block:
            traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)
            network.add_traffic_light(copy.deepcopy(traffic_light), set())

        for intersection_id in intersection_block:
            intersection = self._network.find_intersection_by_id(intersection_id)
            network.add_intersection(copy.deepcopy(intersection))

        # Remove references from lanelets in other blocks
        for lanelet in network.lanelets:
            left_adj = lanelet.adj_left
            if left_adj is not None and left_adj not in lanelet_block:
                if self._network.find_lanelet_by_id(left_adj) is not None:
                    lanelet.adj_left = None

            right_adj = lanelet.adj_right
            if right_adj is not None and right_adj not in lanelet_block:
                if self._network.find_lanelet_by_id(right_adj) is not None:
                    lanelet.adj_right = None

            predecessor = copy.copy(lanelet.predecessor)
            for pre in predecessor:
                if self._network.find_lanelet_by_id(pre) is not None and pre not in lanelet_block:
                    lanelet.predecessor.remove(pre)

            successor = copy.copy(lanelet.successor)
            for suc in successor:
                if self._network.find_lanelet_by_id(suc) is not None and suc not in lanelet_block:
                    lanelet.successor.remove(suc)

        network.cleanup_traffic_sign_references()
        network.cleanup_traffic_light_references()

        return network

    @staticmethod
    def _create_mapping(network: LaneletNetwork, config: MapVerParams) -> HOLMapping:
        """
        Constructor.

        :param network: Lanelet network.
        :param config: Configuration.
        """

        mapping = HOLMapping(network, config)

        return mapping

    @staticmethod
    def _create_verifier(
        mapping: HOLMapping, formula_ids: List[FormulaID]
    ) -> HOLVerificationChecker:
        """
        Creates for the solver a corresponding validity checker.

        :param mapping: Mapping.
        :param formula_ids: Formula IDs.
        :return: Validity checker.
        """

        verifier = HOLVerificationChecker(mapping, formula_ids)

        return verifier

    @staticmethod
    def _create_partitioning(
        formula_type: enum.EnumMeta, network: LaneletNetwork, config: MapVerParams
    ) -> Tuple[Partition, str]:
        """
        Creates a partition of the network.

        :param formula_type: Formula type.
        :param network: Lanelet network.
        :param config: Configuration parameters.
        :return: Partition and corresponding file name.
        """

        if formula_type == LaneletFormulaID:
            partition = LaneletPartitioning(network).normal_partition(
                ref_size=config.partitioning.lanelet_chunk_size, buffered=True
            )
        elif formula_type == TrafficSignFormulaID:
            partition = TrafficSignPartitioning(network).signs_chunks_partition(
                size=config.partitioning.traffic_sign_chunk_size
            )
        elif formula_type == TrafficLightFormulaID:
            partition = TrafficLightPartitioning(network).lights_chunks_partition(
                size=config.partitioning.traffic_light_chunk_size
            )
        else:
            partition = []  # TODO: Implement

        file_name = formula_type.__name__

        return partition, file_name
