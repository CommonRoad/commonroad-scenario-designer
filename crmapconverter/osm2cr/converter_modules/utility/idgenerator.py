"""
This module provides a simple id generator which can be used to draw unique ids
without instantiation across several modules.
"""


class IdGenerator:
    """
    a generator for unique ids
    """

    def __init__(self):
        """
        creates an id generator
        """
        self.counter = 0

    def get(self):
        """
        draws a new id

        :return: new id
        :rtype: int
        """
        res = self.counter
        self.counter += 1
        return res


generator = IdGenerator()


def get_id():
    """
    draws a unique id

    :return: new id
    :rtype: int
    """
    return generator.get()
