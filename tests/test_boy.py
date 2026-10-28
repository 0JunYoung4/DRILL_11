"""State regressions with a controlled clock and no SDL window."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import boy


class BoyStateTests(unittest.TestCase):
    def setUp(self):
        self.clock = 100.0
        self.image = Mock()
        for name, options in (
            ('get_time', {'side_effect': lambda: self.clock}),
            ('get_canvas_width', {'return_value': 800}),
            ('load_image', {'return_value': self.image}),
        ):
            patcher = patch.object(boy, name, **options)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.boy = boy.Boy()

    def key(self, key, event_type=boy.SDL_KEYDOWN):
        self.boy.handle_event(SimpleNamespace(type=event_type, key=key))

    def start_auto(self):
        self.key(boy.SDLK_a)
        self.assertEqual(self.boy.state, 'AUTORUN')

    def test_a_starts_only_from_idle(self):
        self.start_auto()
        self.key(boy.SDLK_LEFT)
        self.key(boy.SDLK_a)
        self.assertEqual(self.boy.state, 'RUN')
        self.key(boy.SDLK_LEFT, boy.SDL_KEYUP)
        self.clock += 5
        self.boy.update()
        self.assertEqual(self.boy.state, 'SLEEP')
        self.key(boy.SDLK_a)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_timeout_at_five_seconds_and_fresh_idle_timer(self):
        self.start_auto()
        self.clock = 104.999
        self.boy.update()
        self.assertEqual(self.boy.state, 'AUTORUN')
        self.clock = 105.0
        self.boy.update()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.idle_started_at, 105.0)
        position = self.boy.x
        self.clock = 109.999
        self.boy.update()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.x, position)
        self.clock = 110.0
        self.boy.update()
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_late_update_still_expires_without_moving(self):
        self.start_auto()
        self.clock += 8
        self.boy.update(8)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.x, 400)

    def test_repeated_a_does_not_extend_timer(self):
        self.start_auto()
        self.clock = 103
        self.key(boy.SDLK_a)
        self.key(boy.SDLK_a, boy.SDL_KEYUP)
        self.assertEqual(self.boy.autorun_started_at, 100)
        self.clock = 105
        self.boy.update()
        self.assertEqual(self.boy.state, 'IDLE')

    def test_arrow_cancels_to_requested_direction_and_release_stops(self):
        for key, direction in ((boy.SDLK_LEFT, -1), (boy.SDLK_RIGHT, 1)):
            with self.subTest(direction=direction):
                self.start_auto()
                self.key(key)
                self.assertEqual(self.boy.state, 'RUN')
                self.assertEqual(self.boy.face_dir, direction)
                position = self.boy.x
                self.boy.update(0.1)
                self.assertAlmostEqual(self.boy.x - position, direction * 50)
                self.key(key, boy.SDL_KEYUP)
                self.assertEqual(self.boy.state, 'IDLE')

    def test_key_release_alone_does_not_cancel_autorun(self):
        self.start_auto()
        self.key(boy.SDLK_LEFT, boy.SDL_KEYUP)
        self.assertEqual(self.boy.state, 'AUTORUN')

    def test_latest_arrow_wins_then_falls_back_to_held_key(self):
        self.key(boy.SDLK_LEFT)
        self.key(boy.SDLK_LEFT)
        self.key(boy.SDLK_RIGHT)
        self.assertEqual(self.boy.face_dir, 1)
        self.key(boy.SDLK_RIGHT, boy.SDL_KEYUP)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.face_dir, -1)
        self.key(boy.SDLK_LEFT, boy.SDL_KEYUP)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_sleep_wakes_with_space_or_arrow(self):
        self.clock += 5
        self.boy.update()
        self.key(boy.SDLK_SPACE)
        self.assertEqual(self.boy.state, 'IDLE')
        self.clock += 5
        self.boy.update()
        self.key(boy.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'RUN')


if __name__ == '__main__':
    unittest.main()
