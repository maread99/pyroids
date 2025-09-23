"""Extensions to Sprite class and helper functions.

Helper functions to create pyglet objects from files in the pyglet resource
directory and to manipulate the created objects.

Classes
-------
The following hierarchy of classes each extend the class before to provide
for an additional layer of functionality with a specific purpose.

AdvSprite(Sprite)
    Enhance end-of-life, scheduling, one-voice sound, flashing and scaling.

OneShotAnimatedSprite(AdvSprite)
    Objects decease automatically when animation ends.

PhysicalSprite(AdvSprite)
    2D movement and collision detection within defined window area.

InteractiveSprite(PhysicalSprite)
    User control via keyboard keys.

Helper classes:
    InRect
        Check if a point lies in a defined rectangle.
    AvoidRect
        Define an area to avoid as a rectangle around a sprite.
"""

from __future__ import annotations

import contextlib
import math
import random
from collections.abc import Sequence
from copy import copy
from itertools import combinations
from typing import TYPE_CHECKING, Callable, ClassVar, Literal

import pyglet
from pyglet.image import Animation, Texture, TextureRegion
from pyglet.sprite import Sprite

from pyroids.utils import physics

from .audio_ext import StaticSourceMixin

if TYPE_CHECKING:
    from pyglet.media import StaticSource


def centre_image(image: TextureRegion | Sequence[TextureRegion]):
    """Set anchor points for an image to centre of that image."""
    if not isinstance(image, Sequence):
        image = [image]
    for img in image:
        img.anchor_x = img.width // 2
        img.anchor_y = img.height // 2


def centre_animation(animation: Animation):
    """Centre all frames of an `animation`."""
    for frame in animation.frames:
        centre_image(frame.image)


def load_image(
    filename: str,
    anchor: Literal["origin", "center"] = "origin",
) -> TextureRegion:
    """Load an image from resource.

    Parameters
    ----------
    filename
        Image to load.

    anchor
        Set anchor points to image 'origin' or 'center'.
    """
    valid = ["origin", "center"]
    if anchor not in valid:
        msg = f"'anchor' must take a value from {valid} although received '{anchor}'."
        raise ValueError(msg)
    img = pyglet.resource.image(filename)
    if anchor == "center":
        centre_image(img)
    return img


def load_image_sequence(
    filename: str,
    num_images: int,
    placeholder: str = "?",
    anchor: Literal["origin", "center"] = "origin",
) -> list[pyglet.image.Texture]:
    """Load sequence of images from resource.

    Example usage:
    load_image_sequence(filename='my_img_seq_?.png', num_images=3,
                        placeholder='?')
    -> list[pyglet.image.Texture] where images loaded from following files
    in resource directory:
        my_img_seq_0.png
        my_img_seq_1.png
        my_img_seq_2.png

    Parameters
    ----------
    filename
        Name of image filename where `filename` includes a `placeholder`
        character that represents position where filenames are sequentially
        enumerated. First filename enumerated 0.

    num_images
        Number of images in sequence.

    placeholder
        Placeholder character in `filename` that represents position where
        filenmaes are sequentially enumerated.

    anchor
        Set anchor points to image 'origin' or 'center'.
    """
    return [
        load_image(filename.replace(placeholder, str(i)), anchor=anchor)
        for i in range(num_images)
    ]


def load_animation(
    filename: str,
    anchor: Literal["origin", "center"] = "origin",
) -> Animation:
    """Load an animation from resource.

    Parameters
    ----------
    filename
        Name of animation file. Acceptable filetypes inlcude .gif.

    anchor
        Anchor each animation image to image 'origin' or 'center'.
    """
    valid = ["origin", "center"]
    if anchor not in valid:
        msg = f"'anchor' must take a value from {valid} although received '{anchor}'."
        raise ValueError(msg)
    animation = pyglet.resource.animation(filename)
    if anchor == "center":
        centre_animation(animation)
    return animation


def anim(
    filename: str,
    rows: int,
    cols: int,
    frame_duration: float = 0.1,
    *,
    loop: bool = True,
) -> Animation:
    """Create Animation object from image of regularly arranged subimages.

    Parameters
    ----------
    filename
        Name of file in resource directory of image of subimages regularly
        arranged over `rows` and `columns`.

    rows
        Number of rows that comprise each subimage.

    columns
        Number of columns that comprise each subimage.

    frame_duration
        Seconds each frame of animation should be displayed.
    """
    img = pyglet.resource.image(filename)
    image_grid = pyglet.image.ImageGrid(img, rows, cols)
    animation = image_grid.get_animation(frame_duration, loop=loop)
    centre_animation(animation)
    return animation


def distance(sprite1: Sprite, sprite2: Sprite) -> int:
    """Return distance in pixels between two sprites.

    Parameters
    ----------
    sprite1, sprite2
        Sprites to evaluate distance bewteen.
    """
    return physics.distance(sprite1.position, sprite2.position)


def vector_anchor_to_rotated_point(
    x: int,
    y: int,
    rotation: float,
) -> tuple[int, int]:
    """Return vector to rotated point.

    Where +x+ and +y+ describe a point relative to an image's anchor
    when rotated 0 degrees, returns the vector, as (x, y) from the anchor
    to the same point if the image were rotated by +rotation+ degrees.

    +rotation+  Degrees of rotation, clockwise positive, 0 pointing 'right',
        i.e. as for a sprite's 'rotation' attribute.
    """
    dist = physics.distance((0, 0), (x, y))
    angle = math.asin(y / x)
    rotation = -math.radians(rotation)
    angle_ = angle + rotation
    x_ = dist * math.cos(angle_)
    y_ = dist * math.sin(angle_)
    return (x_, y_)


