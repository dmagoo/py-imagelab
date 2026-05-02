"""CLI for imagemutate App.

Produce a target image by randomly mutating a base canvas
"""
import json
import time
import pygame
import os
import cv2
from imagelab import mutation, rng
from imagelab.geometry import get_random_clip_rect
from imagelab.geometry import resize_with_pad
from imagelab.compare import match_score, get_match_percentage
from imagelab.canvas import Canvas

OUTPUT_MODE_IMAGE = 0
OUTPUT_MODE_INSTRUCTIONS = 1

DEFAULT_DISPLAY_BG_COLOR = (3, 3, 100)
DEFAULT_DISPLAY_HILIGHT_COLOR = (200, 200, 100)
DEFAULT_DISPLAY_HILIGHT_SUB_COLOR = (100, 100, 40)
DEFAULT_DISPLAY_HILIGHT_WIDTH = 1
DEFAULT_DISPLAY_MARGIN_PX = 20
DEFAULT_BIT_DEPTH = 32

DEFAULT_CHILDREN = 100
DEFAULT_SHAPE = 'circle'
DEFAULT_RADIUS = 20
DEFAULT_IMAGE_SAVE_EXT = 'png'
DEFAULT_SAVE_TEMPLATE = "%PREFIX-%FRAME%CHILDREN%GENERATION"

# consider scaling based on display? nt(450*h/768))
STATS_FONT_SIZE = 32
# STATS_FONT_PATH = "./assets/fonts/RisingSun/RisingSun-Regular.ttf"
STATS_FONT_PATH = "./assets/fonts/luculent/luculent.ttf"

MOVIE_EXTENSIONS = ('.mp4', '.mpeg')


def number_length(num):
    return len(str(num))


def cvimage_to_pygame(image):
    """Convert cvimage into a pygame image"""
    return pygame.image.frombuffer(
        image.tostring(),
        image.shape[1::-1],
        # image.shape[:2],
        # "RGB"
        "BGR"
    )


def get_new_surface(size, color=None):
    surface = pygame.Surface(size)
    if color is not None:
        surface.fill(color)

    return surface


def is_movie_file(path):
    return path.endswith(MOVIE_EXTENSIONS)


