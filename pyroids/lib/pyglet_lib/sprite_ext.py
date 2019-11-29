#! /usr/bin/env python

"""Series of extensions to Sprite class together with helper functions.

CLASSES
The following hierarchy of classes each extend the class before to provide 
for an additional layer of functionality with a specific purpose.

AdvSprite(Sprite) - Enhance end-of-life, scheduling, one-voice sound, 
    flashing and scaling.

OneShotAnimatedSprite(AdvSprite) - Objects decease automatically when 
    animation ends.

PhysicalSprite(AdvSprite) - 2D movement and collision detection within 
    defined window area.

InteractiveSprite(PhysicalSprite) - user control via keyboard keys.

Helper FUNCTIONS:
Various functions to create pyglet objects from files in the pyglet resource 
directory and to manipulate the created objects.

centre_image()  Set image anchor points to image center.
centre_animiation()  Center all Animation frames.
load_image()  Load image from resource directory.
load_animiation()  Load Animation from resource directory.
anim()  Create Animation object from image of subimages.
distance()  Evalute distance between two sprites.
vector_anchor_to_rotated_point()  Evalute vector to rotated point.

Helper CLASSES:
InRect()  Check if a point lies in a defined rectangle
AvoidRect(InRect)  Define an area to avoid as a rectangle around a sprite 
"""

import random, math, time
import collections.abc
from itertools import combinations
from copy import copy
from typing import Optional, Tuple, List, Union, Sequence, Callable, Dict
from functools import wraps

import pyglet
from pyglet.image import Texture, TextureRegion, Animation
from pyglet.sprite import Sprite
from pyglet.media import StaticSource

from .audio_ext import StaticSourceMixin
from .. import physics

def centre_image(image: Union[TextureRegion, Sequence[TextureRegion]]):
    """Set +image+ anchor points to centre of image"""
    if not isinstance(image, collections.abc.Sequence):
        image = [image]
    for img in image:
        img.anchor_x = img.width // 2
        img.anchor_y = img.height // 2

def centre_animation(animation: Animation):
    """Centre all +animation+ frames"""
    for frame in animation.frames:
            centre_image(frame.image)

def load_image(filename: str, anchor: Union['origin', 'center'] = 'origin'
               ) -> TextureRegion:
    """Load image with +filename+ from resource.
    
    +anchor+ Set anchor points to image 'origin' or 'center'"""
    assert anchor in ['origin', 'center']
    img = pyglet.resource.image(filename)
    if anchor == 'center':
        centre_image(img)
    return img

def load_image_sequence(filename: str, num_images: int, placeholder='?',
                        anchor: Union['origin', 'center'] = 'origin'
                        ) -> List[pyglet.image.Texture]:
    """Load sequence of images from resource.
    
    +num_images+ Number of images in sequence.
    +anchor+ Set anchor points to image 'origin' or 'center'.
    +filename+ Name of image filename where +filename+ includes a 
    +placeholder+ character that represents position where filenames 
        are sequentially enumerated. First filename enumerated 0.
    
    Example usage:
    load_image_sequence(filename='my_img_seq_?.png', num_images=3,
                        placeholder='?')
    -> List[pyglet.image.Texture] where images loaded from following files 
    in resource directory:
        my_img_seq_0.png
        my_img_seq_1.png
        my_img_seq_2.png
    """
    return [ load_image(filename.replace(placeholder, str(i)), anchor=anchor) 
            for i in range(0, num_images) ]

def load_animation(filename: str, anchor: Union['origin', 'center'] = 'origin'
                   ) -> Animation:
    """Loads animation from resource.
    
    +filename+ Name of animation file. Acceptable filetypes inlcude .gif.
    +anchor+ Anchor each animation image to image 'origin' or 'center'.
    """
    assert anchor in ['origin', 'center']
    animation = pyglet.resource.animation(filename)
    if anchor == 'center':
        centre_animation(animation)
    return animation

def anim(filename, rows: int, cols: int , 
         frame_duration: float = 0.1, loop=True) -> Animation:
    """Create Animation object from image of regularly arranged subimages.
    
    +filename+ Name of file in resource directory of image of subimages 
        regularly arranged over +rows+ rows and +cols+ columns.
    +frame_duration+ Seconds each frame of animation should be displayed.
    """
    img = pyglet.resource.image(filename)
    image_grid = pyglet.image.ImageGrid(img, rows, cols)
    animation = image_grid.get_animation(frame_duration, True)
    centre_animation(animation)
    return animation

def distance(sprite1: Sprite, sprite2: Sprite) -> int:
    """Return distance between +sprite1+ and +sprite2+ in pixels"""
    return physics.distance(sprite1.position, sprite2.position)

def vector_anchor_to_rotated_point(x: int, y: int, 
                                   rotation: Union[int, float]
                                   ) -> Tuple[int, int]:
    """Return vector to rotated point.
    
    Where +x+ and +y+ describe a point relative to an image's anchor 
    when rotated 0 degrees, returns the vector, as (x, y) from the anchor 
    to the same point if the image were rotated by +rotation+ degrees.
    
    +rotation+  Degrees of rotation, clockwise positive, 0 pointing 'right', 
        i.e. as for a sprite's 'rotation' attribute.
    """
    dist = physics.distance((0,0), (x, y))
    angle = math.asin(y/x)
    rotation = -math.radians(rotation)
    angle_ = angle + rotation
    x_ = dist * math.cos(angle_)
    y_ = dist * math.sin(angle_)
    return (x_, y_)