class InRect:
    """Check if a point lies within a defined rectangle.

    Class only accommodates rectangles that with sides that are parallel
    to the x and y axes.

    Constructor defines rectangle.

    Parameters
    ----------
    x_from
        x coordinate of recectangle's left side
    x_to
        x coordinate of recectangle's right side i.e. x coordinate
        increasingly positive as move right.
    y_from
        y coordinate of recectangle's bottom side
    y_to
        y coordinate of recectangle's top side i.e. y coordinate
        increasingly positive as move up.

    Attributes
    ----------
    width
        rectangle width
    height
        rectangle width
    x_from
        As passed to constuctor.
    x_to
        As passed to constuctor.
    y_from
        As passed to constuctor.
    y_to
        As passed to constuctor.
    """

    def __init__(self, x_from: int, x_to: int, y_from: int, y_to: int):
        self.x_from = x_from
        self.x_to = x_to
        self.y_from = y_from
        self.y_to = y_to
        self.width = x_to - x_from
        self.height = y_to - y_from

    def inside(self, position: tuple[int, int]) -> bool:
        """Query is a `position` lies in rectangle.

        Parameters
        ----------
        position
            Position to query.
        """
        x = position[0]
        y = position[1]
        return self.x_from <= x <= self.x_to and self.y_from <= y <= self.y_to


