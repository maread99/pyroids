#! /usr/bin/env python

"""Modules offes:
    Helper functions to manipulate and load pyglet objects:
        centre_image()
        centre_animiation()
        load_image()
        load_animiation()
        anim()
        load_static_sound()
        num_from_symbol()
        distance()
        vector_anchor_to_rotated_point()

    Helper Classes:
        AvoidRect defines a rectangular area around ++sprite++
    
    Classes that extend pyglet classes to provide additional functionality:
        AdvSprite(Sprite) adds functionality to provide for scaling 
        obj against another obj
        
        OneShotAnimatedSprite(AdvSprite) one animation and gone

        PhysicalSprite(AdvSprite) adds limited 2D physics to move and rotate 
        sprites
        
        InteractiveSprite(PhysicalSprite) adds keyboard events user-interface 
"""

import random, math, time
import collections.abc
from itertools import combinations
from copy import copy
from typing import Optional, Tuple, List, Union, Sequence, Callable
from functools import wraps

import pyglet
from pyglet.image import Texture, TextureRegion, Animation
from pyglet.sprite import Sprite
from pyglet.media import StaticSource

from .audio_ext import StaticSourceMixin
from .. import physics

def centre_image(image: Union[TextureRegion, Sequence[TextureRegion]]):
    """Sets +image+ anchor points to centre of image
    +image+ can be passed as single image object or sequence of image 
    objects"""
    if not isinstance(image, collections.abc.Sequence):
        image = [image]
    for img in image:
        img.anchor_x = img.width // 2
        img.anchor_y = img.height // 2

def centre_animation(animation: Animation):
    """Centres all +animation+ frames"""
    for frame in animation.frames:
            centre_image(frame.image)

def load_image(filename: str, anchor='origin') -> TextureRegion:
    """loads image with +filename+ from resource and returns Image object.
    +anchor+ sets anchor points to reflect 'origin' or 'center' of image"""
    assert anchor in ['origin', 'center']
    img = pyglet.resource.image(filename)
    if anchor == 'center':
        centre_image(img)
    return img

def load_image_sequence(filename: str, num_images: int, anchor='origin',
                        placeholder='?') -> List[pyglet.image.Texture]:

    """Returns a list comprising +num_images+ Textures with those 
    textures loaded from files with names dervied from +filename+ 
    and sequentially enumerated in position of +filename+ that is 
    represented with a +placeholder+ character. First image enumerated 
    0. For example:
    filename='my_img_seq_?.png', num_images=3, placeholder='?' would 
    return a sequence of images loaded from the following files:
        'my_img_seq_0.png'
        'my_img_seq_1.png'
        'my_img_seq_2.png'
    +anchor+ passed on to load_image().
    """
    return [ load_image(filename.replace(placeholder, str(i)), anchor=anchor) 
            for i in range(0, num_images) ]

def load_animation(filename: str, anchor='origin') -> Animation:
    """loads animation with +filename+ from resource and returns 
    Animation object. +filename+ could be, for example, a .gif file.
    +anchor+ sets anchor points of animation's images to reflect 
    'origin' or 'center' of image"""
    assert anchor in ['origin', 'center']
    animation = pyglet.resource.animation(filename)
    if anchor == 'center':
        centre_animation(animation)
    return animation

def anim(filename, rows, cols, frame_duration=0.1, loop=True) -> Animation:
    """Where +filename+ is an image file in resource directory which itself 
    describes subimages distributed over +rows+ and +columns+, returns an 
    Animation object comprising those subimages with each frame showing for 
    +frame_duration+ in seconds.
    """
    img = pyglet.resource.image(filename)
    image_grid = pyglet.image.ImageGrid(img, rows, cols)
    animation = image_grid.get_animation(frame_duration, True)
    centre_animation(animation)
    return animation

def load_static_sound(filename: str) -> StaticSource:
    """Loads a static sound for sound file with +filename+ in resouce 
    directory and returns StaticSound object.
    In order to have immediate playback available direct from 
    StaticSound.play() without delay, creates the player (which otherwise 
    takes sufficient time that on the first occasions .play() is executed 
    a game will freeze momentarily) now.
    NB player created by playing the created StaticSound, albeit with the 
    track immediately skipped. Additionally turns the volume off in the 
    meantime to avoid a 'crackle' when the game starts and the very start of 
    the audio plays"""
    sound = pyglet.resource.media(filename, streaming=False)
    player = sound.play()
    vol = player.volume
    player.volume = 0
    player.next_source()
    player.volume = vol
    return sound

def num_from_symbol(symbol) -> int:
    """Where +symbol+ is an integer which represents a numercial keyboard key 
    (either of the top number row or number pad) and is represented by a 
    constant defined in pyglet.window.key (for example NUM_3, _7 etc) will 
    return an integer representing symbol"""
    symbol_string = pyglet.window.key.symbol_string(symbol)
    num = int(symbol_string[-1])
    return num

def distance(sprite1: Sprite, sprite2: Sprite) -> int:
    """Returns distance between +sprite1+ and +sprite2+ in pixels"""
    return physics.distance(sprite1.position, sprite2.position)

def vector_anchor_to_rotated_point(x, y, rotation) -> Tuple[int, int]:
    """Where +x+ and +y+ describe a point relative to an image's anchor 
    when rotated 0 degrees, returns the vector, as (x, y) from the anchor 
    to the same point if the image were rotated by +rotation+ degrees.
    +rotation+ passed in degrees, clockwise positive, 0 pointing 'left', 
    i.e. as returned by a sprite's -rotation- attribute.
    """
    dist = physics.distance((0,0), (x, y))
    angle = math.asin(y/x)
    rotation = -math.radians(rotation)
    angle_ = angle + rotation
    x_ = dist * math.cos(angle_)
    y_ = dist * math.sin(angle_)
    return (x_, y_)

class InRect(object):
    """Defines a rectangle from parameters passed to the constructor and 
    offers method --inside-- which takes a set of coordinates and returns 
    a boolean indicating whether they fall within the rectangle.
    
    Each parameter passed to the construtor is stored in an attribute of 
    the same name:
    --x_from--
    --x_to--
    --y_from--
    --y_to--
         Other attributes:
    --width-- rectangle width
    --height-- rectangle width
    
    Methods:
    --inside(Tuple: [int, int])--
    """
    
    def __init__(self, x_from: int, x_to: int, y_from: int, y_to: int):
        """For x coordinate increaingly positive moving right.
        For y coordinate increaingly positive moving upward.
        """
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to
        self.width = x_to - x_from
        self.height = y_to - y_from

    def inside(self, position: Tuple[int, int]) -> bool:
        """Where +position+ is a 2-Tuple indiciating a position (x, y), 
        reutrns boolean advising if position lies within the rectangle"""
        x = position[0]
        y = position[1]
        if self.x_from <= x <= self.x_to and self.y_from <= y <= self.y_to:
            return True
        else:
            return False

