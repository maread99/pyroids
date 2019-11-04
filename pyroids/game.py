#! /usr/bin/env python

"""
Asteroids-esque game.
Module includes:
    Setting pyglet clock to instance of ClockExt which provides for pausing 
    scheduled events.
    Player class to represent a player. Via classes of labels modules creates 
      and/or positions various labels and sprites that collectively provide a 
      row of player information along the top of the screen covering lives, 
      ammunition stocks, radiation levels and score.
    Game class subclasses pyglet.window.Window and provides the main game 
      engine, to include main --refresh-- function which serves to update 
      all sprite positions. Via classes of label module, creates labels for 
      various screens.
    Instantiation of main pyglet event execution.
    Definition of default values for following Global Constants and Dynamic 
      Variables:
      'BLUE_CONTROLS', 'RED_CONTROLS',
      'WIN_X', 'WIN_Y', 'LIVES', 'LAST_LEVEL', 'PICKUP_INTERVAL_MIN', 
      'PICKUP_INTERVAL_MAX', 'NUM_ASTEROIDS', 'ASTEROID_SPEED', 
      'NUM_PER_SPAWN', 'SHIP_SPEED', 'SHIP_ROTATION_SPEED', 'BULLET_SPEED',
      'CANNON_RELOAD_RATE', 'RAD_BORDER', 'NAT_EXPOSURE_LIMIT', 
      'HIGH_EXPOSURE_LIMIT', 'NUM_PICKUPS'
      Any of these variables will be overriden if it has have been defined 
      in any configuration file passed at the command line (see 
      pyroids.config.template.__doc__):

The following Batches that collate drawable objects are defined at the module 
level:
  ----start_batch---- holds objects that comprise the start screen
  ----game_batch---- hold objects drawn during the game. Two groups defined:
    ----game_group---- interactive sprites
    ----rad_group---- sprites and primative drawings that comprise the 
      radiation field
  ----info_batch---- sprites and labels that comprise the information row to 
    the top of the screen that provides players with data on stocks, radiation 
    level, lives and score
  ----next_level_batch---- holds only next_level label
  ----end_batch---- comprises labels for the game over screen
  ----inst_batch---- comprises labels for the instructions screen

Development Notes. Rather than having Game and Player both look at the 
globally defined batches and groups, I considered defining them as class 
attributes of Game and then passing through those required by Player. Decided 
could end up going around in circles and that it was reasonable to define 
globally.
"""

from .lib.pyglet_lib.clockext import ClockExt
import pyglet

CLOCK = ClockExt()
pyglet.clock.set_default(CLOCK)

import random, time, importlib, sys
import itertools as it
from typing import Optional, List, Union, Tuple, Type
from collections import OrderedDict as OrdDict
from copy import copy
from threading import Thread

from pyglet.sprite import Sprite
from pyglet.image import TextureRegion
from pyglet.text import Label

import pyroids
from .lib.pyglet_lib.sprite_ext import (PhysicalSprite, SpriteAdv, 
                                        AvoidRect, InRect, load_image)
from .lib.pyglet_lib.drawing import AngledGrid, Rectangle, DrawingBase
from .sprites import (Ship, ShipRed, ControlSystem, Asteroid, 
                      Bullet, Mine, Starburst, PickUp, PickUpRed)
from .labels import (StartLabels, NextLevelLabel, LevelLabel, EndLabels,
                     InstructionLabels, StockLabel, InfoRow)
from .lib.iter_util import (increment_last, factor_last, 
                            repeat_sequence, repeat_last)

LEVEL_AUGMENTATION = 1.05

#SHIP CONTROLS
BLUE_CONTROLS = {'THRUST_KEY': [pyglet.window.key.I],
                 'ROTATE_LEFT_KEY': [pyglet.window.key.J],
                 'ROTATE_RIGHT_KEY': [pyglet.window.key.L],
                 'SHIELD_KEY': [pyglet.window.key.K],
                 'FIRE_KEY': [pyglet.window.key.ENTER],
                 'FIRE_FAST_KEY': [pyglet.window.key.BACKSPACE],
                 'SLD_KEY': [pyglet.window.key.RCTRL],
                 'FIREWORK_KEYS': OrdDict({pyglet.window.key._7: 200,
                                           pyglet.window.key._8: 500,
                                           pyglet.window.key._9: 900}),
                 'MINE_KEYS': OrdDict({pyglet.window.key.M: 1,
                                       pyglet.window.key.COMMA: 3,
                                       pyglet.window.key.PERIOD: 6})
                 }

RED_CONTROLS = {'THRUST_KEY': [pyglet.window.key.W],
                'ROTATE_LEFT_KEY': [pyglet.window.key.A],
                'ROTATE_RIGHT_KEY': [pyglet.window.key.D],
                'SHIELD_KEY': [pyglet.window.key.S],
                'FIRE_KEY': [pyglet.window.key.TAB],
                'FIRE_FAST_KEY': [pyglet.window.key.ESCAPE],
                'SLD_KEY': [pyglet.window.key.LCTRL],
                'FIREWORK_KEYS': OrdDict({pyglet.window.key._1: 200,
                                          pyglet.window.key._2: 500,
                                          pyglet.window.key._3: 900}),
                'MINE_KEYS': OrdDict({pyglet.window.key.Z: 1,
                                      pyglet.window.key.X: 3,
                                      pyglet.window.key.C: 6})
                }

#GLOBAL CONSTANTS
WIN_X = 1200
WIN_Y = 800
LIVES = 5
LAST_LEVEL = 20
PICKUP_INTERVAL_MIN = 15
PICKUP_INTERVAL_MAX = 30
AT_BOUNDARY = 'bounce'

