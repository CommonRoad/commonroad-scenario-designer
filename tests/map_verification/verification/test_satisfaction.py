import unittest

import numpy as np
import warnings

from commonroad.common.common_lanelet import LaneletType
from commonroad.scenario.lanelet import Lanelet, StopLine, LineMarking, LaneletNetwork
from commonroad.scenario.scenario import ScenarioID
from commonroad.scenario.traffic_sign import TrafficSign, TrafficSignElement, TrafficSignIDGermany
from commonroad.scenario.traffic_light import TrafficLight, TrafficLightState, TrafficLightCycleElement, \
    TrafficLightCycle

from crdesigner.verification_repairing.verification.formula_ids import FormulaID, LaneletFormulaID, \
    TrafficSignFormulaID, TrafficLightFormulaID, GeneralFormulaID
from crdesigner.verification_repairing.verification.hol.mapping import HOLMapping
from crdesigner.verification_repairing.verification.hol.satisfaction import HOLVerificationChecker
from crdesigner.verification_repairing.config import VerificationParams

warnings.filterwarnings("ignore")


class TestFormulaPool(unittest.TestCase):
    """
    The class supports methods for testing purposes.
    """

    def check_sat(self, formula_id: FormulaID, road_network: LaneletNetwork, expected: bool):
        """
        Checks whether an invalid state is inferred by a specific formula using desired solvers.

        :param formula_id: Formula ID.
        :param road_network: CommonRoad lanelet network
        :param expected: Boolean indicates the expected value for the assertions. True means violation of specification.
        """

        mapping = HOLMapping(road_network)

        mapping.map_verification_paras()
        mapping.map_lanelet_network()

        verifier = HOLVerificationChecker(mapping, [formula_id])

        invalid_states = []
        config = VerificationParams()
        verifier.check_validity(config, invalid_states)

        self.assertEqual(expected, bool(invalid_states[0]))


class TestGeneralFormulaPool(TestFormulaPool):
    """
    The class tests the verification of lanelet elements.
    """
    def setUp(self) -> None:
        self.lanelet_1 = Lanelet(np.array([[0., 1.], [1., 1.]]), np.array([[0., 0.5], [1., 0.5]]),
                                 np.array([[0., 0.], [1., 0.]]), 1, traffic_signs={3}, traffic_lights={4})
        self.lanelet_2 = Lanelet(np.array([[1., 1.], [1.5, 1.], [2., 1.]]),
                                 np.array([[1., 0.5], [1.5, 0.5], [2., 0.5]]),
                                 np.array([[1., 0.], [1.5, 0.], [2., 0.]]), 2)

        self.network = LaneletNetwork()
        self.scenario_id = ScenarioID()
        self.network.add_lanelet(self.lanelet_1)
        self.network.add_lanelet(self.lanelet_2)

        traffic_sign_element = TrafficSignElement(TrafficSignIDGermany.MAX_SPEED, ['120'])
        self.traffic_sign = TrafficSign(3, [traffic_sign_element], {1}, np.array([0., 0.]))
        self.network.add_traffic_sign(self.traffic_sign, {1})

        self.traffic_light = TrafficLight(4, np.array([00., 0.0]))
        self.network.add_traffic_light(self.traffic_light, {1})

    def test_unique_id(self):
        formula_id = GeneralFormulaID.UNIQUE_ID

        # only supported by HOL
        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.lanelet_id = 1

        self.check_sat(formula_id, self.network, expected=True)


