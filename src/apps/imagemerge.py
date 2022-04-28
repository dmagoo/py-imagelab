from collections.abc import Iterable
import os
import pygame
from imagelab import filters

IMAGE_EXTENSIONS = (".bmp", ".jpg", ".jpeg", ".png", ".gif")
SCREENRECT = pygame.Rect(0, 0, 680, 480)
BG_COLOR = (33, 33, 33)

DEFAULT_IMAGE_SAVE_EXT = 'png'


def flatten(input_list):
    for el in input_list:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def is_image_file(path):
    return path.is_file() and path.suffix.endswith(IMAGE_EXTENSIONS)


class App:
    options = {}
    running = False
    surface = None
    _input_files = []

    bit_depth = 32
    _selected_filter = staticmethod(filters.average_subtract_outlier_surfaces)

    def __init__(self, options=None):
        if options is not None:
            self.set_options(options)
        self.print("starting app")

    def set_options(self, options):
        """Set the config options for this instance
        """
        self.options = options

        # validate the input files
        self.validate_input_files(self.options.get('target_path', []))

    def run(self):
        pass
        self.initialize_display()
        self.running = True
        self._changed = True
        while self.running:
            self.update_display()
            if self._changed:
                self.run_merger()
                self._changed = False
            self.handle_events()

    def initialize_display(self):
        """Set up the display"""
        if self.options.get('no_display', False):
            return

        self.print("initializing display")
        pygame.init()

        self.screen = pygame.display.set_mode(
            SCREENRECT.size,
            pygame.RESIZABLE, self.bit_depth
        )

    def update_display(self):
        pygame.display.update()

    def handle_events(self):
        """ handle keyboard inputs """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit("User Quit")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit("User Quit")
                elif event.key == pygame.K_RETURN:
                    self._changed = True
                    self.save()
            elif event.type == pygame.VIDEORESIZE:
                self.update_display()

    def save(self):
        """ Output to file """
        if not self.surface:
            self.print("image not processed")
            return
        savefile = self.get_save_file_name(DEFAULT_IMAGE_SAVE_EXT)
        self.print(f"saving file {savefile}")
        os.makedirs(os.path.dirname(savefile), exist_ok=True)
        pygame.image.save(self.surface, savefile)

    def get_save_file_name(self, ext=None):
        """ Return a save-file name based on template configuration and
            app state """

        file_name = 'merge-output'

        if ext is not None:
            file_name = file_name + '.' + ext

        path = self.options.get('save_directory', '.')

        return os.path.join(path, file_name)

    def validate_input_files(self, input_file_list):
        unflattened = [
            path if is_image_file(path)
            else [
                file for file in path.iterdir() if
                is_image_file(file) and path.is_dir()
            ]
            for path in input_file_list
        ]
        self._input_files = sorted(set(flatten(unflattened)))
        print(f"{len(self._input_files)} image files found for processing")

    def print(self, output_string):
        if self.options.get('verbose', False):
            print(output_string)

    def run_merger(self):
        background = pygame.Surface(SCREENRECT.size)
        layers = []
        self.print("loading surfaces")
        dimensions = None
        for path in self._input_files:
            surface = pygame.image.load(path)
            if dimensions is None:
                dimensions = surface.get_size()
                self.print(f"setting canvas dimentions: {dimensions}")
                background = pygame.Surface(dimensions)
                self.screen = pygame.display.set_mode(
                    dimensions,
                    pygame.RESIZABLE, self.bit_depth
                )
            current_dimensions = surface.get_size()
            if current_dimensions != dimensions:
                raise ValueError(
                    f"Dimension Mismatch for file: {path.resolve()}"
                )
            surface.convert()
            layers.append(surface)

        self.print("applying filters")
        av = self.filter_surface(layers)
        background.fill(BG_COLOR)
        background.blit(av, (0, 0))
        self.surface = background
        self.screen.blit(background, (0, 0))
        pygame.display.update()

    def filter_surface(self, layers):
        return self._selected_filter(layers)
