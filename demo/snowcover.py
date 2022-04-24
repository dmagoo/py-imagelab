import sys
import pygame
import numpy as np
from imagelab import filters
from imagelab import drawing


SCREENRECT = pygame.Rect(0, 0, 1000, 800)

BG_COLOR = (200, 200, 200)

BIT_DEPTH = 16
clock = pygame.time.Clock()


def snow_cover(background, lighten=False):
    """take a background and cover it with a snow like effect"""
    drawing.draw_random_circle(background, max_radius=40,
                               alpha=np.random.randint(10, 80),
                               color=(150, 150, np.random.randint(150, 200)))

    for i in range(10):
        drawing.draw_random_circle(background, max_radius=80,
                                   alpha=np.random.randint(10, 100),
                                   color=(150, 150,
                                          np.random.randint(150, 255))
                                   if lighten else BG_COLOR)

def main(argv, argc):
    # set up the pygame engine
    pygame.init()

    # Returns a Surface obj, screen is the main display
    screen = pygame.display.set_mode(SCREENRECT.size, 0, BIT_DEPTH)

    # our output buffer
    background = pygame.Surface(SCREENRECT.size)
    background.fill(BG_COLOR)

    # set this to false when it's time to stop this crazy thing
    running = True
    lighten = False

    while running:
        # some gui controls
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_SPACE:
                    # applyEmboss(background)
                    filters.apply_gaussian_blur(background)

                if event.key == pygame.K_RETURN:
                    lighten = ({True: False, False: True}[lighten])

        snow_cover(background, lighten)
        screen.blit(background, (0, 0))
        pygame.display.update()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    _argv = sys.argv[1:]
    main(_argv, len(_argv))
