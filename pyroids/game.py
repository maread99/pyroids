#! /usr/bin/env python

"""Application.

Defines application engine and instantiates application instance.

Global ATTRIBUTES
The following module attributes are assigned default values that can be
overriden by defining an attribute of the same name in a configuration 
file (see pyroids.config.template.py for explanation of each attribute 
and instructions on how to customise values):
    'WIN_X', 'WIN_Y',     
    'BLUE_CONTROLS', 'RED_CONTROLS',
    'LIVES', 'LAST_LEVEL', 
    'SHIP_SPEED', 'SHIP_ROTATION_SPEED', 'BULLET_SPEED', 'CANNON_RELOAD_RATE',
    'RAD_BORDER', 'NAT_EXPOSURE_LIMIT', 'HIGH_EXPOSURE_LIMIT', 
    'PICKUP_INTERVAL_MIN', 'PICKUP_INTERVAL_MAX', 'NUM_PICKUPS',
    'NUM_ASTEROIDS', 'ASTEROID_SPEED', 'NUM_PER_SPAWN', 'AT_BOUNDARY'
   
CLASSES:
Player()  Player representation.
Game()  Application Engine encompassing Game Engine.
RadiationField()  Draws radiation field.
"""

from .lib.pyglet_lib.clockext import ClockExt
import pyglet