class App:
    """
        Evolve the target image by finding the best child over a number of
        generations
    """
    options = {}
    stats = {}
    running = False

    # image processing
    # The target image we are trying to match
    target_surface = None
    canvas = None

    brush_surfaces = None

    current_run = 0
    current_generation = 0
    current_child = 0

    # for movie_mode, initialized when rendering a movie
    current_frame = None
    target_movie = None

    # Display Settings
    # the pygame screen display
    screen = None

    # base background image
    background = None

    display_bg_color = None
    display_margin_px = None
    bit_depth = None

    # should we create all children for a given generation in the same zone
    # for faster comparison speed?
    morph_clipped_sections = True
    # how large is the zome in relation to the radius
    # must be at least two to allow for full radius
    clipped_section_scale = 2
    # after how many ticks should we find a new zone?
    # having a value greater than one results in multiple generations "working"
    # in the same area of the canvas
    clip_change_rate = 1

    stats_font = None

    # internal house-keeping
    _process_start_time = 0
    _clock_start_time = 0

    _tick_process_start_time = 0
    _tick_clock_start_time = 0

    _frame_process_start_time = 0
    _frame_clock_start_time = 0

    _last_flip_time = 0

    _movie_mode = False

    # current clip rectangle being used to optimize comparison
    _clip_rect = None
    # current rectangle of laste-evaluated child
    _clip_sub_rect = None

    _show_highlights = False
    _show_info = False

    def __init__(self, options=None):
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
        """Run this app """
        seed = self.options.get('seed')
        if seed is None:
            seed = int(rng.integers(0, 1000000))
            self.options['seed'] = seed
        rng.seed(seed)
        self.initialize_display()
        self.initialize_target()
        self.initialize_profiler()
        self.running = True

        runs = self.options.get('runs', 1)
        complete = False
        self.current_run = 0
        while not complete and self.running:
            if(self._movie_mode):
                self.evolve_movie_mode()
            else:
                self.evolve_image_mode()
            self.current_run += 1
            if self.current_run >= runs:
                complete = True

    def initialize_display(self):
        """Set up the display"""
        if self.options.get('no_display', False):
            return

        self.print("initializing display")

        self.display_bg_color = DEFAULT_DISPLAY_BG_COLOR
        self.display_highlight_color = DEFAULT_DISPLAY_HILIGHT_COLOR
        self.display_highlight_sub_color = DEFAULT_DISPLAY_HILIGHT_SUB_COLOR
        self.display_highlight_width = DEFAULT_DISPLAY_HILIGHT_WIDTH
        self.display_margin_px = DEFAULT_DISPLAY_MARGIN_PX

        pygame.init()

        self.stats_font = pygame.freetype.Font(
            os.path.normpath(STATS_FONT_PATH),
            STATS_FONT_SIZE
        )

        if self.options.get('iconify', False):
            pygame.display.iconify()

    def initialize_target(self):
        """ Look at the target image or movie
            and set up the config accordingly """
        self.bit_depth = DEFAULT_BIT_DEPTH

        if is_movie_file(self.options.get('target_path')):
            self.initialize_movie_settings()
        else:
            self.initialize_image_settings()

        # allow for two side-by-side comparison images
        screen_width = (
            self.target_surface.get_width() * 2
        ) + (self.display_margin_px * 3)

        screen_height = (
            self.target_surface.get_height() + self.display_margin_px * 2
        )

        screenrect = pygame.Rect(0, 0, screen_width, screen_height)

        self.screen = pygame.display.set_mode(
            (600, 450),
            pygame.RESIZABLE, self.bit_depth
        )

        self.print(f"setting display {screenrect.size} {self.bit_depth}bit")
        self.background = pygame.Surface(screenrect.size)

    def initialize_image_settings(self):
        self.print(f"loading target image: {self.options.get('target_path')}")
        self.target_surface = pygame.image.load(
            self.options.get('target_path')
        )
        self.target_surface.convert(self.bit_depth)

        if(self.options.get('brush_images')):
            self.print(
                f"loading brush images {self.options.get('brush_images')}"
            )
            self.brush_surfaces = []
            for surface_path in self.options.get('brush_images', []):
                brush_surface = pygame.image.load(surface_path)
                brush_surface.convert(self.bit_depth)
                self.brush_surfaces.append(brush_surface)

    def initialize_movie_settings(self):
        self._movie_mode = True
        self.target_movie = cv2.VideoCapture(self.options.get('target_path'))
        width = self.target_movie.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.target_movie.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.target_surface = pygame.Surface((width, height))
        self.total_frames = self.target_movie.get(7)
        self.print(
            f"loaded movie {width}x{height} @ {self.total_frames} frames"
        )
        self.target_surface.convert(self.bit_depth)

    def initialize_profiler(self):
        self.stats = {}
        process_time = time.process_time()
        clock_time = time.perf_counter()
        self._process_start_time = process_time
        self._clock_start_time = clock_time
        self.stats["total_process_time"] = 0
        self.stats["total_clock_time"] = 0
        self.stats["average_generation_process_time"] = 0
        self.stats["average_generation_clock_time"] = 0
        self.stats["current_generation_process_time"] = 0
        self.stats["current_generation_clock_time"] = 0
        if self._movie_mode:
            self.stats["average_frame_process_time"] = 0
            self.stats["average_frame_clock_time"] = 0
            self.stats["current_frame_process_time"] = 0
            self.stats["current_frame_clock_time"] = 0

    def evolve_image_mode(self):
        self.print("starting image evolution")
        canvas_surface = get_new_surface(
            self.target_surface.get_rect().size,
            self.display_bg_color
        )
        self.evolve(canvas_surface)

    def evolve_movie_mode(self):
        self.print("starting movie evolution")
        self.current_frame = self.options.get('frame_start', 0)

        complete = False

        while not complete and self.running:
            self.handle_frame_start()
            self.handle_frame()
            self.current_frame += 1
            if self.movie_complete():
                complete = True

    def handle_frame_start(self):
        process_time = time.process_time()
        clock_time = time.perf_counter()
        self._frame_process_start_time = process_time
        self._frame_clock_start_time = clock_time

    def handle_frame(self):
        self.print(
            f"evolving frame {self.current_frame+1}/{self.total_frames}"
        )
        self.target_movie.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        success, frame = self.target_movie.read()
        self.target_surface = cvimage_to_pygame(frame)
        canvas_surface = get_new_surface(
            self.target_surface.get_rect().size,
            self.display_bg_color
        )
        self.evolve(canvas_surface)

    def handle_frame_end(self):
        pass

    def evolve(self, canvas_surface):
        """ Run the main series of mutations """
        self.print("starting evolution")
        complete = False
        tick = 0

        self.canvas = Canvas(canvas_surface)

        # TODO: make a reset-evolution method, to set current_gen, etc to zero
        # otherwise we do not reset things while in movie mode

        self.update_display()

        self.current_generation = 0

        while not complete and self.running:
            """ Make a random rect.  Allow room to start a circle off screen
                The purpose of this is so that we only create children inside a
                common subdivision of the canvas.  This allows quicker
                comparison, since it's not against the entire canvas.
            """
            # start of tick house-keeping
            self.handle_tick_start()
            # do the actual work for this tick

            try:
                self.handle_evolution_tick(tick)
            except SystemExit:
                self.running = False

            # output results
            self.update_display()
            # poll for input
            self.handle_events()
            # end of tick house-keeping
            self.handle_tick_end()
            if self.evolution_complete():
                complete = True

            tick += 1

        self.print_profiler()

    def handle_tick_start(self):
        """ Start a new image evolution cylcle (begin a tick) """
        self.current_generation += 1
        process_time = time.process_time()
        clock_time = time.perf_counter()
        self._tick_process_start_time = process_time
        self._tick_clock_start_time = clock_time

    def update_profiler(self):
        process_time = time.process_time()
        clock_time = time.perf_counter()
        gen_clock_duration = clock_time - self._tick_clock_start_time
        gen_process_duration = process_time - self._tick_process_start_time
        total_clock_duration = clock_time - self._clock_start_time
        total_process_duration = process_time - self._process_start_time

        self.stats["total_process_time"] = total_process_duration
        self.stats["total_clock_time"] = total_clock_duration

        self.stats["average_generation_process_time"] = (
            (
                self.stats["average_generation_process_time"] *
                (self.current_generation - 1) + gen_process_duration
            )/(self.current_generation)
        )

        self.stats["current_generation_process_time"] = gen_process_duration
        self.stats["current_generation_clock_time"] = gen_clock_duration

        self.stats["average_generation_clock_time"] = (
            (
                self.stats["average_generation_clock_time"] *
                (self.current_generation - 1) + gen_clock_duration
            ) / (self.current_generation)
        )
        self.stats["process_time_per_child"] = \
            self.stats["total_process_time"] / (
                self.current_generation *
                self.options.get('children', DEFAULT_CHILDREN)
        )

        self.stats["clock_time_per_child"] = self.stats["total_clock_time"] / \
            (
                self.current_generation *
                self.options.get('children', DEFAULT_CHILDREN)
        )

    def print_profiler(self):
        print("======================================")
        if self._movie_mode:
            print(f"====== Frame {self.current_frame} / \
            {self.total_frames} ======")

        if self.options.get('runs', 1) != 1:
            print(f"--- run: {self.current_generation}", end='')

        print(f"--- gen: {self.current_generation}", end='')
        if self.options.get('gen_stop', -1) >= 0:
            print(f"/{self.options.get('gen_stop')}", end='')

        print(
            f" child: {self.current_child}/{self.options.get('children')} ---"
        )

        for val in self.stats:
            print(f"{val}:\t{self.stats[val]}")
        print("-------------------")

        """ we could calculate this every tick, but it would add cost """
        score = match_score(self.target_surface, self.canvas.surface)
        print(f"match percentage: {get_match_percentage(score)}")
        print("-------------------")

    def print(self, output_string):
        if self.options.get('verbose', False):
            print(output_string)

    def update_display_minimal(self):
        # update display but in a very light weight way...
        # used for child iterations which need to be as fast as possible

        tmp_bg = self.background.copy()

        if self._show_highlights and self._clip_sub_rect:
            # highlight the working section
            pygame.draw.rect(
                tmp_bg,
                self.display_highlight_sub_color,
                self._clip_sub_rect.move(
                    self.display_margin_px, self.display_margin_px
                ),
                self.display_highlight_width
            )

        if self._show_highlights and self._clip_rect:
            # highlight the working section
            pygame.draw.rect(
                tmp_bg,
                self.display_highlight_color,
                self._clip_rect.move(
                    self.display_margin_px, self.display_margin_px
                ),

                self.display_highlight_width
            )

        screen_size = self.screen.get_size()
        scaled_size = resize_with_pad(
            tmp_bg.get_size(), screen_size
        )

        scaled_screen = pygame.transform.smoothscale(
            tmp_bg,
            scaled_size
        )

        if self._show_info:
            self.render_stats(
                scaled_screen,
                (self.display_margin_px*2, self.display_margin_px*2)
            )

        origin = (
            screen_size[0]/2 - scaled_size[0]/2,
            screen_size[1]/2 - scaled_size[1]/2
        )
        self.screen.blit(scaled_screen, origin)
        pygame.display.update()

    def render_stats(self, surface, pos):
        # fontSurface = self.font.render(("Children: %03d - Frame: %09d -
        # Generation: %06d" % (self.options.get('children'), useFrame,
        # self.generation)), True, (0,200,100))
        line_1 = ""
        if self._movie_mode:
            line_1 = f"frame: {self.current_frame}"

        if self.options.get('runs', 1) != 1:
            line_1 = f"{line_1}run: {self.current_run}"

        line_1 = f"{line_1}gen: {self.current_generation}"

        children = self.options.get('children')
        children_length = number_length(children)

        if self.options.get('gen_stop', -1) > 0:
            line_1 = f"{line_1}/{self.options.get('gen_stop', -1)}"

        line_1 = (
            f"{line_1}"
            f" child: {self.current_child:0{children_length}d}/{children}"
        )

        line_2 = f"maxR: {self.options.get('radius')}"

        line_1_img, _ = self.stats_font.render(
            line_1,
            pygame.Color(255, 255, 255),
            pygame.Color(0, 0, 0, 50)
        )

        line_2_img, _ = self.stats_font.render(
            line_2,
            pygame.Color(255, 255, 255),
            pygame.Color(0, 0, 0, 50)
        )
        _, line_height = line_1_img.get_size()
        surface.blit(line_1_img, pos)
        pos2 = (pos[0], pos[1]+(line_height + (line_height/20)))
        surface.blit(line_2_img, pos2)

    def update_display(self):
        """ Draw current progress to the screen. """
        if self.options.get('no_display', False):
            # required even with display off so we can gather keypresses
            pygame.display.update()
            return

        self.background.fill(self.display_bg_color)
        self.background.blit(
            self.canvas.surface,
            (self.display_margin_px, self.display_margin_px)
        )

        if self.target_surface is not None:
            self.background.blit(
                self.target_surface,
                (self.target_surface.get_rect().width + (
                    self.display_margin_px*2
                ),
                    self.display_margin_px)
            )

        # todo: move highlight into subroutine line stats and update here

        screen_size = self.screen.get_size()
        scaled_size = resize_with_pad(
            self.background.get_size(), screen_size
        )

        scaled_screen = pygame.transform.smoothscale(
            self.background,
            scaled_size
        )

        if self._show_info:
            self.render_stats(
                scaled_screen,
                (self.display_margin_px*2, self.display_margin_px*2)
            )

        origin = (
            screen_size[0]/2 - scaled_size[0]/2,
            screen_size[1]/2 - scaled_size[1]/2
        )
        self.screen.blit(scaled_screen, origin)

        # required even with display off so we can gather keypresses
        pygame.display.update()

    def get_default_save_file_prefix(self):
        return 'imagelab'

    def get_save_file_name(self, ext=None, tpt=None):
        """ Return a save-file name based on template configuration and
            app state """
        if tpt is None:
            tpt = self.options.get('save_template', DEFAULT_SAVE_TEMPLATE)

        tpt = tpt.replace('%PREFIX', self.options.get(
            'prefix', self.get_default_save_file_prefix()
        ))

        if(self.options.get('runs', 1) != 1):
            tpt = tpt.replace('%RUN', 'r%06d' % self.current_run)
        else:
            tpt = tpt.replace('%RUN', '')

        tpt = tpt.replace('%CHILDREN', 'c%06d' % self.options.get('children'))
        tpt = tpt.replace('%WIDTH', 'w%04d' % self.canvas.size[0])
        tpt = tpt.replace('%HEIGHT', 'h%04d' % self.canvas.size[1])
        tpt = tpt.replace('%GENERATION', 'g%06d' % self.current_generation)

        if self._movie_mode:
            tpt = tpt.replace('%FRAME', 'f%09d' % self.current_frame)
        else:
            tpt = tpt.replace('%FRAME', '')

        if ext is not None:
            tpt = tpt + '.' + ext

        path = self.options.get('save_directory', '.')

        return os.path.join(path, tpt)

    def save(self, output_mode=None):
        """ Output current state to file """
        self.print("saving output")

        if output_mode is None:
            output_mode = OUTPUT_MODE_INSTRUCTIONS if \
                self.options.get('instructions') else OUTPUT_MODE_IMAGE

        if output_mode == OUTPUT_MODE_INSTRUCTIONS:
            savefile = self.get_save_file_name('json')
            os.makedirs(os.path.dirname(savefile), exist_ok=True)
            output = open(savefile, 'w')
            output.write(json.dumps(self.canvas.serialize()))
            #print(self.canvas.serialize())
            # savefile = self.get_save_file_name('pkl')
            # output = open(savefile, 'wb')
            # pickle.dump(self.canvas.serialize(), output, 1)

            output.close()
        else:
            savefile = self.get_save_file_name(DEFAULT_IMAGE_SAVE_EXT)
            self.print(f"saving file {savefile}")
            os.makedirs(os.path.dirname(savefile), exist_ok=True)
            pygame.image.save(self.canvas.surface, savefile)

    def handle_events(self):
        """ handle keyboard inputs """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit("User Quit")
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit("User Quit")
                elif event.key == pygame.K_SPACE:
                    self.print_profiler()
                elif event.key == pygame.K_h:
                    self._show_highlights = not self._show_highlights
                elif event.key == pygame.K_i:
                    self._show_info = not self._show_info
                elif event.key == pygame.K_a:
                    self.save(OUTPUT_MODE_INSTRUCTIONS)
                elif event.key == pygame.K_s:
                    self.save(OUTPUT_MODE_IMAGE)
                elif event.key == pygame.K_RETURN:
                    self.save()
            elif event.type == pygame.VIDEORESIZE:
                self.update_display()

        keys = pygame.key.get_pressed()
        if len(keys):
            # if (keys[pygame.K_LALT] | keys[pygame.K_RALT]) and \
            # keys[pygame.K_RETURN]:
            #    pygame.display.toggle_fullscreen()
            if self.options.get('lock_controls'):
                return
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                amount = 10
            else:
                amount = 1

            if keys[pygame.K_LEFT]:
                self.options['children'] = max(
                    1, self.options.get('children') - amount
                )
            if keys[pygame.K_RIGHT]:
                self.options['children'] = min(
                    10000, self.options.get('children') + amount
                )
            if keys[pygame.K_UP]:
                self.options['radius'] = min(
                    1000, self.options.get('radius') + amount
                )
            if keys[pygame.K_DOWN]:
                self.options['radius'] = max(
                    1, self.options.get('radius') - amount
                )

    def handle_tick_end(self):
        save_gen = self.options.get('save_gen')
        if save_gen is not None and self.current_generation % save_gen == 0:
            self.save()

        self.update_profiler()

    def child_callback(self, i, canvas_action, img):
        now_time = time.perf_counter()
        time_since_flip = now_time - self._last_flip_time
        self.current_child = i

        if time_since_flip > 0.1:
            pass
        else:
            return

        self._last_flip_time = now_time
        radius = canvas_action.params.get('radius')
        pos = canvas_action.params.get('pos')
        if pos and radius:
            self._clip_sub_rect = pygame.Rect(
                (pos[0]-radius, pos[1]-radius),
                (radius * 2, radius * 2)
            )
        self.update_display_minimal()
        self.handle_events()

    def handle_evolution_tick(self, tick):
        max_radius = self.options.get('radius', DEFAULT_RADIUS)

        if self.morph_clipped_sections and (
            tick % self.clip_change_rate == 0
        ):
            self._clip_rect = pygame.Rect(get_random_clip_rect(
                self.canvas.surface.get_rect(),
                max_radius*self.clipped_section_scale,
                max_radius*self.clipped_section_scale
            ))

        self.canvas.apply_mutator(
            mutation.mutate_evolve,
            {
                'target': self.target_surface,
                'clip_rect': self._clip_rect,
                'children': self.options.get('children', DEFAULT_CHILDREN),
                'shape': self.options.get('shape', DEFAULT_SHAPE),
                'words': self.options.get('words', None),
                'brush_images': self.brush_surfaces,
                'max_radius': max_radius,
                'child_callback': self.child_callback
            }
        )

    def movie_complete(self):
        """ Boolean: True if frames are done """
        frame_stop = self.options.get("frame_stop", -1)
        seconds_stop = self.options.get("seconds_stop", -1)
        if self.current_frame >= self.total_frames:
            return True
        if frame_stop > -1 and self.current_frame >= frame_stop:
            self.print(f"stopping movie evolution at frame_stop={frame_stop}")
            return True
        if (
            seconds_stop > -1 and
            self.stats.get("total_clock_time") >= seconds_stop
        ):
            self.print(f"stopping evolution at seconds_stop={seconds_stop}")
            return True
        return False

    def evolution_complete(self):
        """ Boolean: True if evolution is complete based on config """
        gen_stop = self.options.get("gen_stop", -1)
        seconds_stop = self.options.get("seconds_stop", -1)
        match_stop = self.options.get("match_stop", 101)
        if gen_stop > -1 and self.current_generation >= gen_stop:
            self.print(f"stopping evolution at gen_stop={gen_stop}")
            return True
        if (
            seconds_stop > -1 and
            self.stats.get("total_clock_time") >= seconds_stop
        ):
            self.print(f"stopping evolution at seconds_stop={seconds_stop}")
            return True
        if(match_stop < 101):
            score = match_score(self.target_surface, self.canvas.surface)
            percentage = get_match_percentage(score)
            if(percentage >= match_stop):
                self.print(f"stopping evolution at match={match_stop}%")
                return True

        return False
