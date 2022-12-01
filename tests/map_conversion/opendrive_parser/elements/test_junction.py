import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.junction import *


class TestJunction(unittest.TestCase):
    def test_initialize_junction(self):
        junction_id = 1
        junction_name = "Junction 1"

        junction = Junction()
        junction.id = junction_id
        junction.name = junction_name

        self.assertEqual(junction_id, junction.id)
        self.assertEqual(junction_name, junction.name)

        # test connections attribute
        connection1 = Connection()
        connection2 = Connection()
        connection3 = Connection()
        junction.addConnection(connection1)
        junction.addConnection(connection2)
        junction.addConnection(connection3)
        self.assertEqual([connection1, connection2, connection3], junction.connections)
        with self.assertRaises(TypeError):
            junction.addConnection("test")
            junction.addConnection(2)

    def test_initialize_connection(self):
        con_id = 100
        incoming_road = 42
        connecting_road = 21

        connection = Connection()
        connection.id = con_id
        connection.incomingRoad = incoming_road
        connection.connectingRoad = connecting_road

        self.assertEqual(con_id, connection.id)
        self.assertEqual(incoming_road, connection.incomingRoad)
        self.assertEqual(connecting_road, connection.connectingRoad)

        # test different values for contactPoint
        contact_point = "start"
        connection.contactPoint = contact_point
        self.assertEqual(contact_point, connection.contactPoint)
        contact_point = "end"
        connection.contactPoint = contact_point
        self.assertEqual(contact_point, connection.contactPoint)
        contact_point = 3
        with self.assertRaises(AttributeError):
            connection.contactPoint = contact_point

        # test laneLinks attribute
        lanelink1 = LaneLink()
        lanelink2 = LaneLink()
        lanelink3 = LaneLink()
        connection.addLaneLink(lanelink1)
        connection.addLaneLink(lanelink3)
        connection.addLaneLink(lanelink2)
        self.assertEqual([lanelink1, lanelink3, lanelink2], connection.laneLinks)
        with self.assertRaises(TypeError):
            connection.addLaneLink("lane")
            connection.addLaneLink(23)

    def test_initialize_laneLink(self):
        incoming_lane = 2
        connection_lane = 4

        lane_link = LaneLink()
        lane_link.fromId = incoming_lane
        lane_link.toId = connection_lane

        self.assertEqual(incoming_lane, lane_link.fromId)
        self.assertEqual(connection_lane, lane_link.toId)
        self.assertEqual(str(incoming_lane) + " > " + str(connection_lane), str(lane_link))


if __name__ == '__main__':
    unittest.main()