class InRect(object):
    """Check if a point lies within a defined rectangle.

    Class only accommodates rectangles that with sides that are parallel 
    to the x and y axes. 
    
    Constructor defines rectangle. 
    
    METHODS
    --inside(position)--  Returns boolean advising if +position+ in rectangle.

    ATTRIBUTES
    --width-- rectangle width
    --height-- rectangle width

    Additionally, each parameter passed to the construtor is stored in 
    an attribute of the same name:
    --x_from--
    --x_to--
    --y_from--
    --y_to--
    """
    
    def __init__(self, x_from: int, x_to: int, y_from: int, y_to: int):
        """Define rectangle.
                
        +x_from+  x coordinate of recectangle's left side
        +x_to+  x coordinate of recectangle's right side
        i.e. x coordinate increasingly positive as move right.

        +y_from+  y coordinate of recectangle's bottom side
        +y_to+  y coordinate of recectangle's top side
        i.e. y coordinate increasingly positive as move up.
        """
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to
        self.width = x_to - x_from
        self.height = y_to - y_from

    def inside(self, position: Tuple[int, int]) -> bool:
        """Return boolean advising if +position+ lies in rectangle.
        +position+  (x, y)
        """
        x = position[0]
        y = position[1]
        if self.x_from <= x <= self.x_to and self.y_from <= y <= self.y_to:
            return True
        else:
            return False

