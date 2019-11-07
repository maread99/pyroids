#! /usr/bin/env python

"""Game Sprite and Weapon Classes.

Hierarchy:
    Ships (Ship and ShipRed) and Asteroids are PhysicalSprites
    Ships have a ControlSystem (++control_sys++)
    The ControlSystem has various weapons where each weapon is a subclass of 
      Weapon. Each weapon held in --_weapons-- dictionary which has keys as 
      subclass of Weapon and instance as instance of that Weapon subclass 
      which is the weapon the control system has access to. For example, 
      if a control system has a Cannon available to it then the class Cannon 
      will be a key of the --weapons-- dictionary with value as the instance 
      of Cannon available to the control system. The ControlSystem also has 
      a shield generator (for the most part just another Weapon) and a 
      RadiationMonitor.

    ControlSystem, post instantiation, have to be --set(ship)-- to a ship. 
    NB The Ship(control_sys) constructor sets the ship instance to the 
    passed ++control_sys++.
        The ControlSystem can be set to a new ship at anytime via --set--. 
        This behaviour allows for a game to employ a single ControlSystem
        per player with new ships (when the player resurrects) being set to 
        the existing ControlSystem (--set-- also provides for resetting 
        initial stock levels).
          
    Weapon(object) is a base class. Subclasses of Weapon define concrete 
      weapons; Cannon, CannonHighVelocity, FireworkLauncher, MineLayer, 
      SLD_Launcher and ShieldGenerator. Each weapon has an AmmoCls attribute 
      which holds the class that defines the weapon's ammunition. 
    Ammunition(object) is a mixin with a minimum definition that only serves 
      to state a couple of class attributes that should be implemented by 
      ammunition classes; Bullet, BulletHighVelocity, Firework, Mine, 
      SuperLaserDefence and Shield. In turn each of these classes is 
      subclassed to provide a customised version for ShipRed. These 
      subclasses take the same name, suffixed with Red, for example, 
      BulletRed.
      All ammunitition classes are subclasses of PhysicalSprite.
    
The following additional classes are defined:
Starburst(object) - Creates multiple bullets fired from or as if from a single 
  origin with bullets directions defined at regular angular intervals. NOT an 
  Ammunition subclass but rather a mere object which contributes to ammunition 
  classes (Firework and SuperLaserDefence).

Explosion and Smoke are both subclasses of OneShotAnimatedSprite and do what 
they say on the can. Employed by the --kill-- methods of Ship and Asteroid 
respectively.

Also defines default values for the following Global Constants, all of which 
will be overriden where these variables have been defined in any 
configuration file passed at the command line (see
pyroids.config.template.__doc__):
'SHIELD_DURATION', 'INITIAL_AMMO_STOCKS', 'COLLECTABLE_IN', 
'COLLECTABLE_FOR', 'PICKUP_AMMO_STOCKS'
"""

import os, random, sys, importlib
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

class Explosion(OneShotAnimatedSprite):
    """One off animated stationary color explosion with accompanying 
    sound (pass ++sound++ as False to not play accompanying sound).
    """

    img = anim('explosion.png', 2, 8)
    snd = load_static_sound('nn_explosion.wav')
        
    def __init__(self, scale_to: Union[Sprite, Texture] = None, **kwargs):
        """+scale_to+ provides for directly scaling, with the constructor, 
        object to the dimensions of object passed as +scale_to+
        ++sound++ as False to not play accompanying sound (by default, as 
        implemented at AdvSprite level, will play sound on instaniating 
        object"""
        super().__init__(**kwargs)
        if scale_to is not None:
            self.scale_to(scale_to)

class Smoke(Explosion):
    """Extends Explosion to simply change image to provide for a one off 
    animated stationary 'smoke explosion'. Accompanying sound as for 
    Explosion.
    """
    img = anim('smoke.png', 1, 8)
 
class Ship(PhysicalSpriteInteractive):
    """Extends PhysicalSpriteInteractive to create a ship object that moves 
    and fires weapons and which, by default, can be interacted with via the 
    following keyboard keys:
          I - thrust forwards
          J - rotate ship anticlockwise.
          L - rotate ship clockwise.
          K - shield up
          ENTER - fire
          BACKSPACE - rapid fire
          RCTRL- super laser defence
          7, 8, 9 - fire firework to explode after travelling 200, 500, 900 
            pixels respectively
          M, COMMA, PERIOD - lay mine to explode in 1, 3, 6 seconds 
            respectively

    Default Ship controls can be customised by passing a dictionary to class 
    method ---set_controls--- with items that will replace the corresponding 
    defaults defined as:
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
    Dictionary keys should be as defined above
    Dictionary values should taken a List or Dictionary defining the key or 
    keys that will result in the corresponding control being executed. Keys 
    defined as constants of the pyglet.windows.key module:
        https://pyglet.readthedocs.io/en/latest/modules/window_key.html
    FIREWORK_KEYS and MINE_KEYS items both define multiples keys by default
      and can be defined to take one or any number of keys.
        Values of FIREWORK_KEYS dictionary represent the distance, in 
          pixels that the firework will travel before exploding
        Values of MINE_KEYS dictionary represent the time, in seconds, 
          before the mine will explode.
    Ship controls can be changed via a configuration file.

    End-of-Life
    .kill() if killed in-game
    .die() if deceasing object out-of-game
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
        if controls is None:
            return
        cls.controls.update(controls)

    def __init__(self, control_sys, cruise_speed=200, **kwargs):
        """++control_sys++ is an instance of ControlSystem"""
        self.handlers = self._handlers()
        super().__init__(cruise_speed=cruise_speed, sound=False, **kwargs)
        self.control_sys = control_sys
        self.flame = Sprite(self.img_flame, 
                            batch=self.batch, group=self.group)
        self.flame.visible = False
        
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
        """Implements method defined on InteractivePhysicalSprite to set 
        up key event handlers. These handlers provide for user to control 
        and fire weapons as described in cls.__doc__"""
        for k, keys in self.controls.items():
            for key in keys:
                self.add_keymod_handler(key=key, **self.handlers[k])

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
        """Play one off 'explosion' animation in the ship's position and of 
        the same size as the ship, complete with explosion sound"""
        Explosion(x=self.x, y=self.y, scale_to=self, 
                  batch=self.batch, group=self.group)
            
    def stop(self):
        """Inhertits inherited method to stop any sound (i.e. thrust sound)"""
        super().stop()
        self.stop_sound()

    def freeze(self):
        super().freeze()
        self.flame.visible = False
                        
    def kill(self):
        """Extends inherited method to enact operations when object killed 
        in-game:
        Shows explositon animation and plays accompanying sound
        """
        self._explode()
        self.control_sys.ship_killed()
        super().kill()
        
    def die(self):
        """Internals - extends inherited method to decease self:
        Delete associated --flame--
        Stop sound of ship's thrust to cover circumstance that ship died 
        whilst thrusting.
        """
        self.flame.delete()
        super().die()
        
    
    @property
    def _pick_up_cls(self):
        return PickUp

    def collided_with(self, other_obj: PhysicalSprite):
        """Enacts consequence for self of collision with +other_obj+.
        Takes no action if +other_obj+ is the ship's own shield!
        """
        if isinstance(other_obj, Shield) and other_obj.ship == self:
            return
        elif isinstance(other_obj, (Asteroid, Bullet, Ship, Shield)):
            self.kill()
        elif type(other_obj) is self._pick_up_cls:
            self.control_sys.process_pickup(other_obj)
            
class ShipRed(Ship):
    """Extends Ship class to provide for a player 2 ship with a different 
    image (as for Ship but red rather than blue) and different default key 
    controls:
          W - thrust forwards. Whilst key held flame visible and thrust 
        sound plays.
          A - rotate ship anticlockwise.
          D - rotate ship clockwise.
          S - shield up
          TAB - fire
          ESCAPE - rapid fire
          LCTRL - super laser defence
          1, 2, 3 - fire firework to explode after travelling 200, 500, 900 
            pixels respectively
          Z, X, C - lay mine to explode in 1, 3, 6 seconds respectively

    See Ship.__doc__ for documentat0ion on using ---set_controls--- class 
    method to change ship controls.
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
        """See cls.__doc__"""
        super().__init__(at_boundary=at_boundary, sound=False, **kwargs)
        self._spawn_level=spawn_level
        self._spawn_limit=spawn_limit
        self._num_per_spawn=num_per_spawn
        
    def _spawn(self):
        """Spawns --_num_per_spawn-- new asteroids with initial position and 
        speed as the object's position and speed and with random rotation (i.e. 
        random orientation). Spawns have spawn_level passed as one higher than 
        object and spawn_limit the same as the object.
        Will only spawn if the spawn_level hasn't reached the spawn_limit"""
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
        """Play one off 'smoke' animation in the asteroid's position and of 
        the same size as the asteroid, complete with explosion sound"""
        Smoke(x=self.x, y=self.y, batch=self.batch, group=self.group, 
              scale_to=self)
        
    def kill(self):
        """Extends inherited method to enact operations when object killed 
        in-game:
        Shows smoke animation in asteroid's last position, plays explosion 
        sound and spawns new asteroids (if spawn_level below spawn_limit).
        """
        self._spawn()
        self._explode()
        super().kill()
        
    def collided_with(self, other_obj):
        """Enacts consequence for self of collision with +other_obj+.
        Self dies if +other_obj+ is a Bullet or Ship, otherwise takes 
        no action
        """
        if isinstance(other_obj, (Bullet, Ship, Shield)):
            self.kill()