CLOCK = ClockExt()
pyglet.clock.set_default(CLOCK)  # set alt. clock with pause functionality

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
from .game_objects import (Ship, ShipRed, ControlSystem, Asteroid, 
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

# LEVEL SETTINGS.
# Each level setting defined as a function that returns an iterator.
# Iterator's first interation returns setting value for level 1 and each 
# subsequent interation returns setting value for each subsequent level.
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

# Override globals with any corresponding setting defined on any 
# declared configuration file.
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
#
# Define batches to hold pyglet objects to be drawn in a specific 
# circumstance.
start_batch = pyglet.graphics.Batch()  # start page
game_batch = pyglet.graphics.Batch()  # during game
info_batch = pyglet.graphics.Batch()  # info row across top of screen
next_level_batch = pyglet.graphics.Batch()  # next level page
end_batch = pyglet.graphics.Batch()  # end page
inst_batch = pyglet.graphics.Batch()  # instructions page

#GROUPS
class RadGroup(pyglet.graphics.OrderedGroup):
    def set_state(self):
        pyglet.gl.glLineWidth(1)

rad_group = RadGroup(0)  # for drawings that comprise radiation field
game_group = pyglet.graphics.OrderedGroup(1)  # all other game objects

# DEVELOPMENT NOTE. 
# Rather than having Game and Player both look at the globally defined 
# batches and groups, considered defining them as class attributes of 
# Game and then passing through those required by Player. Decided cleaner
# to define at module level.

class Player(object):
    """A player of a Game.
    
    Comprises:
        ControlSystem
        InfoRow
        Functionality to:
            Request ship with attributes as currently defined by --game--.
                When killed ship resurrects if lives remaining. If no 
                lives remaining then --game-- advised that player dead.
            Maintain lives and score
            Schedule supply drops with each drop made between 
                ----PICKUP_INTERVAL---- and ----PICKUP_INTERVAL*2----
                seconds after the prior drop (or start of game) and only 
                in event total drops during game will not exceed 
                --max_pickups--
            
    Class ATTRIBUTES
    ---PickUpCls--- dictionary defining PickUp class for each player color

    Instance ATTRIBUTES
    --game-- Game instance in which player participating.
    --control_sys-- ControlSystem.
    --ship-- any current Ship.
    --lives-- number of lives remaining.

    PROPERTIES
    --color-- Player color.
    --score-- current score.
    --max_pickups-- current limit to number of supply drops during a game.

    METHODS
    --__init__()-- create ControlSystem and InfoRow, request initial Ship.
    --add_to_score(increment)-- add +increment+ to score.
    --increase_max_pickups(num)-- increase max pickups by +num+.
    --withdraw_from_game()-- stop Player interaction with --game--.
    --delete()-- delete Player.
    """
        
    PickUpCls = {'blue': PickUp,
                 'red': PickUpRed}

    def __init__(self, game: pyglet.window.Window, 
                 color: Union['blue', 'red'], 
                 avoid: Optional[List[AvoidRect]] = None):
        """Initialises a player.

        ++game++ Game (subclass of pyglet.window.Window) which player to
            participate in.
        ++color++ 'blue' or 'red'
        
        Creates a ControlSystem. Requests a ship positioned to avoid any 
        rectangles defined in +avoid+. Creates an InfoRow to display 
        player related information. Starts supply drop schedule.
        """
        self.game = game
        self._color = color
        self.control_sys = ControlSystem(color=self.color)
        self.ship: Ship  # set via _request_ship
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

    @property
    def color(self):
        return self._color

    def request_ship(self, avoid: Optional[List[AvoidRect]] = None,
                     **kwargs):
        """Request ship from control system.

        Ship given random rotation and random position, albeit avoiding 
        any rectangular areas defined in +avoid+.
        """
        self.ship = self.control_sys.new_ship(initial_speed=0,
                                              at_boundary=AT_BOUNDARY,
                                              batch=game_batch, 
                                              group=game_group,
                                              on_kill=self._lose_life, 
                                              **kwargs)
        self.ship.position_randomly(avoid=avoid)
        self.ship.rotate_randomly()
        
    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        self._info_row.update_score_label(value)
        
    def add_to_score(self, increment: int):
        """Increases player score by +increment+"""
        self.score += increment
        
    @property
    def max_pickups(self):
        return self._max_pickups

    @max_pickups.setter
    def max_pickups(self, value: int):
        self._max_pickups = value

    def increase_max_pickups(self, num: int):
        """Increases maximum number of pickups by +num+"""
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

    def _resurrect(self, dt: Optional[float] = None):
        """Resurrect player.
        
        Requests new ship in position that avoids existing sprites.
        
        +dt+ captures 'elapsed time' if called via scheduled event.
        """
        avoid = []
        for sprite in PhysicalSprite.live_physical_sprites:
            avoid.append(AvoidRect(sprite, margin = 3 * Ship.img.width))
        self.request_ship(avoid=avoid, cruise_speed=self.game.ship_speed,
                          rotation_cruise_speed=self.game.ship_rotation_speed)
                               
    def withdraw_from_game(self):
        """Prevent further player interaction with game"""
        self.control_sys.die()
        self._unschedule_calls()

    def _lose_life(self):
        self.lives -= 1
        self._info_row.remove_a_life()
        if self.lives:
            pyglet.clock.schedule_once(self._resurrect, 2)
        else:
            self.withdraw_from_game()
            self.game.player_dead(self)
        
    def _delete_info_row(self):
        self._info_row.delete()

    def delete(self):
        """Delete player
        
        Removes all traces of player from --game--"""
        self.withdraw_from_game()
        self._delete_info_row()
        if self.ship.live:
            self.ship.die()
        del self

class RadiationField(object):
    """Draws radiation field around edge of screen.
    
    Radiation field defined as two series of parallel lines angled at 
    45 degrees to the vertical, with one series running left-to-right and 
    the other right-to-left such that the lines of each series cross. 
    Regularly spaced 'radiation' symbols placed within field. All defined 
    in shades of grey.

    Constructor only draws parallel lines that fully fill the window.
    Client responsible for subsequently calling --set_field()-- to 
    define field.

    Class ATTRIBUTES
    ---nuclear_img---  radition symbol image as pyglet TextureRegion.

    METHODS
    --set_field(width)-- set/reset radiation field to width +width+.
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
        # Add grid lines to ---game_batch--- as a VectorList
        AngledGrid(x_min=0, x_max=WIN_X, y_min=0, y_max=WIN_Y,
                   vertical_spacing=50, angle=45, color=(80, 80, 80),
                   batch=self.batch, group=self.group)
    
    def _set_blackout_rect(self):
        if self._rect is not None:
            self._rect.remove_from_batch()
        # Do not draw blackout rect if radiation field fills window
        if min(WIN_X, WIN_Y)/2 - self._field_width < 1:
            return
        self._rect = Rectangle(self._field_width, WIN_X - self._field_width,
                               self._field_width, WIN_Y - self._field_width,
                               batch=self.batch, group=self.group,
                               fill_color=(0, 0, 0)
                               )
        
    def _add_nuclear_sprite(self, x, y):
        # Add radiation symbols to ---game_batch--- as sprites
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

        # Create nuclear sprites on LHS
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

        # 'Mirror' LHS to RHS
        rhs_sprites = []
        for lhs_sprite in lhs_sprites[:]:
            sprite = self._add_nuclear_sprite(WIN_X-half_width, lhs_sprite.y)
            rhs_sprites.append(sprite)

        # Create bottom sprites, between existing bot sprites on lhs and rhs
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

        # 'Mirror' bot to top
        for bottom_sprite in bottom_sprites[:]:
            self._add_nuclear_sprite(bottom_sprite.x, top_sprite.y)

    def set_field(self, width: float):
        """Set/reset radiation field to border of width ++width++."""
        assert width <= min(WIN_Y, WIN_X)/2
        self._field_width = width
        self._set_blackout_rect()
        self._set_nuclear_sprites()

            
class Game(pyglet.window.Window):
    """Application and Game Engine.

    Extends pyglet.window.Window such that application engine is itself 
    the application window.

    STATES
    Defines following application states, manages state changes, draws 
    to window as appropriate for current state.
        'start' draws start page inviting user to start a game. User 
            pressing '1' or '2' key starts game for 1 or 2 players and 
            changes state to 'game'. User pressing ENTER changes state to 
            'instructions'.
        'game' draws a live game (see Game Engine section below). User 
            pressing F12 pauses game and changes state to 'instructions'.
        'next_level' draws next level label over live game
        'instructions' draws instructions to include key controls.
            If previous state 'start', user pressing any key returns to 
                start state.
            If previous state 'game', user pressing F12 returns to game 
                state whilst pressing ESCAPE changes to end state.
        'end' draws an end page customised for the circumstances under which 
            game ended. User pressing '1' or '2' starts a new game and 
            changes state to 'game' whilst pressing 'ESCAPE' exits
            the application.
            
    GAME ENGINE
    Deletes players from any previous game.
    Creates players for new game.
    Sets level settings for current level.
    Creates Asteroid sprites.
    During 'game' state repeatedly:
        Checks for any collisions between sprites
        Resolves consequences of any collision
        Updates players' scores
        Updates position of all live sprites
        Redraws screen
    When all asteroids destroyed game briefly paused before advancing to 
    next level.
    Pauses game on F12 key press
    Ends game on earlier of completion of last level or no player having 
    any remaining lives.
        
    PROPERTIES
    --app_state--  Current state
    --all_players--  List of Players
    --player_winning--  Player that is currently winning
    --num_players--  Number of Players
    --players_ships--  List of player's current Ships
    --ship_speed--  Ship speed setting for current level
    --ship_rotation_speed--  Ship rotation speed setting for current level
    """

    def __init__(self, *args, **kwargs):
        """Set up Application.
        
        Create application window.
        Define batches to be drawn for each state.
        Create labels."""
        super().__init__(*args, width=WIN_X, height=WIN_Y, **kwargs)
        PhysicalSprite.setup(window=self, at_boundary='bounce')
        
        self.players_alive = []  # Appended to by --_add_player--
        self.players_dead = []  # Appended to by --_move_player_to_dead--
        self._num_players: int  # Set by --_start_game--

        # Initialise LEVEL SETTINGS.
        # Value of each level setting reassigned for each new level.
        # Each value set by a dedicated method (keys of --_settings_map--)
        # called by --_setup_next_level()--.
        self._level: int = 0
        self._num_asteroids: int = 0
        self._asteroid_speed: int = 0
        self._ship_speed: int = 0
        self._ship_rotation_speed: int = 0
        self._spawn_limit: int = 0
        self._num_per_spawn: int = 0
        
        self._settings_map: dict  # Set / reset by --_set_settings_map()--
        
        self._rad_field = RadiationField()
        
        # Define batches to be drawn for each state.
        # Batches drawn in order by --on_draw()--
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

        # Create labels
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
        # Each item represents a level setting
        #
        # Key a setter function that takes one argument which receives 
        #   the value the level setting is to be set to. Setter function 
        #   responsible for implementing all conseqeunces of change in 
        #   level setting value. NB All setter functions are class methods.
        #
        # Value an iterator that returns the level setting values, with 
        #   first interation returning value for level 1 and each subsequent
        #   call returning value for each successive level. NB iterator 
        #   defined as the return of a function assigned to a corresponding 
        #   global constant.
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

    # Window keypress handler
    #
    # All key presses pass through this handler except when user has 
    # paused game (in which case handled by --_paused_on_key_press-- which 
    # is pushed to the stack temporarily above this method and prevents 
    # propogation of event to this method).
    #
    # Key presses that control ships handled first by handlers on Ship class,
    # event then propogates through this method benignly given that during 
    # game state this handler only enacts a conseqeunce if key pressed is F12.
    def on_key_press(self, symbol, modifiers):
        """Application window key press handler. Overrides inherited method.

        Execution depends on application state:
            If 'game' or 'next level' then only acts on key press of F12 
        which pauses the game.
            If 'instructions' then any key press will return the application 
        to its state prior to entering the 'instructions' state.
            If 'start' or 'end' then key press of 1 or 2 (either top row or 
        number pad) or F1 or F2 will start game for 1 or 2 players whilst 
        key press of escape will exit the application.
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
                self._end_app()
                return
            else:
                return
            self._start_game(players)
            
    # PLAYERS
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
        """Advise game that +player+ has died"""
        self._move_player_to_dead(player)

    def _delete_all_players(self):
        for player in self.all_players:
            player.delete()
        self.players_alive = []
        self.players_dead = []

    @property
    def players_ships(self) -> List[Ship]:
        """Returns list of live Ship objects.
        NB dead or currently resurrecting Players will not be represented.
        """
        ships = []
        for player in self.all_players:
            if player.ship.live:
                ships.append(player.ship)
        return ships

    def _withdraw_players(self):
        for player in self.all_players:
            player.withdraw_from_game()

    # ADD GAME OBJECTS
    def _add_player(self, color: Union['blue', 'red'],
                   avoid: Optional[List[AvoidRect]] = None) -> Player:
        player = Player(game=self, color=color, avoid=avoid)
        self.players_alive.append(player)
        return player
        
    def _set_players(self) -> Player:
        self._delete_all_players()
        player1 = self._add_player(color='blue')
        if self._num_players == 2:
            avoid = [AvoidRect(player1.ship, margin = 2 * player1.ship.width)]
            self._add_player(color='red', avoid=avoid)

    def _add_asteroid(self, avoid: Optional[List[AvoidRect]] = None):
        """Adds asteroid with random rotation and ramdon position, albeit 
        with position avoiding any area represented in +avoid+.
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

    # REFRESH METHOD related methods
    def _asteroid_and_bullet(self, 
                             collision: Tuple[PhysicalSprite, PhysicalSprite],
                             ) -> Union[Bullet, bool]:
        """If +collision+ between Asteroid and Bullet then return Bullet, 
        otherwise return False.
        """
        c = collision
        if isinstance(c[0], Asteroid) and isinstance(c[1], Bullet):
            return c[1]
        elif isinstance(c[0], Bullet) and isinstance(c[1], Asteroid):
            return c[0]
        else:
            return False
        
    def _identify_firer(self, bullet: Bullet) -> Optional[Player]:
        """Return Player responsible for +bullet+"""
        for player in self.all_players:
            if player.control_sys is bullet.control_sys:
                return player

    def _no_asteroids(self) -> bool:
        """Advise if there are any asteroids left"""
        for sprite in PhysicalSprite.live_physical_sprites:
            if isinstance(sprite, Asteroid):
                return False
        return True

    def _check_for_points(self,
                          collision: Tuple[PhysicalSprite, PhysicalSprite]):
        """If +collision+ between Asteroid and Bullet then add one to score 
        of Player responsible for Bullet.
        Only adds to score if ship that fired bullet has not since been 
        destoryed.
        """
        bullet = self._asteroid_and_bullet(collision)
        if bullet:
            firer = self._identify_firer(bullet)
            try:
                firer.add_to_score(1)
            except AttributeError:
                pass

    # REFRESH. Game UPDATE
    # All non-stationary game sprites have PhysicalSprite as a base. The
    # PhysicalSprite class maintains a ---live_physical_sprites--- 
    # attribute that holds a list of all physical sprite instances 
    # that have not subsequently deceased. --_refresh()-- obliges these 
    # live sprites to move by calling each sprite's own refresh method to 
    # which the time since the last call is passed. It is each sprite's 
    # responsiblity to set it's new position given the elapsed time.
    #
    # --_refresh()-- is scheduled, via --_start_refresh--, to be called 
    # 100 times a second.
    #
    # --_refresh()-- is unsheduled by --_stop_refresh()--. 
    #
    # --_refresh()-- is scheduled at the start of each level and unscheduled 
    # at the end of each level and the end of a game.
    #
    # --_refresh()-- is also effectively disabled and enabled by 
    # --_user_pause()-- and --_user_resume()-- which pause and resume the 
    # clock responsible for scheduling calls to --_refresh()--.

    def _refresh(self, dt: float):
        """Update game for passing of +dt+ seconds.

        Checks for collisions between any PhysicalSprite objects. For 
        colliding objects:
            If a Bullet and an Asteroid then identifies player who 
                fired bullet and adds one to player's score.
            Enacts consequence of collision for each object
        If all players dead then moves to end game.
        If no asteroids left then moves to next level
        Otherwise updates position of all PhysicalSprite objects
        """
        collisions = PhysicalSprite.eval_collisions()
        live_physical_sprites = PhysicalSprite.live_physical_sprites
        for c in collisions:
            if c[0] in live_physical_sprites and c[1] in live_physical_sprites:
                self._check_for_points(c)
                c[0].collided_with(c[1])
                c[1].collided_with(c[0])

        if not self.players_alive:
            return pyglet.clock.schedule_once(self._end_game, 1)
        elif self._no_asteroids():
            return self._next_level_page()
        else:
            for sprite in live_physical_sprites:
                sprite.refresh(dt)

    # PAGE AND SOUND CONTROL
    def _decease_game_sprites(self, exceptions: Optional[List[Sprite]] = None,
                              kill_sound=False):
        """Decease all sprites in window save for any +exceptions+.
       
        +excpetions+ list of either specific Sprite instance to exclude 
            or subclass of Sprite in which case all sprites of any subclass 
            will be excluded.
        +kill_sound+ True to stop sound of PhysicalSprites that would 
            otherwise die loudly.
        """
        if kill_sound:
            self._stop_all_sound()
        SpriteAdv.decease_selective(exceptions=exceptions)

    def _start_refresh(self):
        pyglet.clock.schedule_interval(self._refresh, 1/100.0)

    def _stop_refresh(self):
        pyglet.clock.unschedule(self._refresh)

    def _freeze_ships(self):
        for ship in self.players_ships:
            ship.freeze()
    
    def _unfreeze_ships(self):
        for ship in self.players_ships:
            ship.unfreeze()

    def _pause_for_next_level(self):
        """Pause game for purpose of implementing gap between levels"""
        # Clock NOT paused, thereby allowing execution of scheduled calls 
        # including --_next_level()-- scheduled by --_next_level_page()--
        #
        # Sound not stopped, rather bleeds into inter-level pause.
        self._stop_refresh()
        self._freeze_ships()

    def _unpause_for_next_level(self):
        """Resume game for purpose of starting a new level"""
        self._start_refresh()
        self._unfreeze_ships()

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
        """Set 'end' state and set end labels for circumstance 
        dictated by number of players and whether game +escaped+, 
        +completed+ or neither
        """
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

    def _paused_on_key_press(self, symbol, modifiers):
        """Key press handler for when game paused"""
        if symbol == pyglet.window.key.ESCAPE:
            self._user_resume()
            self._end_game(escaped=True)
        elif symbol == pyglet.window.key.F12:
            self._user_resume()
        # return True to prevent event propagating through stack, thereby 
        # limiting user interaction to that provided for by this handler.
        return True

    def _user_pause(self):
        """Pause a live game at the user's request.
        Subsequent user interaction handled by --_paused_on_key_press()--.
        """
        self._stop_all_sound()
        self._freeze_ships()
        CLOCK.pause()  # pause scheduled calls, preventing premature execution
        self.push_handlers(on_key_press=self._paused_on_key_press)
        self._show_instructions_screen(paused=True)
        
    def _user_resume(self):
        """Resume game previously paused at the users request"""
        self._return_from_instructions_screen()
        self.pop_handlers()  # remove pause keypress handler from stack
        CLOCK.resume()
        self._unfreeze_ships()
        self._resume_all_sound()
        
    def _end_app(self):
        self._stop_all_sound()
        self.close()
        self.delete()
    
    # SETTER METHODS for Level Settings (and related methods).
    #
    # Setter functions are only concerned with implementing the 
    # consequence of the new value. This may or may not require the 
    # value to be stored and made available, via a property or otherwise.
    # For example, --_set_ship_speed-- and --_set_ship_rotation_speed-- 
    # directly change any live Ships speeds although also assign the 
    # the new values to instance attributes. These values are then 
    # exposed via properties which allow the Player class access to 
    # the speed values when requesting new ships.
    #
    # Most setter methods, such as --_set_bullet_speed--, do not assign 
    # the value to an instance attribute but rather rather send it 
    # directly to wherever it's required to implement the consequences 
    # of the change.
    
    def _set_level(self, value):
        self._level = value
        self.level_label.update(value)

    def _set_num_asteroids(self, value):
        # NB Number of Asteroids is not stored, rather setter directly 
        # instantiates the required number of asteroids. This requires 
        # that the level settings for --_asteroid_speed--, 
        # --_spawn_limit-- and --_num_per_spawn-- have already been set.
        # This is ensured by the order of the keys in --_settings_map-- 
        # (an OrderedDict) which --_setup_next_level-- iterates through 
        # to enact new level settings.
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

    def _get_field_width(self, border: float) -> int:
        """Return radiation field border width given +border+.
        +border+ total percentage (as float) of window height (or width 
            if higher than wider) to comprise radiation field.
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
            
    def _set_natural_exposure_limit(self, value: int):
        for ship in self.players_ships:
            monitor = ship.control_sys.radiation_monitor
            monitor.set_natural_exposure_limit(value)

    def _set_high_exposure_limit(self, value: int):
        for ship in self.players_ships:
            monitor = ship.control_sys.radiation_monitor
            monitor.set_high_exposure_limit(value)


    def _setup_next_level(self):
        """Assign level settings for next level"""
        for setter_method, iterator in self._settings_map.items():
            setter_method(next(iterator))


    def _play_level(self, first_level=False):
        """Setup next level and set 'game' state"""
        self._setup_next_level()
        if first_level:
            self._start_refresh()
        else:
            self._unpause_for_next_level()
        self.app_state = 'game'

    def _setup_mine_cls(self):
        visible_secs = None if self._num_players == 1 else 2
        Mine._setup_mines(visible_secs=visible_secs)

    def _start_game(self, num_players: int = 1):
        """set/reset game and proceeds to play first level"""
        self._num_players = num_players
        self._setup_mine_cls()
        self._set_settings_map()  # Creates new iterators for level settings
        self._set_players()
        self.set_mouse_visible(False)
        self._play_level(first_level=True)

    def _next_level(self, dt: Optional[float] = None):
        """Play next level after clearing screen of all sprites that should 
        not bleed over.
        """
        self._decease_game_sprites(exceptions=self.players_ships + 
                                   [PickUp, PickUpRed])
        self._play_level()

    def _next_level_page(self):
        """Set next level state, pause and schedule call to play next level.
        Ends game if current level was the last level.
        """
        if self._level == LAST_LEVEL:
            return self._end_game(completed=True)
        self.app_state = 'next_level'        
        self._pause_for_next_level()
        pyglet.clock.schedule_once(self._next_level, 1)

    def _unschedule_calls(self):
        pyglet.clock.unschedule(self._refresh)
        pyglet.clock.unschedule(self._next_level)
        pyglet.clock.unschedule(self._end_game)

    def _end_game(self, dt=None, escaped=False, completed=False):
        """Set end game state and stop player interaction with game.
        
        +escaped+ True if game ended prematurely by user 'escaping'.
        +completed+ True if game ended by way of player(s) completing 
            last level (as opposed to losing all lives).
        """
        self._set_end_state(escaped, completed)
        self._withdraw_players()
        self._decease_game_sprites(kill_sound=True)
        self._unschedule_calls()
        self.set_mouse_visible(True)
        self._num_players = None

    # Event loop to draw to window. Frequency determined by pyglet.
    def on_draw(self):
        """Draws batch corresponding with the curent state.

        Overrides inhertied event handler.
        """
        self.clear()
        for batch in self._state_batches[self.app_state]:
            batch.draw()
        
game_window = Game()  # Create appliation instance
pyglet.app.run()  # Initiate main event loop