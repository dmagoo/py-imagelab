import sys
import pygame
import numpy as np
from imagelab import filters

SCREENRECT = pygame.Rect(0, 0, 1000, 800)

BG_COLOR = (200, 200, 200)

BIT_DEPTH = 16
clock = pygame.time.Clock()


def do_gradient(background):
    # pixel color = d1/d2 * gradient color delta,
    # where d1 is center - pixel,
    # d2 is center - min(w,h) of bitmap dimensions,
    # and gradient color delta is (r2-r1) or (g2-g1) or (b2-b1) of your
    # gradient.
    circle_surface = pygame.Surface(
        (np.random.randint(10, 400), np.random.randint(40, 400))
    )
    circle_surface.set_colorkey((0, 0, 0))
    circle_surface.fill((00, 0, 0))
    src_array = pygame.surfarray.array3d(circle_surface).astype(int)

    l = len(src_array)
    w = len(src_array[0])

    o = (w/2, l/2)

    # center color
    c1 = [0, 0, 200]
    c1 = [np.random.randint(0, 255), np.random.randint(0, 255),
          np.random.randint(0, 255)]

    # outside
    c2 = [0, 200, 0]
    c2 = [255, 200, 200]
    c2 = [np.random.randint(0, 255), np.random.randint(0, 255),
          np.random.randint(0, 255)]

    cdiff = np.subtract(c1, c2)

    maxD = d = np.sqrt(o[0]**2 + o[1]**2)

    # This will draw a black X
    for i in range(l):
        for j in range(w):
            dx = o[0] - j
            dy = o[1] - i

            # distance of pixel from center
            d = np.sqrt(dx**2 + dy**2)

            # $red=$left_color[0]-floor($Y*$color0)
            # $green=$left_color[1]-floor($Y*$color1)
            # $blue=$left_color[2]-floor($Y*$color2)

            rgb = np.subtract(c1, d*(np.array(cdiff) / maxD))
            src_array[i][j] = tuple(rgb)

    pygame.surfarray.blit_array(circle_surface, src_array)

    background.blit(circle_surface, (220, 200))


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

    while running:
        # some gui controls
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_SPACE:
                    filters.apply_gaussian_blur(background)

        do_gradient(background)
        screen.blit(background, (0, 0))
        pygame.display.update()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    _argv = sys.argv[1:]
    main(_argv, len(_argv))
