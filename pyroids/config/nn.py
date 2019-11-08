#! /usr/bin/env python

"""Configuration file template for pyglet_asteroids application.

pyglet_asteroids can be customised by defining a configuration file, as
a copy of this template, and passing the configuration file's name at the 
command line as the first argument, for example:
..\asteroids_script.py my_config_filename

Configuration files must be saved to the pyglet_asteroids.config directory.

The template notes all customisable global constants and dynamic variables 
as commented out lines of code that if uncommented would assign the 
application's default values. The value of any of these variables can be 
customised by simply uncommenting the line and assigning the required value 
as opposed to the default value.

The application distinguishes between Global Constants and Dynamic 
Variables. A Global Constant is assigned a single value which is used for the 
entirety of the application's life, whereas a Dynamic Variable is assigned a 
function that returns an interator which in turn returns values specific to 
a game level.

Dynamic Variables are assigned a *function that returns an iterable 
providing for a number of iterations no fewer than the global constant 
LAST_LEVEL. The first value returned for each dynamic variable represents 
that variable's value for level 1. Each subsequent iteration represents 
that variable's value for each subsequent level, such that the value 
returned by a variable's nth iteration will be its setting for level n.

Before the Dynamic Varible section the itertools module is imported and a 
a number of helper functions are defined that can be employed to define 
suitable customised iterators (these are used to define the default 
iterators).

*NB A Dynamic Variable is assigned a function that returns an iterator as 
opposed to being directly assigned an iterator. The default values use 
lambda to create the function although any function, including a 
generator, can be assigned so long as it's return value will in turn 
return values when passed to next() no fewer than LAST_LEVEL times.
"""
###WILL NEED TO REVISE at least the start of the ABOVE SEGUN HOW WILL ACTUALLY 
###WORK UNDER DISTRIBUTION

from ..sprites import (Cannon, HighVelocityCannon, FireworkLauncher,
                       SLD_Launcher, MineLayer, ShieldGenerator)

##                              **GLOBAL CONSTANTS**

## application window width in pixels
#WIN_X = 1800

## application window height in pixels
#WIN_Y = 800 

## lives per game. Limit is 5 for 'lives left' to 'fit in' with WIN_X = 1200
#LIVES = 5

## number of levels
#LAST_LEVEL = 20

## Minimum seconds between supply drops
PICKUP_INTERVAL_MIN = 10

## Max seconds between supply drops
PICKUP_INTERVAL_MAX = 15

## Shield duration, in seconds
#SHIELD_DURATION = 7

## Initial rounds of ammunition for each weapon. Maximum 9, Minimum 0.
## Uncomment both lines if changing any value.
INITIAL_AMMO_STOCKS = {Cannon: 9, HighVelocityCannon: 7, FireworkLauncher: 1,
                       SLD_Launcher: 1, MineLayer: 1, ShieldGenerator: 1}

## Number of seconds before which a supply drop can NOT be collected. During 
## this period the pickup flashes.
#COLLECTABLE_IN = 2

## Number of seconds during which pickup can be collected before disappearing.
COLLECTABLE_FOR = 17

## Minimum and Maximum number of rounds of ammunition contained in a supply 
## drop for each weapon. Actual number will be randomly choosen between, and 
## inclusive of, the defined values.
## Uncomment all 6 lines if changing any value.
#PICKUP_AMMO_STOCKS = {HighVelocityCannon: (5, 9), 
#                      FireworkLauncher: (2, 5),
#                      MineLayer: (2, 5),
#                      ShieldGenerator: (2, 4),
#                      SLD_Launcher: (3, 5)
#                      }


##                              *Helper Functions*

import itertools as it
from typing import Iterator, Iterable, Union

def repeat_sequence(seq: Iterable) -> Iterator:
    """As itertools.cycle"""
    return it.cycle(seq)

