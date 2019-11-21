#! /usr/bin/env python

"""Pyglet audio Helper functions and Mixin classes.

Helper FUNCTIONS
load_static_sound()  Pre-load a static sound in resouce directory.

Mixin CLASSES
StaticSourceMixin()  'one voice' instantaneous audio for instances.
StaticSourceClassMixin()  'one voice' instantaneous audio for a class.
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
    """Static Source Player Manager offering an object 'one voice'.

    For 'one voice' at a class level use StaticSourceClassMixin.

    Provides inheriting class with functionality to instantaneously play 
    any number of pre-loaded static sound sources albeit any object can 
    only only one sound at any one time. If a request is received to play 
    a new sound whilst a sound is already playing then can either interupt 
    the playing sound and play the new sound or let the playing sound 
    continue and not play the new sound.

    METHODS
    --sound()--  Play a sound
    --main_sound()--  Play main sound
    --stop_sound()--
    --resume_sound()--

    SUBCLASS INTERFACE
    Inheriting class should define a class attribute ---snd--- assigned a 
    StaticSource object which will serve as the main sound for all instances. 
    To optimise in-game performance the helper function 
    ---load_static_sound--- should be used to create the StaticSource. For 
    example:
        snd = load_static_sound('my_main_sound.wav')
    
    All sounds to be played by any class instances should be similarly 
    assigned to class attributes as StaticSources returned by 
    ---load_static_sound()---. For example:
        snd_boom = load_static_sound('boom.wav')

    All sounds played for a class instance should be defined as above and 
    only played via --sound()--. This ensures that any instance can play 
    only one sound at any one time (one voice) and that sound corresponding 
    to any instance can be stopped and resumed via the provided methods.
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

    def sound(self, source: StaticSource, loop: bool = False,
              interupt:  bool = True):
        """Play +source+.
        
        +loop+ Loop if true
        +interupt+ True to stop any current sound and play +source+. False to 
            not play +source+ if any other sound is already playing.
        """
        if not interupt:
            try:
                if self._snd_player.playing:
                    return
            except AttributeError:
                pass

        try:
            self._snd_player.pause()
        except AttributeError:
            pass
        
        self._snd_player = source.play()
        if loop:
            self._snd_player.loop = True

    def main_sound(self, loop: bool = False, interupt: bool = True):
        """Play main sound.
        
        +loop+ Loop if true
        +interupt+ True to stop any current sound and play +source+. False to 
            not play +source+ if any other sound is already playing.
        """
        self.sound(self.snd, loop, interupt)

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


class StaticSourceClassMixin(object):
    """Static Source Player Manager offering a class 'one voice'.

    NB For 'one voice' at an instance level use StaticSourceMixin.

    Provides inheriting class with functionality to instantaneously play 
    any number of pre-loaded static sound sources albeit only one at any 
    one time. If a request is received to play a new sound whilst a sound is 
    already playing then can either interupt the playing sound and play the 
    new sound or let the playing sound continue and not play the new sound.

    METHODS
    --cls_sound()--  Play a sound
    --main_cls_sound()--  Play main class sound
    --stop_cls_sound()--
    --resume_cls_sound()--

    SUBCLASS INTERFACE
    Inheriting class should define a class attribute ---cls_snd--- assigned a 
    StaticSource object which will serve as the class' main sound. To 
    optimise in-game performance the helper function ---load_static_sound--- 
    should be used to create the StaticSource. For example:
        cls_snd = load_static_sound('my_main_class_sound.wav')
    
    All sounds to be played by the class should be similarly assigned to 
    class attributes as StaticSources returned by ---load_static_sound()---. 
    For example:
        cls_snd_boom = load_static_sound('cls_boom.wav')

    All sounds played from the class should be defined as above and only 
    played via --cls_sound()--. This ensures only one sound can be played at 
    a class level at any one time (one voice) and that sound can be stopped 
    and resumed via the provided methods.
    """
    
    cls_snd: StaticSource
    _snd_player: pyglet.media.player.Player
    _snd_was_playing: Optional[bool] = None

    @classmethod
    def cls_sound(cls, source: StaticSource, loop: bool = False,
                  interupt: bool = True):
        """Play +source+.
        
        +loop+ Loop if true
        +interupt+ True to stop any current sound and play +source+. False to 
            not play +source+ if any other sound is already playing.
        """
        if not interupt:
            try:
                if cls._snd_player.playing:
                    return
            except AttributeError:
                pass

        try:
            cls._snd_player.pause()
        except AttributeError:
            pass
        
        cls._snd_player = source.play()
        if loop:
            cls._snd_player.loop = True

    @classmethod
    def main_cls_sound(cls, loop: bool = False, interupt: bool = True):
        """Play main class sound.
        
        +loop+ Loop if true
        +interupt+ True to stop any current sound and play +source+. False to 
            not play +source+ if any other sound is already playing.
        """
        cls.cls_sound(self.cls_snd, loop, interupt)

    @classmethod
    def stop_cls_sound(cls) -> Optional[bool]:
        """If sound playing, stop it.
        
        Returns True if a sound was stopped, None if there was no sound 
        playing.
        """
        try:
            cls._snd_was_playing = cls._snd_player.playing
            cls._snd_player.pause()
        except AttributeError:
            pass
        else:
            return True
        
    @classmethod
    def resume_cls_sound(cls):
        """If last played sound was stopped, resume play.
        
        Returns True if sound was resumed, None if there was no sound 
        to resume.
        """
        if cls._snd_was_playing:
            try:
                cls._snd_player.play()
            except AttributeError:
                pass
            else:
                cls._snd_was_playing = None
                return True
        cls._snd_was_playing = None