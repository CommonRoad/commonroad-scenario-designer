__author__ = "Aaron Kaefer, Marcus Gabler, Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["Priority Program SPP 1835 Cooperative Interacting Automobiles, BMW Car@TUM"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"

import unittest
import numpy as np

from commonroad.scenario.lanelet import Lanelet, LineMarking, LaneletNetwork, StopLine
from commonroad.scenario.scenario import Scenario, ScenarioID

from crdesigner.input_output.gui.misc.map_creator import MapCreator


class TestLanelet(unittest.TestCase):
    def test_set_predecessor_successor_relation(self):
        right_vertices = np.array([[0, 0], [1, 0], [2, 0], [3, .5], [4, 1], [5, 1], [6, 1], [7, 0], [8, 0]])
        left_vertices = np.array([[0, 1], [1, 1], [2, 1], [3, 1.5], [4, 2], [5, 2], [6, 2], [7, 1], [8, 1]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5], [3, 1], [4, 1.5], [5, 1.5], [6, 1.5], [7, .5], [8, .5]])
        stop_line = StopLine(start=np.array([0, 0]), end=np.array([0, 1]), line_marking=LineMarking.SOLID)

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1, stop_line=stop_line)
        lanelet2 = Lanelet(left_vertices, center_vertices, right_vertices, 2, stop_line=stop_line)

        MapCreator.set_predecessor_successor_relation(lanelet, lanelet2)

        np.testing.assert_equal(lanelet.lanelet_id in lanelet2.predecessor, True)
        np.testing.assert_equal(lanelet2.lanelet_id in lanelet.successor, True)

    def test_create_straight(self):
        left_vertices = np.array([[0, 1], [1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 1], [8, 1]])
        right_vertices = np.array([[0, -1], [1, -1], [2, -1], [3, -1], [4, -1], [5, -1], [6, -1], [7, -1], [8, -1]])
        center_vertices = np.array([[0, 0], [1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], [7, 0], [8, 0]])

        scenario = Scenario(0.1, ScenarioID())
        network = LaneletNetwork()
        scenario.lanelet_network = network
        lanelet = MapCreator.create_straight(2, 8, 9, scenario.generate_object_id(), set())

        np.testing.assert_array_almost_equal(lanelet.left_vertices, left_vertices)
        np.testing.assert_array_almost_equal(lanelet.right_vertices, right_vertices)
        np.testing.assert_array_almost_equal(lanelet.center_vertices, center_vertices)

    def test_create_curve(self):
        left_vertices = np.array([[0, 1], [3.66062979, 1.77809088], [6.68830343, 3.97782454], [8.55950865, 7.21884705],
                                  [8.95069706, 10.9407562], [7.79422863, 14.5], [5.29006727, 17.2811529],
                                  [1.87120522, 18.8033284], [-1.87120522, 18.8033284], [-5.29006727, 17.2811529]])
        right_vertices = np.array(
            [[0, -1], [4.47410307, -0.0490000341], [8.17459308, 2.63956333], [10.4616217, 6.60081306],
             [10.9397408, 11.1498131], [9.52627944, 15.5], [6.46563778, 18.8991869],
             [2.2870286, 20.7596236], [-2.2870286, 20.7596236], [-6.46563778, 18.8991869]])
        center_vertices = np.array(
            [[0, 0], [4.06736643, 0.86454542], [7.43144825, 3.30869394], [9.51056516, 6.90983006],
             [9.94521895, 11.04528463], [8.66025404, 15], [5.87785252, 18.09016994],
             [2.07911691, 19.78147601], [-2.07911691, 19.78147601], [-5.87785252, 18.09016994]])

        scenario = Scenario(0.1, ScenarioID())
        network = LaneletNetwork()
        scenario.lanelet_network = network
        lanelet = MapCreator.create_curve(2, 10, np.pi*1.2, 10, scenario.generate_object_id(), set())

        np.testing.assert_array_almost_equal(lanelet.left_vertices, left_vertices)
        np.testing.assert_array_almost_equal(lanelet.right_vertices, right_vertices)
        np.testing.assert_array_almost_equal(lanelet.center_vertices, center_vertices)

    def test_calc_angle_between(self):
        left_vertices = np.array([[0, 1], [1, 1], [2, 1], [3, 1.5], [4, 2], [5, 2], [6, 2], [7, 1], [8, 1]])
        right_vertices = np.array([[0, 0], [1, 0], [2, 0], [3, .5], [4, 1], [5, 1], [6, 1], [7, 0], [8, 0]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5], [3, 1], [4, 1.5], [5, 1.5], [6, 1.5], [7, .5], [8, .5]])
        stop_line = StopLine(start=np.array([0, 0]), end=np.array([0, 1]), line_marking=LineMarking.SOLID)

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1, stop_line=stop_line)
        lanelet2 = Lanelet(left_vertices, center_vertices, right_vertices, 2, stop_line=stop_line)
        test_angle_translated = np.pi*1.2
        lanelet2.translate_rotate(np.array([0, 0]), test_angle_translated)

        angle = MapCreator.calc_angle_between_lanelets(lanelet, lanelet2)

        np.testing.assert_almost_equal(2*np.pi-angle, test_angle_translated, 10)

    def test_fit_to_predecessor(self):
        left_vertices = np.array([[0, 1], [1, 1], [2, 1], [3, 1.5], [4, 2], [5, 2], [6, 2], [7, 1], [8, 1]])
        right_vertices = np.array([[0, 0], [1, 0], [2, 0], [3, .5], [4, 1], [5, 1], [6, 1], [7, 0], [8, 0]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5], [3, 1], [4, 1.5], [5, 1.5], [6, 1.5], [7, .5], [8, .5]])
        stop_line = StopLine(start=np.array([0, 0]), end=np.array([0, 1]), line_marking=LineMarking.SOLID)

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1, stop_line=stop_line)
        lanelet2 = Lanelet(left_vertices, center_vertices, right_vertices, 2, stop_line=stop_line)
        test_angle_translated = np.pi*1.2
        lanelet2.translate_rotate(np.array([-30, 80]), test_angle_translated)

        MapCreator.fit_to_predecessor(lanelet, lanelet2)

        np.testing.assert_array_almost_equal(lanelet.left_vertices[-1], lanelet2.left_vertices[0])
        np.testing.assert_array_almost_equal(lanelet.right_vertices[-1], lanelet2.right_vertices[0])
        np.testing.assert_array_almost_equal(lanelet.center_vertices[-1], lanelet2.center_vertices[0])

    def test_adjacent_left(self):
        left_vertices = np.array([[9, -6], [9, -3], [9, 0], [8.22190912, 3.66062979], [6.02217546, 6.68830343],
                                  [2.78115295, 8.55950865], [-0.94075617, 8.95069706], [-4.5, 7.79422863],
                                  [-7.28115295, 5.29006727], [-8.80332841, 1.87120522], [-8.80332841, -1.87120522],
                                  [-7.28115295, -5.29006727]])
        right_vertices = np.array([[11, -6], [11, -3], [11, 0], [10.04900003, 4.47410307], [7.36043667, 8.17459308],
                                   [3.39918694, 10.46162168], [-1.1498131, 10.93974085], [-5.5, 9.52627944],
                                   [-8.89918694, 6.46563778], [-10.75962361, 2.2870286], [-10.75962361, -2.2870286],
                                   [-8.89918694, -6.46563778]])
        center_vertices = np.array([[10, -6], [10, -3], [10, 0], [9.13545458, 4.06736643], [6.69130606, 7.43144825],
                                    [3.09016994, 9.51056516], [-1.04528463, 9.94521895], [-5, 8.66025404],
                                    [-8.09016994, 5.87785252], [-9.78147601, 2.07911691], [-9.78147601, -2.07911691],
                                    [-8.09016994, -5.87785252]])

        adj_left_vertices = np.array([[7, -6], [7, -3], [7, 0], [6.39481821, 2.84715651], [4.68391425, 5.20201378],
                                      [2.16311896, 6.65739562], [-0.73169924, 6.96165327], [-3.5, 6.06217782],
                                      [-5.66311896, 4.11449676], [-6.84703321, 1.45538184],
                                      [-6.84703321, -1.45538184],
                                      [-5.66311896, -4.11449676]])
        adj_right_vertices = np.array([[9, -6], [9, -3], [9, 0], [8.22190912, 3.66062979], [6.02217546, 6.68830343],
                                       [2.78115295, 8.55950865], [-0.94075617, 8.95069706], [-4.5, 7.79422863],
                                       [-7.28115295, 5.29006727], [-8.80332841, 1.87120522],
                                       [-8.80332841, -1.87120522],
                                       [-7.28115295, -5.29006727]])
        adj_center_vertices = np.array([[8, -6], [8, -3], [8, 0], [7.30836367, 3.25389315], [5.35304485, 5.9451586],
                                        [2.47213595, 7.60845213], [-0.8362277, 7.95617516], [-4, 6.92820323],
                                        [-6.47213595, 4.70228201], [-7.82518081, 1.66329353],
                                        [-7.82518081, -1.66329353], [-6.47213595, -4.70228201]])

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1)
        scenario = Scenario(0.1, ScenarioID())
        network = LaneletNetwork()
        scenario.lanelet_network = network

        lanelet2 = MapCreator.create_adjacent_lanelet(True, lanelet, scenario.generate_object_id(), True, 2, set())
        lanelet._adj_left = None
        lanelet3 = MapCreator.create_adjacent_lanelet(True, lanelet, scenario.generate_object_id(), False, 2,  set())

        np.testing.assert_array_almost_equal(lanelet2.left_vertices, adj_left_vertices)
        np.testing.assert_array_almost_equal(lanelet2.right_vertices, adj_right_vertices)
        np.testing.assert_array_almost_equal(lanelet2.center_vertices, adj_center_vertices)
        np.testing.assert_array_almost_equal(lanelet3.left_vertices, np.flip(adj_right_vertices, axis=0))
        np.testing.assert_array_almost_equal(lanelet3.right_vertices, np.flip(adj_left_vertices, axis=0))
        np.testing.assert_array_almost_equal(lanelet3.center_vertices, np.flip(adj_center_vertices, axis=0))

    def test_adjacent_right(self):
        left_vertices = np.array([[9, -6], [9, -3], [9, 0], [8.22190912, 3.66062979], [6.02217546, 6.68830343],
                                  [2.78115295, 8.55950865], [-0.94075617, 8.95069706], [-4.5, 7.79422863],
                                  [-7.28115295, 5.29006727], [-8.80332841, 1.87120522], [-8.80332841, -1.87120522],
                                  [-7.28115295, -5.29006727]])
        right_vertices = np.array([[11, -6], [11, -3], [11, 0], [10.04900003, 4.47410307], [7.36043667, 8.17459308],
                                   [3.39918694, 10.46162168], [-1.1498131, 10.93974085], [-5.5, 9.52627944],
                                   [-8.89918694, 6.46563778], [-10.75962361, 2.2870286], [-10.75962361, -2.2870286],
                                   [-8.89918694, -6.46563778]])
        center_vertices = np.array([[10, -6], [10, -3], [10, 0], [9.13545458, 4.06736643], [6.69130606, 7.43144825],
                                    [3.09016994, 9.51056516], [-1.04528463, 9.94521895], [-5, 8.66025404],
                                    [-8.09016994, 5.87785252], [-9.78147601, 2.07911691], [-9.78147601, -2.07911691],
                                    [-8.09016994, -5.87785252]])

        adj_left_vertices = np.array([[11, -6], [11, -3], [11, 0], [10.04900003, 4.47410307], [7.36043667, 8.17459308],
                                      [3.39918694, 10.46162168], [-1.1498131, 10.93974085], [-5.5, 9.52627944],
                                      [-8.89918694, 6.46563778], [-10.75962361, 2.2870286],
                                      [-10.75962361, -2.2870286],
                                      [-8.89918694, -6.46563778]])
        adj_right_vertices = np.array([[13, -6], [13, -3], [13, 0], [11.87609094, 5.28757635], [8.69869788, 9.66088273],
                                       [4.01722093, 12.36373471], [-1.35887003, 12.92878464], [-6.5, 11.25833025],
                                       [-10.51722093, 7.64120829], [-12.71591881, 2.70285198],
                                       [-12.71591881, -2.70285198], [-10.51722093, -7.64120829]])
        adj_center_vertices = np.array([[12, -6], [12, -3], [12, 0], [10.96254549, 4.88083971], [8.02956727, 8.9177379],
                                        [3.70820393, 11.41267819], [-1.25434156, 11.93426274], [-6, 10.39230485],
                                        [-9.70820393, 7.05342303], [-11.73777121, 2.49494029],
                                        [-11.73777121, -2.49494029], [-9.70820393, -7.05342303]])

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1)
        scenario = Scenario(0.1, ScenarioID())
        network = LaneletNetwork()
        scenario.lanelet_network = network

        lanelet2 = MapCreator.create_adjacent_lanelet(False, lanelet, scenario.generate_object_id(), True, 2, set())
        lanelet._adj_right = None
        lanelet3 = MapCreator.create_adjacent_lanelet(False, lanelet, scenario.generate_object_id(), False, 2, set())

        np.testing.assert_array_almost_equal(lanelet2.left_vertices, adj_left_vertices)
        np.testing.assert_array_almost_equal(lanelet2.right_vertices, adj_right_vertices)
        np.testing.assert_array_almost_equal(lanelet2.center_vertices, adj_center_vertices)
        np.testing.assert_array_almost_equal(lanelet3.left_vertices, np.flip(adj_right_vertices, axis=0))
        np.testing.assert_array_almost_equal(lanelet3.right_vertices, np.flip(adj_left_vertices, axis=0))
        np.testing.assert_array_almost_equal(lanelet3.center_vertices, np.flip(adj_center_vertices, axis=0))

    def test_connect_lanelets(self):
        left_vertices = np.array([[0, 1], [1, 1], [2, 1], [3, 1.5], [4, 2], [5, 2], [6, 2], [7, 1], [8, 1]])
        right_vertices = np.array([[0, 0], [1, 0], [2, 0], [3, .5], [4, 1], [5, 1], [6, 1], [7, 0], [8, 0]])
        center_vertices = np.array([[0, .5], [1, .5], [2, .5], [3, 1], [4, 1.5], [5, 1.5], [6, 1.5], [7, .5], [8, .5]])
        stop_line = StopLine(start=np.array([0, 0]), end=np.array([0, 1]), line_marking=LineMarking.SOLID)

        lanelet = Lanelet(left_vertices, center_vertices, right_vertices, 1, stop_line=stop_line)
        lanelet2 = Lanelet(left_vertices, center_vertices, right_vertices, 2, stop_line=stop_line)
        test_angle_translated = np.pi*0.7
        lanelet2.translate_rotate(np.array([40, 80]), test_angle_translated)

        scenario = Scenario(0.1, ScenarioID())
        network = LaneletNetwork()
        scenario.lanelet_network = network

        lanelet_connect = MapCreator.connect_lanelets(lanelet, lanelet2, scenario.generate_object_id())

        np.testing.assert_array_almost_equal(lanelet.left_vertices[-1], lanelet_connect.left_vertices[0])
        np.testing.assert_array_almost_equal(lanelet.right_vertices[-1], lanelet_connect.right_vertices[0])
        np.testing.assert_array_almost_equal(lanelet.center_vertices[-1], lanelet_connect.center_vertices[0])
        np.testing.assert_array_almost_equal(lanelet_connect.left_vertices[-1], lanelet2.left_vertices[0])
        np.testing.assert_array_almost_equal(lanelet_connect.right_vertices[-1], lanelet2.right_vertices[0])
        np.testing.assert_array_almost_equal(lanelet_connect.center_vertices[-1], lanelet2.center_vertices[0])
