import unittest
import os
from pathlib import Path

from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLanes import RoadMark
from crdesigner.map_conversion.opendrive.opendrive_parser.parser import *
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.geometry import *


class TestParser(unittest.TestCase):
    def test_parse_opendrive(self):
        file_path = Path(os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/CulDeSac.xodr')
        xodr_file = parse_opendrive(file_path)
        self.assertIsInstance(xodr_file, OpenDrive)

    def test_parse_opendrive_header(self):
        file_path = Path(os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/CulDeSac.xodr')
        odr = parse_opendrive(file_path)

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
        file_path = Path(os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/FourWaySignal.xodr')
        odr = parse_opendrive(file_path)

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
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/zero_width_lanes_map.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/FourWaySignal.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/FourWaySignal.xodr'
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
        parse_opendrive_road_geometry(new_road=road, road_geometry=geometry_xml[0],
                                      offset={"x": "0.0", "y": "0.0", "z": "0.0", "hdg":  "0.0"})

        self.assertIsInstance(road.planView._geometries[0], Arc)
        np.testing.assert_equal(np.array([6.0599999427795410e+0, 7.4040000915527344e+1]),
                                road.planView._geometries[0].start_position)
        self.assertEqual(-1.3311147279124484e+0, road.planView._geometries[0].heading)
        self.assertEqual(5.9969576254056612e+1, road.planView._geometries[0].length)

    def test_parse_orpendrive_road_elevation_profile(self):
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/FourWaySignal.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/FourWaySignal.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) \
                    + '/../../test_maps/opendrive/CrossingComplex8Course.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) \
                    + '/../../test_maps/opendrive/CrossingComplex8Course.xodr'
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
        # roadmarks
        self.assertEqual(0, road.lanes.lane_sections[0].centerLanes[0].road_mark[0].SOffset)
        self.assertEqual("solid", road.lanes.lane_sections[0].centerLanes[0].road_mark[0].type)
        self.assertEqual("standard", road.lanes.lane_sections[0].centerLanes[0].road_mark[0].weight)
        self.assertEqual(0.5, road.lanes.lane_sections[0].centerLanes[0].road_mark[1].SOffset)
        self.assertEqual("none", road.lanes.lane_sections[0].centerLanes[0].road_mark[1].type)
        self.assertEqual("standard", road.lanes.lane_sections[0].centerLanes[0].road_mark[1].weight)

    def test_parse_opendrive_road_signal(self):
        file_path = os.path.dirname(os.path.abspath(__file__)) \
                    + '/../../test_maps/opendrive/CrossingComplex8Course.xodr'
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
        file_path = os.path.dirname(os.path.abspath(__file__)) \
                    + '/../../test_maps/opendrive/CrossingComplex8Course.xodr'
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
        file_path = Path(os.path.dirname(os.path.abspath(__file__)) \
                    + '/../../test_maps/opendrive/CrossingComplex8Course.xodr')
        odr = parse_opendrive(file_path)

        self.assertEqual("", odr.roads[0].name)
        self.assertEqual(69, odr.roads[0].id)
        # junction ID -1 which means None
        junction = odr.getJunction(2)
        self.assertEqual(junction, odr.roads[0].junction)
        # rest of road parser is tested with other tests

    def test_parse_opendrive_road_object(self):
        file_path = os.path.dirname(os.path.abspath(__file__)) + '/../../test_maps/opendrive/four_way_crossing.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
        road_xml = []
        for road in root.findall("road"):
            road_xml.append(road)
        road = Road()
        object_xml = []
        for reference in road_xml[1].find("objects").findall("object"):
            object_xml.append(reference)
        parse_opendrive_road_object(new_road=road, obj=object_xml[1])

        self.assertEqual(81, road.objects[0].id)
        self.assertEqual("House04_BeachColors", road.objects[0].name)
        self.assertEqual(7.3042801461003135e+0, road.objects[0].s)
        self.assertEqual(-1.4759999871253967e+1, road.objects[0].t)
        self.assertEqual(-3.6077709960937501e+0, road.objects[0].zOffset)
        self.assertEqual(1.5707963267948966e+0, road.objects[0].hdg)
        self.assertEqual(0, road.objects[0].roll)
        self.assertEqual(0, road.objects[0].pitch)
        self.assertEqual("none", road.objects[0].type)
        self.assertEqual(1.2868122558593750e+1, road.objects[0].height)
        self.assertEqual(1.6766826171875003e+1, road.objects[0].width)
        self.assertEqual(1.1869543457031250e+1, road.objects[0].validLength)

    def test_lane_access(self):
        file_path = os.path.dirname(os.path.abspath(__file__)) + \
                    '/../../test_maps/opendrive/straight_road_lane_access.xodr'
        with open("{}".format(file_path), "r") as file_in:  # no idea why cleaning up the namespace is not required
            root = etree.parse(file_in).getroot()          # for any other tests in this class but this test breaks
            for elem in root.getiterator():                # without it
                if not (isinstance(elem, etree._Comment) or isinstance(elem, etree._ProcessingInstruction)):
                    elem.tag = etree.QName(elem).localname
            etree.cleanup_namespaces(root)
        laneSection = root.find("road").find("lanes").find("laneSection")

        road = Road()
        parse_opendrive_road_lane_section(new_road=road, lane_section=laneSection, lane_section_id=1)
        self.assertEqual([["pedestrian", "allow", 0.0]], road.lanes.lane_sections[0].leftLanes[0].access)

    def test_default_vals(self):
        """
        Test that investigates the functionality of default values of OpenDRIVE .xodr maps
        within the OpenDRIVE parser in the conversion.
        """
        file_path = os.path.dirname(
            os.path.abspath(__file__)) + '/../../test_maps/opendrive/straight_road_default.xodr'
        with open("{}".format(file_path), "r") as file_in:
            root = etree.parse(file_in).getroot()
            for elem in root.getiterator():
                if not (isinstance(elem, etree._Comment) or isinstance(elem, etree._ProcessingInstruction)):
                    elem.tag = etree.QName(elem).localname
            etree.cleanup_namespaces(root)
            road_xml = root.find("road")
        road = Road()
        parse_opendrive_road_elevation_profile(road, road_elevation_profile=road_xml.find("elevationProfile"))
        parse_opendrive_road_lateral_profile(road, road_lateral_profile=road_xml.find("lateralProfile"))
        parse_opendrive_road_lane_offset(road, road_xml.find("lanes").find("laneOffset"))
        parse_opendrive_road_lane_section(road, lane_section_id=1,
                                          lane_section=road_xml.find("lanes").find("laneSection"))
        for x in road_xml.find("planView").findall("geometry"):
            parse_opendrive_road_geometry(road, road_geometry=x,
                                          offset={"x": "0.0", "y": "0.0", "z": "0.0", "hdg":  "0.0"})
        self.assertEqual(0, road.planView._geometries[1]._curv_start)
        self.assertEqual(0, road.planView._geometries[2]._aU)
        self.assertEqual(1, road.planView._geometries[2]._bU)
        self.assertEqual(0, road.planView._geometries[2]._cU)
        self.assertEqual(0, road.planView._geometries[2]._dU)
        self.assertEqual(0, road.planView._geometries[2]._aV)
        self.assertEqual(0, road.planView._geometries[2]._bV)
        self.assertEqual(0, road.planView._geometries[2]._cV)
        self.assertEqual(0, road.planView._geometries[2]._dV)
        latprof = road.lateralProfile
        for x in latprof.superelevations[0].polynomial_coefficients \
                 + latprof.shapes[0].polynomial_coefficients + latprof.crossfalls[0].polynomial_coefficients:
            self.assertEqual(0, x)
        self.assertEqual("both", latprof.crossfalls[0].side)
        for x in road.elevationProfile.elevations[0].polynomial_coefficients \
                + [road.elevationProfile.elevations[0].start_pos]:
            self.assertEqual(0, x)
        self.assertEqual(0, road.lateralProfile.shapes[0].start_pos)
        offs = road.lanes.laneOffsets[0]
        for x in offs.polynomial_coefficients + [offs.start_pos]:
            self.assertEqual(0, x)
        self.assertEqual(0, road.lanes.lane_sections[0].leftLanes[1].road_mark[0].SOffset)
        self.assertEqual("standard", road.lanes.lane_sections[0].leftLanes[1].road_mark[0].weight)
        test = RoadMark()
        test.SOffset = None
        self.assertEqual(0, test.SOffset)
        test.weight = None
        self.assertEqual("standard", test.weight)


if __name__ == '__main__':
    unittest.main()