#DYNAMIC VARIABLES
NUM_ASTEROIDS = lambda: it.count(1, 1)
ASTEROID_SPEED = lambda: factor_last([200],
                                     factor=LEVEL_AUGMENTATION, 
                                     round_values=True
                                     )
SPAWN_LIMIT = lambda: it.repeat(2)
NUM_PER_SPAWN = lambda: it.repeat(3)
SHIP_SPEED = lambda: factor_last([200],
                                 factor=LEVEL_AUGMENTATION, 
                                 round_values=True
                                 )
SHIP_ROTATION_SPEED = lambda: factor_last([200],
                                          factor=LEVEL_AUGMENTATION, 
                                          round_values=True
                                          )
BULLET_SPEED = lambda: factor_last([200],
                                   factor=LEVEL_AUGMENTATION, 
                                   round_values=True
                                   )
CANNON_RELOAD_RATE = lambda: repeat_last([2]*5 + [1.5]*3 + [1])
RAD_BORDER = lambda: it.chain(it.islice(it.count(0.15, 0.025), 14),
                              it.repeat(0.5))
NAT_EXPOSURE_LIMIT = lambda: it.repeat(68)
HIGH_EXPOSURE_LIMIT = lambda: it.repeat(20)
NUM_PICKUPS = lambda: repeat_last([1]*2 + [2]*2 + [3])

#Override globals with any attributes set on any passed config file
settings = ['BLUE_CONTROLS', 'RED_CONTROLS',
            'WIN_X', 'WIN_Y', 'LIVES', 'LAST_LEVEL', 
            'PICKUP_INTERVAL_MIN', 'PICKUP_INTERVAL_MAX', 'AT_BOUNDARY',
            'NUM_ASTEROIDS', 'ASTEROID_SPEED', 
            'SPAWN_LIMIT', 'NUM_PER_SPAWN', 'SHIP_SPEED', 
            'SHIP_ROTATION_SPEED', 'BULLET_SPEED', 'CANNON_RELOAD_RATE', 
            'RAD_BORDER', 'NAT_EXPOSURE_LIMIT', 'HIGH_EXPOSURE_LIMIT',
            'NUM_PICKUPS']
pyroids.config_import(vars(), settings)
assert PICKUP_INTERVAL_MAX >= PICKUP_INTERVAL_MIN

Ship.set_controls(controls=BLUE_CONTROLS)
ShipRed.set_controls(controls=RED_CONTROLS)

#BATCHES
start_batch = pyglet.graphics.Batch()
game_batch = pyglet.graphics.Batch()
info_batch = pyglet.graphics.Batch()
next_level_batch = pyglet.graphics.Batch()
end_batch = pyglet.graphics.Batch()
inst_batch = pyglet.graphics.Batch()

#GROUPS
class RadGroup(pyglet.graphics.OrderedGroup):
    def set_state(self):
        pyglet.gl.glLineWidth(1)

rad_group = RadGroup(0)
game_group = pyglet.graphics.OrderedGroup(1)

