"""Pyglet audio Helper functions and Mixin classes."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Literal

import pyglet

if TYPE_CHECKING:
    from pyglet.media import StaticSource


def load_static_sound(filename: str) -> StaticSource:
    """Load static sound in resouce directory and return StaticSource.

    Parameters
    ----------
    filename
        Name of sound file (in resource directory) to be loaded.
    """
    sound = pyglet.resource.media(filename, streaming=False)
    # force pyglet to establish player now to prevent in-game delay when
    # sound first played (believe under-the-bonnet pyglet retains reference
    # to player).
    player = sound.play()
    # momentarily minimise volume to avoid 'crackle' on loading sound
    vol = player.volume
    player.volume = 0
    player.next_source()  # skip tracked played on establishing player
    player.volume = vol
    return sound


class StaticSourceMixin:
    """Static Source Player Manager offering an object 'one voice'.

    For 'one voice' at a class level use StaticSourceClassMixin.

    Provides inheriting class with functionality to instantaneously play
    any number of pre-loaded static sound sources albeit any object can
    only only one sound at any one time. If a request is received to play
    a new sound whilst a sound is already playing then can choose to either
    interupt the playing sound and play the new sound or let the playing
    sound continue and not play the new sound.

    Parameters
    ----------
    sound
        True to play initialisation sound.

    loop
        True to loop sound.

    Attributes
    ----------
    sound_playing

    Notes
    -----
    SUBCLASS INTERFACE
    Inheriting class should define a class attribute `snd` assigned to a
    `StaticSource` object which will serve as the main sound for all
    instances.

    To optimise in-game performance the helper function
    `load_static_sound` should be used to create the `StaticSource`. For
    example:
        snd = load_static_sound('my_main_sound.wav')

    All sounds to be played by any class instances should be similarly
    assigned to class attributes as `StaticSource` returned by
    `load_static_sound()`. For example:
        snd_boom = load_static_sound('boom.wav')

    All sounds played for a class instance should be defined as above and
    only played via `sound()`. This ensures that any instance can play
    only one sound at any one time (one voice) and that sound corresponding
    to any instance can be stopped and resumed via the provided methods.
    """

    snd: StaticSource

    def __init__(self, *, sound: bool = True, loop: bool = False):
        self._snd_player: pyglet.media.player.Player
        self._snd_was_playing: bool | None = None
        if sound:
            self.main_sound(loop=loop)

    @property
    def sound_playing(self) -> bool:
        """Query if sound currently playing."""
        return self._snd_player.playing

    def sound(self, source: StaticSource, *, loop: bool = False, interupt: bool = True):
        """Play a source.

        Parameters
        ----------
        source
            Source to play.

        loop
            True to loop sound.

        interupt
            True to stop any current sound and play `source`. False to not
            play `source` if any other sound is already playing.
        """
        if not interupt:
            try:
                if self.sound_playing:
                    return
            except AttributeError:
                pass

        with contextlib.suppress(AttributeError):
            self._snd_player.pause()

        self._snd_player = source.play()
        if loop:
            self._snd_player.loop = True

    def main_sound(self, *, loop: bool = False, interupt: bool = True):
        """Play main sound.

        Parameters
        ----------
        loop
            True to loop sound.

        interupt
            True to stop any current sound and play `source`. False to not
            play `source` if any other sound is already playing.
        """
        self.sound(self.snd, loop=loop, interupt=interupt)

    def stop_sound(self) -> Literal[True] | None:
        """Stop sound if currently playing.

        Returns
        -------
        bool | None
            True if a sound was stopped, None if there was no sound
            playing.
        """
        try:
            self._snd_was_playing = self.sound_playing
            self._snd_player.pause()
        except AttributeError:
            return None
        else:
            return True

    def resume_sound(self) -> Literal[True] | None:
        """Resume play (if last played sound was stopped).

        Returns
        -------
        bool | None
            True if sound was resumed, None if there was no sound to
            resume.
        """
        if self._snd_was_playing:
            try:
                self._snd_player.play()
            except AttributeError:
                rtrn = None
            else:
                rtrn = True
        else:
            rtrn = None
        self._snd_was_playing = None
        return rtrn


class StaticSourceClassMixin:
    """Static Source Player Manager offering a class 'one voice'.

    NB For 'one voice' at an instance level use `StaticSourceMixin`.

    Provides inheriting class with functionality to instantaneously play
    any number of pre-loaded static sound sources albeit only one at any
    one time. If a request is received to play a new sound whilst a sound
    is already playing then can either interupt the playing sound and play
    the new sound or let the playing sound continue and not play the new
    sound.

    Notes
    -----
    SUBCLASS INTERFACE
    Inheriting class should define a class attribute `cls_snd` assigned a
    `StaticSource` object which will serve as the class' main sound. To
    optimise in-game performance the helper function `load_static_sound`
    should be used to create the `StaticSource`. For example:
        cls_snd = load_static_sound('my_main_class_sound.wav')

    All sounds to be played by the class should be similarly assigned to
    class attributes as `StaticSource` returned by `load_static_sound()`.
    For example:
        cls_snd_boom = load_static_sound('cls_boom.wav')

    All sounds played from the class should be defined as above and only
    played via `cls_sound()`. This ensures only one sound can be played at
    a class level at any one time (one voice) and that sound can be stopped
    and resumed via the provided methods.
    """

    cls_snd: StaticSource
    _snd_player: pyglet.media.player.Player
    _snd_was_playing: bool | None = None

    @classmethod
    def cls_sound_playing(cls) -> bool:
        """Return Boolean indicating if class sound currently playing."""
        return cls._snd_player.playing

    @classmethod
    def cls_sound(
        cls,
        source: StaticSource,
        *,
        loop: bool = False,
        interupt: bool = True,
    ):
        """Play source.

        Parameters
        ----------
        source
            Source to play.

        loop
            True to loop sound.

        interupt
            True to stop any current sound and play `source`. False to not
            play `source` if any other sound is already playing.
        """
        if not interupt:
            try:
                if cls.cls_sound_playing():
                    return
            except AttributeError:
                pass

        with contextlib.suppress(AttributeError):
            cls._snd_player.pause()

        cls._snd_player = source.play()
        if loop:
            cls._snd_player.loop = True

    @classmethod
    def stop_cls_sound(cls) -> bool | None:
        """Stop any sound currently playing.

        Returns
        -------
        bool | None
            True if a sound was stopped, None if there was no sound
            playing.
        """
        try:
            cls._snd_was_playing = cls.cls_sound_playing()
            cls._snd_player.pause()
        except AttributeError:
            return None
        else:
            return True

    @classmethod
    def resume_cls_sound(cls) -> Literal[True] | None:
        """Resume play (if last played sound was stopped).

        Returns
        -------
        bool | None
            True if sound was resumed, None if there was no sound
            to resume.
        """
        if cls._snd_was_playing:
            try:
                cls._snd_player.play()
            except AttributeError:
                rtrn = None
            else:
                rtrn = True
        else:
            rtrn = None
        cls._snd_was_playing = None
        return rtrn