class AvoidRect(InRect):
    """Intended use is to define an area which is to be avoided when 
    positioning a ++sprite++.
    
    Extends InRect to define a rectangle that encompasses ++Sprite++ plus 
    any ++margin++. Inherited --inside-- method takes x, y co-ordinates 
    and returns a boolean indicating whether the co-ordinate falls within 
    the rectangle.

    Additional Attributes
        --sprint-- takes ++sprite++
        --margin-- takes ++margin++
    """
    
    def __init__(self, sprite: Sprite, margin: Optional[int] = None):
        """See cls.__doc__"""
        self.sprite = Sprite
        self.margin = margin
        
        if isinstance(sprite.image, Animation):
            anim = sprite.image
            anchor_x = max([f.image.anchor_x for f in anim.frames])
            anchor_y = max([f.image.anchor_y for f in anim.frames])
            width = anim.get_max_width()
            height = anim.get_max_height()
        else:
            anchor_x = sprite.image.anchor_x
            anchor_y = sprite.image.anchor_y
            width = sprite.width
            height = sprite.height

        x_from = sprite.x - anchor_x - margin
        width = width + (margin * 2)
        x_to = x_from + width

        y_from = sprite.y - anchor_y - margin
        height = height + (margin * 2)
        y_to = y_from + height

        super().__init__(x_from, x_to, y_from, y_to)


class SpriteAdv(Sprite, StaticSourceMixin):
    """Extends functionality of standard Sprite class to provide for 
    deceasing sprites (see Life and End-of-Life below), keeping a 
    register of live sprites, accompanying sound and extended 
    scheduling.
    
    Image:
    __init__ assumes image as held in class attribute ---img--- if not 
    otherwise passed as a kwargs ++img++.

    Sound provided for by StaticSourceMixin. See StaticSourceMixin.__doc__.
    
    Life and End-of-Life
    Live sprites are included to the class attbribute list ---live_sprites---
    and they are removed when deceased.
    --live-- property offers a boolean indicating if a sprite is in 
    ---live_sprites---.
    DIE. The instance method .die() is defined to provide for end-of-life 
    operations when the sprite dies naturally. At this level effectively 
    extends and renames the inherited --delete()-- method to additionally 
    unschedule any future calls to instance methods, remove the sprite 
    from ---live_sprites--- and execute any callable passed as ++_on_die++.
    Subclasses should NOT OVERRIDE the .die() method but rarther extend to 
    provide for any additional end-of-life operations.
    KILL. The instance method .kill() is defined to provide for end-of-life 
    tidy up operations when the sprite dies prematurely. At this level only 
    executes any callable passed as ++_on_kill++ and then calls --die()--.
    Subclasses should NOT override this method but rather extend to provide 
    for any additional premature end-of-life tidy-up operations.
    NB for games, the above might resolve as kill representing an object's 
    life ending in-game whilst die, on its own, represnting an object's life 
    ending out-of-game.

    Scheduling
    --schedule_once-- and --schedule_all-- provide an interface to 
    pyglet scheduling which allows for all scheduled events to be 
    subsequently collectively (--unschedule_all--), or individually 
    (--unschedule--).

    CLASS METHODS:
    --stop_all_sound-- will pause the 

    --cull_all-- will kill all live sprites (via sprites' .kill method)
    --decease_all-- will decease all live sprites (via sprites' .die method)
    --cull_selective(exceptions)-- will kill all live sprites except for 
    +exceptions+
    --decease_selective(exceptions)-- will decease all live sprites except 
    for +exceptions+
    
    PROPERTIES
    --live-- returns boolean indicating if object is a live sprite.

    METHODS (in additional to those inherited):
        --scale_to(obj)-- to scale object to size of +obj+
        --flash_start-- to make the sprite flash
        --flash_stop-- to stop the sprite flashing
        --toggle_visibility--
        --schedule_once-- to schedule with pyglet a future call to an instance 
        method
        --schedule_interval-- to schedule with pyglet regular future calls to 
        an instance method
        --unschedule-- to unschedule a future call(s) to an instance method
        --unschedule_all-- to unschedule all call(s) to instance methods 
        previously scheduled via either --schedule_once-- or 
        --schedule_interval--.
        --die-- see Life and End-of-Life section above.
    """
    
    img: Union[Texture, Animation]
    snd: StaticSource

    live_sprites = []

    @classmethod
    def stop_all_sound(cls):
        for sprite in cls.live_sprites:
            sprite.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        for sprite in cls.live_sprites:
            sprite.resume_sound()

    @classmethod
    def _end_lives_all(cls, kill=False):
        """Ends the life of all live sprites, without exception.
        Raises AssertionError in event a live sprite evades death.
        If +kill+ True then will kill all sprites, otherwise just 
        deceases them.
        Internals - if +kill+ True then will kill each live sprite 
        via the sprite's .kill method, otherwise decesaes each 
        via the sprite's .die method"""
        for sprite in cls.live_sprites[:]:
            if kill:
                sprite.kill()
            else:
                sprite.die()
        assert not cls.live_sprites, "following sprites still alive"\
            " after ending all lives: " + str(cls.live_sprites)

    @classmethod
    def _end_lives_selective(cls, exceptions: Optional[List[Sprite]] = None,
                             kill=False):
        """Ends the life of all live sprites except those inlcuded to any 
        +exceptions+ passed as any combination of sprite objects or 
        subclasses of Sprite, in the later case all instances of those 
        subclasses will be spared.
        If +kill+ True then sprites will be killed, otherwise merely 
        deceased.
        Internals - executes either the .kill (if +kill+ True_ or .die 
        method of each live sprite not spared by +exceptions+. Concludes 
        by asserting that any remaining live sprites are explicitely spared 
        by +exceptions+
        """
        if not exceptions:
            return cls._end_lives_all(kill=kill)
        exclude_classes = []
        exclude_objs = []
        for exception in exceptions:
            if type(exception) == type:
                exclude_classes.append(exception)
            else:
                assert isinstance(exception, Sprite)
                exclude_objs.append(exception)
        for sprite in cls.live_sprites[:]:
            if sprite in exclude_objs or type(sprite) in exclude_classes:
                continue
            else:
                if kill:
                    sprite.kill()
                else:
                    sprite.die()
        for sprite in cls.live_sprites:
            assert type(sprite) in exceptions or sprite in exceptions

    @classmethod
    def cull_all(cls):
        """Kills all live sprites without exception.
        Internals - executes the .kill method of each live sprite.
        """
        cls._end_all_lives(kill=True)

    @classmethod
    def decease_all(cls):
        """Deceases all live sprites without exception.
        Internals - executes the .die method of each live sprite."""
        cls._end_all_lives(kill=False)

    @classmethod
    def cull_selective(cls, exceptions: Optional[List[Sprite]] = None):
        """Kills all live sprites except those inlcuded to any 
        +exceptions+ passed as any combination of sprite objects or 
        subclasses of Sprite, in the later case all instance of those 
        subclasses will be spared.
        Internals - sprites killed via their .kill method
        """
        cls._end_lives_selective(exceptions=exceptions, kill=True)

    @classmethod
    def decease_selective(cls, exceptions: Optional[List[Sprite]] = None):
        """Deceases all live sprites except those inlcuded to any 
        +exceptions+ passed as any combination of sprite objects or 
        subclasses of Sprite, in the later case all instance of those 
        subclasses will be spared.
        Internals - sprites deceased via their .die method
        """
        cls._end_lives_selective(exceptions=exceptions, kill=False)

    def __init__(self, sound=True, sound_loop=False, 
                 on_kill: Optional[Callable] = None,
                 on_die: Optional[Callable] = None, **kwargs):
        """Extends inherited constructor to:
            Pass 'img' as ---img--- if not otherwise recieved as ++img++.
            play --sound-- at end of instantiation if ++sound++ True, will 
            loop if ++sound_loop++
        """
        kwargs.setdefault('img', self.img)
        self._on_kill = on_kill if on_kill is not None else lambda: None
        self._on_die = on_die if on_die is not None else lambda: None
        super().__init__(**kwargs)
        self.live_sprites.append(self)
        self._scheduled_funcs = []

        StaticSourceMixin.__init__(self, sound, sound_loop)
        
    @property
    def live(self) -> bool:
        """return Boolean indicating if object is a live sprite"""
        return self in self.live_sprites

    def toggle_visibility(self, dt: Optional[float] = None):
        """Internals - +dt+ provides for calling the function as a pyglet 
        scheduled event"""
        self.visible = not self.visible

    def flash_stop(self, visible=True):
        self.unschedule(self.toggle_visibility)
        self.visible = visible

    def flash_start(self, frequency: Union[float, int] = 3):
        """Starts sprite flashing at +frequence+ per second. Flashing can 
        be stopped by call to --flash_stop()--
        Internals - first stops any existing flashing to provide for 
        consecutive calls to method to change frequency.
        """
        self.flash_stop()
        self.schedule_interval(self.toggle_visibility, 1/(frequency*2))

    def scale_to(self, obj: Union[Sprite, Texture]):
        """Scales object to same size as +obj+"""
        x_ratio = obj.width / self.width
        self.scale_x = x_ratio
        y_ratio = obj.height / self.height
        self.scale_y = y_ratio

    # CLOCK SCHEDULE
    def _add_to_schedule(self, func):
        self._scheduled_funcs.append(func)
        
    def schedule_once(self, func: Callable, time: Union[int, float]):
        """Schedules a call to +func+ in +time+ seconds
        NB +func+ should accommodate first parameter received (after self) 
        as the time elapsed since call scheduled - will be passed on by the 
        pyglet implementation as the actual elapsed time.
        """
        pyglet.clock.schedule_once(func, time)
        self._add_to_schedule(func)

    def schedule_interval(self, func: Callable, freq: Union[int, float]):
        """Schedules a call to +func+ every +freq+ seconds. NB +func+ should 
        accommodate first parameter received (after self) as the time elapsed 
        since call scheduled - will be passed on by the pyglet implementation 
        as the actual elapsed time.
        """
        pyglet.clock.schedule_interval(func, freq)
        self._add_to_schedule(func)

    def _remove_from_schedule(self, func):
        """Internals - ignores calls to unschedule events that have not 
        been previously scheduled, in which repsect mirrors pyglet's 
        clock.unschedule behaviour
        """
        try:
            self._scheduled_funcs.remove(func)
        except ValueError:
            pass

    def unschedule(self, func):
        """Unschedule future call to +func+ where call previously scheduled 
        with either schedule_once or schedule_interval"""
        pyglet.clock.unschedule(func)
        self._remove_from_schedule(func)

    def unschedule_all(self):
        """Unschedules all future calls to instance methods that were 
        scheduled via either --schedule_once-- or --schedule_interval--
        """
        for func in self._scheduled_funcs[:]:
            self.unschedule(func)

    # END-OF-LIFE
    def kill(self):
        """Kills object prematurely.
        Internals - at SpriteAdv level simply calls die(). Subclasses 
        should extend to execute premature end-of-life tidy up operations
        """
        self._on_kill()
        self.die()
        
    def die(self, stop_sound=True):
        """Extends and renames inherited --delete()-- method to carry out 
        additional end-of-life operations, specifically to unschedule any 
        future calls to any instance method"""
        self.unschedule_all()
        if stop_sound:
            self.stop_sound()
        self.live_sprites.remove(self)
        super().delete()
        self._on_die()

