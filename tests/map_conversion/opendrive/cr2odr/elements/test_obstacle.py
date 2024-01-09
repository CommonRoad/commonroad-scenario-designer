import unittest

import numpy as np
from commonroad.geometry.shape import Circle, Polygon, Rectangle
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.trajectory import InitialState
from lxml import etree

from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.obstacle import (
    Obstacle,
)
from crdesigner.map_conversion.opendrive.cr_to_opendrive.elements.road import Road
from crdesigner.ui.gui.utilities.map_creator import MapCreator


class TestObstacle(unittest.TestCase):
    def setUp(self):
        # Initialize lanenet
        lanelet_id = 1000
        self.lanelet = MapCreator.create_straight(2, 8, 9, lanelet_id, set())

        # Initialize road
        writer = etree.Element("ObstacleTest")
        road = Road(lane_list=[self.lanelet], number_of_lanes=1, root=writer, junction_id=-1)

        # Initialize cr2opendrive obstacle
        self.shape = Rectangle(length=3.5, width=6.0)
        self.state = InitialState(
            time_step=0,
            position=np.array([0.3, 0.5]),
            orientation=0.075,
            velocity=0.0,
            acceleration=0.0,
            yaw_rate=0.0,
            slip_angle=0.0,
        )
        self.obstacle = Obstacle(ObstacleType.UNKNOWN, [self.lanelet.lanelet_id], self.shape, self.state)

    def test_initialization(self):
        # Testing initialization is correct
        obstacle = self.obstacle
        self.assertEqual(str(obstacle.id), obstacle.object.get("id"))
        self.assertEqual(obstacle.type, obstacle.object.get("type"))
        self.assertEqual("none", obstacle.object.get("orientation"))
        self.assertEqual(str(self.shape.width), obstacle.object.get("width"))
        self.assertEqual(str(self.shape.length), obstacle.object.get("length"))
        self.assertEqual(None, obstacle.object.get("radius"))

        # Testing coordinates
        final_position = (0.3, -0.5)
        self.assertAlmostEqual(final_position[0], float(obstacle.object.get("s")))
        self.assertAlmostEqual(final_position[1], float(obstacle.object.get("t")))
        self.assertEqual("0.0", obstacle.object.get("zOffset"))

    def test_set_rectangle(self):
        # Testing with Rectangle as shape
        obstacle = self.obstacle
        rectangle = Rectangle(length=2.0, width=3.0)
        obstacle.set_rectangle(rectangle)
        self.assertEqual(str(rectangle.width), obstacle.object.get("width"))
        self.assertEqual(str(rectangle.length), obstacle.object.get("length"))

    def test_set_circle(self):
        obstacle = self.obstacle
        # Testing with Circle as shape
        circle = Circle(radius=5.0)
        obstacle.set_circle(circle)
        self.assertEqual(str(circle.radius), obstacle.object.get("radius"))

    def test_set_polygon(self):
        # Testing with Polygon as shape
        obstacle = self.obstacle
        polygon = Polygon(vertices=np.array([[0.0, 0.0], [2.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]))
        obstacle.set_polygon(polygon)
        etree_vertices = list(obstacle.outline)
        self.assertEqual(len(polygon.vertices) - 1, len(etree_vertices))
        for vert, etreeVert in zip(polygon.vertices[:-1], etree_vertices):
            self.assertEqual(str(vert[0]), etreeVert.get("u"))
            self.assertEqual(str(vert[1]), etreeVert.get("v"))
