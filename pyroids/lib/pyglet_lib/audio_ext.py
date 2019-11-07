#! /usr/bin/env python

"""Pyglet audio Helper functions and Mixin classes.

Helper FUNCTIONS
load_static_sound()  Pre-load a static sound in resouce directory.

Mixin CLASSES
StaticSourceMixin()  Provide a class using StaticSrouces with 'one voice'
"""

from typing import Optional

import pyglet
from pyglet.media import StaticSource, Player

def load_static_sound(filename: str) -> StaticSource:
    """Loads static sound in resouce directory. Returns StaticSource object.

    +filename+ Name of sound file in resource directory.
    """
    sound = pyglet.resource.media(filename, streaming=False)
    # force pyglet to establish player now to prevent in-game delay when 
    # sound first played (believe under-the-bonnet pyglet retains reference 
    # to player).
    player = sound.play()
    # momentarily minimise volume to avoid 'crackle' on loading sound
    vol = player.volume
    player.volume = 0
    player.next_source() # skip tracked played on establishing player
    player.volume = vol
    return sound

class StaticSourceMixin(object):
    """Static Source Player Manager offering 'one voice'.

    Provides inheriting class with functionality to play any number of 
    pre-loaded static sound sources albeit only one at any one time. If a 
    request is received to play a sound whilst a sound is already playing 
    then the playing sound will be stopped and the new sound played.

    METHODS
    --sound()--  Play a sound
    --main_sound()--  Play main sound
    --stop_sound()--
    --resume_sound()--

    SUBCLASS INTERFACE
    Inheriting class should define a class attribute ---snd--- assigned a 
    StaticSource object which will serve as the class' main sound. To 
    optimise in-game performance the helper function ---load_static_sound--- 
    should be used to create the StaticSource. For example:
    snd = load_static_sound('my_main_sound.wav')
    
    All sounds to be played by the class should be similarly assigned to 
    class attributes as StaticSources returned by ---load_static_sound()---. 
    For example:
    snd_boom = load_static_sound('boom.wav')

    All sounds played from the class should be defined as above and only 
    played via --sound()--. This ensures only one sound can be played at 
    any one time (one voice) and that sound can be stopped and resumed via 
    the provided methods.
    """
    
    snd: StaticSource

    def __init__(self, sound: bool = True, loop: bool = False):
        """Setup Mixin.

        ++sound++  If True play initialisation sound and loop if ++loop++ 
            True.
        """
        self._snd_player: pyglet.media.player.Player
        self._snd_was_playing: Optional[bool] = None
        if sound:
            self.main_sound(loop)

    def sound(self, source: StaticSource, loop: bool = False):
        """Play +source+ and loop if +loop+ True."""
        # if sound alread playing, stop it.
        try:
            self._snd_player.pause()
        except AttributeError:
            pass
        
        self._snd_player = source.play()
        if loop:
            self._snd_player.loop = True

    def main_sound(self, loop: bool):
        """Play main sound."""
        self.sound(self.snd, loop)

    def stop_sound(self) -> Optional[bool]:
        """If sound playing, stop it.
        
        Returns True if a sound was stopped, None if there was no sound 
        playing.
        """
        try:
            self._snd_was_playing = self._snd_player.playing
            self._snd_player.pause()
        except AttributeError:
            pass
        else:
            return True
        
    def resume_sound(self):
        """If last played sound was stopped, resume play.
        
        Returns True if sound was resumed, None if there was no sound 
        to resume.
        """
        if self._snd_was_playing:
            try:
                self._snd_player.play()
            except AttributeError:
                pass
            else:
                self._snd_was_playing = None
                return True
        self._snd_was_playing = None