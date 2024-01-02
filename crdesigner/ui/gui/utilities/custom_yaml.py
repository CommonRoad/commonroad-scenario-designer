import yaml
from commonroad.common.util import Interval


def _interval_to_yaml(dumper, data):
    return dumper.represent_mapping("!interval", {"start": data.start, "end": data.end})


def _interval_from_yaml(loader, node):
    value = loader.construct_mapping(node)
    return Interval(value["start"], value["end"])


def add_custom_interval_interpreter():
    yaml.add_representer(Interval, _interval_to_yaml)
    yaml.add_constructor("!interval", _interval_from_yaml)