class Ammunition(object):
    """Internals. Mixin for ammunition classes which exists only to define the 
    need for subclasses to include following class attributes:

    ---img_pickup--- image to be used for sprite representing a pick-up of 
    ammunition of the subclass.
    ---img_stock--- image to be used for sprite representing the current 
    stock of ammunition of the subclass.
    """
    img_pickup: Union[Texture, Animation]
    img_stock: Union[Texture, Animation]

class Bullet(Ammunition, PhysicalSprite):
    """Extends Ammunition to define a Bullet with appropriate boundary 
    treatment (die by default) and collision resolution.
    If object collides with either an Asteroid or Ship then bullet killed

    End-of-life
    Make no practical difference whether life ends via --kill-- or directly 
    via --die-- as neither are extended on this class. i.e. relies on 
    inherited methods such that --kill-- effectively redundant and only 
    action on death is to remove from live sprites and delete the underlying 
    sprite.
    """
    img = load_image('bullet.png', anchor='center')
    snd = load_static_sound('nn_bullet.wav')

    img_pickup = img
    img_stock = img
    
    def __init__(self, control_sys, *args, **kwargs):
        """+control_sys should be passed as instance of ControlSystem 
        responsible for weapon that will fire the bullet"""
        self.control_sys = control_sys
        kwargs.setdefault('at_boundary', 'kill')
        super().__init__(*args, initial_rotation_speed=0,
                         rotation_cruise_speed=0, **kwargs)
        
    def collided_with(self, other_obj):
        """Enacts consequence for self of collision with +other_obj+"""
        if isinstance(other_obj, (Asteroid, Ship, Shield, Mine)):
            self.kill()
        elif isinstance(other_obj, PickUp) and not other_obj.dropping:
                self.kill()

class BulletRed(Bullet):
    snd = load_static_sound('mr_bullet.wav')
        
    
class BulletHighVelocity(Bullet):
    """Internals. NB does NOT define bullet speed but rather only the 
    look and sound of the bullet via ---snd--- and ---img--- (NB ---img--- 
    currently not defined such that uses same image as Bullet).
    """
    snd = load_static_sound('nn_hvbullet.wav')
    img = load_image('bullet_high_velocity.png', anchor='center')
    img_pickup = img
    img_stock = load_image('bullet_high_velocity.png', anchor='origin')

class BulletHighVelocityRed(BulletHighVelocity):
    snd = load_static_sound('mr_hvbullet.wav')
    img = load_image('bullet_high_velocity_red.png', anchor='center')
    img_pickup = img
    img_stock = load_image('bullet_high_velocity_red.png', anchor='origin')

class Starburst(object):
    """Fires +num_bullets+ Bullets at ++bullet_speed++ simultaneously 
    from a single origin, decribed by (+x+, +y+), with one bullet having 
    direction +direction+ and all others at regular rotational intervals.
    Includes firing sound.
    Bullets are attributable to ++control_sys++.

    Internals. NB Starburst is NOT an Ammunition class or a PhysicalSprite, 
    but rather an object, instantiation of which fires multiple bullets, 
    which can be instantiated from an Ammunition class that incorporates a 
    starburst effect.
    
    Following class methods provide client access to the sound played:
    ---stop_all_sound--- will any sound currently being played by any 
    instantiated Starburst.
    ---resume_all_sound--- will resume playing any sound that had been 
    stopped by ---stop_all_sound---.

    Instance methods:
    --sound-- plays sound assocaited with class (as held by ---snd---)
    
    Internals:
    Sound related class methods provided for by keeping a track of live 
    instances of Starburst. All Starburst instances are appended to 
    ---live_starbursts--- on instantiation and subseqeuntly removed 
    by the --die-- method when the Starburst deceseases - which the 
    constructor provides for via a scheduled call to decease the 
    object after the associated sound has been played. 
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
        """+distance_from_epi+ is the distance, in pixels from the epicentre 
        described by --x-- and --y--, that the bullets will appear.
        +direction+ if 0 will fire one bullet to the 'right' (i.e. 
        corresponding to 0 degrees in pyglet) and others at regular intervals 
        of rotation. If any other numerical value then the ++direction++ will 
        be added to what would otherwise have been each bullet's direction if 
        were to have been passed as 0. If ++direction++ 'random' (default) 
        then a random direction will be added to what would otherwise have 
        been each bullet's direction if were to have been passed as 0.
        All bullets will be added to the passed drawing +batch+ and will be 
        attributable to ++control_sys++.
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
        self._snd_player: pyglet.media.player.Player
        self._snd_was_playing: Optional[bool] = None
        self.live_starbursts.append(self)
                
        self._starburst()
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

    def sound(self):
        """Internals - see SpriteAdv.__doc__"""
        self._snd_player = self.snd.play()
                
    def stop_sound(self):
        self._snd_was_playing = self._snd_player.playing
        self._snd_player.pause()
        
    def resume_sound(self):
        if self._snd_was_playing:
            self._snd_player.play()
        self._snd_was_playing = None

    def _starburst(self):
        for direction in self._bullet_directions():
            x, y = self._bullet_birth_position(direction)
            Bullet(self.control_sys, x=x, y=y, 
                   batch=self.batch, group=self.group,
                   sound=False, initial_rotation=direction, 
                   initial_speed=self.bullet_speed)
        self.sound()

    def die(self, dt: Optional[float] = None):
        self.live_starbursts.remove(self)

class SuperLaserDefence(Ammunition, Starburst):
    """As Starburst. Only difference alternative audio and defining 
    class attributes for img_pickup and img_stocks"""

    img: Union[Texture, Animation] # not defined for SuperLaserDefence
    img_stock = load_image('sld_stock.png', anchor='origin')
    img_pickup = load_image('sld_stock.png', anchor='center')
    snd = load_static_sound('nn_superlaserdefence.wav')

