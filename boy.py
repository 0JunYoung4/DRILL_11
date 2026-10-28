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


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = []
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.machine = Machine(
            model=self,
            states=['IDLE', 'SLEEP', 'RUN'],
            transitions=[
                {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'start_run', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_run', 'source': 'RUN', 'dest': 'IDLE'},
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

    def update(self):
        if self.state == 'IDLE':
            if get_time() - self.idle_started_at >= IDLE_TIMEOUT:
                self.fall_asleep()
            else:
                self.frame = (self.frame + 1) % FRAME_COUNT
        elif self.state == 'RUN':
            self.frame = (self.frame + 1) % FRAME_COUNT
            self.x += self.face_dir * 5
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
            self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
