"""Color Routines for imagelab
"""
from imagelab import rng


def get_random_color():
    """Return a random RGB triplet"""
    return (rng.integers(0, 255), rng.integers(0, 255), rng.integers(0, 255))
