__author__ = "Sebastian Maierhofer"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["BMW Car@TUM"]
__version__ = "0.5"
__maintainer__ = "Sebastian Maierhofer"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Development"


def generate_unique_id():
    if not hasattr(generate_unique_id, "counter"):
        generate_unique_id.counter = 0  # it doesn't exist yet, so initialize it
    generate_unique_id.counter += 1
    return generate_unique_id.counter