class SuperLaserDefenceRed(SuperLaserDefence):
    snd = load_static_sound('mr_superdefence.wav')

class Firework(Bullet):
    """Large bullet converts into Starburst when killed on travelling 
    ++explosion_distance++ pixels or earlier if killed by collision or 
    on reaching boundary.
    
    Starburst bullets attributable to ++control_sys++

    End-of-Life. Use:
    .kill() if killed in-game
    .die() if deceasing object out-of-game
    """

    img = load_image('firework.png', anchor='center')
    snd = load_static_sound('nn_firework.wav')
    img_pickup = img
    img_stock = img

    def __init__(self, explosion_distance: int, 
                 num_starburst_bullets=12, 
                 starburst_bullet_speed=200,
                 **kwargs):
        """++explosion_distance++ defines distance in pixels before 
        firework will explode as a Starburst comprising 
        ++num_starburst_bullets++ travelling at 
        ++starburst_bullet_speed++.
        All other ++kwargs++ as for Bullet class
        """
        self.explosion_distance = explosion_distance
        self.num_starburst_bullets = num_starburst_bullets
        self._starburst_bullet_speed = starburst_bullet_speed
        kwargs['at_boundary'] = 'kill'
        super().__init__(**kwargs)
        self._set_fuse()
                     
    def _starburst(self):
        """Internals - directs starburst bullets such that, regardless of 
        --explosion_distance-- blast will not hit the weapon's system's 
        ship if the ship is stationary"""
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self.control_sys,
                  num_bullets=self.num_starburst_bullets, 
                  bullet_speed=self._starburst_bullet_speed,
                  direction=self.control_sys.ship.rotation + 15)

    def _fused(self, dt):
        """Internals - fused firework results in end of life by killing"""
        self.kill()

    def kill(self):
        """Launches starburst in position where killed"""
        self._starburst()
        super().kill()

    def _set_fuse(self):
        """Sets firework fuse so that firework explodes after travelling 
        ++explosion_distance++"""
        fuse = self.explosion_distance / self.speed
        self.schedule_once(self._fused, fuse)

    def die(self):
        super().die(stop_sound=False)

class FireworkRed(Firework):
    snd = load_static_sound('mr_firework.wav')

class Mine(Ammunition, PhysicalSprite):
    """Stationary Mine which shows a countdown from ++fuse_length++ to 
    0 whilst playing 'tick tock' sound. Explodes on earlier of reaching 0 
    or being shot by a bullet. Explosion takes form of Starburst that fires 
    out ++num_starburst_bullets++ at regular intervals with origin on the 
    mine's position ++x++, ++y++ and with speed +bullet_speed+.  Starburst 
    bullets are attributable to ++control_sys++.
    
    Mine can be 'hidden' until the last --visible_seconds-- where the default 
    visible seconds can be set at a class level by ---setup--- which in turn 
    can be overriden at an instance level by passing ++visible_seconds++. If 
    not passed anywhere then mine will be visible from instantiation through 
    to explosion.
       
    End-of-Life
    .kill() if killed in-game
    .die() if deceasing object out-of-game
    """
    
    img = anim('mine.png', 1, 9, frame_duration=1)
    img_pickup = img.frames[-1].image
    img_stock = img_pickup
    snd = load_static_sound('nn_minelaid.wav')

    visible_secs: Optional[int]
    _mines_setup = False

    @classmethod
    def _setup_mines(cls, visible_secs: Optional[int] = None):
        """Optional setup method to set class defaults. Can be 
        executed at any time to define class defaults"""
        cls.visible_secs = visible_secs
        cls._mines_setup = True

    @classmethod
    def _anim(cls, fuse_length) -> Animation:
        """Returns 'Coundown Mine' animation object which shows a number on 
        top of mine which counts down from --fuse_length-- to 0. No sound. 
        Animation lasts +fuse_length+ seconds"""
        anim = copy(cls.img)
        anim.frames = anim.frames[9 - fuse_length:]
        return anim

    def __init__(self, x: int, y: int, batch: pyglet.graphics.Batch, 
                 fuse_length: int, control_sys, 
                 visible_secs: Optional[int] = None, 
                 num_starburst_bullets=12, 
                 bullet_speed=200, **kwargs):
        """Mine will be placed at ++x++, ++y++ and drawn to screen via 
        ++batch++. If not otherwise killed, Mine will explode after 
        ++fuse_length++ seconds. If lives to ++fuse_length++ the object will 
        be visible for the last ++visible_secs++ or throughtout if 
        ++visible_secs++ is None. NB If ++visible_secs+ not otherwise passed 
        here and ---setup--- previously executed then visible_secs will take 
        the class default defined via ---setup---.
        ++control_sys++ is the ControlSystem instance to which the starburst's 
        bullets will be attributable
        """
        if not self._mines_setup:
            self._setup_mines()
        if visible_secs is not None:
            self.visible_secs = visible_secs
        
        assert fuse_length < 10
        self.fuse_length = fuse_length if fuse_length > 1 else 1
        self.control_sys = control_sys
        self.num_starburst_bullets = num_starburst_bullets
        self.bullet_speed = bullet_speed

        super().__init__(img=self._anim(fuse_length), x=x, y=y, batch=batch, 
                         **kwargs)

        if self.visible_secs and fuse_length > self.visible_secs:
            self._hide_anim_for(fuse_length - self.visible_secs)

    def on_animation_end(self):
        """Event handler"""
        self.kill()

    def _hide_anim_for(self, invisible_secs):
        self.visible = False
        self.schedule_once(self._show_anim, invisible_secs)

    def _show_anim(self, dt: Optional[float] = None):
        self.visible = True

    def collided_with(self, other_obj: PhysicalSprite):
        """Enacts consequence for self of collision with +other_obj+.
        Self killed if +other_obj+ is a Bullet, otherwise takes no action
        """
        if isinstance(other_obj, Bullet):
            self.kill()
    
    def refresh(self, dt):
        """Internals - overrides inherited method to do nothing, i.e. does 
        not refresh position on screen such that x and y remain unchanged"""
        pass

    def kill(self):
        """When 'killed' executes Starburst with origin on the mine's 
        position."""
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self.control_sys,
                  num_bullets=self.num_starburst_bullets, 
                  bullet_speed=self.bullet_speed)
        super().kill()

    def die(self):
        """Extends inherited method to stop any timer sound"""
        super().die()

class MineRed(Mine):
    snd = load_static_sound('mr_minelaid_ext.wav')

