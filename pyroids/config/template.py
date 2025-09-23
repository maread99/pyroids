r"""Configuration file template.

A copy of this template can be used to create a configuration file that
defines custom settings for the pyroids application.

Configuration files should:
    Be based on this template.
    Be saved to the directory root\Lib\site_packages\pyroids\config where
        'root' is as returned by sys.prefix() when executed in the python
        environment to which pyroids is installed.
    Have extension .py (a configuration file is imported by pyroids)

This template includes all customisable application settings as commented out
lines of code. Simply uncommenting the line(s) associated with any setting
will result in pyroids assigning the default value for that setting.
The value for any setting can be customised by uncommenting the associated
line(s) of code and replacing the default value with the desired value.

Pyroids will assign default values to any setting that remains commented out.

Pyroids distinguishes between Global Settings and Level Settings.
    A Global Setting is assigned a single value which is used for the
        entirety of the application instance's life.
    A Level Setting is assigned a function that returns an iterator which
        in turn returns values where each value is specific to a game level.

A Level Setting should be assigned a function that returns an iterator
providing for a number of iterations no fewer than the global setting
LAST_LEVEL. The first value returned by a Level Setting should be that
setting's value for level 1. Each subsequent iteration should return the
setting's value for each subsequent level, such that the value
returned by the nth iteration will be the setting's value for level n.

    NB A Level Setting is NOT directly assigned an iterator but rather a
    function that returns an iterator. The default settings use lambda
    to create the function although any function, including a generator,
    can be assigned so long as its return value can in turn be passed to
    next().

This module imports intertools and defines a number of helper functions
that can be employed to create suitable customised iterators (these helper
functions are also used to define the default iterators).
"""

from __future__ import annotations

from collections import OrderedDict

import pyglet

from pyroids.game_objects import (
    Cannon,
    FireworkLauncher,
    HighVelocityCannon,
    MineLayer,
    ShieldGenerator,
    SLD_Launcher,
)

# #                              **GLOBAL SETTINGS**

# # Application window width in pixels.
# WIN_X = 1200

# # Application window height in pixels.
# WIN_Y = 800

# # Lives per game. Limit is 5 for 'lives left' to 'fit in' with WIN_X = 1200.
# LIVES = 5

# # Number of levels.
# LAST_LEVEL = 14

# # Minimum seconds between supply drops.
# PICKUP_INTERVAL_MIN = 15

# # Max seconds between supply drops.
# PICKUP_INTERVAL_MAX = 30

# # Should pyroids 'bounce' or 'wrap' at the boundary?
# AT_BOUNDARY = "bounce"

# # Should ships 'bounce', 'wrap' or 'stop' at the boundary?
# SHIP_AT_BOUNDARY = "stop"

# # Shield duration, in seconds.
# SHIELD_DURATION = 8

# # Speed of high velocity bullet as multiple of standard bullet speed.
# HIGH_VELOCITY_BULLET_FACTOR = 5

# # Initial rounds of ammunition for each weapon. Maximum 9, Minimum 0.
# # Uncomment ALL six lines if changing any value.
# INITIAL_AMMO_STOCKS = {
#     Cannon: 9,
#     HighVelocityCannon: 7,
#     FireworkLauncher: 3,
#     SLD_Launcher: 3,
#     MineLayer: 3,
#     ShieldGenerator: 2,
# }

# # Number of seconds before which a supply drop can NOT be collected. During
# # this period the pickup flashes.
# COLLECTABLE_IN = 2

# # Number of seconds during which pickup can be collected before disappearing.
# COLLECTABLE_FOR = 10

# # Minimum and Maximum number of rounds of ammunition contained in a supply
# # drop for each weapon. Actual number will be randomly choosen between, and
# # inclusive of, the defined values.
# # Uncomment all 6 lines if changing any value.
# PICKUP_AMMO_STOCKS = {
#     HighVelocityCannon: (5, 9),
#     FireworkLauncher: (3, 7),
#     MineLayer: (3, 7),
#     ShieldGenerator: (3, 5),
#     SLD_Launcher: (3, 7),
# }

