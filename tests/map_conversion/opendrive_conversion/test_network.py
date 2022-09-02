import unittest
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import Network
from crdesigner.map_conversion.opendrive.opendrive_conversion.network import LinkIndex
from crdesigner.configurations.get_configs import get_configs


class TestNetwork(unittest.TestCase):
    def test_assign_country_id(self):
        # test assigning country id by name
        id = 'YEMEN'
        n = Network(get_configs().opendrive)

        n.assign_country_id(id)
        self.assertEqual('YEM', n._country_ID)

        # test assigning country id by name
        id = 'Tanzania, United Republic of'
        n.assign_country_id(id)
        self.assertEqual('TZA', n._country_ID)

        # test assigning country id by alpha2
        id = 'SA'
        n.assign_country_id(id)
        self.assertEqual('SAU', n._country_ID)

        # test assigning country id by alpha3
        id = 'BLM'
        n.assign_country_id(id)
        self.assertEqual('BLM', n._country_ID)

        # test nonexistent country
        id = 'ZZZZZZZZZ'
        n.assign_country_id(id)
        self.assertEqual("ZAM", n._country_ID)
        # check if type error raised when not supplying a string
        self.assertRaises(AttributeError, n.assign_country_id, 5)
        # check if country id defaults to ZAM when supplied empty string
        id = ''
        n.assign_country_id(id)
        self.assertEqual("ZAM", n._country_ID)


class TestLinkIndex(unittest.TestCase):
    def test_init(self):
        link_index = LinkIndex()
        self.assertDictEqual({}, link_index._successors)
        self.assertListEqual([], link_index._intersections)
        self.assertDictEqual({}, link_index._intersection_dict)

    def test_get_successors(self):
        link_index = LinkIndex()
        link_index._successors = {'88.0.4.-1': ['79.0.-1.-1', '79.0.-2.-1']}
        self.assertListEqual([], link_index.get_successors('100.0.0.0'))
        self.assertListEqual(['79.0.-1.-1', '79.0.-2.-1'], link_index.get_successors('88.0.4.-1'))

    def test_intersection_maps(self):
        link_index = LinkIndex()
        link_index._intersections = {"foo": 0}
        self.assertDictEqual({"foo": 0}, link_index.intersection_maps())

    def test_add_link(self):
        link_index = LinkIndex()
        link_index.add_link('88.0.4.-1', '79.0.-1.-1', False)
        self.assertDictEqual({'88.0.4.-1': ['79.0.-1.-1']}, link_index._successors)

        link_index = LinkIndex()
        link_index.add_link('69.0.0.-1', '71.0.0.-1', True)
        self.assertDictEqual({'71.0.0.-1': ['69.0.0.-1']}, link_index._successors)

    def test_remove(self):
        link_index = LinkIndex()
        link_index._successors = {'88.0.4.-1': ['79.0.-1.-1', '79.0.-2.-1'], '100.0.0.0': ['101.0.0.0']}
        link_index.remove('88.0.4.-1')
        self.assertDictEqual({'100.0.0.0': ['101.0.0.0']}, link_index._successors)

    def test_get_predecessors(self):
        link_index = LinkIndex()
        link_index._successors = {'88.0.4.-1': ['79.0.-1.-1', '79.0.-2.-1'], '100.0.0.0': ['79.0.-1.-1']}
        self.assertListEqual(['88.0.4.-1', '100.0.0.0'], link_index.get_predecessors('79.0.-1.-1'))
