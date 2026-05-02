"""Mutation utilities for imagelab

   Various utilities for altering a canvas based on different algorithms, etc

   class MutationEvent:

    An event that can be applied to any canvas.
    It keeps track of the Mutator who should run this event.

    a) We tell the Mutator to draw a random shape on our canvas.
       These are the mutatorInstructions
    b) Mutator draws a red circle of radius 3 at x:20, y:20 and then a 2px
       blue line from x:1 - y:33 .  These are mutatorActions

    Storing both gives us the ability to send the same instructions,
    or replay the events exactly.

    This class should remain light weight

    #surface = None
    name = None

    # Input to the Mutator. simple dictionary of instrctions.
    # Might be slimmer to use op-codes, though.
    # When saving, we may opt to only save the actions, actually,
    # since we may not care how
    #They were achieved
    #mutatorInstructions = []

    #Output from the Mutator.  A sequence of actions taken against the canvas
    actions = []

    def __init__(self, name, actions):
        self.name = name
        self.actions = actions

    #def serialize(self):
    #    ret = self.mutatorName, self.mutatorActions
    #    return pickle.dumps(ret)
"""
from imagelab import rng
from imagelab.constants import (
    SHAPE_CIRCLE,
    SHAPE_POLYGON,
    SHAPE_SETTINGS_ARRAY,
    POLYGON_NUM_SIDES,
)
from imagelab.drawing import draw_random_circle, draw_random_polygon, draw_random_word
from imagelab.compare import best_match


def mutator(mutator_fn):
    """Take some arguments and return a surface and actions that were applied
    to it"""

    def wrap(*__args, **__kw):
        actions, surface = mutator_fn(*__args, **__kw)
        # return MutationEvent(mutator_fn.__name__, actions), surface
        return actions, surface, mutator_fn.__name__

    return wrap


@mutator
def mutate_null(surface):
    """Do nothing. Used to test pipeline"""
    return [], surface


@mutator
def mutate_evolve(surface, params):
    """Spawn child surfaces and return the one closes to the target"""
    clip_rect = params.get("clip_rect")
    shape = params.get("shape", SHAPE_CIRCLE)
    max_radius = params.get("max_radius", (clip_rect.width / 2))
    radius = params.get("radius")
    max_edges = params.get("max_edges", 8)
    alpha = params.get("alpha", 180)
    color = params.get("color")
    color_key = params.get("color_key", (0, 0, 0))
    children = params.get("children", 80)
    pos = params.get("pos")
    target = params.get("target")
    child_callback = params.get("child_callback", None)
    words = params.get("words", None)
    brush_images = params.get("brush_images", None)
    score_fn = params.get("score_fn", None)
    # TODO: move above PARAMS into **kwargs and set default vaules via
    # new_params = defaults.copy()
    # new_params.update(params)
    # and maybe filter:
    # whitelist = ['color', clip_rect', ...]
    # cleaned_params = {key: value for key, value in dict.items() if key
    #   in whitelist}
    morph_results = morph_surface(
        surface,
        children,
        clip_rect,
        shape,
        words,
        max_radius,
        radius,
        alpha,
        color,
        color_key,
        pos,
        max_edges,
        child_callback=child_callback,
        brush_images=brush_images,
    )

    # get the list of surfaces
    # surface_candidates = morph_results[2]
    shape_actions, winning_surface, score = best_match(
        target, surface, morph_results, clip_rect,
        score_fn=score_fn,
        candidates_are_clipped=(clip_rect is not None),
    )

    # When clip_rect is active, candidates are clip-sized surfaces.
    # Composite the winner back onto a full canvas copy.
    if clip_rect is not None:
        if shape_actions:
            clipped_rect = surface.get_rect().clip(clip_rect)
            surface = surface.copy()
            surface.blit(winning_surface, clipped_rect.topleft)
        # else: no improvement, surface unchanged
    else:
        surface = winning_surface

    try:
        # get the shape instructions that made the best match
        # shape_actions.append(morph_results[1][id(surface)])
        pass
    except KeyError:
        # no shape showed an improvement, let's note that
        #        shape_actions.append(None)
        pass
    return shape_actions, surface


""" Utility functions
   if your mutator does something special, consider putting it here so all of
   the components can be used by other mutators
"""


def morph_surface(
    canvas,
    count=1,
    clip_rect=None,
    shape=SHAPE_CIRCLE,
    words=None,
    max_radius=0,
    radius=None,
    alpha=None,
    color=None,
    color_key=(0, 0, 0),
    pos=None,
    max_edges=None,
    child_callback=None,
    brush_images=None,
):
    """
    Takes an origin surface (canvas) and creates multiple (count) children.
    Then, randomly plots a 'shape' of random size color and position.
    If return_actions is true, it will return an array containing the
    metadata used to make each child indexed by id(child)
    """
    i = 0

    if shape is None:
        shape = SHAPE_SETTINGS_ARRAY[rng.integers(0, 6)]

    # When clip_rect is active, draw on clip-sized surfaces to avoid copying
    # the full canvas for every child. One full copy is made by mutate_evolve
    # only for the winning child.
    if clip_rect is not None:
        clipped_rect = canvas.get_rect().clip(clip_rect)
        clip_base = canvas.subsurface(clipped_rect).copy()
        surface_origin = clipped_rect.topleft
    else:
        clip_base = None
        surface_origin = (0, 0)

    while i < count:
        i += 1

        img = clip_base.copy() if clip_rect is not None else canvas.copy()

        if words:
            result = draw_random_word(
                img, words, None, clip_rect,
                max_radius, radius, alpha, color, color_key, pos, brush_images,
                surface_origin=surface_origin,
            )
        elif shape in POLYGON_NUM_SIDES or shape == SHAPE_POLYGON:
            numSides = None if shape == SHAPE_POLYGON else POLYGON_NUM_SIDES[shape]
            result = draw_random_polygon(
                img, numSides, None, clip_rect,
                max_radius, radius, alpha, color, color_key, pos, max_edges, brush_images,
                surface_origin=surface_origin,
            )
        else:
            result = draw_random_circle(
                img, clip_rect,
                max_radius, radius, alpha, color, color_key, pos, brush_images,
                surface_origin=surface_origin,
            )

        if child_callback:
            child_callback(i, result, img)

        yield [img, [result]]
