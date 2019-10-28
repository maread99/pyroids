#! /usr/bin/env python

"""Initialisation file for pyglet_asteroids package"""

import os, sys, importlib
from typing import List

import pyglet

### True ONLY TRUE WHEN DEVELOPING, OTHERWISE FALSE!!
pyglet.options['debug_gl'] = False 

# dir_path is path to directory in which this file is located using seperator
# required by pyglet.resource.path
dir_path = '/'.join(os.path.dirname(__file__).split('\\'))
print("dir_path is", dir_path) #DEBUG LINE
pyglet.resource.path = [dir_path + '/resources']
pyglet.resource.reindex()

def config_import(mod_vars: dict, settings: List[str]):
    """Overrides a module's attributes with any settings defined on to 
    a configuration file (in pyglet_asteroids.config) where the name of 
    the configuration file was passed at the command line as the first 
    argument.
    Where +settings+ is a list of attribute names, for each will 
    attempt to add (i.e. override) an item to the module variables 
    dictionary +mod_vars+ (as returned by vars() when called on a module).
    key will take the attribute name and value the value of any 
    corresponding attribute name defined on the configuration file. 
    No change is made to mod_vars for any attribute not defined on the 
    configuration file"""
    if len(sys.argv) is not 2:
        return
    rel_config_file = '.config.' + sys.argv[1]
    config_mod = importlib.import_module(rel_config_file, 'pyglet_asteroids')

    for setting in settings:
        try:
            mod_vars[setting] = getattr(config_mod, setting)
        except AttributeError:
            pass

#from pyglet_asteroids import game
from pyrrhoids import game