import unittest
import os
from crdesigner.map_conversion.opendrive.opendrive_parser.parser import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.geometry import *


class TestParser(unittest.TestCase):
    def test_parse_opendrive(self):
        # get dir tests/map_conversion
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CulDeSac.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CulDeSac.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()

        xodr_file = parse_opendrive(root)

        self.assertIsInstance(xodr_file, OpenDrive)

    def test_parse_opendrive_header(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CulDeSac.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CulDeSac.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        odr = parse_opendrive(root)
        header = root.find("header")
        parse_opendrive_header(opendrive=odr, header=header)

        self.assertIsInstance(odr.header, Header)
        self.assertEqual("1", odr.header.revMajor)
        self.assertEqual("1", odr.header.revMinor)
        self.assertEqual("", odr.header.name)
        self.assertEqual("1.00", odr.header.version)
        self.assertEqual("Tue Mar 11 08:53:30 2014", odr.header.date)
        self.assertEqual("0.0000000000000000e+00", odr.header.north)
        self.assertEqual("0.0000000000000000e+00", odr.header.east)
        self.assertEqual("0.0000000000000000e+00", odr.header.south)
        self.assertEqual("0.0000000000000000e+00", odr.header.west)
        self.assertEqual(None, odr.header.vendor)
        self.assertEqual(None, odr.header.geo_reference)

    def test_parse_opendrive_junction(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/FourWaySignal.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/FourWaySignal.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        odr = parse_opendrive(root)
        for junction in root.findall("junction"):
            parse_opendrive_junction(opendrive=odr, junction=junction)

        for i in odr.junctions:
            self.assertIsInstance(i, Junction)
        junction = odr.getJunction(10)
        self.assertEqual("junction10", junction.name)
        self.assertEqual(0, junction.connections[0].id)
        self.assertEqual(1, junction.connections[0].incomingRoad)
        self.assertEqual(20, junction.connections[0].connectingRoad)
        self.assertEqual("end", junction.connections[0].contactPoint)
        self.assertEqual(1, junction.connections[0].laneLinks[0].fromId)
        self.assertEqual(1, junction.connections[0].laneLinks[0].toId)

    def test_parse_opendrive_road_link(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/zero_width_lanes_map.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/zero_width_lanes_map.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road_link = road_xml[1].find("link")
        road = Road()
        if road_link is not None:
            parse_opendrive_road_link(new_road=road, opendrive_road_link=road_link)

        self.assertEqual("road", road.link.predecessor.elementType)
        self.assertEqual(1, road.link.predecessor.element_id)
        self.assertEqual("end", road.link.predecessor.contactPoint)
        self.assertEqual("road", road.link.successor.elementType)
        self.assertEqual(1, road.link.successor.element_id)
        self.assertEqual("end", road.link.successor.contactPoint)
        self.assertEqual([], road.link.neighbors)

    def test_parse_road_type(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/FourWaySignal.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/FourWaySignal.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road_type = road_xml[0].find("type")
        road = Road()
        parse_opendrive_road_type(road=road, opendrive_xml_road_type=road_type)

        self.assertEqual(0, road.types[0].start_pos)
        self.assertEqual("town", road.types[0].use_type)
        self.assertEqual("40", road.types[0].speed.max)
        self.assertEqual("mph", road.types[0].speed.unit)

    def test_parse_opendrive_road_geometry(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/FourWaySignal.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/FourWaySignal.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        plan_view = road_xml[0].find("planView")
        road = Road()
        geometry_xml = []
        for geometry in plan_view.findall("geometry"):
            geometry_xml.append(geometry)
        parse_opendrive_road_geometry(new_road=road, road_geometry=geometry_xml[0])

        self.assertIsInstance(road.planView._geometries[0], Arc)
        np.testing.assert_equal(np.array([6.0599999427795410e+0, 7.4040000915527344e+1]),
                                road.planView._geometries[0].start_position)
        self.assertEqual(-1.3311147279124484e+0, road.planView._geometries[0].heading)
        self.assertEqual(5.9969576254056612e+1, road.planView._geometries[0].length)

    def test_parse_orpendrive_road_elevation_profile(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/FourWaySignal.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/FourWaySignal.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        elevation_prof = road_xml[0].find("elevationProfile")
        parse_opendrive_road_elevation_profile(new_road=road, road_elevation_profile=elevation_prof)

        self.assertEqual(0, road.elevationProfile.elevations[0].start_pos)
        np.testing.assert_equal([0, 0, 0, 0], road.elevationProfile.elevations[0].polynomial_coefficients)

    def test_parse_opendrive_road_lateral_profile(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/FourWaySignal.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/FourWaySignal.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        lateral_prof = road_xml[0].find("lateralProfile")
        parse_opendrive_road_lateral_profile(new_road=road, road_lateral_profile=lateral_prof)

        self.assertEqual(0, road.lateralProfile.superelevations[0].start_pos)
        np.testing.assert_equal([0, 0, 0, 0], road.lateralProfile.superelevations[0].polynomial_coefficients)

        self.assertEqual(0, road.lateralProfile.shapes[0].start_pos)
        self.assertEqual(-6.6349999999999998e+0, road.lateralProfile.shapes[0].start_pos_t)
        np.testing.assert_equal([0, 0, 0, 0], road.lateralProfile.shapes[0].polynomial_coefficients)

        # crossfall not tested as there are no crossfalls in test maps

    def test_parse_opendrive_road_lane_offset(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CrossingComplex8Course.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CrossingComplex8Course.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        lanes = road_xml[15].find("lanes")
        l_off_xml = []
        for lane_offset in lanes.findall("laneOffset"):
            l_off_xml.append(lane_offset)
        parse_opendrive_road_lane_offset(new_road=road, lane_offset=l_off_xml[1])

        self.assertEqual(2.5000000000000000e+01, road.lanes.laneOffsets[0].start_pos)
        np.testing.assert_equal([-1.8750000000000000e+00, 0, 2.5464010864644634e-03, -3.6119164347013670e-05],
                                road.lanes.laneOffsets[0].polynomial_coefficients)

    def test_parse_opendrive_road_lane_section(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CrossingComplex8Course.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CrossingComplex8Course.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        lanes = road_xml[2].find("lanes")
        lane_sec_xml = []
        for lane_section_id, lane_section in enumerate(lanes.findall("laneSection")):
            lane_sec_xml.append([lane_section_id, lane_section])
        parse_opendrive_road_lane_section(new_road=road, lane_section_id=lane_sec_xml[0][0],
                                          lane_section=lane_sec_xml[0][1])

        self.assertEqual(0, road.lanes.lane_sections[0].sPos)
        self.assertEqual(False, road.lanes.lane_sections[0].singleSide)
        self.assertEqual(0, road.lanes.lane_sections[0].centerLanes[0].id)
        self.assertEqual("driving", road.lanes.lane_sections[0].centerLanes[0].type)
        self.assertEqual(False, road.lanes.lane_sections[0].centerLanes[0].level)
        self.assertEqual(-1, road.lanes.lane_sections[0].rightLanes[0].id)
        self.assertEqual("driving", road.lanes.lane_sections[0].rightLanes[0].type)
        self.assertEqual(False, road.lanes.lane_sections[0].rightLanes[0].level)
        self.assertEqual([], road.lanes.lane_sections[0].leftLanes)
        self.assertEqual(None, road.lanes.lane_sections[0].centerLanes[0].link.predecessorId)
        self.assertEqual(None, road.lanes.lane_sections[0].centerLanes[0].link.successorId)
        self.assertEqual(2, road.lanes.lane_sections[0].rightLanes[0].link.predecessorId)
        self.assertEqual(1, road.lanes.lane_sections[0].rightLanes[0].link.successorId)
        self.assertEqual([], road.lanes.lane_sections[0].centerLanes[0].widths)
        self.assertEqual(0, road.lanes.lane_sections[0].rightLanes[0].widths[0].start_offset)
        np.testing.assert_equal([3.75, 0, 0, 0],
                                road.lanes.lane_sections[0].rightLanes[0].widths[0].polynomial_coefficients)
        # test for unchanged road_marks -> only first is parsed
        self.assertEqual(0, road.lanes.lane_sections[0].centerLanes[0].road_mark.SOffset)
        self.assertEqual("solid", road.lanes.lane_sections[0].centerLanes[0].road_mark.type)
        self.assertEqual("standard", road.lanes.lane_sections[0].centerLanes[0].road_mark.weight)
        """ tests for adapted road_marks
        self.assertEqual(0, road.lanes.lane_sections[0].centerLanes[0].road_mark[0].SOffset)
        self.assertEqual("solid", road.lanes.lane_sections[0].centerLanes[0].road_mark[0].type)
        self.assertEqual("standard", road.lanes.lane_sections[0].centerLanes[0].road_mark[0].weight)
        self.assertEqual(0.5, road.lanes.lane_sections[0].centerLanes[0].road_mark[1].SOffset)
        self.assertEqual("none", road.lanes.lane_sections[0].centerLanes[0].road_mark[1].type)
        self.assertEqual("standard", road.lanes.lane_sections[0].centerLanes[0].road_mark[1].weight)
        """

    def test_parse_opendrive_road_signal(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CrossingComplex8Course.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CrossingComplex8Course.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        signals_xml = []
        for signal in road_xml[0].find("signals").findall("signal"):
            signals_xml.append(signal)
        parse_opendrive_road_signal(new_road=road, road_signal=signals_xml[0])

        self.assertEqual(0, road.signals[0].s)
        self.assertEqual(0, road.signals[0].t)
        self.assertEqual(113, road.signals[0].id)
        self.assertEqual("", road.signals[0].name)
        self.assertEqual("OpenDRIVE", road.signals[0].country)
        self.assertEqual("294", road.signals[0].type)
        self.assertEqual("-1", road.signals[0].subtype)
        self.assertEqual("+", road.signals[0].orientation)
        self.assertEqual("no", road.signals[0].dynamic)
        self.assertEqual(-1, road.signals[0].signal_value)
        self.assertEqual(None, road.signals[0].unit)
        self.assertEqual(None, road.signals[0].text)

    def test_parse_opendrive_road_signal_reference(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CrossingComplex8Course.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CrossingComplex8Course.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        references_xml = []
        for reference in road_xml[0].find("signals").findall("signalReference"):
            references_xml.append(reference)
        parse_opendrive_road_signal_reference(new_road=road, road_signal_reference=references_xml[0])

        self.assertEqual(2, road.signalReference[0].s)
        self.assertEqual(-9.4, road.signalReference[0].t)
        self.assertEqual(217, road.signalReference[0].id)
        self.assertEqual("+", road.signalReference[0].orientation)

    def test_parse_opendrive_road(self):
        # dir_name = os.path.dirname(os.path.abspath(os.curdir))
        # file_path = os.path.join(dir_name, 'test_maps/opendrive/CrossingComplex8Course.xodr')
        file_path = 'tests/map_conversion/test_maps/opendrive/CrossingComplex8Course.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        odr = parse_opendrive(root)
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        parse_opendrive_road(opendrive=odr, road=road_xml[0])

        self.assertEqual("", odr.roads[0].name)
        self.assertEqual(69, odr.roads[0].id)
        # junction ID -1 which means None
        junction = odr.getJunction(2)
        self.assertEqual(junction, odr.roads[0].junction)
        # rest of road parser is tested with other tests


if __name__ == '__main__':
    unittest.main()
