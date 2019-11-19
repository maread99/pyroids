#! /usr/bin/env python

"""Initialisation file for pyroids package.

Sets pyglet resource directory.

FUNCTIONS
config_import() - override default settings with config file settings.

pyroids package comprises:
    Modules:
        __init__ - this package initialisation file.
        game - game engine.
        game_objects - ship, asteroid, weapon and ammunition classes.
        labels - text screens and player info row classes.
        lib.iter_util - Iterator-related utility functions.
        lib.physics - physics functions.
        lib.pyglet_lib.audio_ext - mixins offering convenience functions for 
            pyglet audio functionality.
        lib.pyglet_lib.clockext - extension to pause pyglet Clock
        lib.pyglet_lib.drawing - classes to draw shapes and patterns from 
            primative forms.
        lib.pyglet_lib.sprite_ext - extentions of pyglet Sprite class and 
            helper functions.
        config.template - configuration file template.
    Files:
        resources directory contains all image and sound files.
"""

import os, sys, importlib
from typing import List

import pyglet

# True only if developing, otherwise False.
pyglet.options['debug_gl'] = False 

# dir_path is path to directory in which this file is located using seperator
# required by pyglet.resource.path
dir_path = '/'.join(os.path.dirname(__file__).split('\\'))
pyglet.resource.path = [dir_path + '/resources']
pyglet.resource.reindex()

def config_import(mod_vars: dict, settings: List[str]):
    """Override default settings with configuration file settings.
    
    Overrides a module's default settings with any settings defined in a 
    configuration file (in ..pyroids\config) where the name of 
    the configuration file was passed at the command line as the first 
    argument. Makes no change for to any setting not defined in the 
    configuration file.

    +settings+ list of attribute names that each define a default setting 
        on a module.
    +mod_vars+ the module's variables dictionary as returned by vars() 
        when called from the module.
    """
    if len(sys.argv) is not 2:
        return
    rel_config_file = '.config.' + sys.argv[1]
    config_mod = importlib.import_module(rel_config_file, 'pyroids')

    for setting in settings:
        try:
            mod_vars[setting] = getattr(config_mod, setting)
        except AttributeError:
            pass

from pyroids import game