class AvoidRect(InRect):
    """Define rectangular area around a sprite.

    Intended use is to avoid AvoidRects when positioning other sprites in 
    order that the sprites do not overlap / immediately collide.
    
    Extends InRect to define a rectangle that encompasses a ++sprite++ and 
    any ++margin++.

    ATTRIBUTES
    --sprint--  ++sprite++
    --margin--  ++margin++
    """
    
    def __init__(self, sprite: Sprite, margin: Optional[int] = None):
        """Define rectangle to encompass ++sprite++ plus ++margin++"""
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
    """Extends Sprite class functionality.

    Offers:
        additional end-of-life functionality (see End-Of-Life section)
        additional scheduling events functionality (see Scheduling section)
        register of live sprites
        sound via inherited StaticSourceMixin (see documentation for 
            StaticSourceMixin)
        sprite flashing
        sprite scaling
        
    END-OF-LIFE
    Class makes end-of-life distinction between 'killed' and 'deceased'.
    Deceased - Death. The --die()-- method deceases the object. Any callable
        passed as ++on_die++ will be executed as part of the implementation.
    Killed - Premature Death. The --kill()-- method will kill the object 
        prematurely.  Any callable passed as ++on_kill++ will be executed as 
        part of the implementation. Implementation concludes by deceasing 
        the object.
    For arcade games the above distinction might be implemented such that 
    an object is killed if its life ends as a consequence of an in game 
    action (for example, on being shot) or is otherwise simply deceased 
    when no longer required.
    
    SCHEDULING
    --schedule_once()-- and --schedule_all()-- methods are provided to 
    schedule future calls. So long as all furture calls are scheduled 
    through these methods, scheduled calls can be collectively 
    or individually unscheduled via --unschedule_all()-- and 
    --unschedule()-- respectively.

    Class ATTRIBUTES:
    ---live_sprites---  List of all instantiated sprites not subsequently 
        deceased
    ---snd---  (inherited)  Sprite's main sound (see StaticSourceMixin 
        documentation)
    ---img---  Sprite's image (see Subclass Interface section)

    Class METHODS
    ---stop_all_sound()---  Pause sound of from live sprites
    ---resume_all_sound()---  Resume sound from from all live sprites
    ---cull_all---  Kill all live sprites
    ---decease_all---  Decease all live sprites
    ---cull_selective(exceptions)---  Kill all live sprites save +exceptions+
    ---decease_selective(exceptions)---  Deceease all live sprites save 
        +exceptions+
    
    PROPERTIES
    --live-- returns boolean indicating if object is a live sprite.

    Instance METHODS
    --scale_to(obj)-- Scale object to size of +obj+
    --flash_start()-- Make sprite flash
    --flash_stop()--  Stop sprite flashing
    --toggle_visibility()--  Toggle visibility
    --schedule_once(func)--  Schedule a future call to +func+
    --schedule_interval(func)-- Schedule regular future calls to +func+
    --unschedule(func)--  Unschedule future call(s) to func
    --unschedule_all()--  Unschedule all future calls
    --kill()--  Kill object
    --die()--  Decease object
    
    SUBCLASS INTERFACE
    
    Sound
    Also see Subclass Interface section of StaticSourceMixin documentation

    Image
    Subclass should define class attribute ---img--- and assign it a 
    pyglet Texture or Animation object which will be used as the sprite's 
    default image. Helper functions ----anim()---- and ----load_image---- can 
    be used to directly create Animation and Texture objects from image files 
    in the resources directory, for example:
        img = anim('explosion.png', 2, 8)  # Animation
        img = load_image('ship_blue.png', anchor='center')  # Texture
    
    This default image can be overriden by passing a pyglet image as ++img++.

    End-of-Lfe
    Subclasses should NOT OVERRIDE the --die()-- or --kill()-- methods. 
    Rather these methods should be extended to provide for any additional 
    end-of-life operations that may be required.
    """
    
    img: Union[Texture, Animation]
    snd: StaticSource

    live_sprites = []
    _dying_loudly = []

    @classmethod
    def stop_all_sound(cls):
        """Pause sound from all live sprites."""
        for sprite in cls.live_sprites + cls._dying_loudly:
            sprite.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        """For all live sprites, resume any sound that was paused"""
        for sprite in cls.live_sprites + cls._dying_loudly:
            sprite.resume_sound()

    @classmethod
    def _end_lives_all(cls, kill=False):
        """End life of all live sprites without exception.
        
        +kill+  True to kill all sprites, False to merely decease them.

        Raises AssertionError in event a live sprite evades death.
        """
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
        """End life of all live sprites save +exceptions+.
        
        +exceptions+  List of any combination of Sprite objects or 
            subclasses of Sprite. All instances of any included subclasses 
            will be spared.
        +kill+ True to kill sprites, False to merely decease them.
        
        Raises AssertionError if a non-excluded live sprite evades death.
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
        """Kill all live sprites without exception"""
        cls._end_all_lives(kill=True)

    @classmethod
    def decease_all(cls):
        """Decease all live sprites without exception"""
        cls._end_all_lives(kill=False)

    @classmethod
    def cull_selective(cls, exceptions: Optional[List[Sprite]] = None):
        """Kill all live sprites save for +exceptions+

        +exceptions+  List of any combination of Sprite objects or 
            subclasses of Sprite. All instances of any included subclasses 
            will be spared.
        """
        cls._end_lives_selective(exceptions=exceptions, kill=True)

    @classmethod
    def decease_selective(cls, exceptions: Optional[List[Sprite]] = None):
        """Decease all live sprites save for +exceptions+

        +exceptions+  List of any combination of Sprite objects or 
            subclasses of Sprite. All instances of any included subclasses 
            will be spared.
        """
        cls._end_lives_selective(exceptions=exceptions, kill=False)

    def __init__(self, scale_to: Union[Sprite, Texture] = None, 
                 sound=True, sound_loop=False, 
                 on_kill: Optional[Callable] = None,
                 on_die: Optional[Callable] = None, **kwargs):
        """Extends inherited constructor.
        ++scale_to++  Scale sprite to dimensions of ++scale_to++.
        ++img++  If not received, passes 'img' as ---img---.
        ++sound++  If True will play ---snd--- at end of instantiation 
            which will loop if ++sound_loop++ True.
        ++on_kill++  Callable called if sprite killed.
        ++on_die++  Callable called if sprite deceased.
        """
        kwargs.setdefault('img', self.img)
        self._on_kill = on_kill if on_kill is not None else lambda: None
        self._on_die = on_die if on_die is not None else lambda: None
        super().__init__(**kwargs)
        
        if scale_to is not None:
            self.scale_to(scale_to)

        self.live_sprites.append(self)  # add instance to class attribute
        
        self._scheduled_funcs = []

        StaticSourceMixin.__init__(self, sound, sound_loop)
        
    @property
    def live(self) -> bool:
        """Return Boolean indicating if object is a live sprite"""
        return self in self.live_sprites

    def toggle_visibility(self, dt: Optional[float] = None):
        #  +dt+ provides for calling via pyglet scheduled event
        self.visible = not self.visible

    def flash_stop(self, visible=True):
        self.unschedule(self.toggle_visibility)
        self.visible = visible

    def flash_start(self, frequency: Union[float, int] = 3):
        """Start sprite flashing at +frequency+ time per second.
        
        Can be called on a flashing sprite to change frequency.
        Stop flashing with --flash_stop()--
        """
        self.flash_stop()
        self.schedule_interval(self.toggle_visibility, 1/(frequency*2))

    def scale_to(self, obj: Union[Sprite, Texture]):
        """Scale object to same size as +obj+"""
        x_ratio = obj.width / self.width
        self.scale_x = x_ratio
        y_ratio = obj.height / self.height
        self.scale_y = y_ratio

    # CLOCK SCHEDULE
    def _add_to_schedule(self, func):
        self._scheduled_funcs.append(func)
        
    def schedule_once(self, func: Callable, time: Union[int, float]):
        """Schedule call to +func+ in +time+ seconds.

        +func+ must accommodate first parameter received after self
            as the time elapsed since call was scheduled - name parameter 
            +dt+ by convention. Elapsed time will be passed to function 
            by pyglet.
        """
        pyglet.clock.schedule_once(func, time)
        self._add_to_schedule(func)

    def schedule_interval(self, func: Callable, freq: Union[int, float]):
        """Schedule call to +func+ every +freq+ seconds.
       
        +func+ must accommodate first parameter received after self
            as the time elapsed since call was scheduled - name parameter 
            +dt+ by convention. Elapsed time will be passed to function 
            by pyglet.
        """
        pyglet.clock.schedule_interval(func, freq)
        self._add_to_schedule(func)

    def _remove_from_schedule(self, func):
        # mirrors behaviour of pyglet.clock.unschedule by ignoring requests 
        # to unschedule events that have not been previously scheduled
        try:
            self._scheduled_funcs.remove(func)
        except ValueError:
            pass

    def unschedule(self, func):
        """Unschedule future call to +func+.
       
        +func+ can have been previously scheduled via either schedule_once 
            or schedule_interval. No error raised or advices offered if 
            +func+ not previously scheduled.
        """
        pyglet.clock.unschedule(func)
        self._remove_from_schedule(func)

    def unschedule_all(self):
        """Unschedule all future calls.

        No error raised or advices offer if there are no scheduled functions.
        """
        for func in self._scheduled_funcs[:]:
            self.unschedule(func)

    # END-OF-LIFE
    def kill(self):
        """Kill object prematurely."""
        self._on_kill()
        self.die()
        
    def _waiting_for_quiet(self, dt: float):
        if not self.sound_playing:
            self.unschedule(self._waiting_for_quiet)
            self._dying_loudly.remove(self)

    def _die_loudly(self):
        self._dying_loudly.append(self)
        self.schedule_interval(self._waiting_for_quiet, 0.1)

    def die(self, die_loudly=False):
        """Decease object at end-of-life.
        
        +die_loundly+ True to let any playing sound continue.
        """
        # Extends inherited --delete()-- method to include additional 
        # end-of-life operations
        self.unschedule_all()
        if die_loudly:
            self._die_loudly()
        else:
            self.stop_sound()
        self.live_sprites.remove(self)
        super().delete()
        self._on_die()

class OneShotAnimatedSprite(SpriteAdv):
    """Extends SpriteAdv to offer a one shot animation.
    
    Objects decease automatically when animation ends.
    """
        
    def on_animation_end(self):
        """Event handler"""
        self.die()

class PhysicalSprite(SpriteAdv):
    """Extends SpriteAdv for 2D movement and collision detection.
   
    The PhysicalSprite class:
        defines the window area within which physical sprites can move.
        can evalutate collisions between live physical sprites instances.
        
    A physcial sprite:
        has a speed and a rotation speed.
        has a cruise speed and rotation curise speed that can be set and 
            in turn which the sprite's speed and rotation speed can be set to.
        can update its position for a given elapased time.
        can resolve colliding with a window boundary (see Boundary 
            Response section).
        can resolve the consequence for itself of colliding with another 
            sprite in the window area (requires implementation by subclass - 
            see Subclass Interface).
    
    BOUNDARY RESPONSE
    A physical sprite's reponse to colliding with a window boundary can 
        be defined as one of the following options:
        'wrap' - reappearing at other side of the window.
        'bounce' - bouncing bounce back into the window.
        'stop' - stops at last position within bounds.
        'die' - deceasing sprite.
        'kill' - killing sprite.
    The default option can be set at a class level via 
    ---setup(+at_boundary+)--- (See Subclass Interface section). In turn 
    the class default option can be overriden by any particular instance 
    via --__init__(+at_boundary+)--.

    Class ATTRIBUTES
    ---live_physical_sprites--- List of all instantiated PhysicalSprite 
        instances that have not subsequently deceased.

    The following attributes are available for inspection although it is not 
    intended that the value are reassigned:
    ---X_MIN---  Left boundary
    ---X_MAX---  Right boundary
    ---Y_MIN---  Bottom boundary
    ---Y_MAX---  Top boundary
    ---WIDTH---  Width of window area in which sprite can move
    ---HEIGHT---  Height of window area in which sprite can move
    ---AT_BOUNDARY---  Default response if sprite collides with boundary

    Class METHODS
    ---setup---  Setup class. Must be executed ahead of instantiating an 
        instance. See Setup Interface section.
    ---eval_collisions--- Evaluate collisions between live sprites.
    
    PROPERTIES
    --speed--  sprite's current speed.

    Inherited PROPERTY of note:
    --rotation--  sprite's current orientation

    Instance METHODS
    --refresh(dt)--  Move and rotate sprite given elapsed time +dt+.
    --position_randomly(+avoid+)--  Move sprite to random position within 
        available window area excluding area defined by +avoid+.

    To set the sprite speeds and rotation:
        --speed_set()--  Set current speed.
        --cruise_speed_set()--  Set cruise speed.
        --cruise_speed()--  Set speed to cruise speed.
        --speed_zero()--  Set speed to 0.
        
        --rotation_speed_set()--  Set rotation speed.
        --rotation_cruise_speed_set()--  Set rotation cruise speed.
        --cruise_rotation()--  Set rotation speed to rotation cruise speed.
        --rotation_zero()--  Set rotation speed to 0.
        
        --rotate()-- Rotate sprite.
        --rotate_randomly()--  Rotate sprite to random direction
        --turnaround()--  Rotate sprite 180 degrees.
        
        --stop()--  Stops sprite translationally and rotationally.
            
    --collided_with()--  Not implemented. See Subclass Interface section.

    SUBCLASS INTERFACE
    
    Setup
    Before instantiating any instance, the subclass must set up the class 
    via the class method ---setup()---. This setup method defines the 
    window bounds and response to sprite colliding with boundaries.
    
    Sprite Image
    The sprite image, either assigned to ---img--- or passed as ++img++, 
    must be anchored at the image center in order for the class to 
    evaluate collisions. The following helper functions provide for 
    creating centered pyglet image objects that can be assigned to ---img--- 
    or directly passed as ++img++:
        ----load_image()----
        ----load_animation()----
        ----anim()----

    Collision Resolution
    --collided_with(other_obj)-- is defined on this class although not 
    implemented. If subclass is to resolve collisions then this method 
    should be implemented to enact consequence for the physical sprite of 
    colliding with another live sprite (the +other_obj+). Method should 
    only enact consequences for this physical sprite, NOT +other_obj+, 
    (which the client, should it wish, should advise independently of 
    the collision).
    """
        
    live_physical_sprites: list
    _window: pyglet.window.BaseWindow
    X_MIN: int
    X_MAX: int
    Y_MIN: int
    Y_MAX: int
    WIDTH: int
    HEIGHT: int
    AT_BOUNDARY: str
    
    _setup_complete = False

    @staticmethod
    def chk_atboundary_opt(at_boundary):
        assert at_boundary in ['wrap', 'bounce', 'stop', 'die', 'kill']
        
    @classmethod
    def setup(cls, window: pyglet.window.BaseWindow,
              at_boundary='wrap',
              y_top_border=0, y_bottom_border=0,
              x_left_border=0, x_right_border=0):
        """Class setup. Define bounds and default treatment on reaching.
        
        +at_boundary+  Default response to sprite colliding with boundary, 
            either 'wrap', 'bounce', 'stop', 'die', 'kill'.
        +window+  Game window to which sprite will be drawn
        
        Bounds determined as +window+ extent less width of any corresponding
        border argument passed.
        """
        cls.live_physical_sprites = []
        cls._window = window
        cls.chk_atboundary_opt(at_boundary)
        cls.AT_BOUNDARY = at_boundary
        cls.X_MIN = 0 + x_left_border
        cls.X_MAX = window.width - x_right_border
        cls.Y_MIN = 0 + y_bottom_border
        cls.Y_MAX = window.height - y_top_border
        cls.WIDTH = cls.X_MAX - cls.X_MIN
        cls.HEIGHT = cls.Y_MAX - cls.Y_MIN
        cls._setup_complete = True

    @classmethod
    def eval_collisions(cls) -> List[Tuple[Sprite, Sprite]]:
        """Evaluate which live sprites have collided, if any.

        Returns list of 2-tuples where each tuple signifies a collision 
        between the 2 sprites it contains.
        
        Collisions evaluated based on approximate proximity. Two sprites
        separated by a distance of less than half their combined 
        width are considered to have collided. Perfect for circular 
        images, increasingly inaccurate the further the image deviates 
        from a circle.

        NB Basis for proximity evaluation ASSUJMES sprite image anchored 
        at image's center.
        """
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
        """Extends inherited constructor to define subclass specific settings.
        
        Before any instance can be instantiated class must be setup 
        via class method ---setup()---. Otherwise will raise AssertionError.
                
        ++at_boundary++ will override, for this instance, any default 
            value passed to ---setup()---. Takes either 'wrap', 'bounce', 
            'stop', 'die' or 'kill'.
        """
        assert self._setup_complete, ('PhysicalSprite class must be setup'
                                     ' before instantiating instances')
        super().__init__(**kwargs)
        self.live_physical_sprites.append(self)
        self._at_boundary = at_boundary if at_boundary is not None\
            else self.AT_BOUNDARY
        self.chk_atboundary_opt(self._at_boundary)
        self._speed: int  # Stores current speed. Set by...
        self.speed_set(initial_speed)
        self._speed_cruise: int # Set by...
        self.cruise_speed_set(cruise_speed)
        self._rotation_speed: int  # Stores current rotation speed. Set by...
        self.rotation_speed_set(initial_rotation_speed)
        self._rotation_speed_cruise: int  # Set by...
        self.rotation_cruise_speed_set(rotation_cruise_speed)
        self.rotate(initial_rotation)
        
        # --_refresh_velocities-- updates --_vel_x-- and --_vel_y-- given 
        # current speed and rotation
        self._vel_x = 0.0  # Stores current x velocity
        self._vel_y = 0.0  # Stores current y velocity

    # SPEED
    @property
    def speed(self) -> int:
        return self._speed

    def speed_set(self, speed: int):
        """Set current speed to +speed+, in pixels per second."""
        self._speed = speed
        self._refresh_velocities()

    def cruise_speed_set(self, cruise_speed: int):
        """Set cruise speed to +cruise_speed+."""
        self._speed_cruise = cruise_speed

    def cruise_speed(self):
        """Set speed to cruise speed."""
        self.speed_set(self._speed_cruise)

    def speed_zero(self):
        """Sets speed to 0."""
        self.speed_set(0)

    # ROTATION
    def rotation_speed_set(self, rotation_speed: int):
        """Set rotation speed to +rotation_speed+, in pixels per second.
        
        Positive values rotate clockwise, negative values anticlockwise.
        """
        self._rotation_speed = rotation_speed

    def rotate(self, degrees: int):
        """Rotate sprite by +degrees+ degrees.
        
        Negative values rotate anti-clockwise.
        """
        self.rotation += degrees
        self._refresh_velocities()

    def rotation_cruise_speed_set(self, rotation_cruise_speed: int):
        """Set rotation cruise speed to +rotation_cruise_speed+."""
        self._rotation_speed_cruise = rotation_cruise_speed
        
    def cruise_rotation(self, clockwise=True):
        """Set rotation speed to rotation cruise speed.
        
        +clockwise+ False to rotate anti-clockwise.
        """
        rot_speed = self._rotation_speed_cruise
        rot_speed = rot_speed if clockwise else -rot_speed
        self.rotation_speed_set(rot_speed)

    def rotation_zero(self):
        """Set rotation speed to 0."""
        self.rotation_speed_set(0)

    def rotate_randomly(self):
        """Rotate sprite to random direction."""
        self.rotate(random.randint(0, 360))
        
    def turnaround(self):
        """Rotate sprite by 180 degrees."""
        self.rotate(180)

    def _bounce_randomly(self):
        """Rotate sprite between 130 and 230 degrees."""
        d = random.randint(130, 230)
        if 180 <= self.rotation <= 359:
            self.rotate(-d)
        else:
            self.rotate(d)

    def _rotation_radians(self) -> float:
        """Return current rotation in radians."""
        return -math.radians(self.rotation)

    def _rotate(self, dt: Union[float, int]):
        """Rotate sprite to reflect elapsed time.
        
        +dt+ Seconds elapsed since object last rotated.
        """
        self.rotate(self._rotation_speed*dt)

    # SPEED and ROTATION
    def stop(self):
        """Stop sprite both translationally and rotationally."""
        self.speed_zero()
        self.rotation_zero()

    def _refresh_velocities(self):
        """Update velocities for current speed and rotation."""
        rotation = self._rotation_radians()
        self._vel_x = self._speed * math.cos(rotation)
        self._vel_y = self._speed * math.sin(rotation)

    # BOUNDARY RESPONSE
    def _wrapped_x(self, x: int) -> int:
        """Where +x+ respresents an x coordinate either to the left or right 
        of the available window, return the x coordinate that represents the 
        wrapped position of +x+ on the 'other side' of the window.
        """
        if x < self.X_MIN:
            return x + self.WIDTH
        else:
            assert x > self.X_MAX
            return x - self.WIDTH

    def _wrapped_y(self, y: int) -> int:
        """Where +y+ respresents an x coordinate either to the left or right 
        of the available window, return the y coordinate that represents the 
        wrapped position of +y+ on the 'other side' of the window.
        """
        if y < self.Y_MIN:
            return y + self.HEIGHT
        else:
            assert y > self.Y_MAX
            return y - self.HEIGHT

    def _x_inbounds(self, x: int) -> bool:
        """Return boolean indicating if +x+ within bounds."""
        return self.X_MIN < x < self.X_MAX

    def _y_inbounds(self, y) -> bool:
        """Return boolean indicating if +y+ within bounds."""
        return self.Y_MIN < y < self.Y_MAX

    def _adjust_x_for_bounds(self, x: int) -> int:
        """Where +x+ is the evaluated next x-cordinate although lies out 
        of bounds, return new x value adjusted for boundary response.
        """
        if self._at_boundary == 'wrap':
            return self._wrapped_x(x)
        elif self._at_boundary == 'bounce':
            self._bounce_randomly()
            return self.x
        else:
            raise Exception("no out-of-bounds treatment defined")

    def _adjust_y_for_bounds(self, y: int) -> int:
        """Where +y+ is the evaluated next y-cordinate although lies out 
        of bounds, return new y value adjusted for boundary response.
        """
        if self._at_boundary == 'wrap':
            return self._wrapped_y(y)
        elif self._at_boundary == 'bounce':
            self._bounce_randomly()
            return self.y
        else:
            raise Exception("no out-of-bounds treatment defined")

    # POSITION
    def _default_exclude_border(self):
        # 5 if --_at_boundary-- is bounce to prevent repeated bouncing 
        # if sprite placed on border.
        exclude_border = 5 if self._at_boundary == 'bounce' else 0
        return exclude_border

    def _random_x(self, exclude_border: Optional[int] = None) -> int:
        """Return random x coordinate within available window area 
        excluding +exclude_border+ pixels from the border.
        """
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.X_MIN + exclude_border, 
                              self.X_MAX - exclude_border)

    def _random_y(self, exclude_border: Optional[int] = None) -> int:
        """Return random x coordinate within the available window area 
        excluding +exclude_border+ pixels from the border.
        """
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.Y_MIN + exclude_border, 
                              self.Y_MAX - exclude_border)

    def _random_xy(self) -> Tuple[int, int]:
        """Return random position within available window area."""
        x = self._random_x()
        y = self._random_y()
        return (x, y)

    def _position_randomly(self):
        """Move sprite to random position within available window area."""
        self.update(x=self._random_x(), y=self._random_y())

    def position_randomly(self, avoid: Optional[List[AvoidRect]] = None):
        """Move sprite to random position within available window area.
        
        +avoid+ List of AvoidRect defining rectangular areas to exclude 
            from available window area.
        """
        if not avoid:
            return self._position_randomly()
            
        conflicts = [True] * len(avoid)
        while True in conflicts:
            xy = self._random_xy()
            for i, avd in enumerate(avoid):
                conflicts[i] = True if avd.inside(xy) else False

        self.update(x=xy[0], y=xy[1])

    def _eval_new_position(self, dt: Union[float, int]) -> Tuple[int, int]:
        """Return obj's new position given elapsed time and ignoring bounds.

        +dt+ Seconds elapsed since sprite last moved.
        """
        dx = self._vel_x * dt
        dy = self._vel_y * dt
        x = self.x + dx
        y = self.y + dy
        return (x, y)

    def _move_to(self, x, y):
        """Move obj to position (+x+, +y+)."""
        self.update(x=x, y=y)

    def _move(self, dt: Union[float, int]):
        """Move object to new position given elapsed time.
        
        +dt+ Seconds elapsed since sprite last moved.
        """
        x, y = self._eval_new_position(dt)
        x_inbounds = self._x_inbounds(x)
        y_inbounds = self._y_inbounds(y)
        if x_inbounds and y_inbounds:
            return self._move_to(x, y)
        elif self._at_boundary == 'stop':
            return self.stop()
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
        """Not implemented. Implement on subclass"""
        # Subclasses should incorporate if wish to handle collisions 
        # with other Sprites. Method should enact consequence for self of 
        # collision with +other_obj+.
        pass

    def refresh(self, dt: Union[float, int]):
        """Move and rotate sprite given elapsed time.
        
        +dt+ Seconds elapsed since object last moved.
        """
        self._rotate(dt)
        self._move(dt)

    def die(self, *args, **kwargs):
        self.live_physical_sprites.remove(self)
        super().die(*args, **kwargs)


class PhysicalSpriteInteractive(PhysicalSprite):
    """Extends base to provide user control via keyboard keys.
    
    User control defined via key press, key release and key hold handlers 
    which can be triggered on user interaction with:
        a single key
        a single key plus one or more modifiers
        any numerical key
        any numercial key of the number pad
        any numercial key of the top row

    NB For key hold events class only provides for handling of holding down 
    independently handled single keyboard keys, i.e. does NOT accommodate 
    holding down modifier(s) keys or triggering collective handlers defined 
    for a set of numerical keyboard keys.
    
    Instance METHODS
    --add_keymod_handler()-- Define keyboard event and corresponding handlers.
        See Subclass Interface section.
    --freeze()--  Stop object and prevent further user interaction.
    --unfreeze()--  Return control to user.

    SUBCLASS INTERFACE

    Event definition and handlers
    Subclasses should implement the --setup_keymod_handlers-- method to, 
    via calls to --add_keymod_handler--, define keyboard events and 
    specify corresponding handlers. The handlers will commonly be defined 
    as instance methods of the subclass. See --add_keymod_handler-- for 
    documentation on specifying keyboard events.
    """

    # HANDLER IMPLEMENTATION
    # All handler execution goes through --_execute_any_key_handler-- 
    # although two different routes are employed to get there...
    #
    # key press and key release events are handled by instance methods 
    # --on_key_press-- and --on_key_release-- (which in turn call 
    # --_execute_any_key_handler--). ---_setup_interactive--- pushes self 
    # to the ++window++ which has the effect that pyglet recognises the
    # instance methods as handlers and pushes them to top of handler stack.
    # The --_connect_handlers and --_disconnect_handlers-- methods ensure 
    # only one version of self is ever on the stack.

    # key hold events are identified via a pyglet KeyStateHandler object 
    # which is instantiated and pushed to ++window++ when the class 
    # instantiates its first instance. Every time the sprite is redrawn (via 
    # --refresh()--, the KeyStateHandler object is interrogated to see if 
    # any of the handled keyboard keys is currently pressed. If so, executes 
    # the appropriate handler via --_execute_any_key_handler--.
    

    _NUMPAD_KEYS = (pyglet.window.key.NUM_0,
                   pyglet.window.key.NUM_1,
                   pyglet.window.key.NUM_2,
                   pyglet.window.key.NUM_3,
                   pyglet.window.key.NUM_4,
                   pyglet.window.key.NUM_5,
                   pyglet.window.key.NUM_6,
                   pyglet.window.key.NUM_7,
                   pyglet.window.key.NUM_8,
                   pyglet.window.key.NUM_9)

    _NUMROW_KEYS = (pyglet.window.key._0,
                   pyglet.window.key._1,
                   pyglet.window.key._2,
                   pyglet.window.key._3,
                   pyglet.window.key._4,
                   pyglet.window.key._5,
                   pyglet.window.key._6,
                   pyglet.window.key._7,
                   pyglet.window.key._8,
                   pyglet.window.key._9)

    _NUM_KEYS = _NUMPAD_KEYS + _NUMROW_KEYS

    _pyglet_key_handler: pyglet.window.key.KeyStateHandler
    _interactive_setup = False

    @classmethod
    def _setup_interactive(cls):
        """Setup pyglet key state handler."""
        # Executed only once (on instantiating first instance).
        cls._pyglet_key_handler = pyglet.window.key.KeyStateHandler()
        cls._window.push_handlers(cls._pyglet_key_handler)
        cls._interactive_setup = True

    @staticmethod
    def _as_passed_or_empty_lambda(as_passed: Optional[Callable]) -> Callable:
        if callable(as_passed):
            return as_passed
        else:
            return lambda key, modifier: None

    @staticmethod
    def _eval_keymod(key: Union[int, 'num', 'numrow', 'numpad'],
                     modifiers: Union[int, str] = '') -> str:
        """Evaluate and return internal keymod string that represents 
        +key+ and +modifiers+"""
        if modifiers == '':
            return str(key)
        else:
            return str(key) + ' ' + str(modifiers)

    @staticmethod
    def _keypart(keymod: 'str') -> str:
        """Return first part of the internal keymod string +keymod+.
        
        Examples:
        >>> PhyscialInteractiveSprite._keypart(97) -> '97'
        >>> PhyscialInteractiveSprite._keypart(97 18) -> '97'
        """
        return keymod.split(' ')[0]

    def __init__(self, **kwargs):
        """Pass all arguments as kwargs."""
        super().__init__(**kwargs)
        if not self._interactive_setup:
            self._setup_interactive()

        self._keymod_handlers = {}  # Populated by --setup_keymod_handlers--
        self.setup_keymod_handlers()

        # Set by --_set_keyonly_handlers-- to replicate --_keymod_handlers-- 
        # although only including items that define keyboard events involving 
        # a single keyboard key. Employed by --_key_hold_handlers--.
        self._keyonly_handlers: Dict[int, dict]
        self._set_keyonly_handlers()
        
        # Set by --_set_handle_number_bools--
        self._handle_numbers_together: bool 
        self._num: bool
        self._numpad: bool
        self._numrow: bool
        self._set_handle_number_bools()
        
        self._connected = False  # Set to True by --_connect_handlers--
        self._connect_handlers()
        
        self._frozen = False  # Set by --freeze-- and --unfreeze--

    def _connect_handlers(self):
        """Push to stack event handlers defined as instance methods."""
        if not self._connected:
            self._window.push_handlers(self)
        self._connected = True

    def _disconnect_handlers(self):
        """Remove from stack event handlers defined as instance methods."""
        self._window.remove_handlers(self)
        self._connected = False
    
    def add_keymod_handler(self, key: Union[int, 'num'],  
                           modifiers: Optional[int] = '',
                           on_press: Optional[Callable] = None,
                           on_release: Optional[Callable] = None,
                           while_pressed: Optional[Callable] = None):
        """Add a handler to handle pressing and/or releasing and/or 
        holding a a defined keyboard key or keys.
        
        +on_press+ Callable to be executed when the defined keyboard key 
            or keys is/are pressed.
        +on_release+ Callable to be executed when the defined keyboard key 
            or keys is/are released.
        +while_pressed+ Callable to be executed every time the window 
            refreshes whilst the defined keyboard key is held down. NB Can 
            only handle holding down a single keyboard key. AssertionError 
            raised if both +while_pressed+ and +modifiers+ passed or 
            +key+ passed as 'num', 'numpad' or 'numrow' (see further below).
        Any of +on_press+, +on_release+ and +while_pressed+ can be passed 
            as None, or not passed, if that particular event is not to 
            be handled for the defined keyboard key or keys.
        ALL of any callables passed to +on_press+, +on_release+ and 
            +while_pressed+ MUST accommodate 'key' and 'modifiers' as their 
            first two parameters (after any self parameter). Whenever the 
            handlers are called these parameters will receive the key and 
            modifier(s) values of the actual event (as the integers that 
            pyglet uses to represent keyboard keys - see furher below).
        
        The keyboard key or keys to be handled is defined by the +key+ and 
        +modifiers+ arguments.

        To handle a specific keyboard key plus, optionally, modifier(s):
            +key+ Integer that pyglet uses to represent the specific keyboard 
                key. The pyglet.window.key module defines a set of 
                intelligibly named constants, for example 'A', 'LEFT', 'F3', 
                each of which is assigned a corresponding integer. For
                example, to specify the key 'A' pass key=pyglet.window.key.A
                which results in the key parameter receiving the integer 97.
            +modifiers+ Only if a modifier is to be specified, pass as 
                integer that pyglet uses to represent a specific modifier key 
                or combination of modifier keys. NB the integer for a 
                combination of modifier keys is the sum of the integers that
                represent each of the modifier keys being combined. For 
                example:
                >>> pyglet.window.key.MOD_CTRL
                2
                >>> pyglet.window.key.MOD_SHIFT
                1
                So, to define modifiers as CTRL + SHIFT pass modifiers=3.
        
                pyglet.window.key documentation:
                https://pyglet.readthedocs.io/en/latest/modules/window_key.html
                
        To handle any numerical key:
            +key+ 'num'.
            
        To handle any numerical key of the number pad:
            +key+ 'numpad'.
            
        To handle any numerical key of the number row:
            +key+ 'numrow'.

        When handling numerical keys collectively:
            In all cases can, if required, include modifier(s) by passing 
                +modifiers+ in same way as described above.
            It is NOT possible to add a keymod handler with +key+ 'num' and 
                another with +key+ as either 'numpad' or 'numrow' (which 
                would otherwise create ambiguity as to which handler should 
                be employed).
        """
        if while_pressed is not None:
            assert modifiers == '' and\
                not (isinstance(key, str) and key[:3] == 'num'),\
                "while_pressed handler cannot accommodate modifiers or"\
                " collective handling of numerical keys"
                    
        on_press = self._as_passed_or_empty_lambda(on_press)
        on_release = self._as_passed_or_empty_lambda(on_release)
        while_pressed = self._as_passed_or_empty_lambda(while_pressed)

        keymod = self._eval_keymod(key, modifiers)
        self._keymod_handlers[keymod] = {'on_press': on_press,
                                         'on_release': on_release,
                                         'while_pressed': while_pressed}

    def setup_keymod_handlers(self):
        """Not implemented by this class.
        
        Method should be implemented by subclass in accordance with 
        'Subclass Interface' section of this class' documentation.
        """
        pass

    def _set_keyonly_handlers(self):
        self._keyonly_handlers = {}
        for keymod, handlers in self._keymod_handlers.items():
            try:
                key = int(keymod)
            except ValueError:
                continue
            else:
                self._keyonly_handlers[key] = handlers

    def _set_handle_number_bools(self):
        """Set instance attributes indiciating how numeric keyboard keys 
        are handled.
        
        Raise assertion error if trying to handle indpendently number 
        keys and either number pad keys or number row keys.
        """
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
                "as keymods."

    def _get_keymod(self, key: int, modifiers: Union[int, str] = '') -> str:
        """Return the internal keymod string that would map to any handlers 
        setup to handle a keyboard event defined by +key+ and +modifiers+.

        +key+ Integer used by pyglet to represent a specific keyboard key.
        +modifiers+ Integer used by pyglet to represent a specific keyboard 
            modifier key or combination of modifier keys.

        NB The method makes no claim as to whether any handlers do exist for 
        the keyboard event defined by +key+ and +modifiers+, but only that 
        if such handlers were to exist then the returned internal keymod 
        string would map to them.
        """
        if self._handle_numbers_together:
            ext = ' ' + str(modifiers) if modifiers else ''
            if self._num and key in self._NUM_KEYS:
                return 'num' + ext
            elif self._numpad and key in self._NUMPAD_KEYS:
                return 'numpad' + ext
            elif self._numrow and key in self._NUMROW_KEYS:
                return 'numrow' + ext
        return self._eval_keymod(key, modifiers)

    def _keymod_handled(self, key: int, 
                       modifiers: Union[int, str] = '') -> Union[str, bool]:
        """Return internal keymod string that maps to handlers setup to 
        handle the actual keyboard event defined by +key+ and +modifiers+ 
        (be that event key press, key release or key held) or False if no 
        such handlers exist.

        +key+ Integer used by pyglet to represent a specific keyboard key.
        +modifiers+ Integer used by pyglet to represent a specific keyboard 
            modifier key or combination of modifier keys.
        """
        keymod = self._get_keymod(key, modifiers)
        
        # handler exists for +key+ +modifiers+ combo
        if keymod in self._keymod_handlers:
            return keymod # examples: '97 18', 'num 18'
        
        # Handler exists for +key+ which represents a numerical keyboard 
        # key handled by a collective handler. +modifiers+ are ignored, 
        # thereby ensuring handlers work as intended regardless of whether
        # numlock, capslock etc are on or off.
        elif keymod[0:3] == 'num':
            return self._keypart(keymod)  # 'num', 'numpad', or 'numrow'
        
        # Handler exists for +key+ (which does not represent a numerical 
        # key handled collectively). +modifiers are again ignored.
        elif str(key) in self._keymod_handlers:
            return str(key)  # example: '97'
        
        # No handler exists for defined keyboard event
        else:
            return False

    def _execute_any_key_handler(self, key: int, circumstance: str,
                                 modifiers: Union[int, str] = ''):
        """Execute any handler setup to handle the actual keyboard event 
        defined by +key+, +modifiers+ and +circumstance+.

        +key+ Integer used by pyglet to represent a specific keyboard key.
        +modifiers+ Integer used by pyglet to represent a specific keyboard 
            modifier key or combination of modifier keys.
        +circumstance+ 'on_press', 'on_release' or 'while_pressed'.
        """
        keymod = self._keymod_handled(key, modifiers)
        if not keymod:
            return
        self._keymod_handlers[keymod][circumstance](key, modifiers)
        return True  # Prevents event propaging through stack if handled.

    def on_key_press(self, symbol: int, modifiers: int):
        """Key press handler."""
        self._execute_any_key_handler(symbol, 'on_press', modifiers)
                    
    def on_key_release(self, symbol: int, modifiers: int):
        """Key release handler."""
        self._execute_any_key_handler(symbol, 'on_release', modifiers)

    def _key_hold_handlers(self):
        """Execute any 'while_pressed' handler that exists for any keyboard
        key that is currently pressed.
        """
        for key in self._keyonly_handlers:
            if self._pyglet_key_handler[key]:
                    self._execute_any_key_handler(key, 'while_pressed')


    def freeze(self):
        """Stop object and prevent further user interaction."""
        self.stop()
        self._disconnect_handlers()
        self._frozen = True
    
    def unfreeze(self):
        """Return control to user."""
        self._connect_handlers()
        self._frozen = False
        
    def refresh(self, dt: float):
        """Move sprite for elapsed time +dt+.
        
        Only moves if not frozen.
        """
        if self._frozen:
            return
        self._key_hold_handlers()
        super().refresh(dt)

    def die(self, *args, **kwargs):
        self._disconnect_handlers()
        super().die(*args, **kwargs)