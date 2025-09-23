r"""pyroids.

LAUNCHING THE APPLICATION

If installed via pip it should be possible to launch pyroids from the
command line:

    $ pyroids

...or to launch with settings as defined by a configuration file, for
example 'novice.py':

    $ pyroids novice

Alternatively pyroids can be launched via the play module...

From the command line at the project root:

    $ python -m pyroids.play

...with a configuration file:

    $ python -m pyroids.play expert

Or from a python environment to which pyroids is installed:

    >>> from pyroids import play
    >>> play.launch()

...with a configuration file:

    >>> play.launch('novice')

(See pyroids\config\template.py for instructions on setting up configuration
files.)


The pyroids package comprises:
    Modules:
        __init__:  This package initialisation file.
        play:  Launcher.
        game:  Game engine.
        game_objects:  Ship, asteroid, weapon and ammunition classes.
        labels:  Collections of text objects and player info row classes.
        utils.iter_util:  Iterator-related utility functions.
        utils.physics:  Physics functions.
        utils.pyglet_utils.audio_ext:  Mixins offering convenience
            functions for pyglet audio functionality.
        utils.pyglet_utils.clockext: Extension to pause pyglet Clock
        utils.pyglet_utils.drawing:  Classes to draw shapes and patterns
            from primative forms.
        utils.pyglet_utils.sprite_ext:  Extentions of pyglet Sprite class
            and helper functions.
        config.template:  Configuration file template.
        config.novice:  Configuration file for novice player.
        config.expert:  Configuration file for expert player.
    Files:
        resources:  Directory containing image and sound files.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import pyglet

pyglet.options["debug_gl"] = False  # True only if developing, otherwise False

dir_path: str | Path = Path(__file__).parent.absolute()  # Path to this file's dir..
dir_path = "/".join(str(dir_path).split("\\"))
# Set pyglet resource directory.
pyglet.resource.path = [dir_path + "/resources"]
pyglet.resource.reindex()


class PlayerColor(Enum):
    """All possible players colors."""

    BLUE = "blue"
    RED = "red"
