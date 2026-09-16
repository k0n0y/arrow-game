"""Exercise the real pygame event queue and UI hit-testing using SDL dummy."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
import pytest

from ArrowGame import App
from game_logic import State, available_moves, can_exit, count_arrows, solve


@pytest.fixture
def app():
    instance = App()
    yield instance
    pygame.quit()


def mouse(app, pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    app.step(0)


def press(app, key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    app.step(0)


def blocked_cell(app):
    return next((r, c) for r, row in enumerate(app.game.board) for c, value in enumerate(row)
                if value != "." and not can_exit(app.game.board, r, c))


def test_ui_T01_fly_animation_and_input_lock(app):
    mouse(app, app.buttons["start"].center)
    count = count_arrows(app.game.board)
    mouse(app, app.cell_center(*available_moves(app.game.board)[0]))
    assert app.effect.kind == "removed"
    assert count_arrows(app.game.board) == count - 1
    mouse(app, app.cell_center(*available_moves(app.game.board)[0]))
    assert count_arrows(app.game.board) == count - 1
    app.step(.6)
    assert app.effect is None


def test_ui_T02_collision_feedback(app):
    app.start()
    app.draw()
    cell = blocked_cell(app)
    before = count_arrows(app.game.board)
    mouse(app, app.cell_center(*cell))
    assert app.game.lives == 2 and count_arrows(app.game.board) == before
    assert app.effect.kind == "blocked" and app.message_bad
    app.step(.2)
    assert app.effect is not None


def test_ui_T04_all_three_levels_through_mouse(app):
    mouse(app, app.buttons["start"].center)
    for index in range(3):
        assert app.game.level_index == index
        for cell in solve(app.game.board):
            mouse(app, app.cell_center(*cell))
            app.step(.6)
        if index < 2:
            assert app.game.state is State.WON
            mouse(app, app.buttons["next"].center)
        else:
            assert app.game.state is State.COMPLETE
            assert "start" in app.buttons


def test_ui_T05_failure_retry_and_T06_restart(app):
    mouse(app, app.buttons["level_1"].center)
    original = [row[:] for row in app.game.board]
    cell = blocked_cell(app)
    for _ in range(3):
        mouse(app, app.cell_center(*cell))
        app.step(.6)
    assert app.game.state is State.LOST
    mouse(app, app.buttons["restart"].center)
    assert app.game.state is State.PLAYING
    assert app.game.level_index == 1 and app.game.lives == 3
    mouse(app, app.cell_center(*available_moves(app.game.board)[0]))
    press(app, pygame.K_r)
    assert app.game.board == original and app.game.lives == 3
    assert app.effect is None and app.elapsed == 0


def test_ui_hint_menu_gaps_and_borders(app):
    press(app, pygame.K_RETURN)
    press(app, pygame.K_h)
    assert app.hint_cell is not None and app.game.hints == 1
    assert app.game.lives == 3
    rect, cell = app.geometry()
    for pos in [(0, 0), rect.bottomright, rect.topleft, (rect.right, rect.y + 20)]:
        mouse(app, pos)
    assert app.game.lives == 3 and app.game.moves == 0
    press(app, pygame.K_ESCAPE)
    assert app.game.state is State.MENU


def test_ui_duplicate_events_after_page_change(app):
    pos = app.buttons["start"].center
    for _ in range(2):
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    app.step(0)
    assert app.game.state is State.PLAYING
    assert app.game.lives >= 2


def test_ui_quit(app):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.step(0)
    assert not app.running
