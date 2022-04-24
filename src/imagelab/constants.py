"""Constants for imagelab"""


SHAPE_CIRCLE = 0
SHAPE_POLYGON = 1
SHAPE_TRIANGLE = 3
SHAPE_SQUARE = 4
SHAPE_PENTAGON = 5
SHAPE_HEXAGON = 6
SHAPE_OCTAGON = 8

POLYGON_NUM_SIDES = {
    SHAPE_TRIANGLE: 3,
    SHAPE_SQUARE: 4,
    SHAPE_PENTAGON: 5,
    SHAPE_HEXAGON: 6,
    SHAPE_OCTAGON: 8
}

SHAPE_SETTINGS_ARRAY = [SHAPE_CIRCLE, SHAPE_TRIANGLE, SHAPE_POLYGON,
                        SHAPE_SQUARE, SHAPE_OCTAGON, SHAPE_PENTAGON,
                        SHAPE_HEXAGON]
SHAPE_SETTINGS_NAMES = ['circle', 'triangle', 'polygon', 'square', 'octagon',
                        'pentagon', 'hexagon']

# friendly names to constants
SHAPE_MAP = dict(zip(SHAPE_SETTINGS_NAMES, SHAPE_SETTINGS_ARRAY))

# constants to friendly names
SHAPE_NAME_MAP = dict(zip(SHAPE_SETTINGS_ARRAY, SHAPE_SETTINGS_NAMES))
