from pico2d import *

from boy import Boy
from grass import Grass

running = False
world = []
boy = None

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            boy.handle_event(event)


def reset_world():
    global world
    global boy

    world = []

    grass = Grass()
    world.append(grass)

    boy = Boy()
    world.append(boy)



def update_world(dt):
    for o in world:
        o.update(dt)


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


def main():
    global running
    open_canvas(800, 600)
    try:
        reset_world()
        running = True
        previous_time = get_time()
        while running:
            current_time = get_time()
            dt = max(0.0, current_time - previous_time)
            previous_time = current_time
            handle_events()
            if not running:
                break
            update_world(dt)
            render_world()
            delay(0.01)
    finally:
        close_canvas()


if __name__ == '__main__':
    main()