class Shield(Ammunition, PhysicalSprite):
    """Extends PhysicalSprite to define a Shield, with appropriate image, 
    sound (played on instantiation) and collision resolution.
    NB NO collisions have an effect on a Shield - invinsible.
    Additional Attributes:
    ship: takes Ship being shielded
    Internals - On instantiating the shield sets control system's shield 
    status to up. Then on dying sets to not up. NB NB ASSUMES weapons 
    system at ++ship++.control_sys that that control_sys in turn offers 
    the method --set_shield_status(up: bool)--
    """
    
    img = load_image('shield_blue.png', anchor='center')
    snd = load_static_sound('nn_shieldsup.wav')
    img_stock = load_image('shield_blue_20.png', anchor='origin')
    img_pickup = load_image('shield_pickup_inset_blue.png', anchor='center')

    def __init__(self, ship: Ship, 
                 x: Optional[int] = None, y: Optional[int] = None, 
                 duration: int = 10, **kwargs):
        """++ship++ takes Ship to be shielded
        ++x++ and ++y++ take the x and y coordinate at which to place the 
        shield, which default to the ships coordinates if not passed.
        Internals.
        Does not provide for passing any args or kwargs onto the inherited 
        constructor as pointless given that overriding --refresh-- makes 
        the object's own velocities and rotation redundant
        """
        self.ship = ship
        x = x if x is not None else self.ship.x
        y = y if y is not None else self.ship.y
        super().__init__(x=x, y=y, **kwargs)
        self._set_weapon_sys_shield_status(up=True)
        self.powerdown_duration = duration//4
        self.powerdown_phase2_duration = duration//10
        solid_shield_duration = duration - self.powerdown_duration
        self.schedule_once(self._powerdown_initial, solid_shield_duration)
        
    def _set_weapon_sys_shield_status(self, up: bool):
        self.ship.control_sys.set_shield_status(up=up)

    def refresh(self, dt):
        """Moves object to ++ship++'s position!"""
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
        """Overrides inherited method to explicitely define no actions...
        shield is invincible save for coming up against another shield.
        """
        if isinstance(other_obj, Shield):
            self.ship.kill()
            self.kill()

    def die(self):
        """Extends inherited method to set control system shield status 
        to not up"""
        self._set_weapon_sys_shield_status(up=False)
        super().die()

class ShieldRed(Shield):
    img = load_image('shield_red.png', anchor='center')
    snd = load_static_sound('mr_shieldsup.wav')
    img_stock = load_image('shield_red_20.png', anchor='origin')
    img_pickup = load_image('shield_pickup_inset_red.png', anchor='center')
    
class Weapon(object):
    """Base class from which subclasses can create specific weapons that 
    will be appended to a ControlSystem class.
    Class depends on methods of a ++control_sys++ which is passed to the 
    consructor.
        
    Manages level of ammunitiion stock, initially set to 
    --initial_stock-- and which can not exceed ++max_stock++.
    Creates a StockLabel which offers an image of the ammunition 
    alongside the number of rounds remaining. Updated to always reflect 
    the current stock.

    Internals:
    Ammunition classes defined by ++control_sys++ color in a dictionary 
    assigned to class attribute ---ammo_cls---. The dictionary keys take 
    string of color (e.g. 'blue') and values the Type of the Ammunition 
    subclass that the weapon will discharge for that coloured weapons 
    system. The constructor assigns the actual ammunition class to 
    self.AmmoCls.

    On this base class ammo defined as Bullet and BulletRed for the blue and 
    red ships respectively.

    Class attributes
    ---fire_when_sheild_up--- class attribute should be defined on 
    subclass if not False by default.

    Properties
    --stock-- current stock (int)
    --stock_label-- returns the StockLabel that represents the weapon's 
    stocks

    Methods
    --fire()-- fires one 'round of ammunition' by way of instantiating an 
    instance of --_AmmoCls-- with kwargs as returned by --_ammo_kwargs--. 
    Subclasses should define --_ammo_kwargs-- to return the necessary kwargs. 
    NB ControlSystem provides various methods to aid Weapons in collating 
    kwargs to pass to ammunition classes.
    Any kwargs received to --fire-- are passed through to --_ammo_kwargs--.
    --fire()-- will not fire 'one round of ammunition' if:
        no stock, in which case executes --_no_stock--, empty at this base 
        level
        shield up and ---fire_if_shield_up--- class attribute defined as 
        False (as it is by default), in which case executes --_shield_up--, 
        empty at this base level
    --_no_stock-- and --shields_up-- might be implemented by subclasses 
    to play appropriate audio

    --set_stock(num)-- to directly set stock level to +num+
    --add_to_stock(num)-- to add +num+ to current stock
    --subtract_from_stock(num)-- to reduce current stock by +num+
    
    --die()-- Empty at this level. Implement on subclass to perform any 
    tidy-up operations when weapon no longer required, for example cancelling 
    any scheduled calls
    """
    
    ammo_cls = {'blue': Bullet,
                'red': BulletRed}

    fire_when_shield_up = False

    def __init__(self, control_sys, initial_stock: int = 0,
                 max_stock: int = 9):
        """
        ++control_sys++ takes an instance of ControlSystem which has control 
        over the weapon and in reverse which this weapon can call on for 
        guidance.
        ++initial_stock++ defines the initial number of rounds of 
        ammunition that the weapon has available to fire.
        ++max_stock++ defines the maximum number of rounds of 
        ammunition that the weapon can have in stock at any one time.
        """
        self.control_sys = control_sys
        self.AmmoCls = self.ammo_cls[control_sys.color]
        self._max_stock = max_stock
        self._stock = min(initial_stock, max_stock)
        self._stock_label = StockLabel(image = self.AmmoCls.img_stock,
                                       initial_stock=self._stock,
                                       style_attrs = {'color': (255, 255, 255, 255)})
        
    @property
    def stock(self):
        return self._stock

    @property
    def max_stock(self):
        return self._max_stock

    @property
    def stock_label(self):
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
        """Internals - num +ve to increase stock, -ve to reduce stock"""
        num = self.stock + num
        return self._update_stock(num)

    def add_to_stock(self, num: int):
        """+num+ positive integer by which to increase stock"""
        self._change_stock(num)

    def subtract_from_stock(self, num: int):
        """+num+ positive integer by which to reduce stock"""
        assert not num < 0
        self._change_stock(-num)

    def _shield_up(self):
        """Handler if weapon fired whilst shield up although 
        weapon can't be fired when shield up. Can be implemented by 
        subclass if which to take action in this cirucmstance, for example 
        by playing appropriate audio.
        Not implemented at this base level.
        """
        pass

    def _no_stock(self):
        """Handler if control system attemps to fire weapon when there is 
        no stock. Can be implemented by subclass if which to take action in 
        this cirucmstance, for example by playing appropriate audio.
        Not implemented at this base level.
        """
        pass

    def _ammo_kwargs(self, **kwargs) -> dict:
        """Should be implmeneted on subclass to return a dictionary of kwargs 
        that can be passed to the --AmmoCls-- to fire one 'round of 
        ammunition'. **kwargs passed on as those received by --fire--.
        """
        return kwargs

    def _fire(self, **kwargs):
        """Fires an instance of ammunition.
        Internals - see cls.__doc__"""
        kwargs = self._ammo_kwargs(**kwargs)
        self.AmmoCls(**kwargs)

    def fire(self, **kwargs):
        """Handles request to fire a single item of stock.
        Will only fire if stock available and either shields are down 
        or weapon can fire regardless of shield state"""
        if not self.fire_when_shield_up and self.control_sys.shield_up:
            return self._shield_up()
        if not self._stock:
            return self._no_stock()
        else:
            self._fire(**kwargs)
            self.subtract_from_stock(1)

    def die(self):
        """Implement on subclass to perform any tidy-up operations, for 
        example cancelling scheduled calls"""
        pass

class Cannon(Weapon):
    """Extends Weapon to create a weapon that fires standard Bullets.
    NB Depends on ++control_sys++ for methods to evaluate Bullet attributes.

    Cannon automatically reloads a single round of ammunition each 
    ++reload_rate++ seconds, where reload_rate can be subsequently changed 
    via --set_cannon_reload_rate--"""
    
    def __init__(self, *args, reload_rate: Union[float, int] = 2, **kwargs):
        """++reload_rate++ in seconds to reload one round of ammunition"""
        super().__init__(*args, **kwargs)
        self.set_reload_rate(reload_rate)

    def set_reload_rate(self, reload_rate: Union[float, int]):
        """++reload_rate++ in seconds to reload one round of ammunition"""
        pyglet.clock.unschedule(self.auto_reload)
        pyglet.clock.schedule_interval(self.auto_reload, reload_rate)

    def _ammo_kwargs(self):
        return self.control_sys._bullet_kwargs()

    def auto_reload(self, dt):
        self.add_to_stock(1)

    def die(self):
        pyglet.clock.unschedule(self.auto_reload)
        super().die()