class Player(object):
    """Maintains player lives and score.
    Contructor takes a Game instance (--game--)
    Constructor creates a ControlSystem (--control_sys--) from which a ship 
    is requested. When ship killed, whilst player has lives remaining then 
    the player is resurrected with a new ship. All ships are requested from 
    the --control_sys--.request_ship() which is passed current speed 
    data requested from .game together with a callback to advise the player 
    when the ship is killed. When no lives remaining the player object 
    advises the game (--game--) that player dead.
    
    Game information provided to the player via InfoRow.

    Constructor starts repeated calls to create resupply PickUp objects. 
    The initial resupply is dropped after between, and inclusive of, 
    ----PICKUP_INTERVAL---- and ----PICKUP_INTERVAL*2---- seconds. Each 
    drop triggers a call for the next drop, again to occur after a further 
    between ----PICKUP_INTERVAL---- and ----PICKUP_INTERVAL*2---- seconds.

    Public methods:
    --score-- returns current score and can be set to a new score
    --add_to_score(increment)--
    --withdraw_from_game()-- effectively stops further player interaction 
    with the game, although existing information will remain (such as 
    information labels)
    --delete-- removes all traces of player from the game
    """
        
    PickUpCls = {'blue': PickUp,
                 'red': PickUpRed}

    def __init__(self, game: pyglet.window.Window, 
                 color: Union['blue', 'red'], 
                 avoid: Optional[List[AvoidRect]] = None):
        """++game++ takes game instance of Game class (a subclass of 
        pyglet.window.Window).
        ++color++ passed as string indicating player colour, 'blue' or 'red'
        Constructor gets ship and position randomly in the game window, 
        inserts an InfoRow and starts scheduling pick up drops.
        Initial ship will be positioned randomly albeit avoiding the areas 
        defined in ++avoid++ by a list of AvoidRect objects.
        """
        self.game = game
        self.color = color
        self.control_sys = ControlSystem(color=self.color)
        self.ship: Ship # set via _request_ship
        self.request_ship(avoid=avoid)
        self._score = 0
        self.lives = LIVES

        self._info_row = InfoRow(window=game, batch=info_batch,
                                 control_sys=self.control_sys,
                                 num_lives=LIVES, 
                                 level_label=self.game.level_label.label)

        self._pickups_cumulative = 0
        self._max_pickups = 0
        self._schedule_drop()

    def request_ship(self, avoid: Optional[List[AvoidRect]] = None,
                     **kwargs):
        """Requests a ship from the control system which it randomly
        rotates and randomly postions albeit to a position that lies 
        outside of any AvoidRect's included to any list passed as +avoid+.
        """
        self.ship = self.control_sys.new_ship(initial_speed=0,
                                              at_boundary=AT_BOUNDARY,
                                              batch=game_batch, 
                                              group=game_group,
                                              on_kill=self.ship_killed, 
                                              **kwargs)
        self.ship.position_randomly(avoid=avoid)
        self.ship.rotate_randomly()

    def ship_killed(self):
        """Call when ship killed"""
        self._lose_life()
        
    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        self._info_row.update_score_label(value)
        
    def add_to_score(self, increment):
        """Increases player score by +increment+"""
        self.score += increment
        
    @property
    def max_pickups(self):
        return self._max_pickups

    @max_pickups.setter
    def max_pickups(self, value: int):
        self._max_pickups = value

    def increase_max_pickups(self, num: int):
        self.max_pickups += num

    def _drop_pickup(self, dt):
        if self._pickups_cumulative < self.max_pickups:
            self.PickUpCls[self.color](batch=game_batch, group=game_group)
            self._pickups_cumulative += 1
        self._schedule_drop()
    
    def _schedule_drop(self):
        ext = random.randint(0, PICKUP_INTERVAL_MAX - PICKUP_INTERVAL_MIN)
        drop_time = PICKUP_INTERVAL_MIN + ext
        pyglet.clock.schedule_once(self._drop_pickup, drop_time)

    def _unschedule_calls(self):
        pyglet.clock.unschedule(self._drop_pickup)

    def _resurrect(self, dt = None):
        """Resurrects a player who lost a life although still have lives.
        Resurrected by getting a new ship with a position that avoids all 
        live sprites.
        Calls method on --game-- to move player to players_alive
        +dt+ parameter provides for calling via one-time clock scheduled 
        event which passes actual elapsed time since call scheduled.
        """
        avoid = []
        for sprite in PhysicalSprite.live_physical_sprites:
            avoid.append(AvoidRect(sprite, margin = 3 * Ship.img.width))
        self.request_ship(avoid=avoid, cruise_speed=self.game.ship_speed,
                          rotation_cruise_speed=self.game.ship_rotation_speed)
                               
    def withdraw_from_game(self):
        self.control_sys.die()
        self._unschedule_calls()

    def _lose_life(self):
        """Reduces lives by one. If player has lives remaining then schedules 
        a resurrection.
        """
        self.lives -= 1
        self._info_row.remove_a_life()
        if self.lives:
            pyglet.clock.schedule_once(self._resurrect, 2)
        else:
            self.withdraw_from_game()
            self.game.player_dead(self)
        
    def delete_info_row(self):
        self._info_row.delete()

    def delete(self):
        """Deletes object.
        Internals - tidy up operations including deleting player labels 
        and deceasing ship if it's still alive
        """
        self.withdraw_from_game()
        self.delete_info_row()
        if self.ship.live:
            self.ship.die()
        del self

class RadiationField(object):
    """Class provides for drawing a radiation field around the edge of the 
    screen. Radiation field defined as two series of parallel lines angled at 
    45 degrees to the vertical, with one series running left-to-right and 
    the other right-to-left such that the lines of each series cross. 
    Within this angled grid are regularly spaced 'radiation' symbols. Grid 
    lines added to the game_batch as a VectorList whilst symbols are added as 
    sprites. All defined in shades of grey.

    The constructor only draws the parallel lines which are drawn to fully 
    fill the window. The client is then requried to execute the --set_field-- 
    method to define the actual radiation zone.

    --set_field(width)-- Set or reset the radiation field to comprise a 
        border around the window of width ++width++
    """

    nuclear_img = load_image('radiation.png', anchor='center')

    def __init__(self):
        self.batch = game_batch
        self.group = rad_group
        self._add_grid()

        self._field_width: int
        self._rect = None
        self._nuclear_sprites = []
                
    def _add_grid(self):
        grid = AngledGrid(x_min=0, x_max=WIN_X, y_min=0, y_max=WIN_Y,
                          vertical_spacing=50, angle=45, color=(80, 80, 80),
                          batch=self.batch, group=self.group)
    
    def _set_blackout_rect(self):
        if self._rect is not None:
            self._rect.remove_from_batch()
        # do not draw blackout rect if radiation field fills window
        if min(WIN_X, WIN_Y)/2 - self._field_width < 1:
            return
        self._rect = Rectangle(self._field_width, WIN_X - self._field_width,
                               self._field_width, WIN_Y - self._field_width,
                               batch=self.batch, group=self.group,
                               fill_color=(0, 0, 0)
                               )
        
    def _add_nuclear_sprite(self, x, y):
        sprite = Sprite(self.nuclear_img, x, y, 
                      batch=self.batch, group=self.group)
        if sprite.width > self._field_width:
            sprite.scale = round(self._field_width/sprite.width, 1)
        self._nuclear_sprites.append(sprite)
        return sprite
        
    def _delete_nuclear_sprites(self):
        for sprite in self._nuclear_sprites:
            sprite.delete()
        self._nuclear_sprites = []

    def _set_nuclear_sprites(self):
        if self._nuclear_sprites:
            self._delete_nuclear_sprites()
        if self._field_width is 0:
            return
        half_width = self._field_width//2
        min_separation = self.nuclear_img.height*4

        #create nuclear sprites on LHS
        top_sprite = self._add_nuclear_sprite(half_width, WIN_Y-half_width-8)
        lhs_sprites = [top_sprite]
        bot_sprite = self._add_nuclear_sprite(half_width, half_width)
        
        vert_num = WIN_Y//min_separation
        if vert_num > 2:
            diff = top_sprite.y - bot_sprite.y
            vert_separation = diff//(vert_num -2 +1)
            y = top_sprite.y - vert_separation
            for i in range(0, vert_num-2):
                sprite = self._add_nuclear_sprite(half_width, y)
                lhs_sprites.append(sprite)
                y -= vert_separation
        lhs_sprites.append(bot_sprite)

        #'mirror' LHS to RHS
        rhs_sprites = []
        for lhs_sprite in lhs_sprites[:]:
            sprite = self._add_nuclear_sprite(WIN_X-half_width, lhs_sprite.y)
            rhs_sprites.append(sprite)

        #create bottom sprites, between existing bot sprites on lhs and rhs
        min_separation = round(self.nuclear_img.height*4.5)
        bottom_sprites = []
        horz_num = WIN_X//min_separation
        if horz_num >2:
            diff = rhs_sprites[-1].x - lhs_sprites[-1].x
            horz_separation = diff//(horz_num -2 +1)
            x = lhs_sprites[-1].x + horz_separation 
            for i in range(0, horz_num-2):
                sprite = self._add_nuclear_sprite(x, half_width)
                bottom_sprites.append(sprite)
                x += horz_separation

        #'mirror' bot to top
        for bottom_sprite in bottom_sprites[:]:
            self._add_nuclear_sprite(bottom_sprite.x, top_sprite.y)

    def set_field(self, width: float):
        """Set or reset the radiation field to represent a border of width 
        ++width++.
        """
        assert width <= min(WIN_Y, WIN_X)/2
        self._field_width = width
        self._set_blackout_rect()
        self._set_nuclear_sprites()

            
