"""Check built package."""

import pyglet

from pyroids import play


def build_tst():
    """Test application launches."""
    # TODO: This test doesn't work. Errors can be raised within the app
    # run although that won't prevent the window object being assigned here
    # (i.e. the only thing that's actually checked for).
    play.launch("novice", _testing_script=True)
    win = play.Game.game
    if isinstance(win, pyglet.window.Window):
        print("Build test successful.")  # noqa: T201
    else:
        err_msg = "Build test failed"
        raise RuntimeError(err_msg)  # noqa: TRY004


if __name__ == "__main__":
    build_tst()
