import unittest
from crdesigner.map_conversion.opendrive.opendrive_parser.elements.roadLink import *


class TestRoadLink(unittest.TestCase):
    def test_initialize_predecessor(self):
        element_type = "junction"
        element_id = "1"
        contact_p = "start"
        pre = Predecessor(element_type=element_type, element_id=element_id, contact_point=contact_p)

        self.assertEqual("junction", pre.elementType)
        self.assertEqual(1, pre.element_id)
        self.assertEqual("start", pre.contactPoint)
        with self.assertRaises(AttributeError):
            pre.elementType = "test"
            pre.elementType = 1
            pre.elementType = None
            pre.contactPoint = "test"
            pre.contactPoint = 1
            pre.contactPoint = None
            pre_new = Predecessor(element_type="wrong", element_id=2, contact_point="wrong")

    def test_initialize_neighbor(self):
        side = "left"
        element_id = "9"
        direction = "same"
        neighbor = Neighbor(side=side, element_id=element_id, direction=direction)

        self.assertEqual("left", neighbor.side)
        self.assertEqual(9, neighbor.element_id)
        self.assertEqual("same", neighbor.direction)
        with self.assertRaises(AttributeError):
            neighbor.side = "test"
            neighbor.side = 2
            neighbor.side = None
            neighbor.direction = "test"
            neighbor.direction = 4
            neighbor.direction = None
            neighbor_new = Neighbor(side="wrong", element_id=1, direction="opposite")

    def test_link(self):
        pre = Predecessor(element_type="road", element_id="1", contact_point="start")
        suc = Successor(element_type="junction", element_id="2", contact_point="end")
        n1 = Neighbor(side="left", element_id="3", direction="same")
        n2 = Neighbor(side="right", element_id="-1", direction="opposite")
        road_link = Link(predecessor=pre, successor=suc)

        self.assertEqual(pre, road_link.predecessor)
        self.assertEqual(suc, road_link.successor)
        with self.assertRaises(TypeError):
            road_link.predecessor = "test"
            road_link.predecessor = 2
            road_link.successor = "test"
            road_link.successor = 2
            road_link.neighbors = "test"
            road_link.neighbors = 3
            road_link.addNeighbor(2)
            road_link.addNeighbor("test")
            road_link.neighbors = n1
            road_link.neighbors = [2, n1]
        road_link.neighbors = [n1]
        road_link.addNeighbor(n2)
        self.assertEqual([n1, n2], road_link.neighbors)


if __name__ == '__main__':
    unittest.main()