class OneShotAnimatedSprite(SpriteAdv):
    """Extends SpriteAdv to provide one shot animation
    
    Simply uses the --on_animation_end-- event handler to deceease itself 
    when the animation ends"""
        
    def on_animation_end(self):
        """Event handler"""
        self.die()

class PhysicalSprite(SpriteAdv):
    """Extends SpriteAdv to include a functionality that allows sprite to 
    move in accordance with basic 2D physics.

    NB Sprite images (be they defined as ---img--- or passed as ++img++)
    should have anchor points set to centre of image. NB The following 
    methods of the pyglet_lib module all provide for centering images, 
    either to centre image to be passed as ++img++ or to directly load a 
    centre image to be assigned to ---img---, e.g. 
    ---img--- = load_image('filename.png', 'centre'):
        load_image()
        load_animation()
        anim()
    
    INTERNAL PHYSICS
    --refresh(dt)-- should be CALLED BY CLIENT to move (via --_move(dt)--) 
    and rotate (via --_rotate(dt)--) sprite to a new position / orientation 
    given its current velocities and rotation and +dt+, the time 
    elapsed in seconds since the object was last moved. NB +dt+ has to be 
    passed by the client, i.e. as the +dt+ passed on by a pyglet scheduled 
    event.
    
    The following internal instance attributes store the values that 
    represent the current speeds and velocities:
        --_speed--
        --_rotation_speed--  (positive clockwise, negative anticlockwise)
        --_vel_x--
        --_vel_y--
    The --_refresh_velocities-- method updates --_vel_x-- and --_vel_y-- given 
    the current speed (--_speed--) and rotation (--rotation-- inherited from 
    Sprite).

    SETUP
    Before instantiating any instance, the client MUST set up the class via 
    cls.--setup-- method which allows the class to determine the bounds that 
    limit PhysicalSprite instances. NB if the class has not been previously 
    setup then calls to instantiate instances will give rise to an Assertion 
    Error.
    
    BOUNDARY treatment
    Class provides for the following boundary treatments:
        'wrap' such that sprite disappears from one side and reappears on the 
        other 
        'bounce' to bounce back into the window area
        'die' to decease object (via the object's --die-- method)
        'kill' to kill object (via the object's --kill-- method)
    By default sprites 'wrap' on reaching a boundary. Default boundary 
    treatment can be set at a class level by passing +at_boundary+ to the 
    ---setup--- method as either 'wrap', 'bounce' or 'die'. This default can 
    then be overriden at an instance level by passing ++at_boundary++ to the 
    constructor.
    
    Class Attributes include:
    ---live_physical_sprites--- includes a list of all live PhysicalSprites, 
    defined as all instantiated PhysicalSprite objects which have not 
    subsequently died (via execution of their --die-- method).

    Class METHODS:
    --setup-- see SETUP section of above documentation.
    --eval_collisions-- returns a list of tuples indicating which live 
    physical sprites have collided (based on approximate proximity 
    calculation).
    
    Instance METHODS
    The following methods are defined to set the sprite speed and rotation:
        --speed_set(self, speed)-- set speed in pixels/sec
        --cruise_speed-- set speed to pre-defined cruise speed
        --speed_zero-- set speed to 0
        --rotation_speed_set-- set rotation speed in pixels/sec
        --rotate(degrees)-- rotates sprite by +degrees+. Negative values 
        rotate anti-clockwise
        --cruise_rotation-- set rotation speed to pre-defined rotation cruise 
        speed. Clockwise by default, pass +clockwise+ = False to rotate 
        anti-clockwise
        --rotation_zero-- set rotation speed to 0
        --rotate_randomly-- rotate sprite to random direction
        --stop-- stops obj, both translationally and rotationally

    Other methods:
        --collided_with(other_obj: Sprite)-- not implemented. Should be 
        implemented by subclasses that wish to handle collisions with 
        other sprites. Method should only enact consequences for this 
        object, NOT the other object (which the client should advise 
        independently of the collision if necessary)
    """
        
    live_physical_sprites: list
    window: pyglet.window.BaseWindow
    X_MIN: int
    X_MAX: int
    Y_MIN: int
    Y_MAX: int
    WIDTH: int
    HEIGHT: int
    AT_BOUNDARY: str # 'bounce' or 'wrap'
    setup_complete = False

    @staticmethod
    def chk_atboundary_opt(at_boundary):
        assert at_boundary in ['wrap', 'bounce', 'die', 'kill']

    @classmethod
    def setup(cls, window: pyglet.window.BaseWindow,
              at_boundary='wrap',
              y_top_border=0, y_bottom_border=0,
              x_left_border=0, x_right_border=0):
        """Defines class attributes that deterime the bounds of any and 
        all instances and the default treatment to apply when a sprite 
        reaches a boundary.
        +window+ should be passed as the pyglet window instance within 
        which the sprites are to be displayed"""
        cls.live_physical_sprites = []
        cls.window = window
        cls.chk_atboundary_opt(at_boundary)
        cls.AT_BOUNDARY = at_boundary
        cls.X_MIN = 0 + x_left_border
        cls.X_MAX = window.width - x_right_border
        cls.Y_MIN = 0 + y_bottom_border
        cls.Y_MAX = window.height - y_top_border
        cls.WIDTH = cls.X_MAX - cls.X_MIN
        cls.HEIGHT = cls.Y_MAX - cls.Y_MIN
        cls.setup_complete = True

    @classmethod
    def eval_collisions(cls) -> List[Tuple[Sprite, Sprite]]:
        """Returns a list of tuples indicating which live sprites have 
        collided. Based on approximate proximity where considered as 
        collided any two objects whose distance from one another is less 
        than half their combined width. Accordingly, relies on constructor 
        anchoring passed images to the image centre"""
        collisions = []
        for obj, other_obj in combinations(copy(cls.live_physical_sprites), 2):
            min_separation = (obj.width + other_obj.width)//2
            if distance(obj, other_obj) < min_separation:
                collisions.append((obj, other_obj))
        return collisions
    
    def __init__(self, initial_speed=0, initial_rotation_speed=0,
                 cruise_speed=200, rotation_cruise_speed=200, 
                 initial_rotation=0, at_boundary: Optional[str] = None, 
                 **kwargs):
        """NB before any instance can be instantiated class must be setup 
        via class method ---setup---
        Defines initial parameters as passed kwargs.
        ++at_boundary++ will override, for this sprite, any otherwise default 
        +at_boundary+ parameter previously passed to ---setup---. Can take 
        'wrap', 'bounce' or 'die'.
        """
        assert self.setup_complete, ('PhysicalSprite class must be setup'
                                     ' before instantiating instances')
        super().__init__(**kwargs)
        self.live_physical_sprites.append(self)
        self._at_boundary = at_boundary if at_boundary is not None\
            else self.AT_BOUNDARY
        self.chk_atboundary_opt(self._at_boundary)
        self._speed: int # set by --speed_set--
        self.speed_set(initial_speed)
        self._speed_cruise: int # set by --cruise_speed_set--
        self.cruise_speed_set(cruise_speed)
        self._rotation_speed: int # set by --rotation_speed_set--
        self.rotation_speed_set(initial_rotation_speed)
        self._rotation_speed_cruise: int #set by --rotation_cruise_speed_set--
        self.rotation_cruise_speed_set(rotation_cruise_speed)
        self.rotate(initial_rotation)
        self._vel_x = 0.0
        self._vel_y = 0.0

    @property
    def speed(self) -> int:
        return self._speed

    def _default_exclude_border(self):
        """Default exclude_border is 5 if --at_boundary-- is 'bounce' (to 
        prevent continual bouncing if placed on the border), otherwise 0"""
        exclude_border = 5 if self._at_boundary == 'bounce' else 0
        return exclude_border

    def _random_x(self, exclude_border: Optional[int] = None) -> int:
        """Returns a random x coordinate within the available window area 
        excluding +exclude_border+ pixels from the border"""
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.X_MIN + exclude_border, 
                              self.X_MAX - exclude_border)

    def _random_y(self, exclude_border: Optional[int] = None) -> int:
        """Returns a random x coordinate within the available window area 
        excluding +exclude_border+ pixels from the border"""
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.Y_MIN + exclude_border, 
                              self.Y_MAX - exclude_border)

    def _random_xy(self) -> Tuple:
        """Returns a tuple (x, y) which is a random coordinate within the 
        available window area"""
        x = self._random_x()
        y = self._random_y()
        return (x, y)

    def _position_randomly(self):
        """Moves sprite to a random position within the window"""
        self.update(x=self._random_x(), y=self._random_y())

    def position_randomly(self, avoid: Optional[List[AvoidRect]] = None):
        """Moves sprite to a random position within the window albeit 
        avoiding any AvoidRect's passed in a list to ++avoid++"""
        if not avoid:
            return self._position_randomly()
            
        conflicts = [True] * len(avoid)
        while True in conflicts:
            xy = self._random_xy()
            for i, avd in enumerate(avoid):
                conflicts[i] = True if avd.inside(xy) else False

        self.update(x=xy[0], y=xy[1])

    def _wrapped_x(self, x) -> int:
        """where +x+ respresents an x coordinate either to the left or right 
        of the available window, returns an x coordinate that represents the 
        wrapped position of +x+ on the 'other side' of the window"""
        if x < self.X_MIN:
            return x + self.WIDTH
        else:
            assert x > self.X_MAX
            return x - self.WIDTH

    def _wrapped_y(self, y) -> int:
        """where +y+ respresents an y coordinate either above or below the 
        available window, returns an y coordinate that represents the 
        wrapped position of +y+ on the 'other side' of the window"""
        if y < self.Y_MIN:
            return y + self.HEIGHT
        else:
            assert y > self.Y_MAX
            return y - self.HEIGHT

    def turnaround(self):
        """Rotates sprite by 180 degrees"""
        self.rotate(180)

    def _bounce_randomly(self):
        """Rotates sprite between 110 and 250 degrees from its current 
        rotation"""
        d = random.randint(110, 250)
        if 180 <= self.rotation <= 359:
            self.rotate(-d)
        else:
            self.rotate(d)
    
    def _x_inbounds(self, x) -> bool:
        """Returns boolean indicating if +x+ within window bounds"""
        return self.X_MIN < x < self.X_MAX

    def _y_inbounds(self, y) -> bool:
        """Returns boolean indicating if +y+ within window bounds"""
        return self.Y_MIN < y < self.Y_MAX

    def _adjust_x_for_bounds(self, x) -> int:
        """Where +x+ is the evaluated next x-cordinate although lies out 
        of bounds, returns new x value adjusted as appropriate for action 
        to take at boundary as specified by --_at_boundary--"""
        if self._at_boundary == 'wrap':
            return self._wrapped_x(x)
        elif self._at_boundary == 'bounce':
            self._bounce_randomly()
            return self.x
        else:
            raise Exception("no out-of-bounds treatment defined")

    def _adjust_y_for_bounds(self, y) -> int:
        """Where +y+ is the evaluated next y-cordinate although lies out 
        of bounds, returns new y value adjusted as appropriate for action 
        to take at boundary as specified by --_at_boundary--"""
        if self._at_boundary == 'wrap':
            return self._wrapped_y(y)
        elif self._at_boundary == 'bounce':
            self._bounce_randomly()
            return self.y
        else:
            raise Exception("no out-of-bounds treatment defined")


    def _refresh_velocities(self):
        """Updates internal --_vel_x-- and --_vel_y-- for current speed 
        and rotation"""
        rotation = self._rotation_radians()
        self._vel_x = self._speed * math.cos(rotation)
        self._vel_y = self._speed * math.sin(rotation)


    def speed_set(self, speed: int):
        """Sets current speed to +speed+, in pixels per second"""
        self._speed = speed
        self._refresh_velocities()

    def cruise_speed_set(self, cruise_speed: int):
        self._speed_cruise = cruise_speed

    def cruise_speed(self):
        """Sets speed to cruise speed"""
        self.speed_set(self._speed_cruise)

    def speed_zero(self):
        """Sets speed to 0"""
        self.speed_set(0)


    def rotation_speed_set(self, rotation_speed: int):
        """Sets rotation speed to +rotation_speed+, in pixels per second"""
        self._rotation_speed = rotation_speed

    def rotate(self, degrees: int):
        """Rotates sprite by +degrees+. Negative values rotate 
        anti-clockwise"""
        self.rotation += degrees
        self._refresh_velocities()

    def rotation_cruise_speed_set(self, rotation_cruise_speed):
        self._rotation_speed_cruise = rotation_cruise_speed
        
    def cruise_rotation(self, clockwise=True):
        """Set rotation speed to rotation cruise speed. Will 
        rotate clockwise by default, +clockwise+ = False to rotate 
        anti-clockwise"""
        rot_speed = self._rotation_speed_cruise
        rot_speed = rot_speed if clockwise else -rot_speed
        self.rotation_speed_set(rot_speed)

    def rotation_zero(self):
        """Set rotation speed to 0 """
        self.rotation_speed_set(0)

    def rotate_randomly(self):
        """Rotate sprite to random direction"""
        self.rotate(random.randint(0, 360))
        
    def _rotation_radians(self) -> float:
        """Current rotation in radians"""
        return -math.radians(self.rotation)

    def stop(self):
        """Stops obj, both translationally and rotationally"""
        self.speed_zero()
        self.rotation_zero()

    def _rotate(self, dt):
        """Rotates sprite to reflect elapsed time +dt+, in seconds since 
        object last moved"""
        self.rotate(self._rotation_speed*dt)

    def _eval_new_position(self, dt) -> Tuple[int, int]:
        """Returns what would be obj's new position based on current 
        velocities. +dt+ time elapsed since obj last moved."""
        dx = self._vel_x * dt
        dy = self._vel_y * dt
        x = self.x + dx
        y = self.y + dy
        return (x, y)

    def _move_to(self, x, y):
        """Moves obj to (+x+, +y+)"""
        self.update(x=x, y=y)

    def _move(self, dt):
        """'Moves' object to new position given +dt+, the time elapsed since 
        the object was last moved. Moved based on current velocities and 
        predefined at_boundary treatment"""
        x, y = self._eval_new_position(dt)
        x_inbounds = self._x_inbounds(x)
        y_inbounds = self._y_inbounds(y)
        if x_inbounds and y_inbounds:
            return self._move_to(x, y)
        elif self._at_boundary == 'die':
            return self.die()
        elif self._at_boundary == 'kill':
            return self.kill()
        else:
            if not x_inbounds:
                x = self._adjust_x_for_bounds(x)
            if not y_inbounds:
                y = self._adjust_y_for_bounds(y)
            return self._move_to(x, y)

    def collided_with(self, other_obj: Sprite):
        """Subclasses should incorporate if wish to handle collisions 
        with other Sprites. Method should enact consequence for self of 
        collision with +other_obj+
        """
        pass

    def refresh(self, dt):
        """Moves and rotates sprite to new position / orientation given +dt+, 
        the time elapsed in seconds since the object was last moved"""
        self._rotate(dt)
        self._move(dt)

    def die(self, *args, **kwargs):
        self.live_physical_sprites.remove(self)
        super().die(*args, **kwargs)


