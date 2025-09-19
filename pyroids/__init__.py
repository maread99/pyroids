#! /usr/bin/env python

"""pyroids.

LAUNCHING THE APPLICATION

The pyroids application can be launched either via the pyroids launch()
function or from the command line via the play module.

Launch function:

    >>> import pyroids
    >>> pyroids.launch()

To launch with settings as defined by a configuration file, for example
'novice.py':

    >>> pyroids.launch('novice')

From the Command Line:

    $ python -m pyroids.play

To launch with settings as defined by a configuration file, for example
'expert.py':

    $ python -m pyroids.play expert

See pyroids\config\template.py for instructions on setting up configuration
files.


FUNCTIONS
launch([config_file])  Launch application.

pyroids package comprises:
    Modules:
        __init__  This package initialisation file.
        play  Launcher.
        game  Game engine.
        game_objects  Ship, asteroid, weapon and ammunition classes.
        labels  Collections of text objects and player info row classes.
        utils.iter_util  Iterator-related utility functions.
        utils.physics  Physics functions.
        utils.pyglet_utils.audio_ext  Mixins offering convenience functions for
            pyglet audio functionality.
        utils.pyglet_utils.clockext  Extension to pause pyglet Clock
        utils.pyglet_utils.drawing  Classes to draw shapes and patterns from
            primative forms.
        utils.pyglet_utils.sprite_ext  Extentions of pyglet Sprite class and
            helper functions.
        config.template  Configuration file template.
        config.novice  Configuration file for novice player.
        config.expert  Configuration file for expert player.
    Files:
        resources  Directory containing image and sound files.
"""
# TODO REVISE DOC

import importlib
from pathlib import Path
from typing import List, Optional

import pyglet

# TODO set to False for release...
pyglet.options["debug_gl"] = True  # True only if developing, otherwise False

dir_path = Path(__file__).parent.absolute()  # Path to this file's directory..
dir_path = "/".join(str(dir_path).split("\\"))
# Set pyglet resource directory.
pyglet.resource.path = [dir_path + "/resources"]
pyglet.resource.reindex()

CONFIG_PATH = None


def _set_config_path(config_file: Optional[str]):
    global CONFIG_PATH
    CONFIG_PATH = (
        None if config_file is None else ".config." + config_file.replace(".py", "")
    )


def launch(config_file: Optional[str] = None):
    """Launch application.

    +config_file+  Name of configuration file to apply (configuration file
        should be in the pyroids.config directory). If passed, application
        will launch with settings as determined by the configuration file,
        otherwise will launch with default settings.

    See pyroids\config\template.py for instructions on setting up configuration
    files.
    """
    _set_config_path(config_file)
    from pyroids import game

    game_window = game.Game()
    return pyglet.app.run()  # Initiate main event loop


def _config_import(mod_vars: dict, settings: List[str]):
    """Override default settings with configuration file settings.

    Overrides a module's default settings with settings defined in any
    configuration file. Makes no change for to any setting not defined in
    the configuration file.

    +settings+ List of attribute names that each define a default setting
        on the module with variables dictionary passed as +mod_vars+.
    +mod_vars+ Module's variables dictionary as returned by vars() when
        called from the module.
    """
    if CONFIG_PATH is None:
        return
    config_mod = importlib.import_module(CONFIG_PATH, "pyroids")

    for setting in settings:
        try:
            mod_vars[setting] = getattr(config_mod, setting)
        except AttributeError:
            pass
