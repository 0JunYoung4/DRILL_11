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

    def test_auto_uses_last_facing_and_moves_twice_as_fast(self):
        self.boy.face_dir = -1
        self.start_auto()
        self.boy.update(0.1)
        self.assertEqual(self.boy.x, 300)
        self.assertEqual(self.boy.face_dir, -1)

    def test_both_edges_reflect_including_exact_contact(self):
        cases = ((690, 1, 690, -1), (110, -1, 110, 1),
                 (690, 1, 700, -1), (110, -1, 100, 1))
        for index, (x, direction, expected_x, expected_direction) in enumerate(cases):
            with self.subTest(index=index):
                self.boy.x, self.boy.face_dir = x, direction
                boy.AutoRun.move(self.boy, 0.02 if index < 2 else 0.01)
                self.assertAlmostEqual(self.boy.x, expected_x)
                self.assertEqual(self.boy.face_dir, expected_direction)

    def test_large_step_matches_many_small_steps(self):
        self.start_auto()
        self.boy.update(2.75)
        expected = self.boy.x, self.boy.face_dir
        self.boy.x, self.boy.face_dir = 400, 1
        for _ in range(275):
            self.boy.update(0.01)
            self.assertGreaterEqual(self.boy.x, 100)
            self.assertLessEqual(self.boy.x, 700)
        self.assertEqual((self.boy.x, self.boy.face_dir), expected)

    def test_enter_near_edge_clamps_enlarged_sprite(self):
        for position, expected in ((50, 100), (750, 700)):
            self.boy.x = position
            self.start_auto()
            self.assertEqual(self.boy.x, expected)
            self.boy.finish_autorun()

    def test_narrow_canvas_keeps_character_centered(self):
        with patch.object(boy, 'get_canvas_width', return_value=160):
            self.start_auto()
            self.boy.update(0.5)
            self.assertEqual(self.boy.x, 80)

    def test_enlarged_draw_keeps_feet_and_restores_after_cancel(self):
        self.start_auto()
        self.boy.draw()
        args = self.image.clip_draw.call_args.args
        self.assertEqual(args[-2:], (200, 200))
        self.assertEqual(args[5] - args[-1] / 2, self.boy.y - 50)
        self.assertEqual(args[1], 100)
        self.key(boy.SDLK_LEFT)
        self.boy.draw()
        args = self.image.clip_draw.call_args.args
        self.assertEqual(len(args), 6)  # Default sprite dimensions after exit.
        self.assertEqual(args[1], 0)
        self.assertEqual(args[5], 90)

    def test_frame_coordinates_are_integer_and_wrap(self):
        self.start_auto()
        self.boy.update(0.85)
        self.boy.draw()
        args = self.image.clip_draw.call_args.args
        self.assertIsInstance(args[0], int)
        self.assertEqual(args[0], 0)


if __name__ == '__main__':
    unittest.main()