class PhysicalSpriteInteractive(PhysicalSprite):
    """Extends PhysicalSprite with funcationality that provides for users to 
    interact with objects via key presses.
    
    INTERNALS
    --_keymod_handlers-- holds a dictionary with:
        KEYS as a 'keymod', where a keymod is a string that represents one of:
            a single keyboard key (ex. '97')
            a keyboard key in combination with one or more modifiers 
              (ex. '97 18')
            any of a set of number keys ('numrow', 'numpad' or 'num')
            any of a set of number keys in combination with one or more 
              modifiers (ex. 'num 18', 'numpad 17')

              Where it represents a single key the keymod string is the number 
            that represents the key as specified in the pyglet.window.key 
            module. NB The pyglet.window.key module defines a set of 
            intelligibly named constants that return the corresponding key 
            value. For example, the constant pyglet.window.key.A represents 
            the 'a' key and has value 97 which is unique to the 'a' key. So, 
            the keymod for 'a' is '97'.
              Where it represents a key in combination with modifiers the 
            keymod string has two parts separate by a space, ' '. The first 
            part is as for a single key. The second part is the number that 
            represents the modifier or combination of modifiers as specified 
            in the pyglet.window.key module. For example, the number 
            representing the modifiers MOD_CTRL|MOD_NUMLOCK is 18, such that 
            the keymod for 'a' + 'ctrl' + 'numlock' would be '97 18'.
            Incidently, the number representing a combination of modifiers is 
            the sum of the intengers representing each of the modifiers 
            (MOD_CTRL is represented by 2 and MOD_NUMLOCK by 16, such that 
            in combination they are represented by 18).
              Where it represents any number the key the keymod is simply 
            'num'. That set can be limited to only the number keys of the
            keypad with 'numpad' or only those along the top row with 
            'numrow'.
              Where it represents a number key in combination with one or 
            more modifiers the keymod comprises two parts separated 
             by a space, ' '. The first part is 'num' or 'numpad' or 
             'numrow'. The second part is the number that represents the 
             modifier or combination of modifiers as specified in the 
             pyglet.window.key module. For example the keymod for the 
             numberpad key 6 in combination with MOD_CTRL|MOD_NUMLOCK would 
             be 'numpad 18'
        VALUES take a 3-item dictionary that determine the handlers to be 
        executed in three different 'key events' described by the dictionary 
        keys: 'on_press', 'on_release', 'while_pressed'. Values take the 
        handler (i.e. callable) to be executed when the user interacts 
        with the keys described by the keymod in such a way to trigger the key 
        event (i.e. releases, presses or holds). All handlers should 
        accommodate +key+ and +modifiers+ parameters which will be passed on 
        by the handle caller.

    In short, when a key or combination of keys represented in the keys of --_keymod_handlers-- is pressed, held or released then the associated 
    handler is executed.
    
      The --_keymod_handlers-- dictionary should be populated by the subclass 
    implementing the --setup_keymod_handlers-- method which should in turn be 
    defined to make calls to the --add_keymod_handler-- method which 
    simplifies adding an item. The --add_keymod_handler--'s +key+ and optional 
    +modifiers+ parameters take the integer representations of the main key 
    and any modifiers, whilst the associated handlers are passed as 
    +on_press+, +on_release+ and +while_pressed+ (each of which should 
    accommodate +key+ and +modifiers+ parameters that will be passed on by 
    the handle caller). Any event for which a handler isn't passed is handled 
    by an empty lambda function. The subclass can choose to handle key events 
    involving any number key (0 - 9) with the same set of handlers (i.e. with 
    the same press, release and hold handlers).
        +key+ as 'num' will result in all number keys being handled by the 
        passed handlers
        +key+ as 'numrow' will result in all the number keys along the top 
        row being handled by the passed handlers (but not the number pad keys)
        +key+ as 'numpad' will result in all the number pad keys being 
        handled by the passed handlers (but not the number keys along the top 
        row)
        NB NB whilst 'numrow' and 'numpad' keymods can both be set up for the 
        same subclass, trying to setup either of these together with a 'num' 
        keymod will result in an AssertionError.
    Alongside the 'num' +key+ +modifiers+ can also be optionally passed. For 
    example, one item with the key 'num' would handle all key events 
    involving a numerical key, whilst a separate item with key 'num 18' would 
    handle all key events involving a numerical key in combination with 
    MOD_CTRL|MOD_NUMLOCK.
    
      Internally, handling all numerical key presses with the same handler is 
    provided for by the constructor calling --_set_handle_number_bools()-- 
    which defines a set of instance attributes, each a boolean, that 
    collectively indicate how number keys should be handled. These booleans 
    are then referred to by the internals which call the handlers with the 
    consequenc taht if the keys of --_keymod_handlers-- include any of 'num', 
    'numrow' or 'numpad' then a key event involving a numerical key that 
    corresponds with one of these defined keymods will be handled by the 
    appropriate 'group' handler rather than looking for a handler specific to 
    the number key.
        
    The actual execution of the handlers is undertaken by two different 
    handling routes made available by pyglet, although execultion ends up 
    at --_execute_any_key_handler--.
        Key presses and releases are handled directly by the --on_key_press-- 
        and --on_key_release-- methods defined on this class. To provide for 
        this behaviour the constructor, via --connect_handlers-- pushes self 
        to the ++window++'s handlers  (in pyglet it's the window object which 
        receives key events). The --on_key_press-- and --on_key_release-- 
        methods pass the received +symbol+ and +modifier+ directly to 
        --_execute_any_key_handler-- together with the circumstance, defined 
        as 'on_press' and 'on_release' respectively. NB the inherited .die 
        method is extended to remove self from the window's handlers when the 
        object deceases. It does this via --disconnect_handlers--. 
        Collectively the --connect_handlers-- and --disconnect_handlers-- 
        ensure that only one version of 'self' is ever pushed to the window, 
        thereby preventing multiple version of the same handler permeating 
        the stack (which can occur, with unexpected consequences, if external 
        code were to push/remove the object to/from the window without going 
        through these methods.
        
        Keeping a key pressed (i.e. key hold) is handled by a pyglet 
        KeyStateHandler object. On the first occasion that a 
        PhysicalSpriteInteractive instance is instantiated the KeyStateHandler 
        object is created, assigned to a class attribute and and pushed to 
        the +++window+++. This class extends the inherited --refresh-- method 
        so that --_key_hold_handlers-- is executed every time the sprite is 
        refreshed. --_key_hold_handlers-- uses the KeyStateHandler object to 
        see if any key represented in --_keymod_handlers-- is currently being 
        pressed. If so, it passes execution to --_execute_any_key_handler-- 
        with the circumstance 'while_pressed'.
        NB NB --_key_hold_handlers-- does not consider modifiers, rather it 
        only looks in --_keymod_handlers-- for keymods that represent 
        a single key. That is to say that THIS CLASS DOES NOT PROVIDE FOR 
        HANDLING A KEY EVENT INVOLVING THE 'HOLDING DOWN' OF A KEY +
        MODIFIERS (although, as noted in the prior paragraphs, does provide 
        for handling the pressing and releasing of keys + modifiers).
              
        Worth noting that while --on_key_press-- and --on_key_release-- work 
        by asking if the received event symbol and modifiers is represented 
        in --_keymod_handlers--, --_key_hold_handlers-- declares the single 
        key keymods in --_keymod_handlers-- and asks the KeyStateHandler if 
        any of those keys are currently pressed.

    --_execute_any_key_handler-- is therefore where handler execution ends 
    up in all cases. The method receives the +symbol+ and +modifers+, as 
    initially made available by the pyglet event, together with the 
    +circumstance+ advised by the event capturer (--on_key_press--, 
    --on_key_release-- or --_key_hold_handlers--). From the symbol and 
    modifiers it evaluates whether a handler exists for the keys pressed.
    It gets the keymod by calling --_get_keymod--. --_get_keymod-- converts 
    the symbol and modifiers into a keymod, with consideration as to 
    whether numbers are being handled together, in which case the 'key' 
    part of the keymod is returned as either 'num', 'numpad' or 'numrow', 
    depending on the keys of --_keymod_handlers--.
    --_execute_any_key_handler-- then looks for handlers for the returned 
    keymod. Looks for a key in --_keymod_handlers-- in the following order:
        1) looks for the keymod as is, i.e. looks for a handler that 
          represents the combined +key+ / +modifiers+ key event (which 
          includes the likes of, for example, 'num 18').
        If a key representing the key + modifiers combination isn't found 
        then looks for a key that represents the key part only, on the basis 
        that any number of modifiers could be inadvertantly or pressed 
        (capslock or numlock for example) and what we're interested in, 
        at least if this combination of modifieres isn't handled, is the 
        main key being pressed:
        2a) looks for 'num' if the symbol represents a number key 
          (in --NUM_KEYS--) and 'num' is known to be a defined keymod
        2b) looks for 'numpad' if symbol represents a number key of the 
          number pad (in --NUMPAD_KEYS--) and 'numpad' is known to be a 
          defined keymod
        2c) looks for 'numrow' if symbol represents a number key of the 
          top row of numbers (in --NUMROW_KEYS--) and 'numrow' is known to be 
          a defined keymod
        3) looks for a keymod which represents the symbol alone
    In the event that no handler is found for the received key event then 
    --_execute_any_key_handler-- returns False.
    In the event that a keymod is found then then executes the corresponding 
    circumstance-specific (e.g. 'on_press') handler.

    Worth noting keymods are strings, whilst symbol and modifiers are 
    received from and passed to pyglet functions as integers.

    Public METHODS
    --add_keymod_handler-- should be used to define keyboard events and 
    corresponding handlers
    --setup_keymod_handlers-- should be defined on subclass to define 
    keyboard events and corresponding handlers via calls to 
    --add_keymod_handler--
    --freeze-- Stops object translationally and rotationally and disconnects 
        key event handlers such that end user loses control. NB Does not 
        prevent or pause any scheduled calls, to include any flashing. NB 
        to pause scheduled calls use interfrace provided by 
        pyglet_lib_clockext.ClockExt.
    --unfreeze-- reconnects key event handlers such that end user regains 
        control of the object.
        """

    NUMPAD_KEYS = (pyglet.window.key.NUM_0,
                   pyglet.window.key.NUM_1,
                   pyglet.window.key.NUM_2,
                   pyglet.window.key.NUM_3,
                   pyglet.window.key.NUM_4,
                   pyglet.window.key.NUM_5,
                   pyglet.window.key.NUM_6,
                   pyglet.window.key.NUM_7,
                   pyglet.window.key.NUM_8,
                   pyglet.window.key.NUM_9)

    NUMROW_KEYS = (pyglet.window.key._0,
                   pyglet.window.key._1,
                   pyglet.window.key._2,
                   pyglet.window.key._3,
                   pyglet.window.key._4,
                   pyglet.window.key._5,
                   pyglet.window.key._6,
                   pyglet.window.key._7,
                   pyglet.window.key._8,
                   pyglet.window.key._9)

    NUM_KEYS = NUMPAD_KEYS + NUMROW_KEYS

    _pyglet_key_handler: pyglet.window.key.KeyStateHandler
    _interactive_setup = False

    @classmethod
    def _setup_interactive(cls):
        """Sets up class attribute ---_pgylet_key_handler-- to hold a 
        KeyStateHandler which is pushed to the ---window--- to provide for 
        handling 'key held' events. See cls.__doc__.
        Internals. NB executed only once, call by the constructor when the 
        first instance of PhyscialSpriteInteractive is instantiated"""
        cls._pyglet_key_handler = pyglet.window.key.KeyStateHandler()
        cls.window.push_handlers(cls._pyglet_key_handler)
        cls._interactive_setup = True

    def __init__(self, **kwargs):
        """Takes parameters as PhysicalSprite"""
        super().__init__(**kwargs)
        if not self._interactive_setup:
            self._setup_interactive()

        self._keymod_handlers = {}
        self.setup_keymod_handlers()
        self._handle_numbers_together: bool # set by...
        self._num: bool # set by...
        self._numpad: bool # set by...
        self._numrow: bool # set by...
        self._set_handle_number_bools()
        self._connected = False # set by --connect_handlers-- to True
        self.connect_handlers()
        self._frozen = False # set by --freeze-- and --unfreeze--

    def connect_handlers(self):
        """Connects --on_key_press-- and --on_key_release-- event handlers 
        in order that they handle these key events. See cls.__doc__."""
        if not self._connected:
            self.window.push_handlers(self)
        self._connected = True

    def disconnect_handlers(self):
        """Disconnects --on_key_press-- and --on_key_release-- event handlers 
        such that they will stop handle these key events. See cls.__doc__."""
        self.window.remove_handlers(self)
        self._connected = False

    @staticmethod
    def _as_passed_or_empty_lambda(as_passed: Optional[Callable]) -> Callable:
        """Returns +as_passed+ if passed as function, otherwise if 
        +as_passed+ passed as None then returns empty lambda function"""
        if as_passed is None:
            return lambda key, modifier: None
        else:
            return as_passed

    def add_keymod_handler(self, key: Union[int, 'num'],  
                           modifiers: Optional[int] = '',
                           on_press: Optional[Callable] = None,
                           on_release: Optional[Callable] = None,
                           while_pressed: Optional[Callable] = None):
        """Adds a keymod handler to --_keymod_handlers-- where:
        +key+ takes an integer that represents a specific keyboard key 
        as specified in pyglet.window.key. The pyglet.window.key module 
        defines a set of more intelligible constants which can be passed as 
        +key+. For example pass pyglet.window.key.A to represent the key A. 
        The actual value passed (i.e. the value of the constant A on module 
        pyglet.window.key) is 97
            Alternatively to use the same set of handlers to handle all 
            key events involving numerical keys:
              pass +key+ as 'num' to handle all numerical keys together
              pass +key+ as 'numpad' to handle together all number keys of 
                the number key pad
              pass +key+ as 'numrow' to handle togeher all number keys along 
                the top keyboard row
            NB Do not pass 'num' and either of 'numpad' or 'numrow'
        +modifiers+ optionally takes an intenger that represents a modifier 
        key or combination of modifier keys.
        Where the key and any modifiers represented by +key+ and +modifiers+ 
        are collectively considered the 'key event':
        +on_press+ should be passed as a function to be executed when the
        key(s) of the key event is/are pressed, or None if no execution is 
        to be undertaken in this circumstance.
        +on_release+ should be passed as a function to be executed when the
        key(s) of the key event is/are released, or None if no execution is 
        to be undertaken in this circumstance
        +while_pressed+ should be passed as a function to be executed on 
        every call to --refresh-- when the key(s) of the key event is/are 
        pressed, or None if no execution is to be undertaken in this 
        circumstance
        NB NB all handler functions should accommodate +key+ and +modifiers+ 
        parameters
        """
        on_press = self._as_passed_or_empty_lambda(on_press)
        on_release = self._as_passed_or_empty_lambda(on_release)
        while_pressed = self._as_passed_or_empty_lambda(while_pressed)

        keymod = self._eval_keymod(key, modifiers)
        self._keymod_handlers[keymod] = {'on_press': on_press,
                                         'on_release': on_release,
                                         'while_pressed': while_pressed}

    def setup_keymod_handlers(self):
        """Method should be implemented by subclass to define user 
        interaction with object via key presses.
        Method should populate --_keymod_handlers-- via calls to 
        --add_keymod_handler--, one call for each key press which is to be 
        handled.
        """
        pass

    def _keypart(self, keymod: 'str'):
        """Returns the first part of the keymod, for exmample:
        where +keymod+ is '97 18' returns '97'
        where +keymod+ is '97' returns '97'
        """
        return keymod.split(' ')[0]

    def _eval_keymod(self, key: Union[int, 'num', 'numrow', 'numpad'],
                     modifiers: Union[int, str] = '') -> str:
        """Returns the internal keymod string that represents the passed 
        +key+ and +modifiers+ (see cls.__doc__)"""
        if modifiers == '':
            return str(key)
        else:
            return str(key) + ' ' + str(modifiers)

    def _set_handle_number_bools(self):
        """Sets booleans indiciating how number keys are being handled.
        Evaluates how to handle numbers keys by interrogation of the keymods 
        used as keys of --_keymod_handlers--. (see cls.__doc__)"""
        self._handle_numbers_together = False
        self._numpad = False
        self._numrow = False
        self._num = False
        keyparts = [self._keypart(keymod) for keymod in self._keymod_handlers]
        num_keys = ['num', 'numpad', 'numrow']
        num_keys_used = [nk for nk in num_keys if nk in keyparts]
        if num_keys_used:
            self._handle_numbers_together = True
            if 'numpad' in num_keys_used:
                self._numpad = True
            if 'numrow' in num_keys_used:
                self._numrow = True
            if 'num' in num_keys_used:
                self._num = True
            assert not (self._num and (self._numpad or self._numrow)),\
                "Cannot have both 'num' and either 'numpad' or 'numrow'"\
                "as keymods"

    def _get_keymod(self, key: int, modifiers: Union[int, str] = '') -> str:
        """Returns the internal keymod string that represents the passed 
        +key+ and +modifiers+ (see cls.__doc__)"""
        if self._handle_numbers_together:
            ext = ' ' + str(modifiers) if modifiers else ''
            if self._num and key in self.NUM_KEYS:
                return 'num' + ext
            elif self._numpad and key in self.NUMPAD_KEYS:
                return 'numpad' + ext
            elif self._numrow and key in self.NUMROW_KEYS:
                return 'numrow' + ext
        return self._eval_keymod(key, modifiers)

    def _keymod_handled(self, key: int, 
                       modifiers: Union[int, str] = '') -> Union[str, bool]:
        """Returns, in order of priority:
            1) keymod which represents a defined handler for the combined 
              +key+ / +modifiers+ key event (includes of the like, for 
              example, 'num 18')
            2a) 'num' if +key+ is a number (in --NUM_KEYS--) and 'num' is a 
              defined handler
            2b) 'numpad' if +key+ is a number key of the number pad (in 
              --NUMPAD_KEYS--) and 'numpad' is a defined handler
            2c) 'numrow' if +key+ is a number key of the top row of number 
              keys (in --NUMROW_KEYS--) and 'numrow' is a defined handler
            3) keymod which represents a defined handler for the +key+ key 
              event
            4) False if there is no defined handler for the passed parameters
        See cls.__doc__ for documentation of keymod.
        """
        keymod = self._get_keymod(key, modifiers)
        if keymod in self._keymod_handlers:
            return keymod
        elif keymod[0:3] == 'num':
            return self._keypart(keymod)
        elif str(key) in self._keymod_handlers:
            return str(key)
        else:
            return False

    def _execute_any_key_handler(self, key: int, circumstance: str,
                                 modifiers: Union[int, str] = ''):
        """If a circumstance-specific handler exists for any key event 
        discernable from passed +key+ and any +modifiers+ then executes 
        that handler.
        """
        keymod = self._keymod_handled(key, modifiers)
        if not keymod:
            return
        self._keymod_handlers[keymod][circumstance](key, modifiers)
        #In event there is a handlers exists returns True in order to 
        #prevent handler from futher propagating through the stack.
        #return True

    def on_key_press(self, symbol: int, modifiers: int):
        """Event handler for key presses"""
        self._execute_any_key_handler(symbol, 'on_press', modifiers)
        #return
            
    def on_key_release(self, symbol: int, modifiers: int):
        """Event handler for key releases"""
        self._execute_any_key_handler(symbol, 'on_release', modifiers)

    def _key_hold_handlers(self):
        """For any keymod that represents a key event involving only a single 
        key (i.e. no modifiers) will check if key current pressed and if so 
        executes associated handler for 'while_pressed' circumstance"""
        for keymod in self._keymod_handlers:
            try:
                key = int(keymod)
            except ValueError:
                continue
            else:
                if self._pyglet_key_handler[key]:
                    self._execute_any_key_handler(key, 'while_pressed')


    def freeze(self):
        """Stops object translationally and rotationally and disconnects 
        key event handlers such that end user loses control.
        """
        self.stop()
        self.disconnect_handlers()
        self._frozen = True
    
    def unfreeze(self):
        """reconnects key event handlers such that end user regains 
        control of the object.
        """
        self.connect_handlers()
        self._frozen = False
        
    def refresh(self, dt):
        """extends inherited method to:
            execute any registered 'key hold' handler that corresponds 
              to any pressed key
            skip execution if --_frozen--"""
        if self._frozen:
            return
        self._key_hold_handlers()
        super().refresh(dt)

    def die(self, *args, **kwargs):
        self.disconnect_handlers()
        super().die(*args, **kwargs)