class Game(pyglet.window.Window):
    """Subclasses pyglet.window.Window to create a game application class 
    which is itself the window in which the game is played.

    The following application states are defined:
        'start' comprises start screen inviting user to start a game. This 
          screen cannot be returned  to later. Requires keyboard press to 
          proceed, handled by --on_key_press--. User pressing '1' or '2' key 
          results in game starting for 1 or 2 players respectively (and 
          results in the state changing to 'game'.
        'game' a live continuing game
        'next_level' the period between game levels
        'end' following the end of a game (once all players have lost all 
          lives or if the user forces the end of the game with F10). User 
          can play again via '1' or '2'
          with the game over screen and the option to play again
        'instructions' screen offering end user instructions to include 
          key controls
    
    Internals
    Labels associated with a batch are created via dedicated classes of the 
    labels module: StartLabels, NextLevelLabel, LevelLabel, EndLabels.
    
    The current state is returned by --app_state-- and states are changed by 
    setting --app_state--
    --_state_batches-- associates each state with a tuple of one or more 
    globally defined batches. NB A batch can be associated with one or more 
    states. Drawing to the window provided for by overriding the inherited 
    --on_draw-- event handler to draw, in order, the batches that are 
    associated with the current state. 
    
    Application starts in 'start' state which offers the user a title 
    screen with an invitation to play by pressing 1 or 2, or viewing 
    instructions via Enter. User pressing 1 or 2 is handled by 
    --on_key_press-- which starts game with call to --start_game--.
    DYNAMIC VARIABLES - part of the game setup process involves setting up 
    dynamic variables which can take a different value for each game level. 
    Via a call to --_set_settings_map-- the --_settings_map-- dictionary 
    is defined, each item of which defines a dynamic variable:
          The key takes a setter function that has one argument which takes 
        the new value that the dynamic variable is to be set to, the setter 
        is responsible for implementing the conseqeunce of the change in the 
        dynamic variable's value. All setter functions are defined on this 
        class, for example --_set_number_asteroids-- and 
        --_set_spawn_limit--. The value 
          The value takes an iterator which returns the dynamic variable 
        values, with the first call returning the value for level 1 and each 
        subsequent call representing the value for each successive level. 
        Each value is defined as the return from a function assigned to an 
        associated global attribute, for example NUM_ASTEROIDS, SPAWN_LIMIT, 
        each of which are (by default) assigned lambda functions that 
        return iterators. NB the default functions assigned to these global 
        attributes can be overriden via configurations files, thereby 
        allowing clients to define the dynamic variables for every level.
    Each time a new game is setup a fresh version of --_settings_map-- is 
    created with new iterators (such that dynamic variables will again 
    start from 0).
    The start_game method also deletes any players from a previous game and 
    sets up new players. 
    The method concludes by executing --play_level--.
    
    --play_level-- is executed after the game setup and then again at the 
    start of each new level. The method implements the dynamic variables for 
    the current level and sets the application state to 'game'. Each dynamic 
    variable is implemented by calling its setter function and passing it 
    the next value returned by the associated iterator. Note that the setter 
    functions are only concerned with implementing the consequence of the new 
    value. This may or may not require the value to be stored to an instance 
    attribute. For example instance attributes _ship_speed and 
    ship_rotation_speed are set (by --_set_ship_speed-- and 
    --_set_ship_rotation_speed-- respectively) as these values are required by 
    the Player class to instantiate any ship resurrected during the level. 
    However, the likes of --_set_bullet_speed--, --_set_cannon_reload_rate--, 
    --_set_radiation_field--, --_set_pickups-- etc do not assign the value 
    directly to an instance attribute but rather simply send it on to 
    wherever it's required to implement the consequences of the change. For 
    example the value passed to --_set_cannon_reload_rate-- is passed 
    straight on to the control system. Even the number of asteroids is 
    not stored, rather --_set_num_asteroids-- directly instantiates the 
    required number (NB this is the reason that the --_settings_map-- is 
    an OrderedDict - instantiating the asteroids via --_set_num_asteroids-- 
    requires that --_asteroid_speed--, --_spawn_limit-- and 
    --_num_per_spawn-- have already been set.
    After setting new dynamic values --play_level-- sets the game off by 
    starting --refresh-- (see following) and giving players control of the 
    ships.

    All game sprites have PhysicalSprite as a base. The PhysicalSprite 
    class maintains a ---live_physical_sprites--- attribute that holds a 
    list of all instantiated sprites that have not subsequently deceased. For 
    the purposes of this class, that means it holds a list of all moving 
    sprites in the window, and only those sprites. These sprites are made to 
    'move' via regular calls to each sprite's refresh method to which the 
    time since the last call is passed. It is each sprite's responsiblity to 
    calcualte it's new position given the elapsed time. The 'call out' to 
    all live spreads is made by the --refresh-- method which when scheduled 
    is called 100 times a second.
    Scheduled by --start_refresh-- and cancelled by --stop_refresh--. 
    Scheduled at the start of a level (by --_pause_for_next_level-- via 
    --play_level--) and unscheduled at the end of each level (by 
    --_unpause_for_next_level-- via --next_level_page--) and the end of a 
    game (directly by --end_game--)
    Also, --refresh-- is effectively disabled and enabled by the 
    --_user_pause-- and --_user_resume-- methods which pause and resume 
    the clock responsible for scheduling calls to --refresh--.
    
    PAUSING. Two types of pause and resumption defined, in addition to 
    pausing sprite refresh:
    --_pause_for_next_level-- and --_unpause_for_next_level-- methods 
    provide for pausing between levels. During this pause player ships 
    are frozen although the pyglet clock is not paused such that any 
    scheduled events will continue to execute. The between levels' pause 
    also allows for sound to bleed over between levels.
    --_user_pause-- and --_user_resume-- provide for pausing on such a
    request by a player (via F12 which is picked up by --on_key_press--). 
    The pyglet clock is paused during this period - effectively freezing 
    any scheduled events during the pause to prevent their premature 
    execution. Pushes the --paused_on_key_press-- handler (which returns 
    True) to the top of the stack so that all key presses are handled by 
    that method, which provides for user to return to game with F12 or 
    exit with ESCAPE. Also stops and resumes all sound either side of the 
    pause.

    Levels. The --refresh-- method identifies when there are no more 
    asteroids whilst at least one player remains alive. In this case the 
    game is paused and the --next_level_page-- method is called. If the 
    level just played was the ----LAST_LEVEL---- then end game is called 
    with advices that the game was completed. Otherwise sets the state to 
    'next_level', pauses the game and schedules a call to --next_level-- 
    which gets rid of unrequired sprites (bullets, mines etc) before 
    calling --play_level-- to play the next level.

    End game. Handled by --end_game(escaped, completed)-- which sets the 
    'end' state. Can be called in the following circumstances:
        From the in-game pause screen, via the escape key
        If all players lose all their lives (identified by --refresh--)
        If player(s) completes last level
    Sets the end labels to show information appropriate for the 
    circumstances under which the game ended.
    --end_game-- also 'closes down' the game, stopping --refresh-- and 
    preventing further player interaction. It does not delete the players, 
    thereby allowing for the player information (ammo stocks, score etc) 
    to remain.
    The end labels include instrutions to start a new game by pressing 
    either 1 or 2.

    In-game pause. When in 'game' or 'next_level' states can toggle 
    pause/unpause with F12. When paused enters 'instructions' state and 
    shows a version of the instructions screen.

    Collisions. --refresh-- calls PhysicalSprite.eval_collisions to 
      evaluate collisions between live sprites and resolve those 
      collisions by calling the collided_with method of each 
      of the objects that collided (with the collided_with method of 
      every object being responsible to handle the collision consequence 
      for itself only). Additionally:
        Evaluates if the collision is between a bullet and an asteroid, 
          in which case adds 1 to the score of the player whose ship 
          fired the bullet
    """

    def __init__(self, *args, **kwargs):
        """Sets up PhysicalSprite class attributes
        Initialises labels and sets window to start screen.
        See cls.__doc__ for further documentation.
        """
        super().__init__(*args, width=WIN_X, height=WIN_Y, **kwargs)
        PhysicalSprite.setup(window=self, at_boundary='bounce')
        
        self.players_alive = [] # appended to by --add_player--
        self.players_dead = []
        self._num_players: int # set by --start_game--

        # set by dedicated set methods - as keys of --_settings_map--
        self._level: int = 0
        self._num_asteroids: int = 0
        self._asteroid_speed: int = 0
        self._ship_speed: int = 0
        self._ship_rotation_speed: int = 0
        self._spawn_limit: int = 0
        self._num_per_spawn: int = 0
        
        self._settings_map: dict # set / reset by --_set_settings_map()--
        self._rad_field = RadiationField()
        
        self._state_batches = {'start': (start_batch,),
                               'game': (game_batch, info_batch),
                               'next_level': (game_batch, info_batch,
                                              next_level_batch),
                               'end': (end_batch, info_batch),
                               'instructions': (game_batch, info_batch,
                                                inst_batch)
                               }
        
        self._app_state: str
        self.app_state = 'start'        
        self._pre_instructions_app_state: Optional[str] = None

        self.start_labels = StartLabels(self, start_batch)
        self.next_level_label = NextLevelLabel(self, next_level_batch)
        self.level_label = LevelLabel(self, info_batch)
        self.end_labels = EndLabels(self, end_batch)
        self.instructions_labels = InstructionLabels(BLUE_CONTROLS, 
                                                     RED_CONTROLS, 
                                                     self, inst_batch)

    @property
    def app_state(self):
        return self._app_state

    @app_state.setter
    def app_state(self, state):
        assert state in self._state_batches
        self._app_state = state

    def _set_settings_map(self):
        map = OrdDict({self._set_level: it.count(1, 1),
                       self._set_ship_speed: SHIP_SPEED(),
                       self._set_ship_rotation_speed: SHIP_ROTATION_SPEED(),
                       self._set_asteroid_speed: ASTEROID_SPEED(),
                       self._set_spawn_limit: SPAWN_LIMIT(),
                       self._set_num_per_spawn: NUM_PER_SPAWN(),
                       self._set_num_asteroids: NUM_ASTEROIDS(),
                       self._set_bullet_speed: BULLET_SPEED(),
                       self._set_cannon_reload_rate: CANNON_RELOAD_RATE(),
                       self._set_radiation_field: RAD_BORDER(),
                       self._set_natural_exposure_limit: NAT_EXPOSURE_LIMIT(),
                       self._set_high_exposure_limit: HIGH_EXPOSURE_LIMIT(),
                       self._set_pickups: NUM_PICKUPS()
                       })
        self._settings_map = map


    #window keypress handler
    def on_key_press(self, symbol, modifiers):
        """Key press handler for the window.
        Execution depends on application state:
          If 'game' or 'next level' then only acts on key press of F12 
        which pauses the game.
          If 'instructions' then any key press will return the application 
        to its state prior to entering the 'instructions' state.
          If 'start' or 'end' then key press of 1 or 2 (either top row or 
        number pad) or F1 or F2 will start game for 1 or 2 players whilst 
        key press of escape will exit the application.
        Internals:
        key presses from the pause screen are handled by 
        --paused_on_key_press-- which is pushed to the stack temporarily 
        above this method.
        key presses that control ships are handled by the handlers on the 
        Ship class
        """
        if self.app_state in ['game', 'next_level']:
            if symbol == pyglet.window.key.F12:
                self._user_pause()
            else:
                return
        elif self.app_state == 'instructions':
            self._return_from_instructions_screen()
        else:
            assert self.app_state in ['start', 'end']
            if symbol == pyglet.window.key.ENTER:
                return self._show_instructions_screen(paused=False)
            elif symbol in [pyglet.window.key._1,
                            pyglet.window.key.NUM_1,
                            pyglet.window.key.F1]:
                players=1
            elif symbol in [pyglet.window.key._2, 
                            pyglet.window.key.NUM_2,
                            pyglet.window.key.F2]:
                players=2
            elif symbol == pyglet.window.key.ESCAPE:
                self.end_app()
                return
            else:
                return
            self.start_game(players)
            
    #PLAYERS
    @property
    def all_players(self) -> List[Player]:
        return self.players_alive + self.players_dead

    @property
    def num_players(self) -> int:
        return len(self.all_players)

    @property
    def player_winning(self) -> Optional[Player]:
        """Returns Player with the highest current score, or None 
        if more than one player has the highest current score"""
        scores = [player.score for player in self.all_players]
        max_score = max(scores)
        tie = True if scores.count(max_score) > 1 else False
        if tie:
            return None
        else:
            return max(self.all_players, key= lambda player: player.score)
        
    def _move_player_to_dead(self, player: Player):
        self.players_alive.remove(player)
        self.players_dead.append(player)

    def player_dead(self, player: Player):
        """Call when player dead"""
        self._move_player_to_dead(player)

    def delete_all_players(self):
        for player in self.all_players:
            player.delete()
        self.players_alive = []
        self.players_dead = []

    @property
    def players_ships(self) -> List[Ship]:
        """Returns list of ship objects of players who currently 
        have a live ship. NB Players who do not currently have a ship, 
        due to player having died or being resurrected, will not be 
        represented.
        """
        ships = []
        for player in self.all_players:
            if player.ship.live:
                ships.append(player.ship)
        return ships

    def _withdraw_players(self):
        for player in self.all_players:
            player.withdraw_from_game()

    #ADD GAME OBJECTS
    def add_player(self, color: Union['blue', 'red'],
                   avoid: Optional[List[AvoidRect]] = None) -> Player:
        player = Player(game=self, color=color, avoid=avoid)
        self.players_alive.append(player)
        return player
        
    def set_players(self) -> Player:
        self.delete_all_players()
        player1 = self.add_player(color='blue')
        if self._num_players == 2:
            avoid = [AvoidRect(player1.ship, margin = 2 * player1.ship.width)]
            self.add_player(color='red', avoid=avoid)

    def _add_asteroid(self, avoid: Optional[List[AvoidRect]] = None):
        """Adds asteroid with random rotation and ramdon position albeit 
        avoiding any AvoidRect included in any list passed as ++avoid++.
        """
        asteroid = Asteroid(batch=game_batch, group=game_group,
                            initial_speed=self._asteroid_speed,
                            spawn_limit=self._spawn_limit, 
                            num_per_spawn=self._num_per_spawn,
                            at_boundary=AT_BOUNDARY)
        asteroid.position_randomly(avoid=avoid)
        asteroid.rotate_randomly()

    def _add_asteroids(self, num_asteroids: int):
        avoid = []
        for ship in self.players_ships:
            avoid.append(AvoidRect(ship, margin = 6 * ship.width))
        for i in range(num_asteroids):
            self._add_asteroid(avoid=avoid)

    #REFRESH METHOD CALLS
    def asteroid_and_bullet(self, collision: tuple) -> Union[Bullet, bool]:
        """Advises of any collision between an Asteroid and a Bullet.
        Where +collision+ contains two PhysicalSprite objects, if one 
        is a bullet and the other an asteroid then returns the bullet, 
        otherwise returns False"""
        c = collision
        if isinstance(c[0], Asteroid) and isinstance(c[1], Bullet):
            return c[1]
        elif isinstance(c[0], Bullet) and isinstance(c[1], Asteroid):
            return c[0]
        else:
            return False
        
    def identify_firer(self, bullet: Bullet) -> Optional[Player]:
        """Returns Player responsible for +bullet+"""
        for player in self.all_players:
            if player.control_sys is bullet.control_sys:
                return player

    def no_asteroids(self) -> bool:
        """Returns boolean advising if there are asteroids any left"""
        for sprite in PhysicalSprite.live_physical_sprites:
            if isinstance(sprite, Asteroid):
                return False
        return True

    def check_for_points(self, collision: tuple):
        """Where +collision+ contains two PhysicalSprite objects, 
        if one is a Bullet and one an Asteroid then will add one 
        to the score of any player who fired the bullet, albeit 
        only if the ship that fired the bullet has not been since 
        destoryed.
        """
        bullet = self.asteroid_and_bullet(collision)
        if bullet:
            firer = self.identify_firer(bullet)
            try:
                firer.add_to_score(1)
            except AttributeError:
                pass

    #REFRESH
    def refresh(self, dt):
        """
        Progresses to next level page if there are no asteroids left and 
        there is still at least one player alive, otherwise:
            Checks for collisions between any PhysicalSprite objects. For 
                colliding objects:
                If a Bullet and an Asteroid then identifies player who 
                    fired bullet and adds one to their score.
                Resolves collision via one of the objects' 
                    'collided_with' method (each object being resonponsible 
                    for implementing the consequence of the collision for 
                    itself only).
                Checks if any player lost a life in the collision. If no 
                    player has any remaining lives then moves to end game.
            Updates position of all PhysicalSprite objects
        """
        if self.no_asteroids() and self.players_alive:
            return self.next_level_page()

        collisions = PhysicalSprite.eval_collisions()
        live_physical_sprites = PhysicalSprite.live_physical_sprites
        for c in collisions:
            if c[0] in live_physical_sprites and c[1] in live_physical_sprites:
                self.check_for_points(c)
                c[0].collided_with(c[1])
                c[1].collided_with(c[0])

        if not self.players_alive:
            return pyglet.clock.schedule_once(self.end_game, 1)

        for sprite in live_physical_sprites:
            sprite.refresh(dt)

    #SCREEN AND SOUND CONTROL
    def _decease_game_sprites(self, exceptions: Optional[List[Sprite]] = None,
                              kill_sound=False):
        """Deceases all sprites in window save for any +exceptions+ where 
        excpetions past as specific Sprite instances or a subclass of 
        Sprite, in which all sprites of that subclass will be excluded
        If +kill_sound+ then will stop sound of PhysicalSprites that 
        otherwise die loudly.
        """
        if kill_sound:
            self._stop_all_sound()
        SpriteAdv.decease_selective(exceptions=exceptions)

    def start_refresh(self):
        pyglet.clock.schedule_interval(self.refresh, 1/100.0)

    def stop_refresh(self):
        pyglet.clock.unschedule(self.refresh)

    def freeze_ships(self):
        for ship in self.players_ships:
            ship.freeze()
    
    def unfreeze_ships(self):
        for ship in self.players_ships:
            ship.unfreeze()

    def _pause_for_next_level(self):
        """Internals - to pause game between levels. Clock is not paused, 
        hence scheduled calls (i.e. call to play next level) are not 
        prevented"""
        self.stop_refresh()
        self.freeze_ships()

    def _unpause_for_next_level(self):
        """Internals - to resume game for the purpose of starting a new 
        level"""
        self.start_refresh()
        self.unfreeze_ships()

    def _show_instructions_screen(self, paused: bool = False):
        self._pre_instructions_app_state = self.app_state
        self.instructions_labels.set_labels(paused)
        self.app_state = 'instructions'

    def _return_from_instructions_screen(self):
        self.app_state = self._pre_instructions_app_state
        self._pre_instructions_app_state = None

    def _show_instructions_screen(self, paused: bool = False):
        self._pre_instructions_app_state = self.app_state
        self.instructions_labels.set_labels(paused)
        self.app_state = 'instructions'

    def _return_from_instructions_screen(self):
        self.app_state = self._pre_instructions_app_state
        self._pre_instructions_app_state = None

    def _who_won(self) -> Union['blue', 'red', None]:
        who_won = self.player_winning
        if who_won is not None:
            who_won = who_won.color
        return who_won

    def _set_end_state(self, escaped=False, completed=False):
        self.app_state = 'end'
        if escaped:
                self.end_labels.set_labels(winner=False, completed=False)
        elif self.num_players == 2:
            self.end_labels.set_labels(winner=self._who_won(), 
                                       completed=completed)
        else:
            self.end_labels.set_labels(winner=False, completed=completed)

    def _stop_all_sound(self):
        SpriteAdv.stop_all_sound()
        Starburst.stop_all_sound()
        for ship in self.players_ships:
            ship.control_sys.radiation_monitor.stop_sound()

    def _resume_all_sound(self):
        SpriteAdv.resume_all_sound()
        Starburst.resume_all_sound()
        for ship in self.players_ships:
            ship.control_sys.radiation_monitor.resume_sound()

    def paused_on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self._user_resume()
            self.end_game(escaped=True)
        elif symbol == pyglet.window.key.F12:
            self._user_resume()
        return True

    def _user_pause(self):
        """Provides for pausing application in-game when pause requested 
        by user. Pauses in such a way that subsequent user interaction 
        with program is limited (until --_user_resume-- is called) to 
        that provided for by the key press handler --paused_on_key_press--.
        """
        self._stop_all_sound()
        self.freeze_ships()
        CLOCK.pause()
        self.push_handlers(on_key_press=self.paused_on_key_press)
        self._show_instructions_screen(paused=True)
        
    def _user_resume(self):
        """Resumes game following --_user_pause--"""
        self._return_from_instructions_screen()
        self.pop_handlers()
        CLOCK.resume()
        self.unfreeze_ships()
        self._resume_all_sound()
        
    def end_app(self):
        """Ends program"""
        self._stop_all_sound()
        self.close()
        self.delete()
    
    #PLAY GAME / LEVELS
    def _set_level(self, value):
        self._level = value
        self.level_label.update(value)

    def _set_num_asteroids(self, value):
        self._add_asteroids(value)
                
    def _set_asteroid_speed(self, value):
        self._asteroid_speed = value

    @property
    def ship_speed(self):
        return self._ship_speed

    def _set_ship_speed(self, value):
        self._ship_speed = value
        for ship in self.players_ships:
            ship.cruise_speed_set(value)

    @property
    def ship_rotation_speed(self):
        return self._ship_rotation_speed

    def _set_ship_rotation_speed(self, value):
        self._ship_rotation_speed = value
        for ship in self.players_ships:
            ship.rotation_cruise_speed_set(value)
    
    def _set_spawn_limit(self, value):
        self._spawn_limit = value

    def _set_num_per_spawn(self, value):
        self._num_per_spawn = value

    def _set_bullet_speed(self, value):
        for player in self.players_alive:
            player.control_sys.bullet_discharge_speed = value

    def _set_cannon_reload_rate(self, value):
        for player in self.players_alive:
            player.control_sys.set_cannon_reload_rate(value)

    def _set_pickups(self, num_pickups_for_level):
        for player in self.players_alive:
            player.increase_max_pickups(num_pickups_for_level)

    def _get_field_width(self, border) -> int:
        """Where border is a float representing the total percentage of 
        the window height (or width if higher than wider) that should 
        comprise the radiation field, returns the border width.
        """
        if border < 0:
            border = 0
        elif border > 1:
            border = 1
        field_width = int((min(WIN_X, WIN_Y)*border)//2)
        return field_width

    def _get_cleaner_air_field(self, field_width) -> InRect:
        return InRect(x_from = field_width, x_to = WIN_X - field_width,
                      y_from = field_width, y_to= WIN_Y - field_width)

    def _set_radiation_field(self, border):
        field_width = self._get_field_width(border)
        self._rad_field.set_field(width=field_width)
        cleaner_air = self._get_cleaner_air_field(field_width)
        for ship in self.players_ships:
            monitor = ship.control_sys.radiation_monitor.reset(cleaner_air)
            
    def _set_natural_exposure_limit(self, value):
        for ship in self.players_ships:
            monitor = ship.control_sys.radiation_monitor
            monitor.set_natural_exposure_limit(value)

    def _set_high_exposure_limit(self, value):
        for ship in self.players_ships:
            monitor = ship.control_sys.radiation_monitor
            monitor.set_high_exposure_limit(value)

    def _setup_next_level(self):
        for setting, iterator in self._settings_map.items():
            setting(next(iterator))

    def play_level(self):
        self._setup_next_level()
        self._unpause_for_next_level()
        self.app_state = 'game'

    def _setup_mine_cls(self):
        visible_secs = None if self._num_players == 1 else 2
        Mine._setup_mines(visible_secs=visible_secs)

    def start_game(self, num_players: int = 1):
        """sets / resets game and proceeds to play first level"""
        self._num_players = num_players
        self._setup_mine_cls()
        self._set_settings_map()
        self.set_players()
        self._pause_for_next_level()
        self.set_mouse_visible(False)
        self.play_level()

    def next_level(self, dt: Optional[float] = None):
        """Sets parameters for next level and makes call to play level"""
        self._decease_game_sprites(exceptions=self.players_ships + 
                                   [PickUp, PickUpRed])
        self.play_level()

    def next_level_page(self):
        """Sets screen for next level, pauses game and schedules call to 
        play next level in one second.
        Ends game if the current level was the last level"""
        if self._level == LAST_LEVEL:
            return self.end_game(completed=True)
        self.app_state = 'next_level'        
        self._pause_for_next_level()
        pyglet.clock.schedule_once(self.next_level, 1)

    def end_game(self, dt=None, escaped=False, completed=False):
        """Sets screen for end of game and stops game by ending calls 
        to --refresh-- loop and changing game state to not in game.
        +escaped+ should be passed as True if game ended by player 
        'escaping' rather than ending naturally
        +completed+ should be passed as True if game ended by way of 
        player(s) completing the last level as opposed to losing all 
        lives.
        """
        if escaped:
            pyglet.clock.unschedule(self.next_level)
        self._set_end_state(escaped, completed)
        self._withdraw_players()
        self._decease_game_sprites(kill_sound=True)
        self.stop_refresh()
        self.set_mouse_visible(True)
        self._num_players = None
        
    #DRAW WINDOW
    def on_draw(self):
        """Principal event loop for drawing to the window. Frequency 
        determined by underlying pyglet module
        Draws batches corresponding with the curent app state
        """
        self.clear()
        for batch in self._state_batches[self.app_state]:
            batch.draw()
        

#Sets up instance of appliation and initiates pyglet's main event loop
game_window = Game()

#INVESTIGATION CODE - available to debug in game by pressing F3
#def invest_report():
#    """For investigating and debugging.
#    Executes when press F3 in-game"""
#    print("Invest report:")
#    print("Player ship:", player_ship)
#    print("Physical Sprites:", PhysicalSprite.live_physical_sprites)

#def on_key_press(symbol, modifiers):
#    """ """
#    if symbol == pyglet.window.key.F3:
#        invest_report()
#game_window.push_handlers(on_key_press)

pyglet.app.run()