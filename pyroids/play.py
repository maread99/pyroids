#! /usr/bin/env python

r"""Launch application.

To launch from the command line at the project root:

    $ python -m pyroids.play

Application settings can be optionally customised by passing the name of a
configuration file located in the pyroids.config directory. Example:

    $ python -m pyroids.play novice

Alternatively, from a python environment to which pyroids is installed:

    >>> from pyroids import play
    >>> play.launch()

...with a configuration file:

    >>> play.launch('novice')

See pyroids\config\template.py for instructions on setting up configuration
files.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pyglet

import pyroids
from pyroids import configuration

if TYPE_CHECKING:
    from pyroids import game


TESTING = False  # Set to True if testing app


class Game:
    """Game.

    Holds current game instance. Class should not be instantiated directly.
    """

    game: game.Game

    @classmethod
    def instantiate_game(cls, *, hide: bool = False):
        """Start a game.

        Parameters
        ----------
        hide
            Hide window.
        """
        from pyroids import game  # noqa: PLC0415

        cls.game = game.Game(visible=not hide)


def launch(config_file: str | None = None, *, _testing_script: bool = False) -> None:
    r"""Launch application.

    Parameters
    ----------
    config_file
        Name of configuration file to apply (configuration file should be
        in the pyroids.config directory). If passed, application will
        launch with settings as determined by the configuration file,
        otherwise will launch with default settings. See
        pyroids\config\template.py for instructions on setting up
        configuration files.

    Notes
    -----
    Pass `_testing_script=True` if testing that launches as script. This
    will hide the window and ensure that the app exits after 2 seconds.
    """
    configuration.Config.set_config_mod(config_file)
    Game.instantiate_game(hide=_testing_script or TESTING)
    if TESTING:
        return
    if _testing_script:
        pyglet.clock.schedule_once(lambda dt: pyglet.app.exit(), 2)  # noqa: ARG005
    pyglet.app.run()  # Initiate main event loop


def main():
    """Script interface."""
    testing = False
    args = sys.argv.copy()
    if "--testing" in args:
        testing = True
        args.remove("--testing")
    config_file = args[1] if len(args) == 2 else None  # noqa: PLR2004
    launch(config_file, _testing_script=testing)


if __name__ == "__main__":
    main()
