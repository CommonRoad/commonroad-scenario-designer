from copy import deepcopy

from commonroad.scenario.lanelet import LaneletNetwork
from shapely import Point
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid


class SubMap:
    """
    Class representing a sub map.
    """

    def __init__(self, network: LaneletNetwork, buffer_size: float = 100.0):
        """
        Constructor.

        :param network: Lanelet network.
        :param buffer_size: Buffer size.
        """
        self._network = network
        self._buffer_size = buffer_size

        self._lanelet_ids = set()
        self._traffic_sign_ids = set()
        self._traffic_light_ids = set()
        self._intersection_ids = set()

    @property
    def lanelet_ids(self):
        return self._lanelet_ids

    @property
    def traffic_sign_ids(self):
        return self._traffic_sign_ids

    @property
    def traffic_light_ids(self):
        return self._traffic_light_ids

    @property
    def intersection_ids(self):
        return self._intersection_ids

    def create_subnetwork(self) -> LaneletNetwork:
        """
        Creates a subnetwork from the extracted IDs of lanelets, traffic signs, traffic lights, and intersections.

        :return: Subnetwork.
        """
        network = LaneletNetwork()

        for lanelet_id in self._lanelet_ids:
            if (lanelet := self._network.find_lanelet_by_id(lanelet_id)) is None:
                continue  # it might be the case that some CR element has a non-existent reference
            lanelet = deepcopy(lanelet)
            network.add_lanelet(lanelet)

        for traffic_sign_id in self._traffic_sign_ids:
            if (traffic_sign := self._network.find_traffic_sign_by_id(traffic_sign_id)) is None:
                continue  # it might be the case that some CR element has a non-existent reference
            traffic_sign = deepcopy(traffic_sign)
            network.add_traffic_sign(traffic_sign, set())

        for traffic_light_id in self._traffic_light_ids:
            if (traffic_light := self._network.find_traffic_light_by_id(traffic_light_id)) is None:
                continue  # it might be the case that some CR element has a non-existent reference
            traffic_light = deepcopy(traffic_light)
            network.add_traffic_light(traffic_light, set())

        for intersection_id in self._intersection_ids:
            if (intersection := self._network.find_intersection_by_id(intersection_id)) is None:
                continue  # it might be the case that some CR element has a non-existent reference
            intersection = deepcopy(intersection)
            network.add_intersection(intersection)

        network.cleanup_lanelet_references()
        network.cleanup_traffic_sign_references()
        network.cleanup_traffic_light_references()

        return network

    def extract_from_element(self, element_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the element and contained in the area of the element within a specific buffer size.

        :param element_id: Element ID.
        """
        if self._network.find_lanelet_by_id(element_id):
            self.extract_from_lanelet(element_id)
        elif self._network.find_traffic_sign_by_id(element_id):
            self.extract_from_traffic_sign(element_id)
        elif self._network.find_traffic_light_by_id(element_id):
            self.extract_from_traffic_light(element_id)
        elif self._network.find_intersection_by_id(element_id):
            self.extract_from_intersection(element_id)

    def extract_from_lanelet(self, lanelet_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the lanelet and contained in the area of the lanelet within a specific buffer size.

        :param lanelet_id: Lanelet ID.
        """
        self._extract_refs_from_lanelet(lanelet_id)
        self._extract_area_from_lanelet(lanelet_id)

    def extract_from_traffic_sign(self, traffic_sign_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the traffic sign and contained in the area of the traffic sign within a specific buffer size.

        :param traffic_sign_id: Traffic sign ID.
        """
        self._extract_refs_from_traffic_sign(traffic_sign_id)
        self._extract_area_from_traffic_sign(traffic_sign_id)

    def extract_from_traffic_light(self, traffic_light_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the traffic light and contained in the area of the traffic light within a specific buffer size.

        :param traffic_light_id: Traffic light ID.
        """
        self._extract_refs_from_traffic_light(traffic_light_id)
        self._extract_area_from_traffic_sign(traffic_light_id)

    def extract_from_intersection(self, intersection_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the intersection and contained in the area of the intersection within a specific buffer size.

        :param intersection_id: Intersection ID.
        """
        self._extract_refs_from_intersection(intersection_id)
        self._extract_area_from_intersection(intersection_id)

    def _extract_refs_from_lanelet(self, lanelet_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the lanelet.

        :param lanelet_id: Lanelet ID.
        """
        self._lanelet_ids.add(lanelet_id)

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        if lanelet.adj_left:
            self._lanelet_ids.add(lanelet.adj_left)
        if lanelet.adj_right:
            self._lanelet_ids.add(lanelet.adj_right)
        self._lanelet_ids = self._lanelet_ids.union(set(lanelet.successor))
        self._lanelet_ids = self._lanelet_ids.union(set(lanelet.predecessor))

        self._traffic_sign_ids = self._traffic_sign_ids.union(lanelet.traffic_signs)
        if lanelet.stop_line is not None and lanelet.stop_line.traffic_sign_ref is not None:
            self._traffic_sign_ids = self._traffic_sign_ids.union(
                lanelet.stop_line.traffic_sign_ref
            )
        self._traffic_light_ids = self._traffic_light_ids.union(lanelet.traffic_lights)
        if lanelet.stop_line is not None and lanelet.stop_line.traffic_light_ref is not None:
            self._traffic_light_ids = self._traffic_light_ids.union(
                lanelet.stop_line.traffic_light_ref
            )

    def _extract_refs_from_traffic_sign(self, traffic_sign_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the traffic sign.

        :param traffic_sign_id: Traffic sign ID.
        """
        self._traffic_sign_ids.add(traffic_sign_id)

        traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)

        self._lanelet_ids = self._lanelet_ids.union(traffic_sign.first_occurrence)
        self._lanelet_ids = self._lanelet_ids.union(
            set(
                la.lanelet_id
                for la in self._network.lanelets
                if traffic_sign_id in la.traffic_signs
            )
        )

    def _extract_refs_from_traffic_light(self, traffic_light_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the traffic light.

        :param traffic_light_id: Traffic light ID.
        """
        self._traffic_light_ids.add(traffic_light_id)
        self._lanelet_ids = self._lanelet_ids.union(
            set(
                la.lanelet_id
                for la in self._network.lanelets
                if traffic_light_id in la.traffic_lights
            )
        )

    def _extract_refs_from_intersection(self, intersection_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) referenced by
        the intersection.

        :param intersection_id: Intersection ID.
        """
        self._intersection_ids.add(intersection_id)

        intersection = self._network.find_intersection_by_id(intersection_id)

        for incoming in intersection.incomings:
            self._lanelet_ids = self._lanelet_ids.union(incoming.incoming_lanelets)
        #    self._lanelet_ids = self._lanelet_ids.union(incoming.outgoing_left)
        #    self._lanelet_ids = self._lanelet_ids.union(incoming.outgoing_straight)
        #    self._lanelet_ids = self._lanelet_ids.union(incoming.outgoing_right)
        #    self._lanelet_ids = self._lanelet_ids.union(incoming.crossings)

    def _extract_area_from_lanelet(self, lanelet_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) contained in the area of
        the lanelet within a specific buffer size.

        :param lanelet_id: Lanelet ID.
        """
        self._lanelet_ids.add(lanelet_id)

        lanelet = self._network.find_lanelet_by_id(lanelet_id)

        self._extract_area_from_element(lanelet.polygon.shapely_object)

    def _extract_area_from_traffic_sign(self, traffic_sign_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) contained in the area of
        the traffic sign within a specific buffer size.

        :param traffic_sign_id: Traffic sign ID.
        """
        self._traffic_sign_ids.add(traffic_sign_id)

        traffic_sign = self._network.find_traffic_sign_by_id(traffic_sign_id)

        pos = traffic_sign.position
        self._extract_area_from_element(Point(pos[0], pos[1]))

    def _extract_area_from_traffic_light(self, traffic_light_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) contained in the area of
        the traffic light within a specific buffer size.

        :param traffic_light_id: Traffic light ID.
        """
        self._traffic_light_ids.add(traffic_light_id)

        traffic_light = self._network.find_traffic_light_by_id(traffic_light_id)

        pos = traffic_light.position
        self._extract_area_from_element(Point(pos[0], pos[1]))

    def _extract_area_from_intersection(self, intersection_id: int):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) contained in the area of
        the intersection within a specific buffer size.

        :param intersection_id: Intersection ID.
        """
        pass  # TODO: Implement

    def _extract_area_from_element(self, shape: BaseGeometry):
        """
        Extracts the elements (e.g., lanelets, traffic signs, traffic lights, intersections) contained in the area of
        the shape of the element within a specific buffer size.

        :param shape: Shape.
        """
        shape.buffer(self._buffer_size, join_style=2)

        if not shape.is_valid:
            make_valid(shape)
            if not shape.is_valid:
                shape = shape.convex_hull

        for lanelet in self._network.lanelets:
            if lanelet.polygon.shapely_object.intersects(shape):
                self._lanelet_ids.add(lanelet.lanelet_id)

        for traffic_sign in self._network.traffic_signs:
            pos = traffic_sign.position
            if shape.contains(Point(pos[0], pos[1])):
                self._traffic_sign_ids.add(traffic_sign.traffic_sign_id)

        for traffic_light in self._network.traffic_lights:
            pos = traffic_light.position
            if shape.contains(Point(pos[0], pos[1])):
                self._traffic_light_ids.add(traffic_light.traffic_light_id)
