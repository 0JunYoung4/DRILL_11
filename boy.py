from math import pi
from pathlib import Path

from pico2d import (
    get_canvas_width, get_time, load_image,
    SDL_KEYDOWN, SDL_KEYUP, SDLK_LEFT, SDLK_RIGHT, SDLK_SPACE,
)
from transitions import Machine


FRAME_COUNT = 8
SPRITE_SIZE = 100
RUN_SPEED = 500.0  # Pixels per second; original 5 px per 0.01 s frame.
ANIMATION_FPS = 10.0
IDLE_TIMEOUT = 5.0


class AutoRun:
    """Own the automatic running state's lifecycle and behavior."""

    @staticmethod
    def enter(boy):
        boy.autorun_started_at = get_time()
        boy.frame = 0

    @staticmethod
    def exit(boy):
        boy.frame = 0

    @staticmethod
    def update(boy, dt):
        boy.advance_animation(dt)


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = []
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.machine = Machine(
            model=self,
            states=['IDLE', 'SLEEP', 'RUN', 'AUTORUN'],
            transitions=[
                {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'start_run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'start_autorun', 'source': 'IDLE', 'dest': 'AUTORUN'},
                {'trigger': 'finish_autorun', 'source': 'AUTORUN', 'dest': 'IDLE'},
            ],
            initial='IDLE',
            auto_transitions=False,
        )
        # The initial state does not invoke its on_enter callback automatically.
        self.on_enter_IDLE()

    def on_enter_IDLE(self):
        self.idle_started_at = get_time()
        self.frame = 0

    def on_enter_SLEEP(self):
        self.frame = 0

    def on_enter_RUN(self):
        self.frame = 0

    def on_enter_AUTORUN(self):
        AutoRun.enter(self)

    def on_exit_AUTORUN(self):
        AutoRun.exit(self)

    def handle_event(self, event):
        if self.state == 'SLEEP' and event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            self.wake_up()
            return

        if event.type not in (SDL_KEYDOWN, SDL_KEYUP):
            return
        if event.key not in (SDLK_LEFT, SDLK_RIGHT):
            return

        if event.type == SDL_KEYDOWN:
            if event.key not in self.pressed_directions:
                self.pressed_directions.append(event.key)
            if self.state in ('IDLE', 'SLEEP'):
                self.start_run()
        elif event.key in self.pressed_directions:
            self.pressed_directions.remove(event.key)

        if self.pressed_directions:
            # When both keys are held, the most recently pressed one wins.
            self.face_dir = 1 if self.pressed_directions[-1] == SDLK_RIGHT else -1
        elif self.state == 'RUN':
            self.stop_run()

    def advance_animation(self, dt):
        self.frame = (self.frame + ANIMATION_FPS * dt) % FRAME_COUNT

    def update(self, dt=0.01):
        if self.state == 'AUTORUN':
            AutoRun.update(self, dt)
        elif self.state == 'IDLE':
            if get_time() - self.idle_started_at >= IDLE_TIMEOUT:
                self.fall_asleep()
            else:
                self.advance_animation(dt)
        elif self.state == 'RUN':
            self.advance_animation(dt)
            self.x += self.face_dir * RUN_SPEED * dt
            half_width = SPRITE_SIZE / 2
            self.x = max(half_width, min(get_canvas_width() - half_width, self.x))

    def draw(self):
        row = 300 if self.face_dir == 1 else 200
        if self.state == 'RUN':
            row = 100 if self.face_dir == 1 else 0
        if self.state == 'SLEEP':
            self.image.clip_composite_draw(
                0, row, 100, 100, self.face_dir * pi / 2, '', self.x, self.y - 25, 100, 100
            )
        else:
            self.image.clip_draw(int(self.frame) * SPRITE_SIZE, row,
                                 SPRITE_SIZE, SPRITE_SIZE, self.x, self.y)