# #                              *Ship Controls*

# # Controls for blue / red ship defined by dictionaries assigned to
# # BLUE_CONTROLS / RED_CONTROLS respectively.
# # Dictionary keys (in capital letters) should be left unchanged.
# # Dictionary values take a List or Ordered Dictionary defining the key or
# # keys that will result in the corresponding control being executed. Keys
# # defined as constants of the pyglet.windows.key module:
# #     https://pyglet.readthedocs.io/en/latest/modules/window_key.html
# # FIREWORK_KEYS and MINE_KEYS are both assigned an Ordered Dictionary
# # that defines multiples keys by default although can be defined to take
# # one or any number of keys.
# #   Values of FIREWORK_KEYS ordered dictionary represent the distance, in
# #     pixels that the firework will travel before exploding
# #   Values of MINE_KEYS ordrered dictionary represent the time, in seconds,
# #     before the mine will explode.

# # Uncomment ALL lines of this subsection if changing any value.
# BLUE_CONTROLS = {
#     "THRUST_KEY": [pyglet.window.key.I],
#     "ROTATE_LEFT_KEY": [pyglet.window.key.J],
#     "ROTATE_RIGHT_KEY": [pyglet.window.key.L],
#     "SHIELD_KEY": [pyglet.window.key.K],
#     "FIRE_KEY": [pyglet.window.key.ENTER],
#     "FIRE_FAST_KEY": [pyglet.window.key.BACKSPACE],
#     "SLD_KEY": [pyglet.window.key.RCTRL],
#     "FIREWORK_KEYS": OrderedDict(
#         {
#             pyglet.window.key._7: 200,
#             pyglet.window.key._8: 500,
#             pyglet.window.key._9: 900,
#         },
#     ),
#     "MINE_KEYS": OrderedDict(
#         {
#             pyglet.window.key.M: 1,
#             pyglet.window.key.COMMA: 3,
#             pyglet.window.key.PERIOD: 6,
#         },
#     ),
# }

# # Uncomment ALL lines of this subsection if changing any value.
# RED_CONTROLS = {
#     "THRUST_KEY": [pyglet.window.key.W],
#     "ROTATE_LEFT_KEY": [pyglet.window.key.A],
#     "ROTATE_RIGHT_KEY": [pyglet.window.key.D],
#     "SHIELD_KEY": [pyglet.window.key.S],
#     "FIRE_KEY": [pyglet.window.key.TAB],
#     "FIRE_FAST_KEY": [pyglet.window.key.ESCAPE],
#     "SLD_KEY": [pyglet.window.key.LCTRL],
#     "FIREWORK_KEYS": OrderedDict(
#         {
#             pyglet.window.key._1: 200,
#             pyglet.window.key._2: 500,
#             pyglet.window.key._3: 900,
#         },
#     ),
#     "MINE_KEYS": OrderedDict(
#         {
#             pyglet.window.key.Z: 1,
#             pyglet.window.key.X: 3,
#             pyglet.window.key.C: 6,
#         },
#     ),
# }


#                              *Helper Functions*

import itertools as it
from collections.abc import Iterator, Sequence


def repeat_sequence(seq: Sequence) -> Iterator:
    """As itertools.cycle."""
    return it.cycle(seq)


def repeat_last(seq: Sequence) -> Iterator:
    """Return a sequence as infinite iterator that repeats the last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the final value of `seq`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.
    """
    return it.chain(seq, it.repeat(seq[-1]))


def increment_last(seq: Sequence, increment: float) -> Iterator:
    """Return a sequence as infinite iterator that increments last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the prior value incremented by `increment`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.

    increment
        Value by which to increment last value of `seq` and subsequent
        values.
    """
    return it.chain(seq[:-1], it.count(seq[-1], increment))


