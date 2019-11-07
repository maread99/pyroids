#! /usr/bin/env python

"""Series of extensions to Sprite class together with helper functions.

CLASSES
The following hierarchy of classes each extend the class before to provide 
for an additional layer of functionality with a specific purpose.

AdvSprite(Sprite) - Enhance end-of-life, scheduling, one-voice sound, 
    flashing and scaling

OneShotAnimatedSprite(AdvSprite) - Objects decease automatically when 
    animation ends

PhysicalSprite(AdvSprite) - 2D movement and collision detection within 
    defined window area.

    ##STILL TO COMPLETE CLASSES SECTION        
        InteractiveSprite(PhysicalSprite) adds keyboard events user-interface 

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
from typing import Optional, Tuple, List, Union, Sequence, Callable
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

    ATTRIBUTES (in addition to those inherited):
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

    Class METHODS (in addition to those inherited):
    ---stop_all_sound()---  Pause sound of from live sprites
    ---resume_all_sound()---  Resume sound from from all live sprites
    ---cull_all---  Kill all live sprites
    ---decease_all---  Decease all live sprites
    ---cull_selective(exceptions)---  Kill all live sprites save +exceptions+
    ---decease_selective(exceptions)---  Deceease all live sprites save 
        +exceptions+
    
    PROPERTIES
    --live-- returns boolean indicating if object is a live sprite.

    Instance METHODS (in addition to those inherited):
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

    @classmethod
    def stop_all_sound(cls):
        """Pause sound from all live sprites."""
        for sprite in cls.live_sprites:
            sprite.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        """For all live sprites, resume any sound that was paused"""
        for sprite in cls.live_sprites:
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

    def __init__(self, sound=True, sound_loop=False, 
                 on_kill: Optional[Callable] = None,
                 on_die: Optional[Callable] = None, **kwargs):
        """Extends inherited constructor.
        
        ++img++  If not received, passes 'img' as ---img---
        ++sound++  If True will play ---snd--- at end of instantiation 
            which will loop if ++sound_loop++ True
        ++on_kill++  Callable called if sprite killed
        ++on_die++  Callable called if sprite deceased
        """
        kwargs.setdefault('img', self.img)
        self._on_kill = on_kill if on_kill is not None else lambda: None
        self._on_die = on_die if on_die is not None else lambda: None
        super().__init__(**kwargs)
        
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
        
    def die(self, stop_sound=True):
        """Decease object at end-of-life."""
        # Extends inherited --delete()-- method to include additional 
        # end-of-life operations
        self.unschedule_all()
        if stop_sound:
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
    A physical sprite's s reponse to colliding with a window boundary can 
        be defined as one of the following options:
        'wrap' - reappearing at other side of the window
        'bounce' - bouncing bounce back into the window
        'die' - deceasing sprite
        'kill' - killing sprite
    The default option can be set at a class level via 
    ---setup(+at_boundary+)--- (See Subclass Interface section). In turn 
    the class default option can be overriden by any particular instance 
    via --__init__(+at_boundary+)--.

    Class ATTRIBUTES (in addition to those inherited):
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

    Class METHODS (in addition to those inherited):
    ---setup---  Setup class. Must be executed ahead of instantiating an 
        instance. See Setup Interface section.
    ---eval_collisions--- Evaluate collisions between live sprites.
    
    PROPERTIES (in addition to those inherited):
    --speed--  sprite's current speed.

    Inherited PROPERTY of note:
    --rotation--  sprite's current orientation

    Instance METHODS (in addition to those inherited):
    --refresh(dt)--  Move and rotate sprite given elapsed time +dt+.
    --position_randomly(+avoid+)-- Move sprite to random position within 
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
        assert at_boundary in ['wrap', 'bounce', 'die', 'kill']

    @classmethod
    def setup(cls, window: pyglet.window.BaseWindow,
              at_boundary='wrap',
              y_top_border=0, y_bottom_border=0,
              x_left_border=0, x_right_border=0):
        """Class setup. Define bounds and default treatment on reaching.
        
        +at_boundary+  Default response to sprite colliding with boundary, 
            either 'wrap', 'bounce', 'die' or 'kill'.
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
            'die' or 'kill'.
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
        """Rotate sprite between 110 and 250 degrees."""
        d = random.randint(110, 250)
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


    SUBCLASS INTERFACE


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
        cls._window.push_handlers(cls._pyglet_key_handler)
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
            self._window.push_handlers(self)
        self._connected = True

    def disconnect_handlers(self):
        """Disconnects --on_key_press-- and --on_key_release-- event handlers 
        such that they will stop handle these key events. See cls.__doc__."""
        self._window.remove_handlers(self)
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

#### HERERE - REVISING documentation of ABOVE class, 
#   Update module doc when finished revising this class