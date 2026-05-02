"""Color Routines for imagelab
"""
from numpy.random import randint


def get_random_color():
    """Return a random RGB triplet"""
    return (randint(0, 255), randint(0, 255), randint(0, 255))