def factor_last(
    seq: Sequence,
    factor: float,
    *,
    round_values: bool = False,
) -> Iterator:
    """Return a sequences as infinite iterator that factors last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the prior value factored by `factor`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.

    factor
        Factor by which to augment last value of `seq` and subsequent
        values.

    round_values
        True to round returned values to nearest integer.
    """

    def series():
        cum = seq[-1]
        while True:
            cum *= factor
            yield round(cum) if round_values else cum

    return it.chain(seq, series())


# Helper Attribute
LEVEL_AUGMENTATION = 1.05


# #                              **LEVEL SETTINGS**

# # Number of asteroids, by default increases by 1 each level.
# NUM_ASTEROIDS = lambda: it.count(1, 1)

# # Asteroid speed, by default starts at 200 pixels per second and increases
# # by 5% each level.
# ASTEROID_SPEED = lambda: factor_last(
#     [200],
#     factor=LEVEL_AUGMENTATION,
#     round_values=True,
# )

# # How many times each large asteroid will end up spawning into smaller
# # asteroids. By default, just once.
# SPAWN_LIMIT = lambda: it.repeat(1)

# # Number of smaller asteroids that are spawed each time a larger asteroid
# # is destroyed.
# NUM_PER_SPAWN = lambda: it.repeat(3)

# # By default starts at 200 pixels per second and increases by 5% each level.
# SHIP_SPEED = lambda: factor_last([200], factor=LEVEL_AUGMENTATION, round_values=True)

# # By default starts at 200 pixels per second and increases by 5% each level.
# SHIP_ROTATION_SPEED = lambda: factor_last(
#     [200],
#     factor=LEVEL_AUGMENTATION,
#     round_values=True,
# )

# # Bullet discharge speed. By default starts at 200 pixels per second and
# # increases by 5% each level.
# BULLET_SPEED = lambda: factor_last([200], factor=LEVEL_AUGMENTATION, round_values=True)

# # Seconds to reload one round of ammunition. By default, 2 seconds for each
# # of the first 5 levels, 1.5 seconds for levels 6 through 8 and 1 second
# # thereafter.
# CANNON_RELOAD_RATE = lambda: repeat_last([2] * 5 + [1.5] * 3 + [1])

# # Percent of window height (or width if window higher than wider) to comprise
# # high level radiation zone. Expressed as float from 0 to 1 inclusive. If any
# # value < 0 or > 1 then will be forced to take 0 and 1 respectively.
# # By default 0.15 for level 1 then increases by 0.025 each level until
# # reaching 0.5 on level 14 after which remains at 0.5.
# RAD_BORDER = lambda: it.chain(it.islice(it.count(0.15, 0.025), 14), it.repeat(0.5))

# # Limit of ship's exposure to continuous background radiation, in seconds.
# # By default, 68 seconds for every level.
# NAT_EXPOSURE_LIMIT = lambda: it.repeat(68)

# # Limit of ship's exposure to continuous high level radiation, in seconds.
# # By default, 20 seconds for every level.
# HIGH_EXPOSURE_LIMIT = lambda: it.repeat(20)

# # Maximum number of pickups that can be made available on each level.
# # However note that any available pickups that are not 'dropped' will roll
# # forwards to the next level. For example, if levels 1 and 2 both have a
# # maximum of 3 pickups although only 2 are dropped in level 1 then up to
# # 4 will be dropped during level 2. If by the end of level 2 only a total
# # of 4 pickups have been dropped then 2 will be rolled forward to be
# # available in level 3 (in addition to those specified for level 3). This
# # behaviour reduces any incentive to 'hang around' for pickups.
# # By default 1 pickup available to levels 1 and 2, 2 pickups for levels 3
# # and 4 and 3 pickups for each level thereafter.
# NUM_PICKUPS = lambda: repeat_last([1] * 2 + [2] * 2 + [3])