class TestLaneletFormulaPool(TestFormulaPool):
    """
    The class tests the verification of lanelet elements.
    """

    def setUp(self) -> None:
        self.lanelet_1 = Lanelet(np.array([[0., 1.], [0.5, 1.], [1., 1.]]),
                                 np.array([[0., 0.5], [0.5, 0.5], [1., 0.5]]),
                                 np.array([[0., 0.], [0.5, 0.], [1., 0.]]), 1)
        self.lanelet_2 = Lanelet(np.array([[1., 1.], [1.5, 1.], [2., 1.]]),
                                 np.array([[1., 0.5], [1.5, 0.5], [2., 0.5]]),
                                 np.array([[1., 0.], [1.5, 0.], [2., 0.]]), 2)

        self.network = LaneletNetwork()
        self.network.add_lanelet(self.lanelet_1)
        self.network.add_lanelet(self.lanelet_2)

    def test_same_vertices_size(self):
        formula_id = LaneletFormulaID.SAME_VERTICES_SIZE

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.left_vertices = np.array([[0., 1.], [1., 1.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_vertices_more_than_one(self):
        formula_id = LaneletFormulaID.VERTICES_MORE_THAN_ONE

        self.check_sat(formula_id, self.network, expected=False)

    def test_existence_left_adj(self):
        formula_id = LaneletFormulaID.EXISTENCE_LEFT_ADJ

        self.lanelet_1.adj_left = 2

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_left = 3

        self.check_sat(formula_id, self.network, expected=True)

    def test_existence_right_adj(self):
        formula_id = LaneletFormulaID.EXISTENCE_RIGHT_ADJ

        self.lanelet_1.adj_right = 2

        self.check_sat(formula_id, self.network,  expected=False)

        self.lanelet_1.adj_right = 3

        self.check_sat(formula_id, self.network, expected=True)

    def test_existence_predecessor(self):
        formula_id = LaneletFormulaID.EXISTENCE_PREDECESSOR

        self.lanelet_1.predecessor = [2]

        self.check_sat(formula_id, self.network,  expected=False)

        self.lanelet_1.predecessor = [3]

        self.check_sat(formula_id, self.network,  expected=True)

    def test_existence_successor(self):
        formula_id = LaneletFormulaID.EXISTENCE_SUCCESSOR

        self.lanelet_1.successor = [2]

        self.check_sat(formula_id, self.network,  expected=False)

        self.lanelet_1.successor = [3]

        self.check_sat(formula_id, self.network,  expected=True)

    def test_connections_predecessor(self):
        formula_id = LaneletFormulaID.CONNECTIONS_PREDECESSOR

        self.lanelet_2.left_vertices = np.array([[-1., 1.], [0., 1.]])
        self.lanelet_2.right_vertices = np.array([[-1., 0.], [0., 0.]])
        self.lanelet_1.predecessor = [2]

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.left_vertices = np.array([[-1., 1.], [0., 1.25]])

        self.check_sat(formula_id, self.network,  expected=True)

    def test_connections_successor(self):
        formula_id = LaneletFormulaID.CONNECTIONS_SUCCESSOR

        self.lanelet_1.successor = [2]

        self.check_sat(formula_id, self.network,  expected=False)

        self.lanelet_2.left_vertices = np.array([[0., 1.], [1., 1.25]])

        self.check_sat(formula_id, self.network,  expected=True)

    def test_polylines_left_same_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POLYLINES_LEFT_SAME_DIR_PARALLEL_ADJ

        self.lanelet_2.right_vertices = np.array([[0., 1.], [0.5, 1.], [1., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.right_vertices = np.array([[0., 1.], [0.5, 1.25], [1., 1.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_polylines_left_opposite_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POLYLINES_LEFT_OPPOSITE_DIR_PARALLEL_ADJ

        self.lanelet_2.left_vertices = np.array([[1., 1.], [0.5, 1.], [0., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = False

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.left_vertices = np.array([[1., 1.], [0.5, 0.75], [0., 1.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_polylines_right_same_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POLYLINES_RIGHT_SAME_DIR_PARALLEL_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 0.], [0.5, 0.], [1., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.left_vertices = np.array([[0., 0.], [0.5, 0.9], [1., 0.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_polylines_right_opposite_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POLYLINES_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ

        self.lanelet_2.right_vertices = np.array([[1., 0.], [0.5, 0.], [0., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = False

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.right_vertices = np.array([[1., 0.], [0.5, 0.25], [0., 0.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_connections_left_merging_adj(self):
        formula_id = LaneletFormulaID.CONNECTIONS_LEFT_MERGING

        self.lanelet_2.left_vertices = np.array([[0., 2.], [0.5, 1.5], [1., 1.]])
        self.lanelet_2.right_vertices = np.array([[0., 1.], [0.5, 0.5], [1., 0.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.left_vertices = np.array([[0., 2.], [0.5, 1.5], [1., 1.25]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_connections_right_merging_adj(self):
        formula_id = LaneletFormulaID.CONNECTIONS_RIGHT_MERGING

        self.lanelet_2.left_vertices = np.array([[0., 0.], [0.5, 0.5], [1., 1.]])
        self.lanelet_2.right_vertices = np.array([[0., -1.], [0.5, 0.75], [1., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.right_vertices = np.array([[0., -1.], [0.5, 0.75], [1., -0.25]])

        self.check_sat(formula_id, self.network,  expected=True)

    def test_connections_left_forking_adj(self):
        formula_id = LaneletFormulaID.CONNECTIONS_LEFT_FORKING

        self.lanelet_2.left_vertices = np.array([[0., 1.], [0.5, 1.5], [1., 2.]])
        self.lanelet_2.right_vertices = np.array([[0., 0.], [0.5, 0.5], [1., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.left_vertices = np.array([[0., 1.25], [0.5, 1.5], [1., 2.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_connections_right_forking_adj(self):
        formula_id = LaneletFormulaID.CONNECTIONS_RIGHT_FORKING

        self.lanelet_2.left_vertices = np.array([[0., 1.], [0.5, 0.5], [1., 0.]])
        self.lanelet_2.right_vertices = np.array([[0., 0.], [0.5, -0.5], [1., -1.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_2.right_vertices = np.array([[0., -0.25], [0.5, -0.5], [1., -1.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_successor(self):
        formula_id = LaneletFormulaID.POTENTIAL_SUCCESSOR

        self.lanelet_1.successor = [2]

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.successor = []

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_predecessor(self):
        formula_id = LaneletFormulaID.POTENTIAL_PREDECESSOR

        self.lanelet_2.left_vertices = np.array([[-1., 1.], [-0.5, 1.], [0., 1.]])
        self.lanelet_2.right_vertices = np.array([[-1., 0.], [-0.5, 0.], [0., 0.]])
        self.lanelet_1.predecessor = [2]

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.predecessor = []

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_left_same_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_LEFT_SAME_DIR_PARALLEL_ADJ

        self.lanelet_2.right_vertices = np.array([[0., 1.], [0.5, 1.], [1., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_left = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_left_opposite_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_LEFT_OPPOSITE_DIR_PARALLEL_ADJ

        self.lanelet_2.left_vertices = np.array([[1., 1.], [0.5, 1.], [0., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = False
        self.lanelet_2.adj_left = 1
        self.lanelet_2.adj_left_same_direction = False

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_left = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_right_same_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_RIGHT_SAME_DIR_PARALLEL_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 0.], [0.5, 0.], [1., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_right = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_right_opposite_dir_parallel_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_RIGHT_OPPOSITE_DIR_PARALLEL_ADJ

        self.lanelet_2.right_vertices = np.array([[1., 0.], [0.5, 0.], [0., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = False
        self.lanelet_2.adj_right = 1
        self.lanelet_1.adj_right_same_direction = False

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_right = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_left_merging_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_LEFT_MERGING_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 2.], [0.5, 1.5], [1., 1.]])
        self.lanelet_2.right_vertices = np.array([[0., 1.], [0.5, 0.5], [1., 0.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_left = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_right_merging_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_RIGHT_MERGING_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 0.], [0.5, 0.5], [1., 1.]])
        self.lanelet_2.right_vertices = np.array([[0., -1.], [0.5, 0.75], [1., 0.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_right = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_left_forking_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_LEFT_FORKING_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 1.], [0.5, 1.5], [1., 2.]])
        self.lanelet_2.right_vertices = np.array([[0., 0.], [0.5, 0.5], [1., 1.]])
        self.lanelet_1.adj_left = 2
        self.lanelet_1.adj_left_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_left = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_potential_right_forking_adj(self):
        formula_id = LaneletFormulaID.POTENTIAL_RIGHT_FORKING_ADJ

        self.lanelet_2.left_vertices = np.array([[0., 1.], [0.5, 0.5], [1., 0.]])
        self.lanelet_2.right_vertices = np.array([[0., 0.], [0.5, -0.5], [1., -1.]])
        self.lanelet_1.adj_right = 2
        self.lanelet_1.adj_right_same_direction = True

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.adj_right = None

        self.check_sat(formula_id, self.network, expected=True)

    def test_non_successor_as_predecessor(self):
        formula_id = LaneletFormulaID.NON_SUCCESSOR_AS_PREDECESSOR

        self.lanelet_1.successor = [2]

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.successor = []
        self.lanelet_1.predecessor = [2]

        self.check_sat(formula_id, self.network, expected=True)

    def test_non_predecessor_as_successor(self):
        formula_id = LaneletFormulaID.NON_PREDECESSOR_AS_SUCCESSOR

        self.lanelet_2.left_vertices = np.array([[-1., 1.], [0., 1.]])
        self.lanelet_2.right_vertices = np.array([[-1., 0.], [0., 0.]])
        self.lanelet_1.predecessor = [2]

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.predecessor = []
        self.lanelet_1.successor = [2]

        self.check_sat(formula_id, self.network, expected=True)

    def test_polylines_intersection(self):
        formula_id = LaneletFormulaID.POLYLINES_INTERSECTION

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.left_vertices = np.array([[0., 1.], [0.5, 0.], [1., -1.]])

        self.check_sat(formula_id, self.network, expected=True)

    def test_left_self_intersection(self):
        formula_id = LaneletFormulaID.LEFT_SELF_INTERSECTION

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.left_vertices = np.array([[0., 1.], [0.5, 1.], [0.5, 1.5], [0.25, 1.5], [0.25, 1.5], [0.5, 1.]])
        self.check_sat(formula_id, self.network, expected=True)

        self.lanelet_1.left_vertices = np.array([[0.0, 1.], [0.5, 1.], [0.25, 1.0], [0.75, 1.0]])
        self.check_sat(formula_id, self.network, expected=True)

        self.lanelet_1.left_vertices = np.array([[0.0, 1.], [0.5, 1.], [0.5, 1.0], [0.75, 1.0]])
        self.check_sat(formula_id, self.network, expected=True)

    def test_right_self_intersection(self):
        formula_id = LaneletFormulaID.RIGHT_SELF_INTERSECTION

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.right_vertices = np.array([[0., 1.], [0.5, 1.], [0.5, 1.5], [0.25, 1.5], [0.25, 1.5], [0.5, 1.]])
        self.check_sat(formula_id, self.network, expected=True)

        self.lanelet_1.right_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.25, 1.0], [0.75, 1.0]])
        self.check_sat(formula_id, self.network, expected=True)

        self.lanelet_1.right_vertices = np.array([[0.0, 1.0], [0.5, 1.0], [0.5, 1.0], [0.75, 1.0]])
        self.check_sat(formula_id, self.network, expected=True)

    # def test_lanelet_types_combination(self):
    #     formula_id = LaneletFormulaID.LANELET_TYPES_COMBINATION
    #
    #     self.lanelet_1.lanelet_type = {LaneletType.DRIVE_WAY, LaneletType.SIDEWALK}
    #
    #     self.check_sat(formula_id, self.network, expected=False)
    #
    #     self.lanelet_1.lanelet_type = {LaneletType.CROSSWALK, LaneletType.INTERSTATE, LaneletType.URBAN}
    #     self.lanelet_2.lanelet_type = {LaneletType.BUS_STOP, LaneletType.INTERSTATE}
    #
    #     self.check_sat(formula_id, self.network, expected=True)

    def test_conflicting_lanelet_directions(self):
        formula_id = LaneletFormulaID.LEFT_RIGHT_BOUNDARY_ASSIGNMENT

        self.check_sat(formula_id, self.network, expected=False)

        self.network.add_lanelet(
            Lanelet(np.array([[2., 1.], [1., 1.]]), np.array([[2., 0.5], [1., 0.5]]), np.array([[2., 0.], [1., 0.]]),
                    1111))

        self.check_sat(formula_id, self.network, expected=True)

    def test_left_right_boundary_assignment(self):
        formula_id = LaneletFormulaID.LEFT_RIGHT_BOUNDARY_ASSIGNMENT

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.right_vertices, self.lanelet_1.left_vertices = np.flip(self.lanelet_1.left_vertices), \
            np.flip(self.lanelet_1.right_vertices)

        self.check_sat(formula_id, self.network, expected=True)

    def test_existence_traffic_signs(self):
        formula_id = LaneletFormulaID.EXISTENCE_TRAFFIC_SIGNS

        traffic_sign = TrafficSign(3, [], {1}, np.array([0., 0.]))
        self.network.add_traffic_sign(traffic_sign, {1})
        self.lanelet_1.traffic_signs = {3}

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.traffic_signs = {4}

        self.check_sat(formula_id, self.network, expected=True)

    def test_existence_traffic_lights(self):
        formula_id = LaneletFormulaID.EXISTENCE_TRAFFIC_LIGHTS

        traffic_light = TrafficLight(3, np.array([0., 0.]))
        self.network.add_traffic_light(traffic_light, {1})
        self.lanelet_1.traffic_lights = {3}

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.traffic_lights = {4}

        self.check_sat(formula_id, self.network, expected=True)

    # def test_existence_stop_line_traffic_signs(self):
    #     formula_id = LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_SIGNS
    #
    #     traffic_sign = TrafficSign(3, [], {1}, np.array([0., 0.]))
    #     self.network.add_traffic_sign(traffic_sign, {1})
    #     stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.SOLID)
    #     self.lanelet_1.stop_line = stop_line
    #     self.lanelet_1.stop_line.traffic_sign_ref = {3}
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     self.lanelet_1.stop_line.traffic_sign_ref = {4}
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)

    # def test_existence_stop_line_traffic_lights(self):
    #     formula_id = LaneletFormulaID.EXISTENCE_STOP_LINE_TRAFFIC_LIGHTS
    #
    #     traffic_light = TrafficLight(3, np.array([0., 0.]))
    #     self.network.add_traffic_light(traffic_light, {1})
    #     stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.SOLID)
    #     self.lanelet_1.stop_line = stop_line
    #     self.lanelet_1.stop_line.traffic_light_ref = {3}
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     self.lanelet_1.stop_line.traffic_light_ref = {4}
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)

    def test_included_stop_line_traffic_signs(self):
        formula_id = LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_SIGNS

        traffic_sign = TrafficSign(3, [], {1}, np.array([0., 0.]))
        self.network.add_traffic_sign(traffic_sign, {1})
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.SOLID)
        self.lanelet_1.stop_line = stop_line
        self.lanelet_1.traffic_signs = {3}
        self.lanelet_1.stop_line.traffic_sign_ref = {3}

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.traffic_signs = set()

        self.check_sat(formula_id, self.network, expected=True)

    def test_included_stop_line_traffic_lights(self):
        formula_id = LaneletFormulaID.INCLUDED_STOP_LINE_TRAFFIC_LIGHTS

        traffic_light = TrafficLight(3, np.array([0., 0.]))
        self.network.add_traffic_light(traffic_light, {1})
        stop_line = StopLine(np.array([0., 0.]), np.array([1., 1.]), LineMarking.SOLID)
        self.lanelet_1.stop_line = stop_line
        self.lanelet_1.traffic_lights = {3}
        self.lanelet_1.stop_line.traffic_light_ref = {3}

        self.check_sat(formula_id, self.network, expected=False)

        self.lanelet_1.traffic_lights = set()

        self.check_sat(formula_id, self.network, expected=True)

    def test_zero_or_two_points_stop_line(self):
        formula_id = LaneletFormulaID.ZERO_OR_TWO_POINTS_STOP_LINE

        stop_line = StopLine(start=np.array([0., 0.]), end=np.array([1., 1.]), line_marking=LineMarking.SOLID)
        self.lanelet_1.stop_line = stop_line

        self.check_sat(formula_id, self.network, expected=False)

        stop_line = StopLine(start=np.array([0., 0.]), end=None, line_marking=LineMarking.SOLID)
        self.lanelet_1.stop_line = stop_line

        self.check_sat(formula_id, self.network, expected=True)

    # def test_stop_line_points_on_polylines(self):
    #     formula_id = LaneletFormulaID.STOP_LINE_POINTS_ON_POLYLINES
    #
    #     stop_line = StopLine(start=np.array([1., 1.]), end=np.array([1., 0.]), line_marking=LineMarking.SOLID)
    #     self.lanelet_1.stop_line = stop_line
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     stop_line.start = np.array([1., 1.])
    #     stop_line.end = np.array([1.1, 0.1])
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)


class TestTrafficSignFormulaPool(TestFormulaPool):
    """
    The class tests the repairing of traffic sign elements.
    """

    def setUp(self) -> None:
        lanelet = Lanelet(np.array([[0., 1.], [1., 1.]]),
                          np.array([[0., 0.5], [1., 0.5]]),
                          np.array([[0., 0.], [1., 0.]]), 1, traffic_signs={2})
        traffic_sign_element = TrafficSignElement(TrafficSignIDGermany.MAX_SPEED, ['120'])
        self.traffic_sign = TrafficSign(2, [traffic_sign_element], {1}, np.array([0., 0.]))

        self.network = LaneletNetwork()
        self.network.add_lanelet(lanelet)
        self.network.add_traffic_sign(self.traffic_sign, {1})

    def test_at_least_one_traffic_sign_element(self):
        formula_id = TrafficSignFormulaID.AT_LEAST_ONE_TRAFFIC_SIGN_ELEMENT

        self.check_sat(formula_id, self.network, expected=False)

        self.traffic_sign.traffic_sign_elements = []

        self.check_sat(formula_id, self.network,  expected=True)

    def test_referenced_traffic_sign(self):
        formula_id = TrafficSignFormulaID.REFERENCED_TRAFFIC_SIGN

        self.check_sat(formula_id, self.network, expected=False)

        lanelet = self.network.find_lanelet_by_id(1)
        lanelet.traffic_signs = set()

        self.check_sat(formula_id, self.network, expected=True)

    # def test_given_additional_value(self):
    #     formula_id = TrafficSignFormulaID.GIVEN_ADDITIONAL_VALUE
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     self.traffic_sign.traffic_sign_elements[0].additional_values = []
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)
    #
    # def test_valid_additional_value_speed_sign(self):
    #     formula_id = TrafficSignFormulaID.VALUE_ADDITIONAL_VALUE_SPEED_SIGN
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     self.traffic_sign.traffic_sign_elements[0].additional_values = ['-120']
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)
    #
    # def test_maximal_distance_from_lanelet(self):
    #     formula_id = TrafficSignFormulaID.MAXIMAL_DISTANCE_FROM_LANELET
    #
    #     self.traffic_sign.position = np.array([0., -0.2])
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3, Solver.HOL], expected=False)
    #
    #     self.traffic_sign.position = np.array([0., -10.2])
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3, Solver.HOL], expected=True)


class TestTrafficLightFormulaPool(TestFormulaPool):
    """
    The class tests the repairing of traffic light elements.
    """

    def setUp(self) -> None:
        lanelet = Lanelet(np.array([[0., 1.], [1., 1.]]),
                          np.array([[0., 0.5], [1., 0.5]]),
                          np.array([[0., 0.], [1., 0.]]), 1, traffic_lights={2})
        cycle_element_0 = TrafficLightCycleElement(TrafficLightState.RED, 10)
        cycle_element_1 = TrafficLightCycleElement(TrafficLightState.RED_YELLOW, 5)
        cycle_element_2 = TrafficLightCycleElement(TrafficLightState.GREEN, 10)
        cycle_element_3 = TrafficLightCycleElement(TrafficLightState.YELLOW, 5)
        self.traffic_light = \
            TrafficLight(2, np.array([00., 0.0]),
                         TrafficLightCycle([cycle_element_0, cycle_element_1, cycle_element_2, cycle_element_3]))

        self.network = LaneletNetwork()
        self.network.add_lanelet(lanelet)
        self.network.add_traffic_light(self.traffic_light, {1})

    def test_at_least_one_cycle_element(self):
        formula_id = TrafficLightFormulaID.AT_LEAST_ONE_CYCLE_ELEMENT

        self.check_sat(formula_id, self.network, expected=False)

        self.traffic_light.traffic_light_cycle.cycle_elements = []

        self.check_sat(formula_id, self.network, expected=True)

    def test_traffic_light_per_incoming(self):
        pass

    def test_referenced_traffic_light(self):
        formula_id = TrafficLightFormulaID.REFERENCED_TRAFFIC_LIGHT

        self.check_sat(formula_id, self.network, expected=False)

        lanelet = self.network.find_lanelet_by_id(1)
        lanelet.traffic_lights = set()

        self.check_sat(formula_id, self.network, expected=True)

    # def test_non_zero_duration(self):
    #     formula_id = TrafficLightFormulaID.NON_ZERO_DURATION
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     cycle_element = self.traffic_light.traffic_light_cycle.cycle_elements[0]
    #     cycle_element.duration = -10
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)
    #
    # def test_unique_state_in_cycle(self):
    #     formula_id = TrafficLightFormulaID.UNIQUE_STATE_IN_CYCLE
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=False)
    #
    #     cycle_element_0 = TrafficLightCycleElement(TrafficLightState.RED, 10)
    #     cycle_element_1 = TrafficLightCycleElement(TrafficLightState.RED, 5)
    #     self.traffic_light.traffic_light_cycle.cycle_elements = [cycle_element_0, cycle_element_1]
    #
    #     self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)

    def test_cycle_state_combinations(self):
        formula_id = TrafficLightFormulaID.CYCLE_STATE_COMBINATIONS

        self.check_sat(formula_id, self.network, expected=False)

        # cycle_element_0 = TrafficLightCycleElement(TrafficLightState.RED, 10)
        # cycle_element_1 = TrafficLightCycleElement(TrafficLightState.GREEN, 10)
        #
        # self.traffic_light.traffic_light_cycle.cycle_elements = [cycle_element_0, cycle_element_1]
        #
        # self.check_sat(formula_id, self.network, [Solver.Z3], expected=True)


# class TestIntersectionFormulaPool(TestFormulaPool):
#     """
#     The class tests the repairing of intersection elements.
#     """
#
#     def setUp(self) -> None:
#         lanelet_1 = Lanelet(np.array([[0., 1.], [1., 1.]]),
#                             np.array([[0., 0.5], [1., 0.5]]),
#                             np.array([[0., 0.], [1., 0.]]), 1)
#         lanelet_2 = Lanelet(np.array([[1., 1.], [2., 1.]]),
#                             np.array([[1., 0.5], [2., 0.5]]),
#                             np.array([[1., 0.], [2., 0.]]), 2)
#
#         incoming_element_1 = IncomingGroup(3, incoming_lanelets={1})
#         incoming_element_2 = IncomingGroup(4, incoming_lanelets={2})
#
#         self.intersection = Intersection(5, [incoming_element_1, incoming_element_2])
#
#         self.network = LaneletNetwork()
#         self.network.add_lanelet(lanelet_1)
#         self.network.add_lanelet(lanelet_2)
#         self.network.add_intersection(self.intersection)
#
#     def test_at_least_two_incoming_elements(self):
#         formula_id = IntersectionFormulaID.AT_LEAST_TWO_INCOMING_ELEMENTS
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=False)
#
#         self.intersection.incomings = []
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=True)
#
#     def test_at_least_one_incoming_lanelet(self):
#         formula_id = IntersectionFormulaID.AT_LEAST_ONE_INCOMING_LANELET
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=False)
#
#         incoming_element = self.intersection.incomings[0]
#         incoming_element.incoming_lanelets = set()
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=True)
#
#     def test_existence_incoming_lanelets(self):
#         formula_id = IntersectionFormulaID.EXISTENCE_INCOMING_LANELETS
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=False)
#
#         incoming_element = self.intersection.incomings[0]
#         incoming_element.incoming_lanelets = {7}
#
#         self.check_sat(formula_id, self.network, [Solver.HOL], expected=True)


if __name__ == '__main__':
    unittest.main()
