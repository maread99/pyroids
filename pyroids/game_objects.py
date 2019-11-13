#! /usr/bin/env python

"""Game Sprite and Weapon Classes.

Defines:
    Ammunition.
    Weapons:
        Fire ammunition.
        Manage ammunition stocks.
    Radiation monitor and gauge.
    Ship:
        Player controllable.
        Fires weapons via a control system.
    Ammunition supply pickups.
    Control System for a player.
        Manages ships, weapons, pickups and radiation monitor.

Global ATTRIBUTES
The following module attributes are assigned default values that can be
overriden by defining an attribute of the same name in a configuration 
file (see pyroids.config.template.py for explanation of each attribute 
and instructions on how to customise values):
    'COLLECTABLE_IN', 'COLLECTABLE_FOR', 'PICKUP_AMMO_STOCKS'    
    'SHIELD_DURATION', 'INITIAL_AMMO_STOCKS', HIGH_VELOCITY_BULLET_FACTOR, 
   
CLASSES:
    Explosion(OneShotAnimatedSprite)  Explosion animation with sound.

    Smoke(Explosion)  Smoke Animation with explosion sound.

    Ship(PhysicalSpriteInteractive)  Blue controllable armed spaceship.

    RedShip(Ship)  Red controllable armed spaceship.

    Asteroid(PhysicalSprite)  Asteroid.

    Ammunition()  Base for ammunition clases.

    Bullet(Ammunition, PhysicalSprite)  Bullet sprite for Blue player, with
        sound.
    BulletRed(Bullet)  Bullet sprite for Red player, with sound.

    BulletHighVeloicty(Bullet)  High Velocity Bullet sprite, with sound.
    BulletHighVeloictyRed(Bullet)  High Velocity Bullet sprite, with sound.

    Starburst(StaticSourceMixin)  Explosion from which bullets fire out at 
        regular angular intervals.

    SuperLaserDefence(Ammunition, Starburst)
    SuperLaserDefenceRed(SuperLaserDefence)

    Firework(Bullet)  Large Bullet explodes into Starburst
    FireworkRed(Firework)  Large Bullet explodes into Starburst.

    Mine(Ammunition, PhysicalSprite)  Mine explodes into Starburst after 
        specified time.
    MineRed(Mine)  Mine explodes into Starburst after specified time.

    Shield(Ammunition, PhysicalSprite)  Invincible (almost) shield for Ship.
    ShieldRed(Shield)  Invincible (almost) shield for Ship.

    Weapon()  Base class for creating a weapon class that fires instances of 
        a different Ammunition class for each player.

    Cannon(Weapon)  Fires bullets.

    HighVelocityCannon(Weapon)  Fires high velocity bullets.

    FireworkLauncher(Weapon)  Fires fireworks.

    SLD_Launcher(Weapon)  Fires super laser defence.

    MineLayer(Weapon)  Lays mines.

    ShieldGenerator(Weapon)  Raises Shields.

    RadiationGauge(Sprite)  Displays radiation level.
    RadiationGaugeRed(RadiationGauge)  Displays radiation level for red 
        player.

    RadiationMonitor(StaticSourceMixin)  Manages radiation level.
    RadiationMonitorRed(RadiationMonitor)  Manages red player's radiation 
        level.

    ControlSystem()  Control system for a player.

    PickUp(PhysicalSprite)  Ammunition pickup.
    PickUpRed(PickUp)  Ammunition pickup for red player.
"""

import random
from copy import copy
from math import floor
from typing import Optional, Union, Tuple, Type, List
from collections import OrderedDict

import pyroids
import pyglet
from pyglet.sprite import Sprite
from pyglet.image import Animation, Texture
from pyglet.media import StaticSource

from .labels import StockLabel
from .lib.pyglet_lib.sprite_ext import (PhysicalSprite, 
                                        PhysicalSpriteInteractive,
                                        OneShotAnimatedSprite, 
                                        load_image, load_image_sequence,
                                        anim, vector_anchor_to_rotated_point, 
                                        InRect)
from .lib.pyglet_lib.audio_ext import StaticSourceMixin, load_static_sound

class Ammunition(object):
    """Mixin.

    Class ATTRIUBTES
    ---img_pickup---  Ammo pick-up image.
    ---img_stock---  Ammo stocks image.
    
    Subclass Interface
    Inheriting classes should define the Class Attributes.
    """
    
    img_pickup: Union[Texture, Animation]
    img_stock: Union[Texture, Animation]

class Bullet(Ammunition, PhysicalSprite):
    """PhysicalSprite with bullet image and firing bullet sound.
    
    Bullet killed by colliding with any of Asteroid, Ship, Shield, 
    Mine collectable PickUp or game area boundary.
    """
    img = load_image('bullet.png', anchor='center')
    snd = load_static_sound('nn_bullet.wav')

    img_pickup = img
    img_stock = img
    
    def __init__(self, control_sys, *args, **kwargs):
        """
        ++control_sys++:  ControlSystem instance responsible for weapon 
        that fired bullet.
        """
        self.control_sys = control_sys
        kwargs.setdefault('at_boundary', 'kill')
        super().__init__(*args, initial_rotation_speed=0,
                         rotation_cruise_speed=0, **kwargs)
        
    def collided_with(self, other_obj):
        if isinstance(other_obj, (Asteroid, Ship, Shield, Mine)):
            self.kill()
        elif isinstance(other_obj, PickUp) and not other_obj.dropping:
            self.kill()

class BulletRed(Bullet):
    snd = load_static_sound('mr_bullet.wav')
        
    
class BulletHighVelocity(Bullet):
    """PhysicalSprite with high velocity bullet image and firing 
    high velocity bullet sound for Blue ship.

    NB Does not define bullet speed.
    """
    snd = load_static_sound('nn_hvbullet.wav')
    img = load_image('bullet_high_velocity.png', anchor='center')
    img_pickup = img
    img_stock = load_image('bullet_high_velocity.png', anchor='origin')

class BulletHighVelocityRed(Bullet):
    """PhysicalSprite with high velocity bullet image and firing 
    high velocity bullet sound for Red ship.

    NB Does not define bullet speed.
    """
    snd = load_static_sound('mr_hvbullet.wav')
    img = load_image('bullet_high_velocity_red.png', anchor='center')
    img_pickup = img
    img_stock = load_image('bullet_high_velocity_red.png', anchor='origin')