class AvoidRect(InRect):
    """Define rectangular area around a sprite.

    Intended use is to avoid AvoidRects when positioning other sprites in
    order that the sprites do not overlap / immediately collide.

    Extends InRect to define a rectangle that encompasses a sprite and
    any margin.

    Parameters
    ----------
    sprite
        Sprite to avoid.

    margin
        Margin around sprite to include in avoid rectangle.

    Attributes
    ----------
    sprint
        As passed to constructor.
    margin
        As passed to constructor.
    """

    def __init__(self, sprite: Sprite, margin: int | None = None):
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
        additional end-of-life functionality (see End-Of-Life section).
        additional scheduling events functionality (see Scheduling
            section).
        register of live sprites.
        sound via inherited StaticSourceMixin (see documentation for
            StaticSourceMixin).
        sprite flashing.
        sprite scaling.

    END-OF-LIFE
    Class makes end-of-life distinction between 'killed' and 'deceased':

        Deceased
            Death. The `die()` method deceases the object. Any callable
            passed to constuctor's `on_die` parameter will be executed as
            part of the implementation.

        Killed
            Premature Death. The `kill()` method will kill the object
            prematurely. Any callable passed to constructor's `on_kill`
            parameter will be executed as part of the implementation.
            Implementation concludes by deceasing the object.

    For arcade games the above distinction might be implemented such that
    an object is killed if its life ends as a consequence of an in game
    action (for example, on being shot) or is otherwise simply deceased
    when no longer required.

    SCHEDULING
    `schedule_once()` and `schedule_all()` methods are provided to
    schedule future calls. So long as all furture calls are scheduled
    through these methods, scheduled calls can be collectively
    or individually unscheduled via `unschedule_all()` and
    `unschedule()` respectively.

    Attributes
    ----------
    `live_sprites`
        List of all instantiated sprites not subsequently deceased.
    `snd`
        Sprite's main sound (see StaticSourceMixin documentation)
    `img`
        Sprite image (see Subclass Interface section)
    `live`
        Query if object is a live sprite.

    Methods
    -------
    stop_all_sound
        Pause sound of from live sprites.
    resume_all_sound
        Resume sound from from all live sprites.
    cull_all
        Kill all live sprites.
    decease_all
        Decease all live sprites.
    cull_selective
        Kill all live sprites save exceptions.
    decease_selective
        Deceease all live sprites save exceptions.

    scale_to
        Scale object to size of another object.
    flash_start
        Make sprite flash.
    flash_stop
        Stop sprite flashing.
    toggle_visibility
        Toggle visibility.
    schedule_once
        Schedule a future call to a function.
    schedule_interval
        Schedule regular future calls to a function.
    unschedule
        Unschedule future call(s) to a function.
    unschedule_all
        Unschedule all future calls to a function.
    kill
        Kill object
    die
        Decease object

    Notes
    -----
    SUBCLASS INTERFACE

    Sound
    See Subclass Interface section of `StaticSourceMixin` documentation.

    Image
    Subclass should define class attribute `img` and assign it a pyglet
    `Texture` or `Animation` object which will be used as the sprite's
    default image. Helper functions `anim()` and `load_image()` can be
    used to directly create `Animation` and `Texture` objects from image
    files in the resources directory, for example:
        img = anim('explosion.png', 2, 8)  # Animation
        img = load_image('ship_blue.png', anchor='center')  # Texture

    Note: the default image can be overriden by passing a pyglet image to
    the constructor as `img`.

    End-of-Lfe
    Subclasses should NOT OVERRIDE the die() or kill() methods. These
    methods can be EXTENDED to provide for any additional end-of-life
    operations that may be required.
    """

    img: Texture | Animation
    snd: StaticSource

    live_sprites: ClassVar[list] = []
    _dying_loudly: ClassVar[list] = []

    @classmethod
    def stop_all_sound(cls):
        """Pause sound from all live sprites."""
        for sprite in cls.live_sprites + cls._dying_loudly:
            sprite.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        """Resume all sounds.

        Resumes any sound that was paused for all live sprites.
        """
        for sprite in cls.live_sprites + cls._dying_loudly:
            sprite.resume_sound()

    @classmethod
    def _end_lives_all(cls, *, kill: bool = False):
        """End life of all live sprites without exception.

        Parameters
        ----------
        kill
            True to kill all sprites, False to merely decease them.
        """
        for sprite in cls.live_sprites[:]:
            if kill:
                sprite.kill()
            else:
                sprite.die()
        assert not cls.live_sprites, (  # noqa: S101
            "following sprites still alive"
            " after ending all lives: " + str(cls.live_sprites)
        )

    @classmethod
    def _end_lives_selective(
        cls,
        exceptions: list[Sprite | type[Sprite]] | None = None,
        *,
        kill: bool = False,
    ):
        """End life of all live sprites.

        Parameters
        ----------
        exceptions
            List of exceptions to be spared. Pass as any combination of
            Sprite objects or subclasses of Sprite, where all instances of
            any passed subclass will be spared.

        kill
            True to kill sprites, False to merely decease them.
        """
        if not exceptions:
            cls._end_lives_all(kill=kill)
            return

        exclude_classes = []
        exclude_objs = []
        for exception in exceptions:
            if type(exception) is type:
                exclude_classes.append(exception)
            else:
                exclude_objs.append(exception)

        for sprite in cls.live_sprites[:]:
            if sprite in exclude_objs or type(sprite) in exclude_classes:
                continue
            if kill:
                sprite.kill()
            else:
                sprite.die()

    @classmethod
    def cull_all(cls):
        """Kill all live sprites without exception."""
        cls._end_all_lives(kill=True)

    @classmethod
    def decease_all(cls):
        """Decease all live sprites without exception."""
        cls._end_all_lives(kill=False)

    @classmethod
    def cull_selective(cls, exceptions: list[Sprite | type[Sprite]] | None = None):
        """Kill all live sprites save for `exceptions`.

        Parameters
        ----------
        exceptions
            List of exceptions to be spared. Pass as any combination of
            Sprite objects or subclasses of Sprite, where all instances of
            any passed subclass will be spared.
        """
        cls._end_lives_selective(exceptions=exceptions, kill=True)

    @classmethod
    def decease_selective(cls, exceptions: list[Sprite | type[Sprite]] | None = None):
        """Decease all live sprites save for `exceptions`.

        Parameters
        ----------
        exceptions
            List of exceptions to be spared. Pass as any combination of
            Sprite objects or subclasses of Sprite, where all instances of
            any passed subclass will be spared.
        """
        cls._end_lives_selective(exceptions=exceptions, kill=False)

    def __init__(
        self,
        scale_to: Sprite | Texture = None,
        *,
        sound: bool = True,
        sound_loop: bool = False,
        on_kill: Callable | None = None,
        on_die: Callable | None = None,
        **kwargs,
    ):
        """Instantiate object.

        Parameters
        ----------
        scale_to
            Scale sprite to dimensions of passed object.

        sound
            True to play class `snd` at end of instantiation.

        sound_loop
            True to loop sound at end of instantiation. Ignored if `sound`
            False.

        on_kill
            Handler to call if sprite killed.

        on_die
            Handler to call if sprite deceased.

        img
            Sprite image. Defaults to class `img`.
        """
        kwargs.setdefault("img", self.img)
        self._on_kill = on_kill if on_kill is not None else lambda: None
        self._on_die = on_die if on_die is not None else lambda: None
        super().__init__(**kwargs)

        if scale_to is not None:
            self.scale_to(scale_to)

        self.live_sprites.append(self)  # add instance to class attribute

        self._scheduled_funcs = []

        StaticSourceMixin.__init__(self, sound=sound, loop=sound_loop)

    @property
    def live(self) -> bool:
        """Query if object is a live sprite."""
        return self in self.live_sprites

    def toggle_visibility(self, _: float | None = None):
        """Toggle sprite visibility.

        Parameters
        ----------
        -
            Unused parameter receives seconds since method last called when
            called via pyglet scheduled event.
        """
        self.visible = not self.visible

    def flash_stop(self, *, visible: bool = True):
        """Stop sprite flashing."""
        self.unschedule(self.toggle_visibility)
        self.visible = visible

    def flash_start(self, frequency: float = 3):
        """Start sprite flashing or change flash frequency.

        Parameters
        ----------
        frequency
            Frequency at which to flash sprite, as flashes per second.

        See Also
        --------
        flash_stop
        """
        self.flash_stop()
        self.schedule_interval(self.toggle_visibility, 1 / (frequency * 2))

    def scale_to(self, obj: Sprite | Texture):
        """Scale object to same size as another object.

        Parameters
        ----------
        obj
            Object to which to scale the sprite.
        """
        x_ratio = obj.width / self.width
        self.scale_x = x_ratio
        y_ratio = obj.height / self.height
        self.scale_y = y_ratio

    # CLOCK SCHEDULE
    def _add_to_schedule(self, func: Callable):
        self._scheduled_funcs.append(func)

    def schedule_once(self, func: Callable, dt: float):
        """Schedule call to a function.

        Parameters
        ----------
        func
            Function to schedule. Must be able to accept first parameter as
            the duration since function was last called (this duration will
            be passed to function by pyglet).

        dt
            Duration until `func` should be called, in seconds.
        """
        pyglet.clock.schedule_once(func, dt)
        self._add_to_schedule(func)

    def schedule_interval(self, func: Callable, dt: float):
        """Schedule regular calls to a function.

        Parameters
        ----------
        func
            Function to be regularly called. Must be able to accept first
            parameter as the duration since function was last called (this
            duration will be passed to function by pyglet).

        dt
            Interval between each call to `func`.
        """
        pyglet.clock.schedule_interval(func, dt)
        self._add_to_schedule(func)

    def _remove_from_schedule(self, func: Callable):
        # mirrors behaviour of pyglet.clock.unschedule by ignoring requests
        # to unschedule events that have not been previously scheduled
        with contextlib.suppress(ValueError):
            self._scheduled_funcs.remove(func)

    def unschedule(self, func: Callable):
        """Unschedule future calls to a function.

        Parameters
        ----------
        func
            Function to unschedule. Can be an callable previously scheduled
            via either `schedule_once` or `schedule_interval`. Note: passes
            silently if `func` not previously scheduled.
        """
        pyglet.clock.unschedule(func)
        self._remove_from_schedule(func)

    def unschedule_all(self):
        """Unschedule future calls to all functions."""
        for func in self._scheduled_funcs[:]:
            self.unschedule(func)

    # END-OF-LIFE
    def kill(self):
        """Kill object prematurely."""
        self._on_kill()
        self.die()

    def _waiting_for_quiet(self, _: float):
        if not self.sound_playing:
            self.unschedule(self._waiting_for_quiet)
            self._dying_loudly.remove(self)

    def _die_loudly(self):
        self._dying_loudly.append(self)
        self.schedule_interval(self._waiting_for_quiet, 0.1)

    def die(self, *, die_loudly: bool = False):
        """Decease object at end-of-life.

        Parameters
        ----------
        die_loundly
            True to let any playing sound continue.
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
        """Event handler."""
        self.die()


