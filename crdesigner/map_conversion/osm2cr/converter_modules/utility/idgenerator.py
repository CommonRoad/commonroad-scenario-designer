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
        """
        res = self.counter
        self.counter += 1
        return res

    def reset(self):
        """
        resets id generator

        :return: None
        """

        self.counter = 0


def get_id():
    """
    draws a unique id

    :return: new id
    """
    return generator.get()


def reset():
    """
    resets id generator

    :return: None
    """
    generator.reset()


generator = IdGenerator()
