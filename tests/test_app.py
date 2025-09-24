"""Tests for pyroids app."""

from __future__ import annotations

import subprocess
import sys

import pyglet
import pytest

from pyroids import play

# ruff: noqa: S101


@pytest.fixture
def set_testing_variable():
    play.TESTING = True


def test_app(set_testing_variable: None):
    """Test application.

    Testing limited to ensuring the application can do the following
    without error:
        launch
        show instructions
        enter a 2-player game
        show isntructions during game
        return to game
        exit a game prematurely
        enter a 1-player game
        exit the appliation
    """
    config = "novice"
    play.launch(config)
    win = play.Game.game
    assert isinstance(win, pyglet.window.Window)

    def assertions(dt: float):  # noqa: ARG001
        """Assert win behaving as expected."""

        def press_key(key: int):
            win.dispatch_event("on_key_press", key, 0)

        from pyroids import game

        assert win.app_state is game.GameState.START
        press_key(pyglet.window.key.ENTER)
        assert win.app_state is game.GameState.INSTRUCTIONS
        press_key(pyglet.window.key.H)
        assert win.app_state is game.GameState.START
        press_key(pyglet.window.key._2)  # noqa: SLF001
        assert win.app_state is game.GameState.GAME
        assert win.num_players == 2  # noqa: PLR2004
        assert win.ship_speed == 230  # noqa: PLR2004
        press_key(pyglet.window.key.F12)
        assert win.app_state is game.GameState.INSTRUCTIONS
        press_key(pyglet.window.key.F12)
        assert win.app_state is game.GameState.GAME
        press_key(pyglet.window.key.F12)
        assert win.app_state is game.GameState.INSTRUCTIONS
        press_key(pyglet.window.key.ESCAPE)
        assert win.app_state is game.GameState.END
        press_key(pyglet.window.key._1)  # noqa: SLF001
        assert win.app_state is game.GameState.GAME
        assert win.num_players == 1
        press_key(pyglet.window.key.F12)
        assert win.app_state is game.GameState.INSTRUCTIONS
        press_key(pyglet.window.key.ESCAPE)
        assert win.app_state is game.GameState.END
        press_key(pyglet.window.key.ESCAPE)

    pyglet.clock.schedule_once(assertions, 1)
    pyglet.app.run()


def test_script():
    """Test that executes from script."""
    result = subprocess.run(
        [sys.executable, "-m", "pyroids.play", "--testing"],
        capture_output=True,
    )
    assert result.returncode == 0


def test_script_expert():
    """Test that executes from script with configuration arg."""
    result = subprocess.run(
        [sys.executable, "-m", "pyroids.play", "expert", "--testing"],
        capture_output=True,
    )
    assert result.returncode == 0