class PhysicalSprite(SpriteAdv):
    """Extends SpriteAdv for 2D movement and collision detection.

    The PhysicalSprite class:
        defines the window area within which physical sprites can move.
        can evalutate collisions between live physical sprites instances.

    A physcial sprite:
        has a speed and a rotation speed.
        has a cruise speed and rotation curise speed that can be set and
            in turn which the sprite's speed and rotation speed can be set
            to.
        can update its position for a given elapased time.
        can resolve colliding with a window boundary (see Boundary
            Response section).
        can resolve the consequence of colliding with another sprite in the
        window area (requires implementation by subclass - see Subclas
        Interface).

    BOUNDARY RESPONSE
    A physical sprite's reponse to colliding with a window boundary can
    be defined as one of the following options:
        'wrap' - reappearing at other side of the window.
        'bounce' - bouncing bounce back into the window.
        'stop' - stops at last position within bounds.
        'die' - deceasing sprite.
        'kill' - killing sprite.
    The class default option can be set at a class level via the
    `at_boundary` parameter of the 'setup' function (See Subclass Interface
    section). In turn this class default option can be overriden by any
    particular instance by passing the `at_boundary` parameter to the
    constructor.

    Attributes
    ----------
    live_physical_sprites
        List of all instantiated `PhysicalSprite` instances that have not
        subsequently deceased.
    X_MIN
        Left boundary.
    X_MAX
        Right boundary.
    Y_MIN
        Bottom boundary.
    Y_MAX
        Top boundary.
    WIDTH
        Width of window area in which sprite can move.
    HEIGHT
        Height of window area in which sprite can move.
    AT_BOUNDARY
        Default response if sprite collides with boundary.
    speed
        Sprite's current speed.
    rotation
        Sprite's current orientation.

    Notes
    -----
    SUBCLASS INTERFACE

    Setup
    Before instantiating any instance, the subclass must set up the class
    via the class method `setup()`. This setup method defines the window
    bounds and response to sprite colliding with boundaries.

    Sprite Image
    The sprite image (either assigned to the class attribute `img` or
    passed as `img`) must be anchored at the image center in order for the
    class to evaluate collisions. The following helper functions provide
    for creating centered pyglet image objects:
        load_image()
        load_animation()
        anim()

    Collision Resolution
    collided_with(other_obj) is defined on this class although not
    implemented. If subclass is to resolve collisions then this method
    should be implemented to handle the consequence of the PhysicalSprite
    colliding with another live sprite. NOTE: Method should only handle
    consequences for the `PhysicalSprite` instance, NOT for the `other_obj`
    (the client is responsible for advising the `other_obj` of any
    collision, as the client deems necessary).
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
    def _verify_at_boundary(at_boundary: str):
        valid = ["wrap", "bounce", "stop", "die", "kill"]
        if at_boundary not in valid:
            msg = (
                f"{at_boundary} is not a valid value for the 'at_boundary' parameter."
                " Valid values are: '{valid}'."
            )
            raise ValueError(msg)

    @classmethod
    def setup(  # noqa: PLR0913
        cls,
        window: pyglet.window.BaseWindow,
        at_boundary: Literal["wrap", "bounce", "stop", "die", "kill"] = "wrap",
        y_top_border: int = 0,
        y_bottom_border: int = 0,
        x_left_border: int = 0,
        x_right_border: int = 0,
    ):
        """Class setup. Define bounds and default treatment on reaching.

        Parameters
        ----------
        window
            Game window to which sprite will be drawn
        at_boundary
            Default response to sprite colliding with boundary, From
            ['wrap', 'bounce', 'stop', 'die', 'kill'].
        y_top_border, y_bottom_border, x_left_border, x_right_border
            Provide margin within window when evaluating 'bounds'. Bounds
            will be evaluated as window extent less width of corresponding
            border argument.
        """
        cls.live_physical_sprites = []
        cls._window = window
        cls._verify_at_boundary(at_boundary)
        cls.AT_BOUNDARY = at_boundary
        cls.X_MIN = 0 + x_left_border
        cls.X_MAX = window.width - x_right_border
        cls.Y_MIN = 0 + y_bottom_border
        cls.Y_MAX = window.height - y_top_border
        cls.WIDTH = cls.X_MAX - cls.X_MIN
        cls.HEIGHT = cls.Y_MAX - cls.Y_MIN
        cls._setup_complete = True

    @classmethod
    def eval_collisions(cls) -> list[tuple[Sprite, Sprite]]:
        """Evaluate live sprites that have collided.

        Returns list of 2-tuples where each tuple signifies a collision
        between the 2 sprites it contains.

        Collisions evaluated based on approximate proximity. Two sprites
        separated by a distance of less than half their combined
        width are considered to have collided. Perfect for circular
        images, increasingly inaccurate the further the image deviates
        from a circle.

        NB Basis for proximity evaluation ASSUMES sprite image anchored at
        image's center.
        """
        collisions = []
        for obj, other_obj in combinations(copy(cls.live_physical_sprites), 2):
            min_separation = (obj.width + other_obj.width) // 2
            if distance(obj, other_obj) < min_separation:
                collisions.append((obj, other_obj))
        return collisions

    def __init__(  # noqa: PLR0913
        self,
        initial_speed: int = 0,
        initial_rotation_speed: int = 0,
        cruise_speed: int = 200,
        rotation_cruise_speed: int = 200,
        initial_rotation: int = 0,
        at_boundary: str | None = None,
        **kwargs,
    ):
        """Instantiate instance.

        Before any instance can be instantiated class must be setup
        via class method ---setup()---. Otherwise will raise AssertionError.

        Parameters (added by this subclass)
        ----------
        initial_speed
            Sprite's initial speed.
        initial_rotation_speed
            Sprite's initial rotation speed.
        cruise speed
            Sprite's cruise speed.
        rotation_curise_speed
            Sprite's cruise rotational speed.
        initial_rotation
            Sprite's initial rotation.
        at_boundary
            Default response to sprite colliding with boundary, From
            ['wrap', 'bounce', 'stop', 'die', 'kill']. NB: will override,
            for this instance, any default value perviously passed to
            `setup()`.

        Notes
        -----
        Extends inherited constructor to define subclass specific settings.
        """
        if not self._setup_complete:
            msg = "PhysicalSprite class must be setup before instantiating instances"
            raise RuntimeError(msg)

        super().__init__(**kwargs)
        self.live_physical_sprites.append(self)
        self._at_boundary = at_boundary if at_boundary is not None else self.AT_BOUNDARY
        self._verify_at_boundary(self._at_boundary)
        self._speed: int  # Stores current speed. Set by...
        self.speed_set(initial_speed)
        self._speed_cruise: int  # Set by...
        self.cruise_speed_set(cruise_speed)
        self._rotation_speed: int  # Stores current rotation speed. Set by...
        self.rotation_speed_set(initial_rotation_speed)
        self._rotation_speed_cruise: int  # Set by...
        self.rotation_cruise_speed_set(rotation_cruise_speed)
        self.rotate(initial_rotation)

        # `_refresh_velocities` updates `_vel_x` and `_vel_y`` given
        # current speed and rotation
        self._vel_x = 0.0  # Stores current x velocity
        self._vel_y = 0.0  # Stores current y velocity

    # SPEED
    @property
    def speed(self) -> int:
        """Sprite's current speed."""
        return self._speed

    def speed_set(self, speed: int):
        """Set current speed.

        Parameters
        ----------
        speed
            Speed to set, in pixels per second.
        """
        self._speed = speed
        self._refresh_velocities()

    def cruise_speed_set(self, cruise_speed: int):
        """Set cruise speed.

        Parameters
        ----------
        cruise_speed
            Cruise speed to set, in pixels per second.
        """
        self._speed_cruise = cruise_speed

    def cruise_speed(self):
        """Set speed to cruise speed."""
        self.speed_set(self._speed_cruise)

    def speed_zero(self):
        """Set speed to 0."""
        self.speed_set(0)

    # ROTATION
    def rotation_speed_set(self, rotation_speed: int):
        """Set rotation speed.

        Parameters
        ----------
        rotation_speed
           Rotation speed to set, in pixels per second. Negative values
           rotate anticlockwise.
        """
        self._rotation_speed = rotation_speed

    def rotate(self, degrees: int):
        """Rotate sprite.

        Parameters
        ----------
        degrees
            Degrees by which to rotate sprite. Negative values rotate
            anti-clockwise.
        """
        self.rotation += degrees
        self._refresh_velocities()

    def rotation_cruise_speed_set(self, rotation_cruise_speed: int):
        """Set rotation cruise speed to +rotation_cruise_speed+."""
        self._rotation_speed_cruise = rotation_cruise_speed

    def cruise_rotation(self, *, clockwise: bool = True):
        """Set rotation speed to rotation cruise speed.

        Parameters
        ----------
        clockwise
            False to rotate anti-clockwise.
        """
        rot_speed = self._rotation_speed_cruise
        rot_speed = rot_speed if clockwise else -rot_speed
        self.rotation_speed_set(rot_speed)

    def rotation_zero(self):
        """Set rotation speed to 0."""
        self.rotation_speed_set(0)

    def rotate_randomly(self):
        """Rotate sprite to random direction."""
        self.rotate(random.randint(0, 360))  # noqa: S311

    def turnaround(self):
        """Rotate sprite by 180 degrees."""
        self.rotate(180)

    def _bounce_randomly(self):
        """Rotate sprite somewhere between 130 and 230 degrees."""
        d = random.randint(130, 230)  # noqa: S311
        if 180 <= self.rotation <= 359:  # noqa: PLR2004
            self.rotate(-d)
        else:
            self.rotate(d)

    def _rotation_radians(self) -> float:
        """Return current rotation in radians."""
        return -math.radians(self.rotation)

    def _rotate(self, dt: float):
        """Rotate sprite to reflect elapsed time.

        Parameters
        ----------
        dt
            Seconds elapsed since object last rotated.
        """
        self.rotate(self._rotation_speed * dt)

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
        """Return wrapped x coordinate.

        Where `x` respresents an x coordinate either to the left or right
        of the available window, evaluates the x coordinate representing
        the wrapped position of `x` on the 'other side' of the window.

        Parameters
        ----------
        x
            x coordinate to be wrapped.
        """
        return x + self.WIDTH if x < self.X_MIN else x - self.WIDTH

    def _wrapped_y(self, y: int) -> int:
        """Return wrapped x coordinate.

        Where `y` respresents a y coordinate either to the left or right
        of the available window, evaluates the y coordinate representing
        the wrapped position of `y` on the 'other side' of the window.

        Parameters
        ----------
        y
            y coordinate to be wrapped.
        """
        return y + self.HEIGHT if y < self.Y_MIN else y - self.HEIGHT

    def _x_inbounds(self, x: int) -> bool:
        """Query if `x` within bounds."""
        return self.X_MIN < x < self.X_MAX

    def _y_inbounds(self, y: int) -> bool:
        """Query if `y` within bounds."""
        return self.Y_MIN < y < self.Y_MAX

    def _adjust_x_for_bounds(self, x: int) -> int:
        """Evaluate new x coordinate at bounds.

        Parameters
        ----------
        x
            Evaluated next x-cordinate which lies out of bounds.

        Returns
        -------
        int
            x coordinate adjusted for boundary response.
        """
        if self._at_boundary == "wrap":
            return self._wrapped_x(x)
        if self._at_boundary == "bounce":
            self._bounce_randomly()
            return self.x
        err_msg = "no out-of-bounds treatment defined"
        raise Exception(err_msg)  # noqa: TRY002

    def _adjust_y_for_bounds(self, y: int) -> int:
        """Evaluate new y coordinate at bounds.

        Parameters
        ----------
        y
            Evaluated next y-cordinate which lies out of bounds.

        Returns
        -------
        int
            y coordinate adjusted for boundary response.
        """
        if self._at_boundary == "wrap":
            return self._wrapped_y(y)
        if self._at_boundary == "bounce":
            self._bounce_randomly()
            return self.y
        err_msg = "no out-of-bounds treatment defined"
        raise Exception(err_msg)  # noqa: TRY002

    # POSITION
    def _default_exclude_border(self):
        # exclude border 5 if `_at_boundary` is bounce to prevent repeated
        # bouncing if sprite placed on border.
        exclude_border = 5 if self._at_boundary == "bounce" else 0
        return exclude_border  # noqa: RET504

    def _random_x(self, exclude_border: int | None = None) -> int:
        """Get a random x coordinate.

        Returns random x coordinate within available window area
        excluding `exclude_border` pixels from the border.
        """
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.X_MIN + exclude_border, self.X_MAX - exclude_border)  # noqa: S311

    def _random_y(self, exclude_border: int | None = None) -> int:
        """Get a random y coordinate.

        Returns random y coordinate within available window area
        excluding `exclude_border` pixels from the border.
        """
        if exclude_border is None:
            exclude_border = self._default_exclude_border()
        return random.randint(self.Y_MIN + exclude_border, self.Y_MAX - exclude_border)  # noqa: S311

    def _random_xy(self) -> tuple[int, int]:
        """Return random position within available window area."""
        x = self._random_x()
        y = self._random_y()
        return (x, y)

    def _position_randomly(self):
        """Move sprite to random position within available window area."""
        self.update(x=self._random_x(), y=self._random_y())

    def position_randomly(self, avoid: list[AvoidRect] | None = None):
        """Move sprite to random position within available window area.

        Parameters
        ----------
        avoid
            List of `AvoidRect` defining rectangular areas to exclude
            from available window area.
        """
        if not avoid:
            self._position_randomly()
            return

        conflicts = [True] * len(avoid)
        while True in conflicts:
            xy = self._random_xy()
            for i, avd in enumerate(avoid):
                conflicts[i] = avd.inside(xy)

        self.update(x=xy[0], y=xy[1])

    def _eval_new_position(self, dt: float) -> tuple[int, int]:
        """Return obj's new position given elapsed time and ignoring bounds.

        Parameters
        ----------
        dt
            Seconds elapsed since sprite last moved.
        """
        dx = self._vel_x * dt
        dy = self._vel_y * dt
        x = self.x + dx
        y = self.y + dy
        return (x, y)

    def _move_to(self, x: int, y: int):
        """Move obj to position (+x+, +y+)."""
        self.update(x=x, y=y)

    def _move(self, dt: float):
        """Move object to new position given elapsed time.

        Parameters
        ----------
        dt
            Seconds elapsed since sprite last moved.
        """
        x, y = self._eval_new_position(dt)
        x_inbounds = self._x_inbounds(x)
        y_inbounds = self._y_inbounds(y)
        if x_inbounds and y_inbounds:
            return self._move_to(x, y)
        if self._at_boundary == "stop":
            return self.stop()
        if self._at_boundary == "die":
            return self.die()
        if self._at_boundary == "kill":
            return self.kill()

        if not x_inbounds:
            x = self._adjust_x_for_bounds(x)
        if not y_inbounds:
            y = self._adjust_y_for_bounds(y)
        return self._move_to(x, y)

    def collided_with(self, other_obj: Sprite):  # noqa: ARG002
        """Not implemented. Implement on subclass.

        Notes
        -----
        Subclasses should implement if wish to handle collisions with other
        Sprites. Method should enact consequence for `self` of collision
        with other_obj, NOT any consequences for `other_obj`.
        """
        return

    def refresh(self, dt: float):
        """Move and rotate sprite given an elapsed time.

        Parameters
        ----------
        dt
            Seconds elapsed since object last moved.
        """
        self._rotate(dt)
        self._move(dt)

    def die(self, *args, **kwargs):
        """Decease object."""
        self.live_physical_sprites.remove(self)
        super().die(*args, **kwargs)