def repeat_last(seq: Iterable) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ repeats the final value of +seq+"""
    return it.chain(seq, it.repeat(seq[-1]))

def increment_last(seq: Iterable, increment: Union[float, int]) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ returns the previous value incremented by +increment+"""
    return it.chain(seq[:-1], it.count(seq[-1], increment))

def factor_last(seq: Iterable, factor: Union[float, int], 
                round_values=False) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ returns the previous value factored by +factor+.
    Values rounded to the nearest integer if +round_values+ True.
    """
    def series():
        cum = seq[-1]
        while True:
            cum *= factor
            yield round(cum) if round_values else cum
    return it.chain(seq, series())

#Helper Attribute
LEVEL_AUGMENTATION = 1.05


##                              **DYNAMIC VARIABLES**

## Number of asteroids, by default increases by 1 each level.
#NUM_ASTEROIDS = lambda: it.count(1, 1)

## Asteroid speed, by default starts at 200 pixels per second and increases
## by 5% each level.
#ASTEROID_SPEED = lambda: factor_last([200],
#                                     factor=LEVEL_AUGMENTATION, 
#                                     round_values=True
#                                     )

## How many times each large asteroid will end up spawning into smaller 
## asteroids. By default WHAT WHAT?
SPAWN_LIMIT = lambda: it.repeat(1)

## Number of smaller asteroids that are spawed each time a larger asteroid 
## is destroyed
#NUM_PER_SPAWN = lambda: it.repeat(3)

## By default starts at 200 pixels per second and increases by 5% each level.
#SHIP_SPEED = lambda: factor_last([200],
#                                 factor=LEVEL_AUGMENTATION, 
#                                 round_values=True
#                                 )
## By default starts at 200 pixels per second and increases by 5% each level.
#SHIP_ROTATION_SPEED = lambda: factor_last([200],
#                                          factor=LEVEL_AUGMENTATION, 
#                                          round_values=True
#                                          )

## Bullet discharge speed. By default starts at 200 pixels per second and 
## increases by 5% each level.
#BULLET_SPEED = lambda: factor_last([200],
#                                   factor=LEVEL_AUGMENTATION, 
#                                   round_values=True
#                                   )

## Seconds to reload one round of ammunition. By default, 2 seconds for each 
## of the first 5 levels, 1.5 seconds for levels 6 through 8 and 1 second 
## thereafter
#CANNON_RELOAD_RATE = lambda: repeat_last([2]*5 + [1.5]*3 + [1])

## Percent of window height (or width if window higher than wider) to comprise 
## high level radiation zone. Expressed as float from 0 to 1 inclusive. If any 
## value < 0 or > 1 then will be forced to take 0 and 1 respectively.
## By default 0.15 for level 1 then increases by 0.025 each level until 
## reaching 0.5 on level 14 then remains at 0.5 thereafter
#RAD_BORDER = lambda: it.chain(it.islice(it.count(0.15, 0.025), 14),
#                              it.repeat(0.5))

## Limit of ship's exposure to continuous background radiation, in seconds.
## By default, 68 seconds for every level
#NAT_EXPOSURE_LIMIT = lambda: it.repeat(68)

## Limit of ship's exposure to continuous high level radiation, in seconds
## By default, 20 seconds for every level
#HIGH_EXPOSURE_LIMIT = lambda: it.repeat(20)

## Maximum number of pickups that can be made available on each level.
## However NB that any available pickups that are not 'dropped' will roll 
## forwards to the next level. For example, if levels 1 and 2 both have a 
## maximum of 3 pickups although only 2 are dropped in level 1 then up to 
## 4 will be dropped during level 2. If by the end of level 2 only a total 
## of 4 pickups have been dropped then 2 will be rolled forward to be 
## available in level 3 (in addition to those specified for level 3). This 
## behaviour reduces any incentive to 'hang around' for pickups.
## By default 1 pickup available to levels 1 and 2, 2 pickups for levels 3 
## and 4 and 3 pickups for each level thereafter.
NUM_PICKUPS = lambda: repeat_last([3]*2 + [4]*2 + [5])