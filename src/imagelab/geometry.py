"""Math and geometry utilities for imagelab
"""
import math
from numpy.random import randint
from numpy.random import choice
from imagelab.color import get_random_color

def get_random_clip_rect(rect, clip_width, clip_height, constrain=False):
    """ Take an input rectangle and return a random sub rectange if constrain
        is true, do not allow the output rect to extend beyond
        input rect bounds
    """
    if constrain:
        x_pos = randint(0, rect.width - clip_width)
        y_pos = randint(0, rect.height - clip_height)
    else:
        x_pos = randint(0 - (clip_width/2), rect.width - (clip_width/2))
        y_pos = randint(0 - (clip_height/2), rect.height - (clip_height/2))

    return (x_pos, y_pos, clip_width, clip_height)


def resize_with_pad(source_size, target_size):
    (source_width, source_height) = source_size
    (target_width, target_height) = target_size
    target_ratio = target_height / target_width
    source_ratio = source_height / source_width
    if target_ratio > source_ratio:
        # It must be fixed by width
        resize_width = target_width
        resize_height = round(resize_width * source_ratio)
    else:
        # Fixed by height
        resize_height = target_height
        resize_width = round(resize_height / source_ratio)

    return (resize_width, resize_height)


def get_random_circle(canvas, clip_rect=None, max_radius=20, radius=None,
                      color=None, color_key=(0, 0, 0), pos=None):
    """Create a random circle, defined by color position and radius"""
    if not radius:
        radius = randint(1, max_radius)

    if not color:
        color = get_random_color()

    if not pos:
        if clip_rect:
            pos = (randint(clip_rect.left + radius, clip_rect.right - radius),
                   randint(clip_rect.top + radius, clip_rect.bottom - radius))
        else:
            pos = (randint(0, max(canvas.get_rect().size)),
                   randint(0, max(canvas.get_rect().size)))

    return (color, pos, radius)


# todo: allow for random irregular polygons:
# https://observablehq.com/@tarte0/generate-random-simple-polygon
# todo: look into getting rid of max_(edges, radius) and simply letters
# edge/radius,etc be a tuple: (min,max) or a single value
def get_random_polygon(canvas, edges=None, rotation=None, clip_rect=None,
                       max_radius=20, radius=None, color=None, pos=None,
                       max_edges=8):
    """Create a random polygon defined by color position
       edges rotation and radius"""
    if not radius:
        radius = randint(1, max_radius + 1)

    if not color:
        color = get_random_color()

    if not edges:
        edges = randint(3, max_edges)

    if rotation is None:
        rotation = randint(0, 361)

    if not pos:
        if clip_rect:
            pos = (randint(clip_rect.left + max_radius,
                           clip_rect.right - max_radius + 1),
                   randint(clip_rect.top + max_radius,
                           clip_rect.bottom - max_radius + 1))
        else:
            pos = (randint(0, max(canvas.get_rect().size)),
                   randint(0, max(canvas.get_rect().size)))

    return (color, pos, radius, edges, rotation)


def get_random_word(canvas, words, rotation=None, clip_rect=None,
                    max_radius=20, radius=None, color=None, pos=None):
    word = choice(words, size=None)
    if not radius:
        radius = randint(1, max_radius + 1)

    if not color:
        color = get_random_color()

    if rotation is None:
        rotation = randint(0, 361)

    if not pos:
        if clip_rect:
            pos = (randint(clip_rect.left + max_radius,
                           clip_rect.right - max_radius + 1),
                   randint(clip_rect.top + max_radius,
                           clip_rect.bottom - max_radius + 1))
        else:
            pos = (randint(0, max(canvas.get_rect().size)),
                   randint(0, max(canvas.get_rect().size)))

    return (color, pos, radius, word, rotation)


def get_polygon(edges=3, radius=10, pos=(0, 0), rotation=0):
    d_angle = 2*math.pi / edges

    rad = rotation * (180/math.pi)

    ret = []

    for i in range(edges):
        point = (pos[0] + radius*math.cos(rad), pos[1] + radius*math.sin(rad))

        ret.append(point)

        rad += d_angle

    return ret