class HighVelocityCannon(Weapon):
    """Extends Weapon to create a weapon that fires high velocity Bullets 
    which are ++bullet_speed+factor++ quicker than the standard bullets 
    handled by ++control_sys++.
    NB Depends on ++control_sys++ for methods to evaluate Bullet attributes.
    """

    ammo_cls = {'blue': BulletHighVelocity,
                'red': BulletHighVelocityRed}

    def __init__(self, *args, bullet_speed_factor=5,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._factor = bullet_speed_factor

    def _ammo_kwargs(self):
        u = self.control_sys._bullet_initial_speed(factor=self._factor)
        kwargs = self.control_sys._bullet_kwargs(initial_speed=u)
        return kwargs

class FireworkLauncher(Weapon):
    """Extends Weapon to create a weapon that launches Fireworks.
    Internals:
    Fireworks will explode at a distance from the launcher determined as:
        +explosion_distance+ passed to --fire--, or if not passed...
        +dflt_explosion_distance+ passed to constructor, or if not passed
        Default +dflt_explosion_distance+ defined by constructor
    The resulting starburst will comprise a number of Bullets determined as:
        +num_bullets+ passed to --fire--, or if not passed...
        +dflt_num_bullets+ passed to constructor, or if not passed...
        +dflt_num_starburst_bullets+ passed to constructor of ++control_sys++ 
        or as otherwise defined by default by that constructor
    --margin-- describes in pixels the minimum distance from the centre of 
    the associated ship that a Firework can first appear without immediately 
    colliding with the firing ship.
    """

    ammo_cls = {'blue': Firework,
                'red': FireworkRed}

    def __init__(self, *args, dflt_explosion_distance=200,
                 dflt_num_bullets: Optional[int] = None, **kwargs):
        """Internals - defines default values as noted to cls.__doc__"""
        super().__init__(*args, **kwargs)
        self._dflt_exp_dist = dflt_explosion_distance
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
        
    @property
    def margin(self):
        return (self.control_sys.ship.width + Firework.img.width)//2 + 1

    def _ammo_kwargs(self, **kwargs) -> dict:
        u = self.control_sys._bullet_initial_speed(factor=2)
        kwargs = self.control_sys._bullet_kwargs(initial_speed=u, 
                                                 margin=self.margin, 
                                                 **kwargs)
        kwargs.setdefault('explosion_distance', self._dflt_exp_dist)
        kwargs.setdefault('num_starburst_bullets', self._dflt_num_bullets)
        kwargs.setdefault('starburst_bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs
        
    def fire(self, **kwargs):
        """Following can be included to **kwargs:
        +explosion_distance+, in pixels, from launcher
        +num_bullets+ to determine number of bullets that comprise the 
        resulting starburst
        If not passed then default values will be assigned as noted to 
        FireworkLauncher.__doc__
        """
        super().fire(**kwargs)

class SLD_Launcher(Weapon):
    """Extends Weapon to create a weapon that fires a SuperLaserDefence.
    Internals:
    The resulting starburst will comprise a number of Bullets determined as:
        +num_bullets+ passed to --fire--, or if not passed...
        +dflt_num_bullets+ passed to constructor, or if not passed...
        +dflt_num_starburst_bullets+ passed to constructor of ++control_sys++ 
        or as otherwise defined by default by that constructor
    """

    ammo_cls = {'blue': SuperLaserDefence,
                'red': SuperLaserDefenceRed}
    
    def __init__(self, *args, dflt_num_bullets: Optional[int] = None, 
                 **kwargs):
        """Internals - defines default values as noted to cls.__doc__"""
        super().__init__(*args, **kwargs)
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
        
    def _ammo_kwargs(self, **kwargs):
        kwargs = self.control_sys._ammo_base_kwargs()
        kwargs.setdefault('control_sys', self.control_sys)
        kwargs.setdefault('num_bullets', self._dflt_num_bullets)
        kwargs['distance_from_epi'] = self.control_sys.bullet_margin
        kwargs.setdefault('bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs

class MineLayer(Weapon):
    """Extends Weapon to create a weapon that lays Mines.
    Unlike most weapons, mines can be laid whilst the shield is up 
    (internals - provided for by defining class attribute 
    ---fire_when_shield_up-- as True for this class)
    Internals:
    Mine will explode after a time in seconds determined as:
        +fuse_length+ passed to --fire--, or if not passed...
        +dflt_fuse_length+ passed to constructor, or if not passed
        Default +dflt_fuse_length+ defined by constructor
    The resulting starburst will comprise a number of Bullets determined as:
        +num_starburst_bullets+ passed to --fire--, or if not passed...
        +dflt_num_bullets+ passed to constructor, or if not passed...
        +dflt_num_starburst_bullets+ passed to constructor of ++control_sys++ 
        or as otherwise defined by default by that constructor
    """
    
    ammo_cls = {'blue': Mine,
                'red': MineRed}

    fire_when_shield_up = True

    def __init__(self, *args, dflt_fuse_length=5,
                 dflt_num_bullets: Optional[int] = None, **kwargs):
        """Internals - defines default values as noted to cls.__doc__"""
        super().__init__(*args, **kwargs)
        self._dflt_fuse_length = dflt_fuse_length
        self._dflt_num_bullets =\
            dflt_num_bullets if dflt_num_bullets is not None\
            else self.control_sys._dflt_num_starburst_bullets
    
    def _ammo_kwargs(self, **kwargs) -> dict:
        for kw , v in self.control_sys._ammo_base_kwargs().items():
            kwargs[kw] = v
        kwargs.setdefault('control_sys', self.control_sys)
        kwargs.setdefault('fuse_length', self._dflt_fuse_length)
        kwargs.setdefault('num_starburst_bullets', self._dflt_num_bullets)
        kwargs.setdefault('bullet_speed',
                          self.control_sys.bullet_discharge_speed)
        return kwargs
        
    def fire(self, **kwargs):
        """Following can be included to **kwargs:
             +fuse_length+ to describe number of seconds until mine will 
             explode with the consequence of firing...
             +num_starburst_bullets+ out from its centre
        If not passed then default values will be assigned as noted to 
        MineLayer.__doc__
        """
        super().fire(**kwargs)

class ShieldGenerator(Weapon):
    """Extends Weapon to create a weapon that can generate an invincible 
    Shield, save if hit by another shield.

    --fire-- generates a shield. Only one shield can be generated at any 
    one time (internals - provided for by class attribute 
    ---fire_when_shield_up--- being False by default.
    
    Internals:
    Shield duration in seconds determined as:
        +duration+ passed to --fire--, or if not passed...
        ++duration++ passed to constructor, or if not passed
        Default value defined for constructor paramater ++duration++
    NB class does NOT advise the ++control_sys++ of shield status, instead 
    relying on the instantiated Shield objects.
    """
    
    ammo_cls = {'blue': Shield,
                'red': ShieldRed}

    def __init__(self, *args, duration=5, **kwargs):
        """++duration++ defines shield duration in seconds.
        Internals - defines default values as noted to cls.__doc__"""
        self._dflt_duration = duration
        super().__init__(*args, **kwargs)
                
    def _ammo_kwargs(self, **kwargs) -> dict:
        for kw , v in self.control_sys._ammo_base_kwargs().items():
            kwargs[kw] = v
        kwargs.setdefault('ship', self.control_sys.ship)
        kwargs.setdefault('duration', self._dflt_duration)
        return kwargs
        
    def fire(self, **kwargs):
        """Following can be included to **kwargs:
             +duration+ to describe number of seconds until Shield dies
        If not passed then default values will be assigned as noted to 
        Shield.__doc__
        """
        super().fire(**kwargs)


class RadiationGauge(Sprite):
    """8 stage colour guage that goes from empty (0) through 
    green(1) to red(7). Set --reading-- to required value
    
    --reset-- to reset the gauge to 0.
    """
    
    img_seq = load_image_sequence('rad_gauge_r2l_?.png', 8)
    
    def __init__(self, *args, **kwargs):
        super().__init__(self.img_seq[0], *args, **kwargs)
        self._reading = 0
        self._max_reading = len(self.img_seq) - 1

    @property
    def max_reading(self):
        return self._max_reading

    @property
    def reading(self):
        return self._reading

    @reading.setter
    def reading(self, value):
        self._reading = min(floor(value), self._max_reading)
        self.image = self.img_seq[self._reading]
                
    def reset(self):
        self.reading = 0

class RadiationGaugeRed(RadiationGauge):
    
    img_seq = load_image_sequence('rad_gauge_l2r_?.png', 8)

    
class RadiationMonitor(StaticSourceMixin):
    """Calculates a ++control_sys++'s ship's cumulative radiation 
    exposure and expresses value on a colour RadiationGauge.
    Assumes natural background radiation levels in an area defined 
    as ++cleaner_air++ with all other areas assumed of high level 
    radiation.
    
    Cleaner air zone defined as a InRect object which can be 
    passed to either the constructor or --set_field--. Can be 
    redefined at any time by passing +cleaner_air+ to either 
    --set_field-- or --reset--. If clearner_air passed as None 
    then all air assumed dirty, i.e. of high level radiation.

    Limits of exposure to natural background radiation and high 
    level radiation are set to, respectively, 68 and 20 seconds of 
    continuous exposure. Limits can be changed at any time via 
    --set_natural_exposure_limit()-- and --set_high_exposure_limit()-- 
    respectively.

    Plays warning audio when exposure reaches 70% of limit. Plays 
    further 'last words' audio when limit reached although ship only 
    killed when this audio is due to finish (such that if monitor is 
    --reset()-- before the last words have finished being spoken then 
    ship will be saved by the skin of its teeth).

    Gauge is a Sprite, accessible via the --gauge-- attribute. Client 
    responsible for positioning and attaching to any batch / group as 
    requried (which the client can do via the sprite's attributes).

    --start_monitoring-- starts monitoring, updating the exposure level 
    every 0.5 seconds.
    --halt-- stops monitoring, stops any audio and cancels any scheduled 
    call (including to kill the ship after the 'last words' audio has 
    concluded.
    --set_field(cleaner_air)-- to define field of clearner air, with all 
    other air considered dirty
    --reset-- as halt, then sets monitor and gauge to 0 before starting 
    monitoring. Can optionally take +cleaner_air+ in which case the 
    radiation field will be updated
    """
    
    warning = load_static_sound('nn_radiation_warning.wav')
    last_words = load_static_sound('nn_too_much_radiation.wav')
    
    def __init__(self, control_sys):
        super().__init__(sound=False)
        self.control_sys = control_sys
        self.gauge = self._get_gauge()
        
        self._exposure_level = 0
        self._exposure_limit = self.gauge.max_reading
        self._frequency = 0.5
        
        self._cleaner_air: Optional[InRect]
        self.set_field()
        self._nat_exposure_increment: int
        self.set_natural_exposure_limit()
        self._high_exposure_increment: int
        self.set_high_exposure_limit()
        
        self._warning_level = self._exposure_limit * 0.7
    
    def _get_gauge(self):
        return RadiationGauge()

    def reset(self, cleaner_air: Optional[InRect] = None):
        """Internals, halts first to prevent duplicate handlers and 
        to offer last minute repreive if last words being spoken.
        ++cleaner_air++ defined as the rectangular area represented 
        by an InRect object, with all other air considered dirty. If 
        passed then radiation field will be reset.
        """
        self.halt()
        self.exposure = 0
        self.gauge.reset()
        if cleaner_air is not None:
            self.set_field(cleaner_air)
        self.start_monitoring()

    def set_field(self, cleaner_air: Optional[InRect] = None):
        """Sets radiation field data.
        ++cleaner_air++ defined as the rectangular area represented 
        by an InRect object. All other air considered dirty. If 
        ++cleaner_air++ not passed or passed as None then all air 
        assumed dirty.
        """
        self._cleaner_air = cleaner_air
                
    def set_natural_exposure_limit(self, limit=68):
        """++limit++ is ship's limit of continuous background radiation 
        expsure in secs"""
        steps = limit / self._frequency
        self._nat_exposure_increment = self._exposure_limit / steps

    def set_high_exposure_limit(self, limit=20):
        """++limit++ is ship's limit of continuous high level radiation 
        exposure in secs"""
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
        if self._cleaner_air is None:
            return True
        ship_pos = (self.control_sys.ship.x, self.control_sys.ship.y)
        return not self._cleaner_air.inside(ship_pos)

    @property
    def exposure(self):
        return self._exposure_level

    @exposure.setter
    def exposure(self, value):
        """Ensure exposure level no lower than 0 and no higher than 
        the exposure limit"""
        value = min(value, self._exposure_limit)
        value = max(value, 0)
        self._exposure_level = value
        self.gauge.reading = value

    def _increment_high_exposure(self):
        self.exposure += self._high_exposure_increment

    def _increment_nat_exposure(self):
        self.exposure += self._nat_exposure_increment
    
    def _update(self, dt):
        prev = self.exposure
        if self._in_high_rad_zone():
            self._increment_high_exposure()
        else:
            self._increment_nat_exposure()
        new = self.exposure
        if (prev < self._warning_level) and (new >= self._warning_level):
            self._warn()
        if new >= self._exposure_limit:
            self._kill_ship()

    def _stop_monitoring(self):
        pyglet.clock.unschedule(self._update)

    def start_monitoring(self):
        pyglet.clock.schedule_interval(self._update, self._frequency)

    def halt(self):
        """Stops monitoring and cancels any scheduled calls"""
        self._stop_monitoring()
        self.stop_sound()
        pyglet.clock.unschedule(self.__kill_ship)

class RadiationMonitorRed(RadiationMonitor):
    
    warning = load_static_sound('mr_radiation_warning.wav')
    last_words = load_static_sound('mr_too_much_radiation.wav')

    def _get_gauge(self):
        return RadiationGaugeRed()

#GLOBALS
SHIELD_DURATION = 7 # default shield duration

INITIAL_AMMO_STOCKS = {Cannon: 9,
                       HighVelocityCannon: 7,
                       FireworkLauncher: 2,
                       SLD_Launcher: 2,
                       MineLayer: 2,
                       ShieldGenerator: 2}

settings = ['SHIELD_DURATION', 'INITIAL_AMMO_STOCKS']
pyroids.config_import(vars(), settings)

class ControlSystem(object):
    """Houses / Manages:
        multiple weapons (each a subclass of Weapon) that can be 
          fired from a Ship
        Shields
        Radiation Monitor
    Only one Ship can be associated with the ControlSystem at a time. 
    POST instantiation a ship associated with the ControlSystem can be 
    generated via --new_ship-- (which returns the generated ship). 
    Subsequent ships can be generated via the same method which has the 
    effect of reinitalising the control system (by resetting ammo 
    stocks to initial levels and resetting the radiation monitor). A single 
    control system for multiple ships allows for a game to employ a single 
    ControlSystem per player.
    
    Depends on the generated --ship--'s attributes for data on location, 
    orientation and speed.

    The weapons available to the object are described by the instance 
    attribute --_weapons-- which takes a dictionary with Weapon Classes 
    as keys and values as of the corresopnding Weapon Class, with those 
    instances being the weapons available to the object. NB each Weapon 
    class is a subclass of Weapon. Each class of weapon can be added to 
    --weapons-- via a corresopnding method:
        Cannon:  --_add_cannon--
        HighVelocityCannon  --_add_hv_cannon--
        FireworkLauncher  --_add_firework_launcher--
        SLD_Launcher  --_add_sld_launcher--
        MineLayer       --_add_minelayer--
        ShieldGenerator  --_add_shieldgenerator--
    
    Internals. Subclasses can intercept the above methods to pass through 
    additional kwargs to the Weapon subclass.
    In turn each the methods call --add_weapon-- which instantiates the 
    actual weapon and provides for default initial stock if not otherwise 
    defined (see Stock below).
    In turn, --add_weapons()-- method adds weapons via calls to the above 
    methods and the constructor calls --add_weapons()--.
    NB each weapon will look at the ++control_sys++.color to determine 
    the class of ammo that the weapon should fire (this is handled by the 
    base class constructor Weapon.__init__).

    Stocks
    Initial stocks set by the constructor by the --_get_initial_stock-- 
    which returns a dictionary with Weapon classes as keys and values as 
    integers which represent the corresponding inital stock for that 
    Weapon. Internals. Each Weapon class takes --initial_stock-- as a 
    parameter. If not otherwise provided, the --add_weapon-- passes the 
    corresponding default value as returned by --_get_initial_stock--.
    Accordingly, subclasses can customise initial stocks by either 
    overriding or extending --_get_initial_stocks-- or overriding or 
    extending the corresponding --_add_'weapon'-- method (for example 
    --_add_cannon-- to pass through an +initial_stock+ kwarg.
    
    Constructor provides for setting default values for the following, 
    which in each case take the default value noted if parameter not 
    otherwise passed:;
    ++bullet_discharge_speed++=200,
    ++dflt_num_starburst_bullets++=12,
    ++shield_duration++=10

    Properties
    --weapons-- returns a list of weapons (i.e. a list containing one 
    instance of each class of weapon in --_weapons--)
    --shield_up-- allows Weapon subclasses to ask the question of the 
    control system and hence decide whether can fire given the shield's 
    current status (handled within the Weapon object's --fire-- method.
    NB --set_shield_status-- method is provided for the associated 
    ShieldGenerator to advise when shields are raised and lowered.

    Methods and Attibutes

    --radiation_monitor-- in turn holds .gauge which is a Sprite that 
    the client can position to provide for a visual monitor of current 
    radiation level.

    --new_ship-- as above, creates an initial or subsequent ship to be 
    associated with the control system.

    NB class attributes ShipCls and RadiationMonitor hold dictionaries 
    that describe the class/subclass of these class that should be 
    instantiated according to the player ++color++ passed to the 
    constructor.

    --fire(Weapon)-- fires one round of the Weapon passed as the class 
    of the Weapon to be fired. Passes instruction on ot the Weapon's 
    own --fire--. NB does NOT consider whether the shield is up on not, 
    rather leaves that to the Weapon's own --fire-- method to assess.

    --die()-- Carries out end-of-life tidy-up operations, to include 
    instigating the die method of each managed weapon.

    The following properties, attributes and methods are provided to aid 
    associated Weapons:

    --bullet_margin-- describes in pixels the minimum distance from the 
    centre of the associated ship that a bullet can first appear without 
    immediately colliding with the firing ship.
    Bullet speeds:
    --bullet_discharge_speed-- returns the current bullet_discharge_speed
    --_bullet_initial_speed()-- returns bullet_discharge_speed plus the 
    ship's current speed and provides for the bullet_discharge_speed 
    component to be factored
    The following methods aid Weapons by returning appropriate kwargs 
    for passing to the contructor of certain ammunition classes:
    --_ammo_base_kwargs--
    --_bullet_base_kwargs--
    --_bullet_kwargs--
    """
    
    ShipCls = {'blue': Ship,
                'red': ShipRed}

    RadiationMonitorCls = {'blue': RadiationMonitor,
                           'red': RadiationMonitorRed}

    def __init__(self, color: Union['blue', 'red'] = 'blue',
                 bullet_discharge_speed=200, dflt_num_starburst_bullets=12):
        self.color = color
        self.ship: Ship # set by --new_ship--
        self.radiation_monitor = self.RadiationMonitorCls[color](self)
        self._shield_duration = SHIELD_DURATION
        self._dflt_num_starburst_bullets = dflt_num_starburst_bullets
        self._bullet_discharge_speed = bullet_discharge_speed
                       
        self._initial_stock = INITIAL_AMMO_STOCKS

        self._weapons = {Cannon: None,
                         HighVelocityCannon: None,
                         FireworkLauncher: None,
                         SLD_Launcher: None,
                         MineLayer: None,
                         ShieldGenerator: None}

        self.add_weapons()
        self._shield_up = False

    def _set_initial_stocks(self):
        for Weapon, weapon in self._weapons.items():
            weapon.set_stock(self._initial_stock[Weapon])

    def new_ship(self, **kwargs) -> Ship:
        self.ship = self.ShipCls[self.color](control_sys=self, **kwargs)
        self._set_initial_stocks()
        self.radiation_monitor.reset()
        return self.ship

    def ship_killed(self):
        """Called when ship killed"""
        self.radiation_monitor.halt()

    @property
    def weapons(self) -> List[Weapon]:
        return self._weapons.values()

    @property
    def bullet_margin(self):
        return (self.ship.image.width + Bullet.img.width)//2 +2

    @property
    def shield_up(self) -> bool:
        return self._shield_up
                
    def set_shield_status(self, up: bool):
        self._shield_up = up

    @property
    def bullet_discharge_speed(self):
        return self._bullet_discharge_speed

    @bullet_discharge_speed.setter
    def bullet_discharge_speed(self, value):
        self._bullet_discharge_speed = max(value, self.ship._speed_cruise)

    def set_cannon_reload_rate(self, reload_rate: Union[float, int]):
        self._weapons[Cannon].set_reload_rate(reload_rate)

    def _add_weapon(self, Weapon: Weapon, **kwargs):
        self._weapons[Weapon] = Weapon(self, **kwargs)

    def _add_cannon(self, **kwargs):
        self._add_weapon(Cannon, **kwargs)

    def _add_hv_cannon(self, **kwargs):
        self._add_weapon(HighVelocityCannon, **kwargs)

    def _add_sld_launcher(self, **kwargs):
        self._add_weapon(SLD_Launcher, **kwargs)
        
    def _add_firework_launcher(self, **kwargs):
        self._add_weapon(FireworkLauncher, **kwargs)

    def _add_minelayer(self, **kwargs):
        self._add_weapon(MineLayer, **kwargs)
        
    def _add_shieldgenerator(self, **kwargs):
        kwargs.setdefault('duration', self._shield_duration)
        self._add_weapon(ShieldGenerator, **kwargs)
    
    def add_weapons(self):
        self._add_cannon()
        self._add_hv_cannon()
        self._add_sld_launcher()
        self._add_firework_launcher()
        self._add_minelayer()
        self._add_shieldgenerator()
        
    def fire(self, weapon: Type[Weapon], **kwargs):
        self._weapons[weapon].fire(**kwargs)

    def process_pickup(self, pickup):
        """Where +pickup+ is an instance of PickUp, adds the pickup 
        ammunition to the corresponding weapon"""
        self._weapons[pickup.Weapon].add_to_stock(pickup.number_rounds)

    def _bullet_initial_speed(self, factor=1) -> int:
        """Returns bullet's intiial speed, with discharge speed factored 
        by any +factor+"""
        return self.ship.speed + (self.bullet_discharge_speed * factor)

    def _ammo_base_kwargs(self) -> dict:
        """Internals - returns as a dictionary the following kwargs that may 
        be of use to pass to an ammunition class constructor:
        'x' - ship's current x co-ordinate
        'y' - ship's current y co-ordinate
        'batch' - batch object to which ship is drawn
        """
        ship = self.ship
        kwargs = {'x': ship.x,
                  'y': ship.y,
                  'batch': ship.batch,
                  'group': ship.group}
        return kwargs

    def _bullet_base_kwargs(self, margin: Optional[int] = None) -> dict:
        """Internals - returns as a dictionary the following kwargs for the 
        Bullet class: 'x', 'y', 'batch', 'control_sys' where x and y are 
        co-ordinates such that the bullet will first appear in front of the 
        --ship--'s nose at a distance of +margin+ from the ship's centre, i.e.
        +margin+ takes minimum distance from the ship's centre that a bullet 
        can first appear without collidiing with the ship. Defaults to 
        --bullet_margin-- if not passed.
        """
        margin = margin if margin is not None else self.bullet_margin
        x_, y_ = vector_anchor_to_rotated_point(margin, 0, self.ship.rotation)
        kwargs = self._ammo_base_kwargs()
        kwargs['control_sys'] = self
        kwargs['x'] += x_
        kwargs['y'] += y_
        return kwargs

    def _bullet_kwargs(self, margin: Optional[int] = None, **kwargs):
        """Provides kwargs for Bullet class to fire bullet out the nose of 
        the --ship--.
              'initial_speed' defaults to --_bullet_speed-- plus 
            the ship's current speed (to ensure a moving ship doesn't fly 
            straight into its own bullet).
              'initial_rotation' defaults to the ship's rotation to ensure 
            the bullet travels in the same direction as the ship's facing.
        +kwargs+ can be passed to override the above and/or include 
        additional kwargs although cannot include kwargs 'x', 'y' or 'batch', 
        which are necessarily evaluted internally.
        """
        assert False not in \
            [ kwarg not in kwargs for kwarg in ['x', 'y', 'batch'] ]
        for kwarg, value in self._bullet_base_kwargs(margin=margin).items():
            kwargs[kwarg] = value
        kwargs.setdefault('initial_speed', self._bullet_initial_speed())
        kwargs.setdefault('initial_rotation', self.ship.rotation)
        return kwargs

    def die(self):
        """Carries out end-of-life tidy-up operations, to include 
        instigating the die method of each managed weapon"""
        self.radiation_monitor.halt()
        for weapon in self.weapons:
            weapon.die()

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
    """Creates randomly positioned static sprite that represents an 
    ammunition 'pick up' available to a particular player, as identified 
    by the class attribute ---color---.

    Ammunition is for --Weapon-- which is randomly assigned a Weapon from 
    the keys of class attribute ---info---. The number of rounds of 
    ammunition is --number_rounds-- which is assigned a random value between 
    and inclusive of the (min, max) value assigned to the corresponding 
    weapon in ---info---.
    
    During the first ----COLLECTABLE_IN---- seconds the sprite will flash 
    and cannot be interacted with. Thereafter:
        a collision with either a bullet or a non-friendly shield (i.e. not 
          of the colour ---color---) will result in the pick up being killed 
          with the consequence:
            explosion animation if pick up represnted shields, otherwise...
            starburst with origin as the pick up, with number of bullets 
              corresponding with the number of ammunition rounds the pick up 
              held. Starburst bullets will be attributed to the weapons 
              system responsible for the bullet / shield that killed the 
              pick up
        a collision with a friendly ship will result in playing the sound 
          ---snd_pickup--- and the pick up deceasing itself. NB such a 
          collision will NOT result in the pick up advising the friendly ship 
          that it has picked up the pick up NOR will it result in the pick-up 
          deceasing. IT IS THE FRIENDLY SHIP'S --collided_with-- METHOD'S 
          RESPONSIBILITY TO HANDLE THE PICK UP OF AMMUNITION
        if a collision has not occured within a further 
          ----COLLECTABLE_FOR---- seconds then the pick up deceases itself, 
          flashing rapidly during the last ---final_secs---.
    
    Properties
    --dropping-- boolean indicating if pickup is within the first 
    ----COLLECTABLE_IN---- seconds of its life (i.e. supply still dropping)
    """
    
    img = load_image('pickup_blue.png', anchor='center')
    snd = load_static_sound('supply_drop_blue.wav')
    snd_pickup = load_static_sound('nn_resupply.wav')

    info = PICKUP_AMMO_STOCKS
    
    color = 'blue'
    final_secs = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_randomly()
        self.Weapon = random.choice(list(self.info.keys()))
        self.number_rounds = random.randint(*self.info[self.Weapon])
        ammo_img = self.Weapon.ammo_cls[self.color].img_pickup
        self.ammo_sprite = Sprite(ammo_img, self.x, self.y, 
                                  batch=self.batch, group=self.group)
        
        self.flash_start(frequency=4)
        self._collectable = False
        self.schedule_once(self._now_collectable, COLLECTABLE_IN)

    @property
    def dropping(self):
        return not self._collectable

    def _now_collectable(self, dt: Optional[float] = None):
        self.flash_stop()
        self._collectable = True
        self.schedule_once(self._dying, COLLECTABLE_FOR - self.final_secs)

    def _dying(self, dt: Optional[float] = None):
        self.flash_start(frequency=8)
        self.schedule_once(self.die, self.final_secs)

    @property    
    def _pick_up_ship_cls(self):
        return Ship

    def play_pickup(self):
        self.sound(self.snd_pickup)

    def _starburst(self):
        Starburst(x=self.x, y=self.y, batch=self.batch, group=self.group,
                  control_sys=self._killer_control_sys,
                  num_bullets=self.number_rounds, 
                  bullet_speed=275)

    def _explode(self):
        """Play one off 'explosion' animation in the pickup's position and 
        of the same size as the pickup"""
        Explosion(x=self.x, y=self.y, scale_to=self, 
                  batch=self.batch, group=self.group)

    @property
    def _NotFriendlyShieldCls(self):
        return ShieldRed

    def collided_with(self, other_obj):
        """Enacts consequence for self of collision with +other_obj+"""
        if self.dropping:
            return
        elif isinstance(other_obj, Bullet):
            self._killer_control_sys = other_obj.control_sys
            self.kill()
        elif type(other_obj) is self._NotFriendlyShieldCls:
            self._killer_control_sys = other_obj.ship.control_sys
            self.kill()
        elif type(other_obj) is self._pick_up_ship_cls:
            self.play_pickup()
            self.die()

    def kill(self):
        self._explode()
        if self.Weapon is not ShieldGenerator:
            self._starburst()
        super().kill()

    def die(self, dt: Optional[float] = None):
        super().die(stop_sound=False)

    def refresh(self, dt):
        """Internals - overrides inherited method to do nothing, i.e. does 
        not refresh position on screen such that x and y remain unchanged"""
        pass

class PickUpRed(PickUp):

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