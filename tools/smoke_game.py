"""Exercise real SDL events, textures and the five-second timer off screen.

Run from the repository root: python tools/smoke_game.py --output-dir <folder>
"""

import argparse
import ctypes
import importlib
import json
import os
from pathlib import Path
import sys
import time

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['SDL_RENDER_DRIVER'] = 'software'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main
import pico2d
import sdl2
from sdl2.sdlimage import IMG_SavePNG

backend = importlib.import_module('pico2d.pico2d')


def key_event(key, pressed=True):
    event = sdl2.SDL_Event()
    event.type = sdl2.SDL_KEYDOWN if pressed else sdl2.SDL_KEYUP
    event.key.type = event.type
    event.key.state = sdl2.SDL_PRESSED if pressed else sdl2.SDL_RELEASED
    event.key.repeat = 0
    event.key.keysym.sym = key
    assert sdl2.SDL_PushEvent(ctypes.byref(event)) == 1
    main.handle_events()


def snapshot(path):
    pico2d.clear_canvas()
    for obj in main.world:
        obj.draw()
    surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, 800, 600, 32, sdl2.SDL_PIXELFORMAT_RGBA32)
    assert surface
    try:
        assert sdl2.SDL_RenderReadPixels(
            backend.renderer, None, surface.contents.format.contents.format,
            surface.contents.pixels, surface.contents.pitch,
        ) == 0
        assert IMG_SavePNG(surface, str(path).encode('utf-8')) == 0
    finally:
        sdl2.SDL_FreeSurface(surface)
    pico2d.update_canvas()


def run(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    pico2d.open_canvas(800, 600)
    try:
        assert backend.renderer, sdl2.SDL_GetError()
        main.reset_world()
        main.running = True
        snapshot(output_dir / 'idle.png')
        key_event(pico2d.SDLK_a)
        key_event(pico2d.SDLK_a, False)
        assert main.boy.state == 'AUTORUN'
        started = previous = pico2d.get_time()
        bounces = 0
        saved_auto = False
        while main.boy.state == 'AUTORUN':
            now = pico2d.get_time()
            direction = main.boy.face_dir
            main.update_world(now - previous)
            previous = now
            main.render_world()
            if direction != main.boy.face_dir:
                bounces += 1
            assert 100 <= main.boy.x <= 700
            if not saved_auto and now - started >= 0.2:
                snapshot(output_dir / 'autorun.png')
                saved_auto = True
            assert now - started < 7, 'AutoRun failed to expire'
            time.sleep(0.005)
        elapsed = pico2d.get_time() - started
        assert main.boy.state == 'IDLE'
        assert 5 <= elapsed < 6
        assert bounces >= 2
        snapshot(output_dir / 'timeout_idle.png')

        key_event(pico2d.SDLK_a)
        key_event(pico2d.SDLK_LEFT)
        assert main.boy.state == 'RUN' and main.boy.face_dir == -1
        snapshot(output_dir / 'cancel_run.png')
        key_event(pico2d.SDLK_LEFT, False)
        assert main.boy.state == 'IDLE'
        key_event(pico2d.SDLK_a, False)
        key_event(pico2d.SDLK_a)
        key_event(pico2d.SDLK_RIGHT)
        assert main.boy.state == 'RUN' and main.boy.face_dir == 1
        key_event(pico2d.SDLK_RIGHT, False)
        assert main.boy.state == 'IDLE'
        key_event(pico2d.SDLK_ESCAPE)
        assert not main.running
        main.running = True
        quit_event = sdl2.SDL_Event()
        quit_event.type = sdl2.SDL_QUIT
        assert sdl2.SDL_PushEvent(ctypes.byref(quit_event)) == 1
        main.handle_events()
        assert not main.running
        result = {'autorun_seconds': round(elapsed, 3), 'boundary_bounces': bounces,
                  'left_right_cancel': True, 'escape_and_quit': True,
                  'real_textures_and_rendering': True}
        (output_dir / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    run(parser.parse_args().output_dir.resolve())