class PhysicalSpriteInteractive(PhysicalSprite):
    """Extends `PhysicalSprite` to provide user control via keyboard keys.

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

    Methods
    -------
    add_keymod_handler()
        Define keyboard event and corresponding handlers. See Subclass
        Interface section.
    freeze()
        Stop object and prevent further user interaction.
    unfreeze()
        Return control to user.

    Notes
    -----
    SUBCLASS INTERFACE

    Event definition and handlers
    Subclasses should implement the `setup_keymod_handlers` method to, via
    calls to `add_keymod_handler`, define keyboard events and specify
    corresponding handlers. The handlers will commonly be defined as
    instance methods of the subclass. See `add_keymod_handler` for
    documentation on specifying keyboard events.

    HANDLER IMPLEMENTATION
    All handler execution goes through `_execute_any_key_handler`
    although two different routes are employed to get there...

    key press and key release events are handled by instance methods
    `on_key_press` and `on_key_release` (which in turn call
    `_execute_any_key_handler`). `_setup_interactive` pushes self
    to the `window` which has the effect that pyglet recognises the
    instance methods as handlers and pushes them to top of handler stack.
    The `_connect_handlers` and `_disconnect_handlers` methods ensure
    only one version of self is ever on the stack.

    key hold events are identified via a pyglet `KeyStateHandler` object
    which is instantiated and pushed to `window` when the class
    instantiates its first instance. Every time the sprite is redrawn (via
    `refresh()`, the `KeyStateHandler` object is interrogated to see if
    any of the handled keyboard keys is currently pressed. If so, executes
    the appropriate handler via `_execute_any_key_handler`.
    """

    _NUMPAD_KEYS = (
        pyglet.window.key.NUM_0,
        pyglet.window.key.NUM_1,
        pyglet.window.key.NUM_2,
        pyglet.window.key.NUM_3,
        pyglet.window.key.NUM_4,
        pyglet.window.key.NUM_5,
        pyglet.window.key.NUM_6,
        pyglet.window.key.NUM_7,
        pyglet.window.key.NUM_8,
        pyglet.window.key.NUM_9,
    )

    _NUMROW_KEYS = (
        pyglet.window.key._0,  # noqa: SLF001
        pyglet.window.key._1,  # noqa: SLF001
        pyglet.window.key._2,  # noqa: SLF001
        pyglet.window.key._3,  # noqa: SLF001
        pyglet.window.key._4,  # noqa: SLF001
        pyglet.window.key._5,  # noqa: SLF001
        pyglet.window.key._6,  # noqa: SLF001
        pyglet.window.key._7,  # noqa: SLF001
        pyglet.window.key._8,  # noqa: SLF001
        pyglet.window.key._9,  # noqa: SLF001
    )

    _NUM_KEYS = _NUMPAD_KEYS + _NUMROW_KEYS

    _pyglet_key_handler: pyglet.window.key.KeyStateHandler
    _interactive_setup = False

    @classmethod
    def _setup_interactive(cls):
        """Set up pyglet key state handler."""
        # Executed only once (on instantiating first instance).
        cls._pyglet_key_handler = pyglet.window.key.KeyStateHandler()
        cls._window.push_handlers(cls._pyglet_key_handler)
        cls._interactive_setup = True

    @staticmethod
    def _as_passed_or_empty_lambda(as_passed: Callable | None) -> Callable:
        return as_passed if callable(as_passed) else lambda key, modifier: None  # noqa: ARG005

    @staticmethod
    def _eval_keymod(
        key: int | Literal["num", "numrow", "numpad"],
        modifiers: int | str = "",
    ) -> str:
        """Evaluate keymod string.

        Evalutes internal keymod string that represents `key` and `modifiers`.
        """
        return str(key) if modifiers == "" else str(key) + " " + str(modifiers)

    @staticmethod
    def _keypart(keymod: str) -> str:
        """Return first part of the internal keymod string `keymod`.

        Examples
        --------
        >>> PhyscialInteractiveSprite._keypart(97) -> '97'
        >>> PhyscialInteractiveSprite._keypart(97 18) -> '97'
        """
        return keymod.split(" ")[0]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self._interactive_setup:
            self._setup_interactive()

        self._keymod_handlers = {}  # Populated by `setup_keymod_handlers`
        self.setup_keymod_handlers()

        # Set by `_set_keyonly_handlers` to replicate `_keymod_handlers`
        # although only including items that define keyboard events involving
        # a single keyboard key. Employed by `_key_hold_handlers`.
        self._keyonly_handlers: dict[int, dict]
        self._set_keyonly_handlers()

        # Set by `_set_handle_number_bools`
        self._handle_numbers_together: bool
        self._num: bool
        self._numpad: bool
        self._numrow: bool
        self._set_handle_number_bools()

        self._connected = False  # Set to True by `_connect_handlers`
        self._connect_handlers()

        self._frozen = False  # Set by `freeze` and `unfreeze`

    def _connect_handlers(self):
        """Push to stack event handlers defined as instance methods."""
        if not self._connected:
            self._window.push_handlers(self)
        self._connected = True

    def _disconnect_handlers(self):
        """Remove from stack event handlers defined as instance methods."""
        self._window.remove_handlers(self)
        self._connected = False

    def add_keymod_handler(
        self,
        key: int | Literal["num"],
        modifiers: int | None = "",
        on_press: Callable | None = None,
        on_release: Callable | None = None,
        while_pressed: Callable | None = None,
    ):
        """Add a keymod handler.

        Adds a handler for pressing and/or releasing and/or holding a
        sepcific keyboard key or combination of keys, including in
        conjunction with modifier keys.

        `on_press`, `on_release` and `while_pressed` should be passed a
        callable that accommodates 'key' and 'modifiers' as the first two
        parameters. Whenever the handlers are called these parameters will
        receive the key and modifier(s) values of the actual event (as the
        integers that pyglet uses to represent keyboard keys - see doc for
        `key` and `modifiers` parameters). These parameters can be passed
        as None, or not passed, if that particular event is not to be
        handled for the defined keyboard key or keys.

        Parameters
        ----------
        key
            Key or keys to be handled as integer that pyglet uses to
            represent the specific keyboard key. The pyglet.window.key
            module defines a set of intelligibly named constants, for
            example 'A', 'LEFT', 'F3', each of which is assigned a
            corresponding integer. For example, to specify the key 'A' pass
            `key=pyglet.window.key.A`  which results in the key parameter
            receiving the integer 97.

            To handle any numerical key:
                +key+ 'num'.
            To handle any numerical key of the number pad:
                +key+ 'numpad'.
            To handle any numerical key of the number row:
                +key+ 'numrow'.
        modifiers
            Modifier key or keys to be handled in combination with `key.
            Only pass if a modifier is to be specified. Pass as integer
            that pyglet uses to represent a specific modifier key or
            combination of modifier keys. NB the integer for a combination
            of modifier keys is the sum of the integers that represent each
            of the modifier keys being combined. For example:
                >>> pyglet.window.key.MOD_CTRL
                2
                >>> pyglet.window.key.MOD_SHIFT
                1
            So, to define modifiers as CTRL + SHIFT pass modifiers=3.
        on_press
            Callable to be executed when the defined keyboard key or keys
            is/are pressed.
        on_release
            Callable to be executed when the defined keyboard key or keys
            is/are released.
        while_pressed
            Callable to be executed every time the window refreshes whilst
            the defined keyboard key is held down. NB Can only handle
            holding down a single keyboard key. AssertionError raised if
            both `while_pressed` and `modifiers` passed or `key` passed as
            'num', 'numpad' or 'numrow' (see further below).

        Notes
        -----
        It is NOT possible to add a keymod handler with +key+ 'num' and
        another with +key+ as either 'numpad' or 'numrow' (which would
        otherwise create ambiguity as to which handler should be employed).

        References
        ----------
        pyglet.window.key documentation:
            https://pyglet.readthedocs.io/en/latest/modules/window_key.html
        """
        if while_pressed is not None and (
            modifiers or (isinstance(key, str) and key[:3] == "num")
        ):
            err_msg = (
                "while_pressed handler cannot accommodate modifiers or"
                " collective handling of numerical keys."
            )
            raise RuntimeError(err_msg)

        on_press = self._as_passed_or_empty_lambda(on_press)
        on_release = self._as_passed_or_empty_lambda(on_release)
        while_pressed = self._as_passed_or_empty_lambda(while_pressed)

        keymod = self._eval_keymod(key, modifiers)
        self._keymod_handlers[keymod] = {
            "on_press": on_press,
            "on_release": on_release,
            "while_pressed": while_pressed,
        }

    def setup_keymod_handlers(self):
        """Not implemented by this class.

        Method should be implemented by subclass in accordance with
        'Subclass Interface' section of this class' documentation.
        """
        return

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
        """Set boolean advices for handlers of numeric keyboard keys.

        Raises
        ------
        ValueError
            If trying to handle indpendently number keys and either number
            pad keys or number row keys.
        """
        self._handle_numbers_together = False
        self._numpad = False
        self._numrow = False
        self._num = False
        keyparts = [self._keypart(keymod) for keymod in self._keymod_handlers]
        num_keys = ["num", "numpad", "numrow"]
        num_keys_used = [nk for nk in num_keys if nk in keyparts]
        if num_keys_used:
            self._handle_numbers_together = True
            if "numpad" in num_keys_used:
                self._numpad = True
            if "numrow" in num_keys_used:
                self._numrow = True
            if "num" in num_keys_used:
                self._num = True
            if self._num and (self._numpad or self._numrow):
                err_msg = (
                    "Cannot have both 'num' and either 'numpad' or 'numrow'as keymods."
                )
                raise ValueError(err_msg)

    def _get_keymod(self, key: int, modifiers: int | str = "") -> str:
        """Get keymod for `key`, `modifiers` combination.

        Returns the internal keymod string that would map to any handlers
        set up to handle a keyboard event defined by `key` and `modifiers`.

        NB method makes no claim as to whether any handlers exist for the
        keyboard event defined by `key` and `modifiers`, but only that
        if such handlers were to exist then the returned internal keymod
        string would map to them.

        Parameters
        ----------
        key
            Integer used by pyglet to represent a specific keyboard key.
        modifiers
            Integer used by pyglet to represent a specific keyboard
            modifier key or combination of modifier keys.
        """
        if self._handle_numbers_together:
            ext = " " + str(modifiers) if modifiers else ""
            if self._num and key in self._NUM_KEYS:
                return "num" + ext
            if self._numpad and key in self._NUMPAD_KEYS:
                return "numpad" + ext
            if self._numrow and key in self._NUMROW_KEYS:
                return "numrow" + ext
        return self._eval_keymod(key, modifiers)

    def _keymod_handled(
        self,
        key: int,
        modifiers: int | str = "",
    ) -> str | Literal[False]:
        """Get keymod to handle a combination of `key` and `modifiers`.

        Returns internal keymod string that maps to handlers setup to
        handle the actual keyboard event defined by `key` and `modifiers`
        (be that event key press, key release or key held). Returns False
        if no such handlers exist.

        Parameters
        ----------
        key
            Integer used by pyglet to represent a specific keyboard key.
        modifiers
            Integer used by pyglet to represent a specific keyboard
            modifier key or combination of modifier keys.
        """
        keymod = self._get_keymod(key, modifiers)

        # handler exists for +key+ +modifiers+ combo
        if keymod in self._keymod_handlers:
            return keymod  # examples: '97 18', 'num 18'

        # Handler exists for +key+ which represents a numerical keyboard
        # key handled by a collective handler. +modifiers+ are ignored,
        # thereby ensuring handlers work as intended regardless of whether
        # numlock, capslock etc are on or off.
        if keymod[0:3] == "num":
            return self._keypart(keymod)  # 'num', 'numpad', or 'numrow'

        # Handler exists for +key+ (which does not represent a numerical
        # key handled collectively). +modifiers are again ignored.
        if str(key) in self._keymod_handlers:
            return str(key)  # example: '97'

        # No handler exists for defined keyboard event
        return False

    def _execute_any_key_handler(
        self,
        key: int,
        circumstance: str,
        modifiers: int | str = "",
    ) -> None | Literal[True]:
        """Execute any handler set up to handle a given circumstnace.

        Executes any handlers set up to hanled an actual keyboard event
        defined by +key+, +modifiers+ and +circumstance+.

        Parameters
        ----------
        key
            Integer used by pyglet to represent a specific keyboard key.
        modifiers
            Integer used by pyglet to represent a specific keyboard
            modifier key or combination of modifier keys.
        circumstance
            One of 'on_press', 'on_release' or 'while_pressed'.
        """
        keymod = self._keymod_handled(key, modifiers)
        if not keymod:
            return None
        self._keymod_handlers[keymod][circumstance](key, modifiers)
        return True  # Prevents event propaging through stack if handled.

    def on_key_press(self, symbol: int, modifiers: int):
        """Key press handler."""
        self._execute_any_key_handler(symbol, "on_press", modifiers)

    def on_key_release(self, symbol: int, modifiers: int):
        """Key release handler."""
        self._execute_any_key_handler(symbol, "on_release", modifiers)

    def _key_hold_handlers(self):
        """Execute any 'while_pressed' handler for any currently pressed key."""
        for key in self._keyonly_handlers:
            if self._pyglet_key_handler[key]:
                self._execute_any_key_handler(key, "while_pressed")

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
        """Decease sprite."""
        self._disconnect_handlers()
        super().die(*args, **kwargs)
