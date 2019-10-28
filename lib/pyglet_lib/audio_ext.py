#! /usr/bin/env python

"""Module offers classes that extend pyglet's audio functionalities:

StaticSourceMixin provides for managing player one or more pre-loaded 
static sources from a class, and only playing one at any one time, with 
previously played sounds being stopped in preference of any latter sounds 
that are called"""

from pyglet.media import StaticSource, Player

class StaticSourceMixin(object):
    """By default provides play sound held in class attribute ---snd--- on 
    instantiation. If subclass does not require sound to be played on 
    instantiation then ++sound++ should be passed as False. Initial 
    sound can be looped by passing ++sound_loop++ as True.
    Sound can be stopped at any time with stop_sound() and subsequently 
    resumed with resume_sound().
        
    Sound Internals - constructor call's --init_sound()-- which in turn plays 
    ---snd---. Accordingly possible for inheriting class to hack into process 
    by overriding --init_sound()--. NB --init_sound()-- in turn calls 
    --sound--. ANY sound, be that ---snd--- or otherwise, should be played 
    through --sound()-- which ensures only one sound is played at any time 
    and that any sound being played will be stopped by --stop_sound-- and 
    can be subseqeuntly resumed with resume_sound(). NB if attempt to play 
    two sounds concurrently through --sound-- then the sound which was 
    initially called will be stopped and the sound called subsequently will 
    be played.

    --sound(source)-- all static sources should be played via this method
    --init_sound-- plays StaticSound assigned to ---snd---. Will play on 
    instantiation unless ++sound++ False
    --stop_sound-- to stop any current playing sound (no advese behaviour 
    if there is no sound playing)
    --resume_sound-- resumes any sound that was previously stopped.
    """
    
    snd: StaticSource

    def __init__(self, sound: bool = True, loop: bool = False):
        self._snd_player: pyglet.media.player.Player
        self._snd_was_playing: Optional[bool] = None
        if sound:
            self.init_sound(loop)

    def sound(self, source: StaticSource, loop: bool = False):
        """Internals - see StaticSourceMixin.__doc__"""
        try:
            self._snd_player.pause()
        except AttributeError:
            pass
        self._snd_player = source.play()
        if loop:
            self._snd_player.loop = True

    def init_sound(self, loop: bool):
        """Internals - see StaticSourceMixin.__doc__"""
        self.sound(self.snd, loop)

    def stop_sound(self):
        try:
            self._snd_was_playing = self._snd_player.playing
            self._snd_player.pause()
        except AttributeError:
            pass
        
    def resume_sound(self):
        if self._snd_was_playing:
            try:
                self._snd_player.play()
            except AttributeError:
                pass
        self._snd_was_playing = None