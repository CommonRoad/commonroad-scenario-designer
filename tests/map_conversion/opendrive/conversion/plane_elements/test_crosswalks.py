import os
import unittest
from pathlib import Path
import numpy as np

from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from crdesigner.map_conversion.opendrive.opendrive_conversion.plane_elements.crosswalks import get_crosswalks
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.road import Road
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadObject import Object as RoadObject, \
    ObjectOutlineCorner


class MyTestCase(unittest.TestCase):

    def test_crosswalk_conversion(self):
        """
        test the crosswalk conversion for two crosswalks
        """
        road = Road()
        road.id = 1
        road.planView.add_line([8.3403508337802787e-2, -9.6810741424560440], 1.5673435784035967, 2.3086208844004261)
        road.planView.add_line([9.1375475641369830e-2, -7.3722074887383080], 1.5673435784035967, 1.1876406667659012e-1)
        road.planView.add_arc([9.1785537266776185e-2, -7.2534441299822312],
                              1.5673435784035969, 1.0385725110755295e+1, -1.5091325804710767e-1)
        road.planView.add_line([6.7180692975847407, -6.4999997615814209e-1], 0.0000000000000000, 1.1902359860622713e-1)
        road.planView.add_line([6.8370928961909669, -6.4999997615814187e-1], 6.2831853071795862, 2.2464710503781191)
        road.planView.add_line([9.0835639465690861, -6.4999997615814209e-1], 6.2831853071795862, 6.2149880108918865e-2)

        odr_crosswalk1 = RoadObject()
        odr_crosswalk1.id = 1
        odr_crosswalk1.type = "crosswalk"
        odr_crosswalk1.s = 3.5528468214044042
        odr_crosswalk1.t = 0.046060059926838148
        odr_crosswalk1.hdg = 1.6954780978973598
        outline = [[4.5497031009155489, 1.4666291880958617],
                   [4.3208401665634053, -1.0478578669707854],
                   [-4.0977533368067887, -1.4669024187635786],
                   [-4.5497373135523880, 1.0136947485698924]]
        corners = []
        for o in outline:
            corner = ObjectOutlineCorner()
            corner.u = o[0]
            corner.v = o[1]
            corners.append(corner)
        odr_crosswalk1.outline = corners
        road.addObject(odr_crosswalk1)

        odr_crosswalk2 = RoadObject()
        odr_crosswalk2.id = 2
        odr_crosswalk2.type = "crosswalk"
        odr_crosswalk2.s = 1.1687453686666524e+1
        odr_crosswalk2.t = 4.4724161850102639e-2
        odr_crosswalk2.hdg = 1.4461280020844021
        outline = [[-4.5497906440108160, -1.0134603605502015],
                   [-4.0963408001529702, 1.4670497205049662],
                   [4.3222350669670337, 1.0476448297566963],
                   [4.5497581683391735, -1.4667906311019827]]
        corners = []
        for o in outline:
            corner = ObjectOutlineCorner()
            corner.u = o[0]
            corner.v = o[1]
            corners.append(corner)
        odr_crosswalk2.outline = corners
        road.addObject(odr_crosswalk2)

        cr_crosswalks = get_crosswalks(road)

        crosswalk1_left_vertices = np.array([[-4.11917897, -4.86917131], [4.30983202, -4.85975667]])
        crosswalk1_right_vertices = [[-4.46997289, -7.36956469], [4.64072752, -7.35938864]]
        crosswalk1_center_vertices = [[-4.29457593, -6.119368], [4.47527977, -6.10957266]]

        np.testing.assert_array_almost_equal(cr_crosswalks[0].left_vertices, crosswalk1_left_vertices)
        np.testing.assert_array_almost_equal(cr_crosswalks[0].right_vertices, crosswalk1_right_vertices)
        np.testing.assert_array_almost_equal(cr_crosswalks[0].center_vertices, crosswalk1_center_vertices)

        crosswalk2_left_vertices = [[4.30983202, -4.85975667], [4.34835011, 3.56917188]]
        crosswalk2_right_vertices = [[6.80830036, -5.20064224], [6.84993415, 3.91009668]]
        crosswalk2_center_vertices = [[5.55906619, -5.03019945], [5.59914213, 3.73963428]]

        np.testing.assert_array_almost_equal(cr_crosswalks[1].left_vertices, crosswalk2_left_vertices)
        np.testing.assert_array_almost_equal(cr_crosswalks[1].right_vertices, crosswalk2_right_vertices)
        np.testing.assert_array_almost_equal(cr_crosswalks[1].center_vertices, crosswalk2_center_vertices)

    def test_four_way_crossing(self):
        """Test the crosswalk conversion for four_way_crossing.xodr"""
        xodr_file_name = "four_way_crossing"
        scenario = opendrive_to_commonroad(Path(os.path.dirname(os.path.realpath(__file__)) +
                                           "/../../../test_maps/opendrive/{}.xodr".format(xodr_file_name)))

        lanelet_7 = scenario.lanelet_network.find_lanelet_by_id(7)
        lanelet_6 = scenario.lanelet_network.find_lanelet_by_id(6)
        lanelet_11 = scenario.lanelet_network.find_lanelet_by_id(11)
        lanelet_12 = scenario.lanelet_network.find_lanelet_by_id(12)

        np.testing.assert_array_almost_equal(lanelet_7.left_vertices,
                                             [[4.30983202, -4.85975667], [4.34835011, 3.56917188]])
        np.testing.assert_array_almost_equal(lanelet_7.right_vertices,
                                             [[6.80830036, -5.20064224], [6.84993415, 3.91009668]])
        np.testing.assert_array_almost_equal(lanelet_7.center_vertices,
                                             [[5.55906619, -5.03019945], [5.59914213, 3.73963428]])

        np.testing.assert_array_almost_equal(lanelet_6.left_vertices,
                                             [[-4.11917897, -4.86917131], [4.30983202, -4.85975667]])
        np.testing.assert_array_almost_equal(lanelet_6.right_vertices,
                                             [[-4.46997289, -7.36956469], [4.64072751, -7.35938864]])
        np.testing.assert_array_almost_equal(lanelet_6.center_vertices,
                                             [[-4.29457593, -6.119368], [4.47527977, -6.10957265]])

        np.testing.assert_array_almost_equal(lanelet_11.left_vertices,
                                             [[-4.08066122, 3.55975695], [-4.11917897, -4.86917131]])
        np.testing.assert_array_almost_equal(lanelet_11.right_vertices,
                                             [[-6.57912958, 3.90064261], [-6.620763, -5.21009635]])
        np.testing.assert_array_almost_equal(lanelet_11.center_vertices,
                                             [[-5.3298954, 3.73019978], [-5.36997099, -5.03963383]])

        np.testing.assert_array_almost_equal(lanelet_12.left_vertices,
                                             [[4.34835011, 3.56917188], [-4.08066122, 3.55975695]])
        np.testing.assert_array_almost_equal(lanelet_12.right_vertices,
                                             [[4.6991442, 6.06956526], [-4.4115563, 6.05938891]])
        np.testing.assert_array_almost_equal(lanelet_12.center_vertices,
                                             [[4.52374715, 4.81936857], [-4.24610876, 4.80957293]])

        self.assertSetEqual(scenario.lanelet_network.find_intersection_by_id(84).crossings, {6, 7, 11, 12})


if __name__ == '__main__':
    unittest.main()
