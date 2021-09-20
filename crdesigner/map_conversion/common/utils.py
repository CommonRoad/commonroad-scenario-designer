__author__ = "Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["BMW Car@TUM"]
__version__ = "0.2"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Released"


def generate_unique_id(set_id: int = None):
    if not hasattr(generate_unique_id, "counter"):
        generate_unique_id.counter = 0  # it doesn't exist yet, so initialize it
    if set_id is not None:
        generate_unique_id.counter = set_id
        return generate_unique_id.counter
    generate_unique_id.counter += 1
    return generate_unique_id.counter
