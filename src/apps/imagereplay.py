"""CLI for imagemutate App.

Produce a target image by randomly mutating a base canvas
"""
import json
import pygame
import os
from imagelab.geometry import resize_with_pad
from imagelab.canvas import Canvas

DEFAULT_DISPLAY_BG_COLOR = (3, 3, 100)
DEFAULT_DISPLAY_MARGIN_PX = 20
DEFAULT_BIT_DEPTH = 32

DEFAULT_IMAGE_SAVE_EXT = "png"
DEFAULT_SAVE_TEMPLATE = "%PREFIX-%FRAME%CHILDREN%GENERATION"

# consider scaling based on display? nt(450*h/768))
STATS_FONT_SIZE = 32
# STATS_FONT_PATH = "./assets/fonts/RisingSun/RisingSun-Regular.ttf"
STATS_FONT_PATH = "./assets/fonts/luculent/luculent.ttf"

clock = pygame.time.Clock()


class App:
    """
    Replay a saved output file.
    """

    options = {}
    running = False

    canvas = None

    # Display Settings
    # the pygame screen display
    screen = None

    # base background image
    background = None

    display_bg_color = None
    display_margin_px = None
    bit_depth = None

    stats_font = None

    current_run = 0
    current_generation = 0
    current_frame = None
    _movie_mode = False

    _last_flip_time = 0
    _show_info = False

    def __init__(self, options=None):
        self.bit_depth = DEFAULT_BIT_DEPTH
        if options is not None:
            self.set_options(options)
        self.print("starting app")

    def __del__(self):
        self.print("exiting")
        pygame.quit()

    def set_options(self, options):
        """Set the config options for this instance
        Positional arguments:
        options -- a simple dict of options used by this app
        """
        self.options = options

    def run(self):
        """Run this app"""
        self.load()
        self.initialize_display()
        self.running = True
        while self.running:
            self.main_loop()

    def load(self):
        with open(self.options.get("input_path"), "r") as f:
            data = json.load(f)
            self.canvas = Canvas.deserialize(data)

    def main_loop(self):
        self.handle_events()
        self.update_display()
        clock.tick(30)

    def initialize_display(self):
        """Set up the display"""
        if self.options.get("no_display", False):
            return

        self.print("initializing display")

        self.display_bg_color = DEFAULT_DISPLAY_BG_COLOR
        self.display_margin_px = DEFAULT_DISPLAY_MARGIN_PX

        pygame.init()

        self.stats_font = pygame.freetype.Font(
            os.path.normpath(STATS_FONT_PATH), STATS_FONT_SIZE
        )

        if self.options.get("iconify", False):
            pygame.display.iconify()

        screen_width = self.canvas.surface.get_width() + (self.display_margin_px * 2)

        screen_height = self.canvas.surface.get_height() + self.display_margin_px * 2

        screenrect = pygame.Rect(0, 0, screen_width, screen_height)

        self.screen = pygame.display.set_mode(
            (600, 450), pygame.RESIZABLE, self.bit_depth
        )

        self.print(f"setting display {screenrect.size} {self.bit_depth}bit")
        self.background = pygame.Surface(screenrect.size)

    def update_display(self):
        """Draw current progress to the screen."""
        if self.options.get("no_display", False):
            # required even with display off so we can gather keypresses
            pygame.display.update()
            return

        self.background.fill(self.display_bg_color)
        self.background.blit(
            self.canvas.surface, (self.display_margin_px, self.display_margin_px)
        )

        screen_size = self.screen.get_size()
        scaled_size = resize_with_pad(self.background.get_size(), screen_size)

        scaled_screen = pygame.transform.smoothscale(self.background, scaled_size)

        origin = (
            screen_size[0] / 2 - scaled_size[0] / 2,
            screen_size[1] / 2 - scaled_size[1] / 2,
        )
        self.screen.blit(scaled_screen, origin)

        # required even with display off so we can gather keypresses
        pygame.display.update()

    def get_default_save_file_prefix(self):
        return "imagelab"

    def get_save_file_name(self, ext=None, tpt=None):
        """Return a save-file name based on template configuration and
        app state"""
        if tpt is None:
            tpt = self.options.get("save_template", DEFAULT_SAVE_TEMPLATE)

        tpt = tpt.replace(
            "%PREFIX", self.options.get("prefix", self.get_default_save_file_prefix())
        )

        if self.options.get("runs", 1) != 1:
            tpt = tpt.replace("%RUN", "r%06d" % self.current_run)
        else:
            tpt = tpt.replace("%RUN", "")

        tpt = tpt.replace("%CHILDREN", "c%06d" % self.options.get("children"))
        tpt = tpt.replace("%WIDTH", "w%04d" % self.canvas.size[0])
        tpt = tpt.replace("%HEIGHT", "h%04d" % self.canvas.size[1])
        tpt = tpt.replace("%GENERATION", "g%06d" % self.current_generation)

        if self._movie_mode:
            tpt = tpt.replace("%FRAME", "f%09d" % self.current_frame)
        else:
            tpt = tpt.replace("%FRAME", "")

        if ext is not None:
            tpt = tpt + "." + ext

        path = self.options.get("save_directory", ".")

        return os.path.join(path, tpt)

    def print(self, output_string):
        if self.options.get("verbose", False):
            print(output_string)

    def save(self, output_mode=None):
        """Output current state to file"""
        self.print("saving output")
        savefile = self.get_save_file_name(DEFAULT_IMAGE_SAVE_EXT)
        self.print(f"saving file {savefile}")
        os.makedirs(os.path.dirname(savefile), exist_ok=True)
        pygame.image.save(self.canvas.surface, savefile)

    def handle_events(self):
        """handle keyboard inputs"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit("User Quit")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit("User Quit")
                elif event.key == pygame.K_RETURN:
                    self.save()
                elif event.key == pygame.K_RIGHT:
                    self.canvas.replay()
                elif event.key == pygame.K_LEFT:
                    self.canvas.clear_surface()

            elif event.type == pygame.VIDEORESIZE:
                self.update_display()

        return
        keys = pygame.key.get_pressed()
        if len(keys):
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                amount = 10
            else:
                amount = 1

            if keys[pygame.K_LEFT]:
                self.options["speed"] = max(1, self.options.get("speed") - amount)
            if keys[pygame.K_RIGHT]:
                self.options["speed"] = min(10000, self.options.get("speed") + amount)
