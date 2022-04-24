"""Canvas utilities for imagelab

A canvas contains a pygame surface and represents the current state and history
of an drawing
"""
import pickle
import pygame
from imagelab.constants import SHAPE_CIRCLE
from imagelab.geometry import get_polygon


class Canvas:
    """A wrapper for a pygame surface.  Holds the surface, its history
      and provides some methods
    """
    surface = None
    history = []

    def __init__(self, surface=None):
        self.surface = surface

    @property
    def size(self):
        """ Pass through to surface size """
        if self.surface is None:
            return (0, 0)
        return self.surface.get_size()

    def apply_mutator(self, mutator, args={}):
        # mutation_event = mutator(self.surface, args)
        actions, surface, _ = mutator(self.surface, args)
        # self.surface = mutation_event.surface
        self.surface = surface

        # clear out the surface from the event.  We don't need it in Mem
        # IMPORTANT!
        # mutation_event.surface = None

        # self.history.append(mutation_event)
        self.history.extend(actions)

    def apply_canvas_action(self, canvas_action):
        pass

    def serialize(self):
        pass

    def deserialize(self, serialized_data):
        pass


class CanvasAction:
    """Abstract (interface, really) These are single actions.
        They should be kept simple. They must be serializable. This is what the
        Mutators use to record the history of their actions.  Think of them as
        serializable wrappers to function calls.  One rule of thumb for these
        mutators is that given input, output should always be identical. These
        are wrappers for primitive drawing routines. None of the routines
        called should do anything random. If you are tempted to have this do
        something random... use a Mutator
    """
    params = {}

    def __init__(self, params):
        self.params = params

    def run(self, canvas):
        pass

    def serialize(self):
        return pickle.dumps(self.params)

    def unserialize(self, params):
        self.params = pickle.loads(params)


class CanvasActionDrawShape(CanvasAction):
    """Draw a shape on the canvas"""

    opCode = "s"

    def run(self, canvas):
        alpha = self.params.get('alpha', 220)
        color = self.params.get('color')
        pos = self.params.get('pos')
        radius = self.params.get('radius')
        color_key = self.params.get('color_key', (0, 0, 0))
        shape = self.params.get('shape')
        rotation = self.params.get('rotation')
        edges = self.params.get('edges')

        if SHAPE_CIRCLE == shape:
            if alpha:
                circle_surface = pygame.Surface((radius*2, radius*2))
                circle_surface.set_colorkey(color_key)
                circle_surface.fill(color_key)
                circle_surface.set_alpha(alpha)
                pygame.draw.circle(circle_surface, color,
                                   (radius, radius), radius, 0)

                canvas.blit(circle_surface, (pos[0] - radius, pos[1] - radius))

            else:
                pygame.draw.circle(canvas, color, pos, radius, 0)
        else:
            if alpha:
                polySurface = pygame.Surface((radius*2, radius*2))
                polySurface.set_colorkey(color_key)
                polySurface.fill(color_key)
                polySurface.set_alpha(alpha)
                pygame.draw.polygon(polySurface, color, get_polygon(
                    edges, radius, (radius, radius), rotation))

                canvas.blit(polySurface, (pos[0] - radius, pos[1] - radius))

            else:
                pygame.draw.polygon(canvas, color,
                                    get_polygon(edges, radius, pos, rotation))
