import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main


class MainLoopTests(unittest.TestCase):
    def setUp(self):
        self.saved = main.boy, main.world, main.running
        self.addCleanup(self.restore)
        main.boy = Mock()
        main.world = [Mock(), main.boy]
        main.running = True

    def restore(self):
        main.boy, main.world, main.running = self.saved

    def test_normal_events_reach_boy(self):
        event = SimpleNamespace(type=main.SDL_KEYDOWN, key=main.SDLK_a)
        with patch.object(main, 'get_events', return_value=[event]):
            main.handle_events()
        main.boy.handle_event.assert_called_once_with(event)

    def test_escape_and_window_close_end_loop(self):
        for event in (SimpleNamespace(type=main.SDL_QUIT),
                      SimpleNamespace(type=main.SDL_KEYDOWN, key=main.SDLK_ESCAPE)):
            main.running = True
            with patch.object(main, 'get_events', return_value=[event]):
                main.handle_events()
            self.assertFalse(main.running)
        main.boy.handle_event.assert_not_called()

    def test_world_receives_same_elapsed_time(self):
        main.update_world(0.025)
        for obj in main.world:
            obj.update.assert_called_once_with(0.025)

    def test_initialization_failure_still_closes_canvas(self):
        with patch.object(main, 'open_canvas') as opened, \
             patch.object(main, 'close_canvas') as closed, \
             patch.object(main, 'reset_world', side_effect=RuntimeError('resource error')):
            with self.assertRaisesRegex(RuntimeError, 'resource error'):
                main.main()
        opened.assert_called_once_with(800, 600)
        closed.assert_called_once()


if __name__ == '__main__':
    unittest.main()
