"""Drawing Routines to be applied as CanvasActions
"""
from imagelab.constants import SHAPE_POLYGON, SHAPE_CIRCLE
from imagelab.geometry import (get_random_circle, get_random_polygon,
                               get_random_word)
from imagelab.canvas import CanvasActionDrawShape
from imagelab.canvas import CanvasActionDrawText


def draw_random_circle(canvas, clipRect=None, max_radius=20, radius=None,
                       alpha=None, color=None, color_key=(0, 0, 0), pos=None):
    """Apply paint to the canvas, return details of the circle."""

    (color, pos, radius) = get_random_circle(canvas, clipRect, max_radius,
                                             radius, color, pos)

    params = {'color': color, 'pos': pos, 'radius': radius, 'alpha': alpha,
              'shape': SHAPE_CIRCLE}

    ca = CanvasActionDrawShape(params)
    ca.run(canvas)

    return ca


def draw_random_polygon(canvas, edges=None, rotation=None, clipRect=None,
                        max_radius=20, radius=None, alpha=None, color=None,
                        color_key=(0, 0, 0), pos=None, max_edges=8):
    """Apply paint to the canvas, return details of the polygon."""

    (color, pos, radius, edges, rotation) = get_random_polygon(
        canvas, edges, rotation, clipRect, max_radius, radius, color,
        pos, max_edges)

    params = {'color': color, 'pos': pos, 'radius': radius, 'edges': edges,
              'rotation': rotation, 'alpha': alpha, 'shape': SHAPE_POLYGON}

    ca = CanvasActionDrawShape(params)
    ca.run(canvas)

    return ca


def draw_random_word(canvas, words, rotation=None, clip_rect=None,
                     max_radius=20, radius=None, alpha=None, color=None,
                     color_key=(0, 0, 0), pos=None):
    """ Apply paint to the canvas, return details of a random word from
        candidate list """

    (color, pos, radius, word, rotation) = get_random_word(
        canvas, words, rotation, clip_rect, max_radius, radius, color, pos)

    params = {'color': color, 'pos': pos, 'radius': radius,
              'rotation': rotation, 'alpha': alpha,
              'text': word}

    ca = CanvasActionDrawText(params)
    ca.run(canvas)

    return ca
