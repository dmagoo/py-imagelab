"""Shared random number generator for imagelab."""
import numpy.random as npr

_rng = npr.default_rng()


def seed(value=None):
    # Replace the global generator. In parallel workers, call with
    # seed + worker_index so each worker is deterministic but distinct.
    global _rng
    _rng = npr.default_rng(value)


def integers(low, high=None):
    return _rng.integers(low, high)


def choice(a, size=None):
    return _rng.choice(a, size=size)