class Starburst(StaticSourceMixin):
    """Explosion from which bullets fire out at regular intervals.
    
    Fires multiple bullets at regular angular intervals from a point with 
    accompanying explosion sound. Intended to be instantiated from 
    Ammunition classes that require a Starburst effect.

    Class ATTRIBUTES
    ---live_starbursts---  List of all instantiated instances that have 
        not subsequently deceased.

    Class METHODS
    ---stop_all_sound---  Stop any sound being played by any live instance.
    ---resume_all_sound---  Resume any sound by any live instance 
        that had been previously stopped.
    """
    
    snd = load_static_sound('gun_shot_shortened.wav')
    live_starbursts = []

    @classmethod
    def stop_all_sound(cls):
        for starburst in cls.live_starbursts:
            starburst.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        for starburst in cls.live_starbursts:
            starburst.resume_sound()

    def __init__(self, x: int, y: int, batch: pyglet.graphics.Batch,
                 control_sys, 
                 group: pyglet.graphics.Group = pyglet.graphics.null_group,
                 num_bullets: int = 6, bullet_speed: int = 200, 
                 direction: Union[int, 'random'] = 'random',
                 distance_from_epi: int = 0, sound=True):
        """
        ++num_bullets++ Number of bullets to be simultanesouly fired at 
        ++bullet_speed++ as if from origin (++x++, ++y++) although actually 
        starting their lives at ++distance_from_epi++ from origin. 
        
        ++direction++ 0 <= degrees < 360 or 'random'.
            0 will fire one bullet to the 'right' and others at regular 
            angular intervals. Any other value will effectively add 
            ++direction++ to what would have been each bullet's direction 
            if ++direction++ were to have been 0 (positive clockwise). 
            'random' (default) will add a random value to what would 
            otherwise have been each bullet's direction if ++direction++ 0.
        ++control_sys++ ControlSystem instance to which bullets to be 
            attributable.
        ++batch++ Batch to which bullets to be drawn.
        ++group++ Rendering group to which bullets to be included.
        """
        self.x = x
        self.y = y
        self.control_sys = control_sys
        self.num_bullets =  num_bullets
        self.batch = batch
        self.group = group
        self.bullet_speed = bullet_speed
        self.direction = direction if direction != 'random'\
           else random.randint(0, 360//self.num_bullets)
        self.distance_from_epi = distance_from_epi
        
        self.live_starbursts.append(self)
                
        self._starburst()
        super().__init__()
        
        # Decease starburst when sound ends
        pyglet.clock.schedule_once(self.die, self.snd.duration)
        
    def _bullet_directions(self) -> range:
        for direction in range(0, 360, (360//self.num_bullets)):
            yield direction + self.direction

    def _bullet_birth_position(self, direction: int) -> Tuple[int, int]:
        if not self.distance_from_epi:
            return (self.x, self.y)
        
        x, y = vector_anchor_to_rotated_point(self.distance_from_epi,
                                              0, direction)
        x += self.x
        y += self.y
        return (x, y)
    
    def _starburst(self):
        for direction in self._bullet_directions():
            x, y = self._bullet_birth_position(direction)
            Bullet(self.control_sys, x=x, y=y, 
                   batch=self.batch, group=self.group,
                   sound=False, initial_rotation=direction, 
                   initial_speed=self.bullet_speed)

    def die(self, dt: Optional[float] = None):
        self.live_starbursts.remove(self)

class SuperLaserDefence(Ammunition, Starburst):
    """Ammunitionises Starburst for SLD_Launcher for Blue player."""

    img_stock = load_image('sld_stock.png', anchor='origin')
    img_pickup = load_image('sld_stock.png', anchor='center')
    snd = load_static_sound('nn_superlaserdefence.wav')

class SuperLaserDefenceRed(SuperLaserDefence):
    snd = load_static_sound('mr_superdefence.wav')

class Firework(Bullet):
    """Large Bullet explodes into Starburst.

    Firework explodes on the earlier of colliding, reaching boundary or 
    travelling a specified distance.
    """

    img = load_image('firework.png', anchor='center')
    snd = load_static_sound('nn_firework.wav')
    img_pickup = img
    img_stock = img

    def __init__(self, explosion_distance: int, 
                 num_starburst_bullets=12, 
                 starburst_bullet_speed=200,
                 **kwargs):
        """
        ++explosion_distance++ Distance, in pixels, before firework 
            will explode.
        ++num_starburst_bullets++ Number of bullets Starburst to comprise of.
        ++starburst_bullet_speed++ Starburst bullet speed.

        All other kwargs as for Bullet class.
        """
        self.explosion_distance = explosion_distance
        self.num_starburst_bullets = num_starburst_bullets
        self._starburst_bullet_speed = starburst_bullet_speed
        super().__init__(**kwargs)
        self._set_fuse()
                     
    def _starburst(self):
        # Directs starburst bullets so as to minimise possibility that 
        # they will hit a stationary ship from which Firework launched
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self.control_sys,
                  num_bullets=self.num_starburst_bullets, 
                  bullet_speed=self._starburst_bullet_speed,
                  direction=self.control_sys.ship.rotation + 15)

    def _fused(self, dt):
        self.kill()

    def kill(self):
        self._starburst()
        super().kill()

    def _set_fuse(self):
        fuse = self.explosion_distance / self.speed
        self.schedule_once(self._fused, fuse)

    def die(self):
        # prevent sound being cut short when fuse short
        super().die(stop_sound=False)

class FireworkRed(Firework):
    snd = load_static_sound('mr_firework.wav')

class Mine(Ammunition, PhysicalSprite):
    """Mine explodes into Starburst after specified time.

    Mine shows a countdown to 0 whilst playing 'tick tock' sound. Mine 
    can be visible throughout life or only for the last ++visible_secs++.
    Explodes into Starburst on earlier of reaching 0 or being shot by a 
    Bullet.
    
    Class METHODS
    ---setup_mines()---  Define class default settings.
    """
    
    img = anim('mine.png', 1, 9, frame_duration=1)
    img_pickup = img.frames[-1].image
    img_stock = img_pickup
    snd = load_static_sound('nn_minelaid.wav')

    _visible_secs: Optional[int]
    _mines_setup = False

    @classmethod
    def setup_mines(cls, visible_secs: Optional[int] = None):
        """Override class defaults.
        
        ++visible_secs++ Final number of seconds during which mine to 
            be visible. Pass None if mine to be visible throughout life.
        """
        cls._visible_secs = visible_secs
        cls._mines_setup = True

    @classmethod
    def _anim(cls, fuse_length) -> Animation:
        """Return 'Coundown Mine' animation object showing number on 
        top of mine which counts down from +fuse_length+ to 0 over 
        +fuse_length+ seconds. No sound.
        """
        anim = copy(cls.img)
        anim.frames = anim.frames[9 - fuse_length:]
        return anim

    def __init__(self, x: int, y: int, batch: pyglet.graphics.Batch, 
                 fuse_length: int, control_sys, 
                 visible_secs: Optional[int] = None, 
                 num_starburst_bullets=12, 
                 bullet_speed=200, **kwargs):
        """
        ++x++ Mine x position.
        ++y++ Mine y position.
        ++batch++ Batch to which mine will be drawn.
        ++fuse_length++ Mine life span in seconds. Maximum 9.
        ++visible_secs++ Number of seconds during which mine will be visible 
            at end of a natural life. If not passed then will take any class 
            default defined by ---setup_mines--- or otherwise will be 
            visible throughout life.
        ++num_starburst_bullets++ Number of Bullets that Starburst is to 
            comprise of.
        ++bullet_speed++ Speed of Starburst bullets.
        ++control_sys++ ControlSystem instance to which Starburst's Bullets 
            to be attributed.
        """
        if not self._mines_setup:
            self.setup_mines()
        if visible_secs is not None:
            self._visible_secs = visible_secs
        
        assert fuse_length < 10
        self.fuse_length = fuse_length if fuse_length > 1 else 1
        self.control_sys = control_sys
        self.num_starburst_bullets = num_starburst_bullets
        self.bullet_speed = bullet_speed

        super().__init__(img=self._anim(fuse_length), x=x, y=y, batch=batch, 
                         **kwargs)

        if self._visible_secs and fuse_length > self._visible_secs:
            self._hide_anim_for(fuse_length - self._visible_secs)

    def on_animation_end(self):
        """Event handler."""
        self.kill()

    def _hide_anim_for(self, invisible_secs):
        self.visible = False
        self.schedule_once(self._show_anim, invisible_secs)

    def _show_anim(self, dt: Optional[float] = None):
        self.visible = True

    def collided_with(self, other_obj: PhysicalSprite):
        if isinstance(other_obj, Bullet):
            self.kill()
    
    def refresh(self, dt: float):
        # As object stationary, overrides to avoid superfluous execution
        pass

    def kill(self):
        """Instantiate Starburst with origin on the mine's position."""
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self.control_sys,
                  num_bullets=self.num_starburst_bullets, 
                  bullet_speed=self.bullet_speed)
        super().kill()

class MineRed(Mine):
    snd = load_static_sound('mr_minelaid_ext.wav')

class Shield(Ammunition, PhysicalSprite):
    """Ship Shield.
    
    Shield invincible save for against other shields. Plays sound on 
    raising shield. Flashes during final 25% of natural life, with 
    flash frequency doubling over last 12.5%.

    PROPERITES
    --ship-- Ship being shielded
    """
    
    img = load_image('shield_blue.png', anchor='center')
    snd = load_static_sound('nn_shieldsup.wav')
    img_stock = load_image('shield_blue_20.png', anchor='origin')
    img_pickup = load_image('shield_pickup_inset_blue.png', anchor='center')

    def __init__(self, ship, duration: int = 10, **kwargs):
        """
        ++ship++ Ship to be shielded.
        ++duration++ Shield duration.
        """
        self._ship = ship
        super().__init__(**kwargs)
        self.powerdown_duration = duration//4
        self.powerdown_phase2_duration = duration//8
        solid_shield_duration = duration - self.powerdown_duration
        self.schedule_once(self._powerdown_initial, solid_shield_duration)
        
    @property
    def ship(self):
        return self._ship

    def refresh(self, dt: float):
        """Overrides to place object to position of ship being shielded."""
        self.update(x=self.ship.x, y=self.ship.y)

    def shield_down(self, dt: Optional[float] = None):
        self.die()
        
    def _powerdown_final(self, dt: Optional[float] = None):
        self.flash_start(4)
        self.schedule_once(self.shield_down, self.powerdown_phase2_duration)

    def _powerdown_initial(self, dt: Optional[float] = None):
        self.flash_start(2)
        duration = self.powerdown_duration - self.powerdown_phase2_duration
        self.schedule_once(self._powerdown_final, duration)
        
    def collided_with(self, other_obj):
        if isinstance(other_obj, Shield):
            self.ship.kill() # self killed indirectly via ship being killed.
            
class ShieldRed(Shield):
    img = load_image('shield_red.png', anchor='center')
    snd = load_static_sound('mr_shieldsup.wav')
    img_stock = load_image('shield_red_20.png', anchor='origin')
    img_pickup = load_image('shield_pickup_inset_red.png', anchor='center')
    
class Weapon(object):
    """Base class to create weapons that will be appended to a 
    ControlSystem class.
    
    For a specific Ammunition class:
        Handlers fire requests, providing for following circumstances:
            No ammunition.
            Shield raised and weapon cannot fire through shield.
            Firing an instance of ammunition.
        Manages ammunition stock levels.
        Creates and maintains a StockLabel offering graphical representation 
            of current stock level.

    PROPERTIES
    --stock--  Current ammunition rounds in stock.
    --max_stock--  Maximum number of ammunition rounds weapon can stock.
    --stock_label--  StockLabel representing weapon's ammunition stock.

    Instance METHODS:
    --set_stock(num)--  Set stock to +num+ rounds.
    --add_to_stock(num)--  Add +num+ rounds to stock.
    --subtract_from_stock(num)--  Subtract +num+ rounds from stock.
    --fire()--  Handle request to fire a single instance of ammunition.
    
    SUBCLASS INTERFACE
    Subclass should define the following class attributes if require values 
    other than the defaults:
    ---ammo_cls---  Dictionary with keys as possible player colours and 
        values as the weapon's ammunition Type for corresponding player. 
        Implemented on this base class to provide for Bullet and 
        BulletRed ammunition classes for 'blue' and 'red' players 
        respectively. Implement on subclass if weapon fires alternative 
        ammunition class.
    ---fire_when_sheild_up---  Boolean defines if weapon can be fired 
        when the ++control_sys++ has the shield raised. Implemented on base 
        class as 'False'. Implement on subclass as True if weapon can be 
        fired when shield raised.

    Subclass should implement the following methods if corresponding 
    functionality requried.
    --_ammo_kwargs(**kwargs)--  Implement on subclass to return a dictionary 
        of kwargs to be passed to the ammunition class in order to fire a 
        single instance of ammunition. Should accommodate incorporating any 
        received **kwargs.
    --_shield_up()--  Handler. Will be called if weapon cannot be fired 
        when shield raised and receive request to fire weapon when shield 
        raised.
    --_no_stock()--  Handler. Called if receive request to fire when out of 
        ammunition.
    --die()--  Subclass should implement to perform any end-of-life tidy-up 
        operations, for example cancelling any scheduled calls. Called by 
        ++control_sys++ as part of control system's end-of-life. NB there are 
        various methods on the ControlSystem class that aid getting kwargs for
        ammunition classes.
    """
    
    ammo_cls = {'blue': Bullet,
                'red': BulletRed}

    fire_when_shield_up = False

    def __init__(self, control_sys, initial_stock: int = 0,
                 max_stock: int = 9):
        """
        ++control_sys++ ControlSystem instance which controls the weapon and 
            in reverse which weapon can call on for guidance.
        ++initial_stock++  Initial number of ammunition rounds.
        ++max_stock++ Maximum number of ammunition rounds that weapon can stock.
        """
        self.control_sys = control_sys
        self._AmmoCls = self.ammo_cls[control_sys.color]
        self._max_stock = max_stock
        self._stock = min(initial_stock, max_stock)
        self._stock_label = StockLabel(image = self._AmmoCls.img_stock,
                                       initial_stock=self._stock,
                                       style_attrs = {'color': (255, 255, 255, 255)})
        
    @property
    def stock(self) -> int:
        """Current number of ammunition rounds in stock."""
        return self._stock

    @property
    def max_stock(self) -> int:
        """Maximum number of ammunition rounds weapon can stock."""
        return self._max_stock

    @property
    def stock_label(self) -> StockLabel:
        """StockLabel representing weapon's ammunition stock."""
        return self._stock_label
            
    def _update_stock(self, num: int):
        assert not num < 0
        num = num if num < self.max_stock else self.max_stock
        self._stock = num
        self._stock_label.update(self._stock)

    def set_stock(self, num: int):
        """Change stock to +num+"""
        self._update_stock(num)

    def _change_stock(self, num: int):
        """Change stock level.

        +num+ Change in stock levels, +ve to increase stock, -ve to reduce.
        """
        num = self.stock + num
        return self._update_stock(num)

    def add_to_stock(self, num: int):
        """+num+ Number of ammunition rounds to add to stock."""
        self._change_stock(num)

    def subtract_from_stock(self, num: int):
        """+num+ Reduce ammunition stock by +num+ rounds (positive int)."""
        assert not num < 0
        self._change_stock(-num)

    def _shield_up(self):
        """Not implemented.
        
        Implement on subclass to handle requests to fire whilst shield up.
        """
        pass

    def _no_stock(self):
        """Not implemented.
        
        Implement on subclass to handle requests to fire when no stock.
        """
        pass

    def _ammo_kwargs(self, **kwargs) -> dict:
        """Implement on subclass to return dictionary of kwargs to 
        instantiate one instance of associated ammunition class."""
        return kwargs

    def _fire(self, **kwargs):
        """Fire one instance of ammunition."""
        kwargs = self._ammo_kwargs(**kwargs)
        return self._AmmoCls(**kwargs)

    def fire(self, **kwargs):
        """Fire one instance of stock or handle if unable to fire."""
        if not self.fire_when_shield_up and self.control_sys.shield_up:
            return self._shield_up()
        if not self._stock:
            return self._no_stock()
        else:
            self.subtract_from_stock(1)
            return self._fire(**kwargs)

    def die(self):
        """Not implemented.
        
        Implement on subclass to perform any tidy-up operations.
        """
        pass

class Cannon(Weapon):
    """Cannon that fires standard bullets.

    Cannon automatically reloads. Cannot be fired through shield.
    
    METHODS
    --set_reload_rate()--  Set time to reload a round of ammunition.
    """
    
    def __init__(self, *args, reload_rate: Union[float, int] = 2, **kwargs):
        """++reload_rate++ Seconds to reload one round of ammunition."""
        super().__init__(*args, **kwargs)
        self.set_reload_rate(reload_rate)

    def set_reload_rate(self, reload_rate: Union[float, int]):
        """++reload_rate++ Seconds to reload one round of ammunition."""
        pyglet.clock.unschedule(self._auto_reload)
        pyglet.clock.schedule_interval(self._auto_reload, reload_rate)

    def _ammo_kwargs(self):
        # Relies on control system to evaluate bullet kwargs
        return self.control_sys.bullet_kwargs()

    def _auto_reload(self, dt):
        self.add_to_stock(1)

    def die(self):
        pyglet.clock.unschedule(self._auto_reload)
        super().die()

class HighVelocityCannon(Weapon):
    """Cannon that fires High Velocity Bullets. 
    
    Cannot be fired through shield.
    """

    ammo_cls = {'blue': BulletHighVelocity,
                'red': BulletHighVelocityRed}

    def __init__(self, *args, bullet_speed_factor=3, **kwargs):
        """
        ++bullet_speed_factor++ High Velocity Bullet speed as multiple 
        of standard bullet speed.
        """
        super().__init__(*args, **kwargs)
        self._factor = bullet_speed_factor

    def _ammo_kwargs(self):
        # Relies on control system to evaluate bullet kwargs
        u = self.control_sys.bullet_initial_speed(factor=self._factor)
        kwargs = self.control_sys.bullet_kwargs(initial_speed=u)
        return kwargs

class FireworkLauncher(Weapon):
    """Fires fireworks.
    
    Cannot be fired through shield.

    PROPERTIES
    --margin--  Minimum distance, in pixels, from centre of associated ship 
        that a Firework can appear without immediately colliding with ship.
    """

    ammo_cls = {'blue': Firework,
                'red': FireworkRed}

    def __init__(self, *args, dflt_explosion_distance=200,
                 dflt_num_bullets: Optional[int] = None, **kwargs):
        """
        ++dflt_explosion_distance++ Default for distance, in pixels, a 
            firework will travel before exploding naturally (can be overriden 
            for any particular firework by passing +explosion_distance+ 
            to --fire()--).
        ++dflt_num_bullets++ Default for number of bullets that the starburst 
            will comprise of when a firework explodes (can be overriden 
            for any particular firework by passing +num_bullets+ to 
            --fire()--). If not passed then default takes the default number 
            of starburst bullets defined on the ++control_sys++.
        """
        super().__init__(*args, **kwargs)
        self._dflt_exp_dist = dflt_explosion_distance
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
        
    @property
    def margin(self):
        return (self.control_sys.ship.width + Firework.img.width)//2 + 1

    def _ammo_kwargs(self, **kwargs) -> dict:
        u = self.control_sys.bullet_initial_speed(factor=2)
        kwargs = self.control_sys.bullet_kwargs(initial_speed=u, 
                                                 margin=self.margin, 
                                                 **kwargs)
        kwargs.setdefault('explosion_distance', self._dflt_exp_dist)
        kwargs.setdefault('num_starburst_bullets', self._dflt_num_bullets)
        kwargs.setdefault('starburst_bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs
        
    def fire(self, **kwargs):
        """Keyword argument options can include the following, both of which 
        will take default values (see constructor documentation) if not 
        passed:
        +explosion_distance+ Distance, in pixels, the firework will travel 
            before exploding naturally.
        +num_bullets+ Number of bullets that the starburst will comprise of 
            when the firework explodes.
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)

class SLD_Launcher(Weapon):
    """Super Laser Defence Launcher.
    
    Fires starbursts centered on the ship with the bullets first appearing 
    at the appearing at the ship's periphery. Has effect of bullets being 
    fired from ship in 'all directions'.

    Cannot be fired through shield.
    """

    ammo_cls = {'blue': SuperLaserDefence,
                'red': SuperLaserDefenceRed}
    
    def __init__(self, *args, dflt_num_bullets: Optional[int] = None, 
                 **kwargs):
        """
        ++dflt_num_bullets++ Default for number of bullets starbursts will 
            comprise of (can be overriden for any particular SLD by passing
            +num_bullets+ to --fire()--). If not passed then default takes 
            the default number of starburst bullets defined on the 
            ++control_sys++.
        """
        super().__init__(*args, **kwargs)
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
        
    def _ammo_kwargs(self, **kwargs):
        kwargs = self.control_sys.ammo_base_kwargs()
        kwargs.setdefault('control_sys', self.control_sys)
        kwargs.setdefault('num_bullets', self._dflt_num_bullets)
        kwargs['distance_from_epi'] = self.control_sys.bullet_margin
        kwargs.setdefault('bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs

    def fire(self, **kwargs):
        """Keyword argument options can include:
        +num_bullets+ Number of bullets that the super laser defence 
            starburst will comprise of. If not passed then will take 
            default value (see constructor documentation).            
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)

class MineLayer(Weapon):
    """Lays mines.
    
    Mines can be laid whilst shield raised.
    """
    
    ammo_cls = {'blue': Mine,
                'red': MineRed}

    fire_when_shield_up = True

    def __init__(self, *args, dflt_fuse_length=5,
                 dflt_num_bullets: Optional[int] = None, **kwargs):
        """
        ++dflt_fuse_length++ Default number of seconds after which mine will 
            explode naturally (can be overriden for any particular mine by 
            passing +fuse_length+ to --fire()--).
        ++dflt_num_bullets++ Default for number of bullets that starbursts 
            of exploding mines will comprise of (can be overriden for any 
            particular mine by passing +num_starburst_bullets+ to --fire()--).
            If not passed then default takes the default number of starburst 
            bullets defined on the ++control_sys++.
        """
        super().__init__(*args, **kwargs)
        self._dflt_fuse_length = dflt_fuse_length
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
    
    def _ammo_kwargs(self, **kwargs) -> dict:
        for kw , v in self.control_sys.ammo_base_kwargs().items():
            kwargs[kw] = v
        kwargs.setdefault('control_sys', self.control_sys)
        kwargs.setdefault('fuse_length', self._dflt_fuse_length)
        kwargs.setdefault('num_starburst_bullets', self._dflt_num_bullets)
        kwargs.setdefault('bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs
        
    def fire(self, **kwargs):
        """Keyword argument options can include the following, both of which 
        will take default values (see constructor documentation) if not 
        passed:
        +fuse_length+ Seconds after which mine will explode naturally.
        +num_starburst_bullets+ Number of bullets that will be fired out by 
            exploding mine.
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)

class ShieldGenerator(Weapon):
    """Raises shield when fired.
    
    Only one shield can be generated at a time.
    
    PROPERTIES
    --shield_raised-- True if shield raised, otherwise False.
    
    METHODS
    --lower_shield()-- Lower any raised shield.
    """
    
    ammo_cls = {'blue': Shield,
                'red': ShieldRed}

    # fire_when_shield_up defined as False on base class. Ensures only one 
    # shield can be raised at any time.

    def __init__(self, *args, dflt_duration=5, **kwargs):
        """
        ++dflt_duration++ Default shield duration in seconds.
        """
        self._dflt_duration = dflt_duration
        self._current_shield = None
        super().__init__(*args, **kwargs)
                        
    def _ammo_kwargs(self, **kwargs) -> dict:
        for kw , v in self.control_sys.ammo_base_kwargs().items():
            kwargs[kw] = v
        kwargs.setdefault('ship', self.control_sys.ship)
        kwargs.setdefault('duration', self._dflt_duration)
        return kwargs
        
    def fire(self, **kwargs):
        """Keyword argument options can include:
        +duration+ Shield duaration in seconds. If not passed then duration 
            will take default value (see constructor documentation).
        """
        funcs = [self._shield_lowered]
        if 'on_die' in kwargs:
            funcs.append(copy(kwargs['on_die']))
        kwargs['on_die'] = lambda: [ f() for f in funcs ]
        self._current_shield = super().fire(**kwargs)

    @property
    def shield_raised(self) -> bool:
        """True if shield raised, otherwise False."""
        if self._current_shield is None:
            return False
        else:
            return True
        
    def _shield_lowered(self):
        self._current_shield = None

    def lower_shield(self):
        """Lower any raised shield."""
        if self._current_shield is not None:
            self._current_shield.die()


class RadiationGauge(Sprite):
    """8 stage colour radiation guage.
    
    METHODS
    --reset()--  Reset gauge to 0.

    PROPERTIES
    --reading-- Read/Write. Current reading (0 through 7)
    --max_reading-- Maximum reading accommodated.
    """
    
    img_seq = load_image_sequence('rad_gauge_r2l_?.png', 8)
    
    def __init__(self, *args, **kwargs):
        super().__init__(self.img_seq[0], *args, **kwargs)
        self._reading = 0
        self._max_reading = len(self.img_seq) - 1

    @property
    def max_reading(self):
        """Maximum gauge reading accommodated."""
        return self._max_reading

    @property
    def reading(self):
        """Current gauge reading."""
        return self._reading

    @reading.setter
    def reading(self, value: int):
        """
        +value+ Integer from 0 (zero raditation detected) to 7 (maximum 
            radiation level).
        """
        self._reading = min(floor(value), self._max_reading)
        self.image = self.img_seq[self._reading]
                
    def reset(self):
        """Reset gauge to 0."""
        self.reading = 0

class RadiationGaugeRed(RadiationGauge):
    
    img_seq = load_image_sequence('rad_gauge_l2r_?.png', 8)

    
class RadiationMonitor(StaticSourceMixin):
    """Monitors, displays and mangages a Ship's radiation exposure.

    Offers:
        Continuous evaluation of a ship's radiation exposure
        Continuous updating of a RadiationGauge to display exposure.
        Radiation field definition as rectangular area of clean space
            with all other space considered dirty. Ship exposed to 
            background radiation when in clean space, and high level 
            radiation when in dirty space.
        Ship exposure limits can be set at any time.
        Audio warning when exposure reaches 70% of limit.
        On reaching exposure limit plays 'last words' then requests 
            control system kill ship. Give ship a last minute repreive 
            if monitor reset before last words have finished being spoken.
            
    Class creates the radiation guage object which is assigned to attribute 
    --gauge--. Client is responsible for positioning gauge and attaching 
    it to any batch and/or group. This can be done via the gauge's 'x', 'y', 
    'batch' and 'group' attributes (gauge based on Sprite).

    ATTRIBUTES
    --gauge--  RadiationGauge (Sprite). 

    PROPERTIES
    --exposure--  Read/Write. Current exposure level

    METHODS
    --set_natural_exposure_limit()--  Set background radiation exposure limit.
    --set_high_exposure_limit()--  Set high level radiation exposure limit.
    --start_monitoring--  Start monitoring.
    --halt()--  Stop monitoring.
    --reset()--  Stop existing processes and reset monitor (optional) for new 
        radiation field data.
    """
    
    warning = load_static_sound('nn_radiation_warning.wav')
    last_words = load_static_sound('nn_too_much_radiation.wav')
    
    def __init__(self, control_sys, cleaner_space: Optional[InRect] = None,
                 nat_exp_limit=68, high_exp_limit=20):
        """
        ++control_sys++ ControlSystem instance responsible for monitor.
        ++cleaner_space++ InRect representing clean space. All other space 
            considered dirty. If not passed or None then all space assumed 
            dirty. Can be subsequently set via --reset()--.
        ++nat_exp_limit++ Limit of continuous natural background radiation 
            exposure, in seconds.
        ++high_exp_limit++ Limit of continuous high level radiation exposure, 
            in seconds.
        """
        super().__init__(sound=False)
        self.control_sys = control_sys
        self.gauge = self._get_gauge()
        
        self._exposure_level = 0
        self._exposure_limit = self.gauge.max_reading
        self._frequency = 0.5 # monitor update frequency
        
        self._cleaner_space = cleaner_space  # Also set by --reset()--
        
        self._nat_exposure_increment: int
        self.set_natural_exposure_limit(nat_exp_limit)
        self._high_exposure_increment: int
        self.set_high_exposure_limit(high_exp_limit)
        
        self._warning_level = self._exposure_limit * 0.7
    
    def _get_gauge(self):
        return RadiationGauge()
                
    def set_natural_exposure_limit(self, limit: int):
        """Set limit of natural background radiation explosure.

        ++limit++ Limit of continuous background radiation exposure in 
        seconds.
        """
        steps = limit / self._frequency
        self._nat_exposure_increment = self._exposure_limit / steps

    def set_high_exposure_limit(self, limit: int):
        """Set limit of high level radiation explosure.
        
        ++limit++ Limit of continuous high level radiation exposure in 
        seconds.
        """
        steps = limit / self._frequency
        self._high_exposure_increment = self._exposure_limit / steps

    def _warn(self):
        self.sound(self.warning)

    def _play_last_words(self):
        self.sound(self.last_words)

    def __kill_ship(self, dt):
        self.control_sys.ship.kill()

    def _kill_ship(self):
        self._play_last_words()
        self._stop_monitoring()
        pyglet.clock.schedule_once(self.__kill_ship, self.last_words.duration)
                
    def _in_high_rad_zone(self) -> bool:
        """Return True if ship in dirty space, False if ship in clean 
        space.
        """
        if self._cleaner_space is None:
            return True
        ship_pos = (self.control_sys.ship.x, self.control_sys.ship.y)
        return not self._cleaner_space.inside(ship_pos)

    @property
    def exposure(self):
        """Current exposure level."""
        return self._exposure_level

    @exposure.setter
    def exposure(self, value: int):
        """Set exposure level.
        
        +value+ New exposure level. Will be adjusted to bounds of 0 through 
            maximum exposure limit.
        """
        value = min(value, self._exposure_limit)
        value = max(value, 0)
        self._exposure_level = value
        self.gauge.reading = value

    def _increment_high_exposure(self):
        self.exposure += self._high_exposure_increment

    def _increment_nat_exposure(self):
        self.exposure += self._nat_exposure_increment
    
    def _update(self, dt: float):
        prev = self.exposure
        if self._in_high_rad_zone():
            self._increment_high_exposure()
        else:
            self._increment_nat_exposure()
        new = self.exposure
        if new >= self._exposure_limit:
            self._kill_ship()
        elif (prev < self._warning_level) and (new >= self._warning_level):
            self._warn()
        
    def _stop_monitoring(self):
        pyglet.clock.unschedule(self._update)

    def start_monitoring(self):
        pyglet.clock.schedule_interval(self._update, self._frequency)

    def halt(self):
        """Stop monitoring."""
        self._stop_monitoring()
        self.stop_sound()
        pyglet.clock.unschedule(self.__kill_ship)

    def reset(self, cleaner_space: Optional[InRect] = None):
        """Stop existing processes and reset monitor.

        ++cleaner_space++ InRect representing clean space. All other space 
            considered dirty. If not passed or None then all space assumed 
            dirty.
        """
        self.halt()
        self.exposure = 0
        self.gauge.reset()
        if cleaner_space is not None:
            self._cleaner_space = cleaner_space
        self.start_monitoring()

class RadiationMonitorRed(RadiationMonitor):
    
    warning = load_static_sound('mr_radiation_warning.wav')
    last_words = load_static_sound('mr_too_much_radiation.wav')

    def _get_gauge(self):
        return RadiationGaugeRed()


class Explosion(OneShotAnimatedSprite):
    """One off animated explosion with sound."""

    img = anim('explosion.png', 2, 8)
    snd = load_static_sound('nn_explosion.wav')
        
class Smoke(Explosion):
    """One off animated smoke cloud, with explosion sound."""
    img = anim('smoke.png', 1, 8)
 
class Ship(PhysicalSpriteInteractive):
    """Blue Player's Ship.
    
    Ship can move and fire weapons. Default controls via keyboard keys:
        I - thrust forwards.
        J - rotate ship anticlockwise.
        L - rotate ship clockwise.
        K - shield up.
        ENTER - fire.
        BACKSPACE - rapid fire.
        RCTRL- super laser defence.
        7, 8, 9 - fire firework to explode after travelling 200, 500, 900 
            pixels respectively.
        M, COMMA, PERIOD - lay mine to explode in 1, 3, 6 seconds 
            respectively.

    class METHODS
    ---set_controls()--- to set ship controls (to alternative from default). 
        NB ship controls can also be set via configuration file.
    """

    img = load_image('ship_blue.png', anchor='center')
    img_flame = load_image('flame.png', anchor='center')
    img_flame.anchor_x -= 2
    snd_thrust = load_static_sound('thrusters.wav')

    controls = {'THRUST_KEY': [pyglet.window.key.I],
                'ROTATE_LEFT_KEY': [pyglet.window.key.J],
                'ROTATE_RIGHT_KEY': [pyglet.window.key.L],
                'SHIELD_KEY': [pyglet.window.key.K],
                'FIRE_KEY': [pyglet.window.key.ENTER],
                'FIRE_FAST_KEY': [pyglet.window.key.BACKSPACE],
                'SLD_KEY': [pyglet.window.key.RCTRL],
                'FIREWORK_KEYS': OrderedDict({pyglet.window.key._7: 200,
                                              pyglet.window.key._8: 500,
                                              pyglet.window.key._9: 900}),
                'MINE_KEYS': OrderedDict({pyglet.window.key.M: 1,
                                          pyglet.window.key.COMMA: 3,
                                          pyglet.window.key.PERIOD: 6})
                }
    
    @classmethod
    def set_controls(cls, controls: Optional[dict] = None):
        """Set ship controls.
        
        If method not executed then default controls will be assigned 
        according to dictionary:
            {
            'THRUST_KEY': [pyglet.window.key.I],
            'ROTATE_LEFT_KEY': [pyglet.window.key.J],
            'ROTATE_RIGHT_KEY': [pyglet.window.key.L],
            'SHIELD_KEY': [pyglet.window.key.K],
            'FIRE_KEY': [pyglet.window.key.ENTER],
            'FIRE_FAST_KEY': [pyglet.window.key.BACKSPACE],
            'SLD_KEY': [pyglet.window.key.RCTRL],
            'FIREWORK_KEYS': OrderedDict({pyglet.window.key._7: 200,
                                            pyglet.window.key._8: 500,
                                            pyglet.window.key._9: 900}),
            'MINE_KEYS': OrderedDict({pyglet.window.key.M: 1,
                                        pyglet.window.key.COMMA: 3,
                                        pyglet.window.key.PERIOD: 6})
            }

        +controls+  Dictionary with same keys as for the default above. 
            Values define the keyboard key or keys that will result in 
            the corresponding control being executed. A keyboard key is 
            defined as the integer used by pyglet to represent that 
            specific keyboard key and which can be defined as a corresponding,
            intelligibly named, constant of the pyglet.window.key module:
            https://pyglet.readthedocs.io/en/latest/modules/window_key.html
            Values take a List of these pyglet constants or an OrderedDict
            with keys as these pyglet constants.
            FIREWORK_KEYS and MINE_KEYS both take OrderedDict that provide 
            for supplying an additional parameter for each keyboard key:
                Values of FIREWORK_KEYS OrderedDict represent the distance, 
                    in pixels, that the firework will travel before exploding.
                Values of MINE_KEYS OrderedDict represent the time, in 
                    seconds, before the mine will explode.
        """
        if controls is None:
            return
        cls.controls.update(controls)

    def __init__(self, control_sys, cruise_speed=200, **kwargs):
        """++control_sys++:  ControlSystem."""
        self.handlers = self._handlers()
        super().__init__(cruise_speed=cruise_speed, sound=False, **kwargs)
        self.control_sys = control_sys
        self.flame = Sprite(self.img_flame, 
                            batch=self.batch, group=self.group)
        self.flame.visible = False
        
    @property
    def _pick_up_cls(self):
        return PickUp

    def _handlers(self) -> dict:
        h = {'THRUST_KEY': {'on_press': self._thrust_key_onpress_handler,
                            'on_release': self._thrust_key_onrelease_handler,
                            'while_pressed': self._thrust_key_pressed_handler
                            },
             'ROTATE_LEFT_KEY': {'on_press': self._rotate_left_key_onpress_handler,
                                 'on_release': self._rotate_key_onrelease_handler
                                 },
             'ROTATE_RIGHT_KEY': {'on_press': self._rotate_right_key_onpress_handler,
                                  'on_release': self._rotate_key_onrelease_handler
                                  },
             'SHIELD_KEY': {'on_press': self._shield_key_onpress_handler},
             'FIRE_KEY': {'on_press': self._fire_key_onpress_handler},
             'FIRE_FAST_KEY': {'on_press': self._fire_fast_key_onpress_handler},
             'SLD_KEY': {'on_press': self._sld_key_onpress_handler},
             'FIREWORK_KEYS': {'on_press': self._firework_key_onpress_handler},
             'MINE_KEYS': {'on_press': self._mine_key_onpress_handler},
             }
        return h

    def setup_keymod_handlers(self):
        """Implements inherited method."""
        for key, keyboard_keys in self.controls.items():
            for keyboard_key in keyboard_keys:
                self.add_keymod_handler(key=keyboard_key, 
                                        **self.handlers[key])

    def _thrust_key_onpress_handler(self, key, modifier):
        self._sound_thrust()
        self.flame.visible = True
        self.cruise_speed()
        
    def _thrust_key_onrelease_handler(self, key, modifier):
        self.flame.visible = False
        self.speed_zero()
        self.stop_sound()
        
    def _thrust_key_pressed_handler(self, key, modifier):
        self.flame.x = self.x
        self.flame.y = self.y
        self.flame.rotation = self.rotation

    def _rotate_right_key_onpress_handler(self, key, modifier):
        self.cruise_rotation()

    def _rotate_key_onrelease_handler(self, key, modifier):
        self.rotation_zero()

    def _rotate_left_key_onpress_handler(self, key, modifier):
        self.cruise_rotation(clockwise=False)

    def _fire_fast_key_onpress_handler(self, key, modifier):
        self.control_sys.fire(HighVelocityCannon)
        
    def _fire_key_onpress_handler(self, key, modifier):
        self.control_sys.fire(Cannon)

    def _sld_key_onpress_handler(self, key, modifier):
        self.control_sys.fire(SLD_Launcher)

    def _shield_key_onpress_handler(self, key, modifier):
        self.control_sys.fire(ShieldGenerator)

    def _firework_key_onpress_handler(self, key, modifier):
        dist = self.controls['FIREWORK_KEYS'][key]
        self.control_sys.fire(FireworkLauncher, explosion_distance=dist)

    def _mine_key_onpress_handler(self, key, modifier):
        fuse_length = self.controls['MINE_KEYS'][key]
        self.control_sys.fire(MineLayer, fuse_length=fuse_length)
                    
    def _sound_thrust(self):
        self.sound(self.snd_thrust, loop=True)

    def _explode(self):
        """Play 'explosion' animation at ship's position and scaled to ship 
        size."""
        Explosion(x=self.x, y=self.y, scale_to=self, 
                  batch=self.batch, group=self.group)
            
    def stop(self):
        super().stop()
        self.stop_sound()

    def freeze(self):
        super().freeze()
        self.flame.visible = False

    def collided_with(self, other_obj: PhysicalSprite):
        # take no action if 'collided with' ship's own shield
        if isinstance(other_obj, Shield) and other_obj.ship == self:
            return
        elif isinstance(other_obj, (Asteroid, Bullet, Ship, Shield)):
            self.kill()
        elif type(other_obj) is self._pick_up_cls:
            self.control_sys.process_pickup(other_obj)
                        
    def kill(self):
        self._explode()
        super().kill()
        
    def die(self):
        self.flame.delete()
        super().die()
            
class ShipRed(Ship):
    """Red Player's Ship.
    
    Default Controls via keyboard keys:
        W - thrust forwards. Whilst key held flame visible and thrust 
            sound plays.
        A - rotate ship anticlockwise.
        D - rotate ship clockwise.
        S - shield up.
        TAB - fire.
        ESCAPE - rapid fire.
        LCTRL - super laser defence.
        1, 2, 3 - fire firework to explode after travelling 200, 500, 900 
            pixels respectively.
        Z, X, C - lay mine to explode in 1, 3, 6 seconds respectively.
    """
    
    img = load_image('ship_red.png', anchor='center')
    img_flame = load_image('flame.png', anchor='center')
    img_flame.anchor_x -= 2
    
    controls = {'THRUST_KEY': [pyglet.window.key.W],
                'ROTATE_LEFT_KEY': [pyglet.window.key.A],
                'ROTATE_RIGHT_KEY': [pyglet.window.key.D],
                'SHIELD_KEY': [pyglet.window.key.S],
                'FIRE_KEY': [pyglet.window.key.TAB],
                'FIRE_FAST_KEY': [pyglet.window.key.ESCAPE],
                'SLD_KEY': [pyglet.window.key.LCTRL],
                'FIREWORK_KEYS': OrderedDict({pyglet.window.key._1: 200,
                                              pyglet.window.key._2: 500,
                                              pyglet.window.key._3: 900}),
                'MINE_KEYS': OrderedDict({pyglet.window.key.Z: 1,
                                          pyglet.window.key.X: 3,
                                          pyglet.window.key.C: 6})
                }

    @property
    def _pick_up_cls(self):
        return PickUpRed

class Asteroid(PhysicalSprite):
    """Extends PhysicalSprite to define an Asteroid with suitable image 
    and spawning functionality such that spawn's ++num_per_spawn++ asteroids 
    when object killed. Asteroid will spawn ++spawn_limit++ times and each 
    spawned asteroid will be half the size of the asteroid that spawned it.
    Resolves collision with Bullets and Ships by considering asteroid 
    to have been killed - plays smoke animation in the asteroid's last 
    position, together with playing explosion auido.
    By default asteroid will bounce at the window boundary. Pass 
    ++at_boundary++ as 'wrap' to change this behaviour.

    End-of-Life
    .kill() if killed in-game
    .die() if deceasing object out-of-game
    """
    
    img = load_image('pyrrhoid.png', anchor='center')

    def __init__(self, spawn_level=0, spawn_limit=5, num_per_spawn=3, 
                 at_boundary='bounce', **kwargs):
        """
        ++spawn_level++ How many times the origin Asteroid has now
            spawned.
        ++spawn_limit++ How many times the origin Asteroid should 
            spawn.
        ++num_per_spawn++  How many asteroids this asteroid should break 
            up into when killed.
        """
        super().__init__(at_boundary=at_boundary, sound=False, **kwargs)
        self._spawn_level=spawn_level
        self._spawn_limit=spawn_limit
        self._num_per_spawn=num_per_spawn
        
    def _spawn(self):
        """Spawn new asteroids if spawn level below spawn limit."""
        if self._spawn_level < self._spawn_limit - 1:
            for i in range (self._num_per_spawn):
                ast = Asteroid(x=self.x, y=self.y,
                               spawn_level = self._spawn_level + 1,
                               spawn_limit = self._spawn_limit,
                               num_per_spawn = self._num_per_spawn,
                               initial_speed = self.speed,
                               initial_rotation = random.randint(0, 359),
                               at_boundary=self._at_boundary,
                               batch=self.batch, group=self.group)
                scale_factor = 0.5 ** (self._spawn_level + 1)
                ast.scale = scale_factor
        
    def _explode(self):
        """Play 'smoke' animation in asteroid's current position."""
        Smoke(x=self.x, y=self.y, batch=self.batch, group=self.group, 
              scale_to=self)
        
    def kill(self):
        self._spawn()
        self._explode()
        super().kill()
        
    def collided_with(self, other_obj):
        if isinstance(other_obj, (Bullet, Ship, Shield)):
            self.kill()


#GLOBALS
COLLECTABLE_IN = 2
COLLECTABLE_FOR = 8 

PICKUP_AMMO_STOCKS = {HighVelocityCannon: (5, 9),
                      FireworkLauncher: (2, 5),
                      MineLayer: (2, 5),
                      ShieldGenerator: (2, 4),
                      SLD_Launcher: (3, 5)
                      }

settings = ['COLLECTABLE_IN', 'COLLECTABLE_FOR', 'PICKUP_AMMO_STOCKS']
pyroids.config_import(vars(), settings)

class PickUp(PhysicalSprite):
    """Ammunition pickup for friendly ship (blue).
    
    Pickup offers the friendly ship a resupply of ammunition of a specific, 
    albeit random, ammunition class. Pickup contains a random number of 
    rounds albeit bounded by minimum and maximum limits defined for each 
    ammunition class.
    
    Pickup appears in a random position as a circle, of the same color as 
    the friendly ship, placed behind an image representing the specific 
    ammunition class. Pickup flashes for an initial period during 
    which it cannot be interacted with.
    
    On a firendly ship colliding with the pickup, the pickup disappears and 
    audio plays advising of resupply. NB This class does NOT advise the 
    collecting ship that the pickup has been collected. It is the collecting 
    Ship's responsibility to detect the collision and add the collected 
    ammunition to the corresponding Weapon.

    Pickup killed if bullet or another ship's shield collides with it, in 
    which case explodes as a starburst centered on the pickup position and 
    with as many bullets as the pickup had ammunition rounds. Exception is 
    if specific ammunitiion class is Shield, in which case explodes without 
    a starburst. Bullets of any starburst are attributed to the ship 
    responsible for bullet or shield that killed the pickup.

    Pickup will decease naturally if it not collected within a specified 
    time. Pickup flashes during the final stage of natural life.
    
    Class ATTRIBUTES
    ---color---  Pickup color (corresponding to color of ship / control 
        system that can collect the pickup)
    ---stocks---  Dictionary defining possible weapons that a pickup can 
        resupply and quantities of ammunition rounds that a pickup could 
        contain. Keys take Weapon classes, one key for each weapon that a 
        pickup could resupply. Values take a 2-tuple of integers 
        representing the minimum and maximum rounds of ammunition that 
        could be in a pickup for the corresponding weapon.
    ---collectable_in---  Seconds before a pickup can be collected.
    ---collectable_for---  Seconds that a pickup can be collected for before 
        naturally deceasing.

    PROPERTIES
    --dropping--  True if not yet collectable (i.e. supply still dropping).
    """
    
    img = load_image('pickup_blue.png', anchor='center')  # Background
    snd = load_static_sound('supply_drop_blue.wav')
    snd_pickup = load_static_sound('nn_resupply.wav')

    color = 'blue'
    stocks = PICKUP_AMMO_STOCKS
    collectable_in = COLLECTABLE_IN
    collectable_for = COLLECTABLE_FOR
    final_secs = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_randomly()
        self.Weapon = random.choice(list(self.stocks.keys()))
        self.number_rounds = random.randint(*self.stocks[self.Weapon])

        ammo_img = self.Weapon.ammo_cls[self.color].img_pickup
        # Place ammo sprite over the pickup background.
        self.ammo_sprite = Sprite(ammo_img, self.x, self.y, 
                                  batch=self.batch, group=self.group)
        
        self._killer_control_sys: ControlSystem

        self.flash_start(frequency=4)
        self._collectable = False
        self.schedule_once(self._now_collectable, self.collectable_in)

    @property
    def dropping(self):
        return not self._collectable

    def _now_collectable(self, dt: Optional[float] = None):
        self.flash_stop()
        self._collectable = True
        self.schedule_once(self._dying, 
                           self.collectable_for - self.final_secs)

    def _dying(self, dt: Optional[float] = None):
        self.flash_start(frequency=8)
        self.schedule_once(self.die, self.final_secs)

    @property    
    def _pick_up_ship_cls(self):
        return Ship

    def _play_pickup(self):
        self.sound(self.snd_pickup)

    def _starburst(self):
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self._killer_control_sys,
                  num_bullets=self.number_rounds, 
                  bullet_speed=275)

    def _explode(self):
        """Play explosion animation of pickup size in pickup position."""
        Explosion(x=self.x, y=self.y, scale_to=self, 
                  batch=self.batch, group=self.group)

    def kill(self):
        self._explode()
        if self.Weapon is not ShieldGenerator:
            self._starburst()
        super().kill()

    def die(self, dt: Optional[float] = None):
        super().die(stop_sound=False)

    @property
    def _NotFriendlyShieldCls(self):
        return ShieldRed

    def collided_with(self, other_obj):
        if self.dropping:
            return
        elif isinstance(other_obj, Bullet):
            self._killer_control_sys = other_obj.control_sys
            self.kill()
        elif type(other_obj) is self._NotFriendlyShieldCls:
            self._killer_control_sys = other_obj.ship.control_sys
            self.kill()
        elif type(other_obj) is self._pick_up_ship_cls:
            self._play_pickup()
            self.die()

    def refresh(self, dt: float):
        """Remain stationary on refresh."""
        pass

class PickUpRed(PickUp):
    """Ammunition pickup for Red ship."""

    img = load_image('pickup_red.png', anchor='center')
    snd = load_static_sound('supply_drop_red.wav')
    snd_pickup = load_static_sound('mr_resupply.wav')
    color = 'red'

    @property    
    def _pick_up_ship_cls(self):
        return ShipRed

    @property
    def _NotFriendlyShieldCls(self):
        return Shield


#GLOBAL default values
SHIELD_DURATION = 8
HIGH_VELOCITY_BULLET_FACTOR = 3

INITIAL_AMMO_STOCKS = {Cannon: 9,
                       HighVelocityCannon: 7,
                       FireworkLauncher: 2,
                       SLD_Launcher: 2,
                       MineLayer: 2,
                       ShieldGenerator: 2}

settings = ['SHIELD_DURATION', 'INITIAL_AMMO_STOCKS', 
            'HIGH_VELOCITY_BULLET_FACTOR']
pyroids.config_import(vars(), settings)

class ControlSystem(object):
    """Control system for a player.
    
    Provides:
        Ship creation
        Weapons creation and management
        Shield Status
        Ammunition pickup management
        Radiation monitor creation and management

    Only one Ship can be associated with the control system at any time. 
    Creation of a new ship results in managed systems being reset (radiation
    monitor, weapons' ammuntion stocks).
    
    Weapons available to control system:
        Cannon
        HighVelocityCannon
        FireworkLauncher
        SLD_Launcher
        MineLayer
        ShieldGenerator

    Class ATTRIUBTES 
    ---ShipCls--- Associated Ship class.
    ---shield_duration---  Shield Duration
    ---hvb_factor---  High Velocity Bullet speed as multiple of standard 
        bullet speed.
    ---initial_stock---  Dictionary representing initial ammuntion stocks. 
        Each item represents initial ammunition stock for a specific weapon.
        Key takes a Weapon class. Value takes integer representing that 
        weapon's initial stock of ammuntion.

    Instance ATTRIBUTES
    --radiation_monitor--  Associated RadiationMonitor.

    PROPERTIES
    --weapons--  List of controlled weapons.
    --shield_up--  True if shield raised.
    --bullet_margin--  Margin to avoid immediate collision with ship.
    --bullet_discharge_speed--  Bullet discharge speed. Read/Write

    METHODS
    --new_ship()--  Create new ship.
    --fire(weapon)--  Attempt to fire one round of ammunition from +weapon+.
    --process_pickup(pickup)--  Add ammunition from +pickup+.
    
    Methods available to aid Weapon classes instantiating ammunition objects:
    --bullet_initial_speed()-- Speed a bullet should have if fired now.
    --ammo_base_kwargs()--  Options for ammunition class.
    --bullet_kwargs()--  Options to fire bullet from ship's nose.
    """
    
    ShipCls = {'blue': Ship,
               'red': ShipRed}

    _RadiationMonitorCls = {'blue': RadiationMonitor,
                            'red': RadiationMonitorRed}

    shield_duration = SHIELD_DURATION
    hvb_factor = HIGH_VELOCITY_BULLET_FACTOR
    initial_stock = INITIAL_AMMO_STOCKS

    def __init__(self, color: Union['blue', 'red'] = 'blue',
                 bullet_discharge_speed=200, dflt_num_starburst_bullets=12):
        """
        ++color++ Color of player who will use the control system.
        ++bullet_discharge_speed++ Default bullet speed. Can be subsequently 
            set via property --bullet_discharge_speed--.
        ++dflt_num_starburst_bullets++ Default number of bullets that 
            a starburst comprises of.
        """
        self.color = color
        self.ship: Ship # set by --new_ship--
        self.radiation_monitor = self._RadiationMonitorCls[color](self)

        self._dflt_num_starburst_bullets = dflt_num_starburst_bullets
        self._bullet_discharge_speed = bullet_discharge_speed
                       
        # --add_weapons()-- sets values to instance of corresponding Weapon
        self._weapons = {Cannon: None,
                         HighVelocityCannon: None,
                         FireworkLauncher: None,
                         SLD_Launcher: None,
                         MineLayer: None,
                         ShieldGenerator: None}

        self.add_weapons()

    def _set_initial_stocks(self):
        for Weapon, weapon in self._weapons.items():
            weapon.set_stock(self.initial_stock[Weapon])

    def _ship_killed(self):
        self.radiation_monitor.halt()
        self._weapons[ShieldGenerator].lower_shield()

    def new_ship(self, **kwargs) -> Ship:
        """Create new ship for player using control system."""
        funcs = [self._ship_killed]
        if 'on_kill' in kwargs:
            funcs.append(copy(kwargs['on_kill']))
        kwargs['on_kill'] = lambda: [ f() for f in funcs ]
        self.ship = self.ShipCls[self.color](control_sys=self, **kwargs)
        self._set_initial_stocks()
        self.radiation_monitor.reset()
        return self.ship

    @property
    def weapons(self) -> List[Weapon]:
        """List of controlled weapons."""
        return self._weapons.values()

    @property
    def bullet_margin(self):
        """Minimum distance, in pixels, from center of associated ship to 
        a point where a bullet can be instantiated without immediately 
        colliding with ship.
        """
        return (self.ship.image.width + Bullet.img.width)//2 +2

    @property
    def shield_up(self) -> bool:
        """True if shield current raised, otherwise False."""
        return self._weapons[ShieldGenerator].shield_raised
                
    @property
    def bullet_discharge_speed(self):
        """Component of Bullet speed from propulsion. Read/Write.

        NB Actual bullet speed should include ship speed.
        
        Read/Write."""
        return self._bullet_discharge_speed

    @bullet_discharge_speed.setter
    def bullet_discharge_speed(self, value):
        self._bullet_discharge_speed = max(value, self.ship._speed_cruise)

    def set_cannon_reload_rate(self, reload_rate: Union[float, int]):
        """+reload_rate+ Seconds to reload one round of ammunition."""
        self._weapons[Cannon].set_reload_rate(reload_rate)

    def _add_weapon(self, Weapon: Weapon, **kwargs):
        self._weapons[Weapon] = Weapon(self, **kwargs)

    def _add_cannon(self, **kwargs):
        self._add_weapon(Cannon, **kwargs)

    def _add_hv_cannon(self, **kwargs):
        kwargs.setdefault('bullet_speed_factor', self.hvb_factor)
        self._add_weapon(HighVelocityCannon, **kwargs)

    def _add_sld_launcher(self, **kwargs):
        self._add_weapon(SLD_Launcher, **kwargs)
        
    def _add_firework_launcher(self, **kwargs):
        self._add_weapon(FireworkLauncher, **kwargs)

    def _add_minelayer(self, **kwargs):
        self._add_weapon(MineLayer, **kwargs)
        
    def _add_shieldgenerator(self, **kwargs):
        kwargs.setdefault('dflt_duration', self.shield_duration)
        self._add_weapon(ShieldGenerator, **kwargs)
    
    def add_weapons(self):
        self._add_cannon()
        self._add_hv_cannon()
        self._add_sld_launcher()
        self._add_firework_launcher()
        self._add_minelayer()
        self._add_shieldgenerator()
        
    def fire(self, weapon: Type[Weapon], **kwargs):
        """Attempt to fire one round of ammunition from type of +weapon+."""
        self._weapons[weapon].fire(**kwargs)

    def process_pickup(self, pickup):
        """Add ammunition in +pickup+ to corresponding weapon.

        +pickup+: Pickup of same color as control system.

        Raises assertion error is pickup is of a different color to control 
        system.
        """
        assert pickup.color == self.color, "Pickup color should be the"\
            " same as color of control system."
        self._weapons[pickup.Weapon].add_to_stock(pickup.number_rounds)

    def bullet_initial_speed(self, factor=1) -> int:
        """Return speed a bullet should have if fired now.

        +factor+ Factor by which to multiple bullet discharge speed.
        """
        return self.ship.speed + (self.bullet_discharge_speed * factor)

    def ammo_base_kwargs(self) -> dict:
        """Return dictionary of options for an ammunition class.

        Pass dictionary as kwargs to ammunition class to set following 
        options to same values as for associated ship - 'x', 'y', 'batch', 
        'group'.
        """
        ship = self.ship
        kwargs = {'x': ship.x,
                  'y': ship.y,
                  'batch': ship.batch,
                  'group': ship.group}
        return kwargs

    def _bullet_base_kwargs(self, margin: Optional[int] = None) -> dict:
        """Return dictionary that can be passed to a Bullet class 
        constructor to set options 'x', 'y', 'batch', 'group' and 
        'control_sys'.
        
        +margin+ Distance from centre of ship to point where bullet to 
            first appear. Should be sufficient to ensure that bullet does not
            immediately collide with ship. If not passed then will use default
            margin.
        """
        margin = margin if margin is not None else self.bullet_margin
        x_, y_ = vector_anchor_to_rotated_point(margin, 0, self.ship.rotation)
        kwargs = self.ammo_base_kwargs()
        kwargs['control_sys'] = self
        kwargs['x'] += x_
        kwargs['y'] += y_
        return kwargs

    def bullet_kwargs(self, margin: Optional[int] = None, **kwargs):
        """Options for Bullet class to fire bullet from nose of ship.
        
        Pass returned dictionary to Bullet class constructor as kwargs.
              
        +margin+ Distance from centre of ship to point where bullet to 
            first appear. Should be sufficient to ensure that bullet does not
            immediately collide with ship. If not passed then will use default
            margin.
        +kwargs+ Any option taken by Bullet class. Will be added to returned 
            dictionary and override any option otherwise defined by method.
        """
        assert False not in \
            [ kwarg not in kwargs for kwarg in ['x', 'y', 'batch'] ]
        for kwarg, value in self._bullet_base_kwargs(margin=margin).items():
            kwargs[kwarg] = value
        kwargs.setdefault('initial_speed', self.bullet_initial_speed())
        kwargs.setdefault('initial_rotation', self.ship.rotation)
        return kwargs

    def die(self):
        self.radiation_monitor.halt()
        for weapon in self.weapons:
            weapon.die()