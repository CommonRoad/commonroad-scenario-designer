import os
import unittest

from tests.map_conversion.opendrive.cr2odr.conversion_base_test import (
    ConversionBaseTestCases,
)


class TestConverterConvert(ConversionBaseTestCases.ConversionBaseTest):
    def __init__(self, *args, **kwargs):
        super(TestConverterConvert, self).__init__(*args, **kwargs)

    def test_convert_DEU_Guetersloh(self):
        self.prepare_conversion("DEU_Guetersloh-11_2_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ARG_Carcarana(self):
        self.prepare_conversion("ARG_Carcarana-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_zero_width_lanes_map(self):
        self.prepare_conversion("zero_width_lanes_map")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_DEU_Test(self):
        self.prepare_conversion("DEU_Test-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_DEU_Muehlhausen(self):
        self.prepare_conversion("DEU_Muehlhausen-2_2_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_lanelet_no_succ_or_pred(self):
        self.prepare_conversion("lanelet_no_succ_or_pred")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_function_checkAllVisited(self):
        self.prepare_conversion("DEU_Test-1_1_T-1")
        self.converter.id_dict.popitem()
        self.assertRaises(KeyError, lambda: self.converter.check_all_visited())

    def test_convert_BEL_Wervik(self):
        self.prepare_conversion("BEL_Wervik-2_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_CulDeSac(self):
        self.prepare_conversion("CulDeSac")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_Over(self):
        self.prepare_conversion("ZAM_Over-1_1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_town03_right_width_coefficient(self):
        self.prepare_conversion("town03_right_width_coefficient")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_random(self):
        self.prepare_conversion("ZAM_OpenDrive-1_1_T-1")
        self.converter.convert(self.file_path_out)  # self.check_with_ground_truth(os.path.join(self.cwd_path,
        # self.path_reference_xodr_file))

    def test_convert_ZAM_straight_lanelet(self):
        self.prepare_conversion("ZAM_Lanelet-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_curved_lanelet(self):
        self.prepare_conversion("ZAM_CurvedLanelet-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_lanelet_with_obstacles(self):
        self.prepare_conversion("ZAM_LaneletWithObstacle-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))

    def test_convert_ZAM_three_way_intersection(self):
        self.prepare_conversion("ZAM_Threewayintersection-1_1_T-1")
        self.converter.convert(self.file_path_out)
        self.check_with_ground_truth(os.path.join(self.cwd_path, self.path_reference_xodr_file))


if __name__ == "__main__":
    unittest.main()
