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

import pyglet

from pyroids import configuration


def launch(config_file: str | None = None) -> None:
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
    """
    configuration.Config.set_config_mod(config_file)
    from pyroids import game  # noqa: PLC0415

    game.Game()
    pyglet.app.run()  # Initiate main event loop


def main(config_file: str | None = None):
    """Script interface."""
    config_file = sys.argv[1] if len(sys.argv) == 2 else None  # noqa: PLR2004
    launch(config_file)


if __name__ == "__main__":
    main()
