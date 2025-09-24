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

Attributes
----------
The following module attributes are assigned default values that can be
overriden by defining an attribute of the same name in a configuration
file (see pyroids.config.template.py for explanation of each attribute
and instructions on how to customise values):
COLLECTABLE_IN
COLLECTABLE_FOR
PICKUP_AMMO_STOCKS
SHIELD_DURATION
INITIAL_AMMO_STOCKS
HIGH_VELOCITY_BULLET_FACTOR

AmmoClasses
    List of Ammunition classes

Classes
-------
Explosion(OneShotAnimatedSprite)
    Explosion animation with sound.

Smoke(Explosion)
    Smoke Animation with explosion sound.

Ship(PhysicalSpriteInteractive)
    Blue controllable armed spaceship.
RedShip(Ship)
    Red controllable armed spaceship.

Asteroid(PhysicalSprite)
    Asteroid.

Ammunition()
    Base for ammunition clases.
Bullet(Ammunition, PhysicalSprite)
    Bullet sprite for Blue player, with sound.
BulletRed(Bullet)
    Bullet sprite for Red player, with sound.
BulletHighVeloicty(Bullet)
    High Velocity Bullet sprite, with sound.
BulletHighVeloictyRed(Bullet)
    High Velocity Bullet sprite, with sound.
Starburst(StaticSourceMixin)
    Explosion from which bullets fire out at regular angular intervals.
SuperLaserDefence(Ammunition, Starburst)
SuperLaserDefenceRed(SuperLaserDefence)
Firework(Bullet)
    Large Bullet explodes into Starburst
FireworkRed(Firework)
    Large Bullet explodes into Starburst.
Mine(Ammunition, PhysicalSprite)
    Mine explodes into Starburst after specified time.
MineRed(Mine)
    Mine explodes into Starburst after specified time.
Shield(Ammunition, PhysicalSprite)
    Invincible (almost) shield for Ship.
ShieldRed(Shield)
    Invincible (almost) shield for Ship.

Weapon()
    Base class for creating a weapon class that fires instances of a
    different Ammunition class for each player.
Cannon(Weapon)
    Fires bullets.
HighVelocityCannon(Weapon)
    Fires high velocity bullets.
FireworkLauncher(Weapon)
    Fires fireworks.
SLD_Launcher(Weapon)
    Fires super laser defence.
MineLayer(Weapon)
    Lays mines.
ShieldGenerator(Weapon)
    Raises Shields.

RadiationGauge(Sprite)
    Displays radiation level.
RadiationGaugeRed(RadiationGauge)
    Displays radiation level for red player.

RadiationMonitor(StaticSourceMixin)
    Manages radiation level.
RadiationMonitorRed(RadiationMonitor)
    Manages red player's radiation level.

ControlSystem()  Control system for a player.

PickUp(PhysicalSprite)  Ammunition pickup.
PickUpRed(PickUp)  Ammunition pickup for red player.
"""

from __future__ import annotations

import random
from collections import OrderedDict
from copy import copy
from math import floor
from typing import TYPE_CHECKING, ClassVar, Literal

import pyglet
from pyglet.sprite import Sprite

from . import PlayerColor
from .configuration import Config
from .labels import StockLabel
from .utils.pyglet_utils.audio_ext import (
    StaticSourceClassMixin,
    StaticSourceMixin,
    load_static_sound,
)
from .utils.pyglet_utils.sprite_ext import (
    InRect,
    OneShotAnimatedSprite,
    PhysicalSprite,
    PhysicalSpriteInteractive,
    anim,
    load_image,
    load_image_sequence,
    vector_anchor_to_rotated_point,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyglet.image import Animation, Texture
    from pyglet.media import StaticSource


class Ammunition(StaticSourceClassMixin):
    """Mixin.

    Attributes
    ----------
    img_pickup
        Ammo pick-up image.
    img_stock
        Ammo stocks image.
    snd_no_stock
        Out of ammunition audio.

    Methods
    -------
    play_no_stock
        Play out of ammunition audio.

    SUBCLASS INTERFACE
    Inheriting classes should define the Class Attributes.

    snd_no_stock should be assigned a StaticSource returned by helper
    function `load_static_sound()`. For example:
        snd_boom = load_static_sound('boom.wav')
    """

    img_pickup: Texture | Animation
    img_stock: Texture | Animation

    snd_no_stock: StaticSource

    @classmethod
    def play_no_stock(cls):
        """Play out of ammunition audio."""
        cls.cls_sound(cls.snd_no_stock, interupt=False)


class Bullet(Ammunition, PhysicalSprite):
    """`PhysicalSprite` with bullet image and firing bullet sound.

    Bullet killed by colliding with any of Asteroid, Ship, Shield,
    Mine collectable PickUp or game area boundary.
    """

    img = load_image("bullet.png", anchor="center")
    snd = load_static_sound("nn_bullet.wav")

    img_pickup = img
    img_stock = img

    snd_no_stock = load_static_sound("nn_no_stock_cannon.wav")

    def __init__(self, control_sys: ControlSystem, *args, **kwargs):
        """Instantiate Bullet.

        Parameters
        ----------
        control_sys
            ControlSystem instance responsible for weapon that fired
            bullet.
        """
        self.control_sys = control_sys
        kwargs.setdefault("at_boundary", "kill")
        super().__init__(
            *args,
            initial_rotation_speed=0,
            rotation_cruise_speed=0,
            **kwargs,
        )

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        if isinstance(other_obj, (Asteroid, Ship, Shield, Mine)) or (
            isinstance(other_obj, PickUp) and not other_obj.dropping
        ):
            self.kill()


class BulletRed(Bullet):
    """Bullet for Red ship."""

    snd = load_static_sound("mr_bullet.wav")

    snd_no_stock = load_static_sound("mr_no_stock_cannon.wav")


class BulletHighVelocity(Bullet):
    """High velocity bullet.

    Bullet with high velocity bullet image and sound for Blue ship.

    Notes
    -----
    Does not define bullet speed.
    """

    snd = load_static_sound("nn_hvbullet.wav")
    img = load_image("bullet_high_velocity.png", anchor="center")
    img_pickup = img
    img_stock = load_image("bullet_high_velocity.png", anchor="origin")

    snd_no_stock = load_static_sound("nn_no_stock_hvc.wav")


class BulletHighVelocityRed(Bullet):
    """High velocity bullet for Red Ship."""

    snd = load_static_sound("mr_hvbullet.wav")
    img = load_image("bullet_high_velocity_red.png", anchor="center")
    img_pickup = img
    img_stock = load_image("bullet_high_velocity_red.png", anchor="origin")

    snd_no_stock = load_static_sound("mr_no_stock_hvc.wav")


class Starburst(StaticSourceMixin):
    """Explosion from which bullets fire out at regular intervals.

    Fires multiple bullets at regular angular intervals from a point with
    accompanying explosion sound. Intended to be instantiated from
    Ammunition classes that require a Starburst effect.

    Attributes
    ----------
    live_starbursts
        List of all instantiated instances that have not subsequently
        deceased.

    Methods
    -------
    stop_all_sound
        Stop any sound being played by any live instance.
    resume_all_sound
        Resume any sound by any live instance that had been previously
        stopped.
    """

    snd = load_static_sound("starburst.wav")
    live_starbursts: ClassVar[list] = []

    @classmethod
    def stop_all_sound(cls):
        """Stop any sound being played by any live starburst."""
        for starburst in cls.live_starbursts:
            starburst.stop_sound()

    @classmethod
    def resume_all_sound(cls):
        """Resume any sound (that had been paused) for any live starburst."""
        for starburst in cls.live_starbursts:
            starburst.resume_sound()

    def __init__(  # noqa: PLR0913
        self,
        x: int,
        y: int,
        batch: pyglet.graphics.Batch,
        control_sys: ControlSystem,
        group: pyglet.graphics.Group = pyglet.graphics.null_group,
        num_bullets: int = 6,
        bullet_speed: int = 200,
        direction: int | Literal["random"] = "random",
        distance_from_epi: int = 0,
    ):
        """Instatiate object.

        Parameters
        ----------
        x
            x coordinate of starburst origin.
        y
            y coordinate of starburst origin.
        batch
            Batch to which bullets to be drawn.
        control_sys
            ControlSystem instance to which bullets to be attributable.
        group
            Rendering group to which bullets to be included.
        num_bullets
            Number of bullets to be simultanesouly fired.
        bullet_speed
            Speed of each bullet.
        direction
            From 0 through 360, or 'random'.

            0 will fire one bullet to the 'right' and others at regular
            angular intervals. Any other value will effectively add
            'direction' to what would have been each bullet's direction if
            `direction` were to have been 0 (positive clockwise).

            'random' (default) will add a random value to what would
            otherwise have been each bullet's direction if `direction` = 0.
        distance_from_epi
            Start bullet's life at this distance from origin.
        """
        self.x = x
        self.y = y
        self.control_sys = control_sys
        self.num_bullets = num_bullets
        self.batch = batch
        self.group = group
        self.bullet_speed = bullet_speed
        self.direction = (
            direction
            if direction != "random"
            else random.randint(0, 360 // self.num_bullets)  # noqa: S311
        )
        self.distance_from_epi = distance_from_epi

        self.live_starbursts.append(self)

        self._starburst()
        super().__init__()

        # Decease starburst when sound ends
        pyglet.clock.schedule_once(self.die, self.snd.duration)

    def _bullet_directions(self) -> Iterator[int]:
        for direction in range(0, 360, (360 // self.num_bullets)):
            yield direction + self.direction

    def _bullet_birth_position(self, direction: int) -> tuple[int, int]:
        if not self.distance_from_epi:
            return (self.x, self.y)

        x, y = vector_anchor_to_rotated_point(self.distance_from_epi, 0, direction)
        x += self.x
        y += self.y
        return (x, y)

    def _starburst(self):
        for direction in self._bullet_directions():
            x, y = self._bullet_birth_position(direction)
            Bullet(
                self.control_sys,
                x=x,
                y=y,
                batch=self.batch,
                group=self.group,
                sound=False,
                initial_rotation=direction,
                initial_speed=self.bullet_speed,
            )

    def die(self, _: float | None = None):
        """Decease object.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.live_starbursts.remove(self)


class SuperLaserDefence(Ammunition, Starburst):
    """Ammunitionises Starburst for SLD_Launcher for Blue player."""

    img_stock = load_image("sld_stock.png", anchor="origin")
    img_pickup = load_image("sld_stock.png", anchor="center")
    snd = load_static_sound("nn_superlaserdefence.wav")

    snd_no_stock = load_static_sound("nn_no_stock_sld.wav")


class SuperLaserDefenceRed(SuperLaserDefence):
    """SLD for red ship."""

    snd = load_static_sound("mr_superdefence.wav")

    snd_no_stock = load_static_sound("mr_no_stock_sld.wav")


class Firework(Bullet):
    """Large `Bullet` that explodes into a starburst.

    Firework explodes on the earlier of colliding, reaching boundary or
    travelling a specified distance.
    """

    img = load_image("firework.png", anchor="center")
    snd = load_static_sound("nn_firework.wav")
    img_pickup = img
    img_stock = img

    snd_no_stock = load_static_sound("nn_no_stock_fireworks.wav")

    def __init__(
        self,
        explosion_distance: int,
        num_starburst_bullets: int = 12,
        starburst_bullet_speed: int = 200,
        **kwargs,
    ):
        """Instantiate object.

        Parameters
        ----------
        explosion_distance
            Distance, in pixels, before firework will explode.
        num_starburst_bullets
            Number of bullets Starburst to comprise of.
        starburst_bullet_speed
            Starburst bullet speed.
        **kwargs
            All as kwargs for `Bullet`.
        """
        self.explosion_distance = explosion_distance
        self.num_starburst_bullets = num_starburst_bullets
        self._starburst_bullet_speed = starburst_bullet_speed
        super().__init__(**kwargs)
        self._set_fuse()

    def _starburst(self):
        # Directs starburst bullets so as to minimise possibility that
        # they will hit a stationary ship from which Firework launched
        Starburst(
            x=self.x,
            y=self.y,
            batch=self.batch,
            group=self.group,
            control_sys=self.control_sys,
            num_bullets=self.num_starburst_bullets,
            bullet_speed=self._starburst_bullet_speed,
            direction=self.control_sys.ship.rotation + 15,
        )

    def _fused(self, _: float | None = None):
        """Implement fuse burn out.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.kill()

    def kill(self):
        """Instatiate starburst and kill this object."""
        self._starburst()
        super().kill()

    def _set_fuse(self):
        fuse = self.explosion_distance / self.speed
        self.schedule_once(self._fused, fuse)

    def die(self):
        """Decease object."""
        # Prevent sound being cut short when fuse short.
        super().die(die_loudly=True)


class FireworkRed(Firework):
    """`Firework` for red ship."""

    snd = load_static_sound("mr_firework.wav")

    snd_no_stock = load_static_sound("mr_no_stock_fireworks.wav")


class Mine(Ammunition, PhysicalSprite):
    """Mine explodes into Starburst after specified time.

    Mine shows a countdown to 0 whilst playing 'tick tock' sound. Mine
    can be visible throughout life or only for the last `visible_secs`.
    Explodes into `Starburst` on earlier of reaching 0 or being shot by a
    Bullet.

    Methods
    -------
    setup_mines
        Define class default settings.
    """

    img = anim("mine.png", 1, 9, frame_duration=1)
    img_pickup = img.frames[-1].image
    img_stock = img_pickup
    snd = load_static_sound("nn_minelaid.wav")

    snd_no_stock = load_static_sound("nn_no_stock_mines.wav")

    _visible_secs: int | None
    _mines_setup = False

    @classmethod
    def setup_mines(cls, visible_secs: int | None = None):
        """Override class defaults.

        Parameters
        ----------
        visible_secs
            Number of seconds during which mine to be visible before
            exploding. None if mine to be visible throughout life.
        """
        cls._visible_secs = visible_secs
        cls._mines_setup = True

    @classmethod
    def _anim(cls, fuse_length: int) -> Animation:
        """Animation object for mine with specified fuse length.

        'Coundown Mine' animation object shows a number on top of mine
        which counts down from `fuse_length` to 0 over `fuse_length`
        seconds. No sound.
        """
        anim = copy(cls.img)
        anim.frames = anim.frames[9 - fuse_length :]
        return anim

    def __init__(  # noqa: PLR0913
        self,
        x: int,
        y: int,
        batch: pyglet.graphics.Batch,
        fuse_length: int,
        control_sys: ControlSystem,
        visible_secs: int | None = None,
        num_starburst_bullets: int = 12,
        bullet_speed: int = 200,
        **kwargs,
    ):
        """Instatiate object.

        Parameters
        ----------
        x
            x coordinate.
        y
            y coordinate.
        batch
            Batch to which mine will be drawn.
        fuse_length
            Mine life span in seconds. Maximum 9.
        visible_secs
            Number of seconds during which mine will be visible at end of a
            natural life. If not passed then will take any class default
            defined by `setup_mines` or otherwise will be visible
            throughout life.
        num_starburst_bullets
            Number of `Bullet` that `Starburst` is to comprise of.
        bullet_speed
            Speed of `Starburst` bullets.
        control_sys
            `ControlSystem` instance to which starburst's bullets to be
            attributed.
        **kwargs
            All as kwargs for `Ammunition`.
        """
        if not self._mines_setup:
            self.setup_mines()
        if visible_secs is not None:
            self._visible_secs = visible_secs

        if fuse_length > 9:  # noqa: PLR2004
            err_msg = f"fuse_length {fuse_length} too long, maximum is 9."
            raise ValueError(err_msg)
        self.fuse_length = max(1, fuse_length)
        self.control_sys = control_sys
        self.num_starburst_bullets = num_starburst_bullets
        self.bullet_speed = bullet_speed

        super().__init__(img=self._anim(fuse_length), x=x, y=y, batch=batch, **kwargs)

        if self._visible_secs and fuse_length > self._visible_secs:
            self._hide_anim_for(fuse_length - self._visible_secs)

    def on_animation_end(self):
        """Event handler."""
        self.kill()

    def _hide_anim_for(self, invisible_secs: float):
        self.visible = False
        self.schedule_once(self._show_anim, invisible_secs)

    def _show_anim(self, _: float | None = None):
        """Show animation.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.visible = True

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        if isinstance(other_obj, Bullet):
            self.kill()

    def refresh(self, _: float):
        """Refresh object.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        # As object stationary, overrides to avoid superfluous execution

    def kill(self):
        """Instantiate `Starburst` and kill mine object.

        Instantiates Starburst with origin on the mine's position
        """
        Starburst(
            x=self.x,
            y=self.y,
            batch=self.batch,
            group=self.group,
            control_sys=self.control_sys,
            num_bullets=self.num_starburst_bullets,
            bullet_speed=self.bullet_speed,
        )
        super().kill()


class MineRed(Mine):
    """Mine for red ship."""

    snd = load_static_sound("mr_minelaid.wav")

    snd_no_stock = load_static_sound("mr_no_stock_mines.wav")


class Shield(Ammunition, PhysicalSprite):
    """Ship Shield.

    Shield invincible save for against other shields. Plays sound on
    raising shield. Flashes during final 25% of natural life, with
    flash frequency doubling over last 12.5%.

    Attributes
    ----------
    ship
    """

    img = load_image("shield_blue.png", anchor="center")
    snd = load_static_sound("nn_shieldsup.wav")
    img_stock = load_image("shield_blue_20.png", anchor="origin")
    img_pickup = load_image("shield_pickup_inset_blue.png", anchor="center")

    snd_no_stock = load_static_sound("nn_no_stock_shields.wav")

    def __init__(self, ship: Ship, duration: int = 10, **kwargs):
        """Instantiate object.

        Parameters
        ----------
        ship
            Ship to be shielded.
        duration
            Shield duration.
        """
        self._ship = ship
        super().__init__(**kwargs)
        self.powerdown_duration = duration / 4
        self.powerdown_phase2_duration = duration / 8
        solid_shield_duration = duration - self.powerdown_duration
        self.schedule_once(self._powerdown_initial, solid_shield_duration)

    @property
    def ship(self):
        """Ship being shielded."""
        return self._ship

    def refresh(self, _: float | None = None):
        """Refresh shield position to coincide with ship being shielded.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.update(x=self.ship.x, y=self.ship.y)

    def shield_down(self, _: float | None = None):
        """Decease shield.

        Parameters
        ----------
        -
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.die()

    def _powerdown_final(self, _: float | None = None):
        """End powerdown shield phase.

        Parameters
        ----------
        -
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.flash_start(frequency=4)
        self.schedule_once(self.shield_down, self.powerdown_phase2_duration)

    def _powerdown_initial(self, _: float | None = None):
        """Start powerdown shield phase.

        Parameters
        ----------
        -
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.flash_start(frequency=2)
        duration = self.powerdown_duration - self.powerdown_phase2_duration
        self.schedule_once(self._powerdown_final, duration)

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        if isinstance(other_obj, Shield):
            self.ship.kill()  # self killed indirectly via ship being killed.


class ShieldRed(Shield):
    """Shield for red ship."""

    img = load_image("shield_red.png", anchor="center")
    snd = load_static_sound("mr_shieldsup.wav")
    img_stock = load_image("shield_red_20.png", anchor="origin")
    img_pickup = load_image("shield_pickup_inset_red.png", anchor="center")

    snd_no_stock = load_static_sound("mr_no_stock_shields.wav")


AmmoClasses = [
    Bullet,
    BulletRed,
    BulletHighVelocity,
    BulletHighVelocityRed,
    Mine,
    MineRed,
    Firework,
    FireworkRed,
    SuperLaserDefence,
    SuperLaserDefenceRed,
    Shield,
    ShieldRed,
]


class Weapon:
    """Weapon Base class.

    Weapon instances are designed to be attached to a `ControlSystem`
    instance.

    For a specific `AmmoClass`:
        Handles fire requests, providing for following circumstances:
            No ammunition.
            Shield raised and weapon cannot fire through shield.
            Firing an instance of ammunition.
        Manages ammunition stock levels.
        Creates and maintains a `StockLabel` offering graphical
            representation of current stock level.

    Attributes
    ----------
    stock
        Current ammunition rounds in stock.
    max_stock
        Maximum number of ammunition rounds weapon can stock.
    stock_label
        `StockLabel` representing weapon's ammunition stock.

    Methods
    -------
    set_stock
    set_max_stock
    add_to_stock
    subtract_from_stock
    fire

    Notes
    -----
    SUBCLASS INTERFACE
    Subclass should define the following class attributes if require values
    other than the defaults:
    ammo_cls
        Dictionary with keys as possible player colours and values as the
        weapon's ammunition Type for corresponding player. Implemented on
        this base class to provide for `Bullet` and `BulletRed` ammunition
        classes for 'blue' and 'red' players respectively. Implement on
        subclass if weapon fires alternative ammunition class.
    fire_when_sheild_up
        Boolean defines if weapon can be fired when the `control_sys` has
         shield raised. Implemented on base class as 'False'. Implement on
        subclass as True if weapon can be fired when shield raised.

    Subclass should implement the following methods if corresponding
    functionality required.
    _ammo_kwargs
        Implement on subclass to return a dictionary of kwargs to be passed
        to the ammunition class to fire a single instance of ammunition.
        Should accommodate incorporating any received **kwargs.
    _shield_up
        Handler to be called if weapon cannot be fired when shield raised
        and receive request to fire weapon when shield raised.
    die
        Subclass should implement to perform any end-of-life tidy-up
        operations, for example cancelling any scheduled calls. Called by
        `control_sys` as part of end-of-life process.

    NOTE: there are various methods on the `ControlSystem` class that aid
        getting kwargs for ammunition classes.
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: Bullet,
        PlayerColor.RED: BulletRed,
    }

    fire_when_shield_up = False

    def __init__(
        self,
        control_sys: ControlSystem,
        initial_stock: int = 0,
        max_stock: int = 9,
    ):
        """Instantiate object.

        Parameters
        ----------
        control_sys
            `ControlSystem` instance which controls the weapon and in
            reverse which weapon can call on for guidance.
        initial_stock
            Initial number of ammunition rounds.
        max_stock
            Maximum number of ammunition rounds that weapon can stock.
        """
        self.control_sys = control_sys
        self._AmmoCls = self.ammo_cls[control_sys.color]
        self._max_stock = max_stock
        self._stock = min(initial_stock, max_stock)
        self._stock_label = StockLabel(
            image=self._AmmoCls.img_stock,
            initial_stock=self._stock,
            style_attrs={"color": (255, 255, 255, 255)},
        )

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
        num = min(num, self.max_stock)
        self._stock = num
        self._stock_label.update(self._stock)

    def set_stock(self, num: int):
        """Set stock level.

        Parameters
        ----------
        num
            New stock level.
        """
        self._update_stock(num)

    def set_max_stock(self):
        """Set stock level to maximum."""
        self.set_stock(self.max_stock)

    def _change_stock(self, num: int):
        """Change stock level by `num`.

        Parameters
        ----------
        num
            Amount to change stock by, positive to increase stock, negative
            to reduce stock.
        """
        num = self.stock + num
        return self._update_stock(num)

    def add_to_stock(self, num: int):
        """Add to stock.

        Parameters
        ----------
        num
            Number of ammunition rounds to add to stock.
        """
        self._change_stock(num)

    def subtract_from_stock(self, num: int):
        """Subtract from stock.

        Parameters
        ----------
        num
            Number of ammunition rounds to subtract from stock (as positive
            integer).
        """
        self._change_stock(-num)

    def _shield_up(self):
        """Not implemented.

        Notes
        -----
        Implement on subclass to handle requests to fire whilst shield up.
        """

    def _no_stock(self):
        self._AmmoCls.play_no_stock()

    def _ammo_kwargs(self, **kwargs) -> dict:
        """Kwargs to instantiate single instance of associated ammo class.

        Notes
        -----
        Implement on subclass.
        """
        return kwargs

    def _fire(self, **kwargs):
        """Fire one instance of ammunition."""
        kwargs = self._ammo_kwargs(**kwargs)
        return self._AmmoCls(**kwargs)

    def fire(self, **kwargs) -> Ammunition | Literal[False]:
        """Fire one instance of ammunition or handle if unable to fire.

        Returns
        -------
        Ammunition | False
            Ammunition object fired or False if nothing fired.
        """
        if not self.fire_when_shield_up and self.control_sys.shield_up:
            self._shield_up()
            return False
        if not self._stock:
            self._no_stock()
            return False
        self.subtract_from_stock(1)
        return self._fire(**kwargs)

    def die(self):
        """Decease weapon.

        Notes
        -----
        Implement on subclass as required to perform any end-of-life
        operations.
        """


class Cannon(Weapon):
    """Cannon that fires standard bullets.

    Cannon automatically reloads. Cannot be fired through shield.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    reload_rate
        Seconds to reload one round of ammunition.
    **kwargs
        Passed to `Weapon` constructor.

    Methods
    -------
    set_reload_rate
        Set time to reload a round of ammunition.
    full_reload
        Reload to maximum stock level.
    """

    def __init__(self, *args, reload_rate: float = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_reload_rate(reload_rate)

    def set_reload_rate(self, reload_rate: float):
        """Set reload rate.

        Parameters
        ----------
        reload_rate
            Seconds to reload one round of ammunition.
        """
        pyglet.clock.unschedule(self._auto_reload)
        pyglet.clock.schedule_interval(self._auto_reload, reload_rate)

    def full_reload(self):
        """Reload to maximum stock level."""
        self.set_max_stock()

    def _ammo_kwargs(self):
        # Relies on control system to evaluate bullet kwargs
        return self.control_sys.bullet_kwargs()

    def _auto_reload(self, _: float | None = None):
        self.add_to_stock(1)

    def die(self):
        """Implement end-of-life."""
        pyglet.clock.unschedule(self._auto_reload)
        super().die()


class HighVelocityCannon(Weapon):
    """Cannon that fires High Velocity Bullets.

    Cannot be fired through shield.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    bullet_speed_factor
        High Velocity Bullet speed as multiple of standard bullet speed.
    **kwargs
        Passed to `Weapon` constructor.
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: BulletHighVelocity,
        PlayerColor.RED: BulletHighVelocityRed,
    }

    def __init__(self, *args, bullet_speed_factor: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self._factor = bullet_speed_factor

    def _ammo_kwargs(self):
        # Relies on control system to evaluate bullet kwargs
        u = self.control_sys.bullet_initial_speed(factor=self._factor)
        return self.control_sys.bullet_kwargs(initial_speed=u)


class FireworkLauncher(Weapon):
    """Fire fireworks.

    Cannot be fired through shield.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    dflt_explosion_distance
        Default for distance, in pixels, a firework will travel before
        exploding naturally (can be overriden for any particular firework
        by passing `explosion_distance` to `fire`).
    dflt_num_bullets
         Default for number of bullets that the starburst will comprise of
         when a firework explodes (can be overriden for any particular
         firework by passing `num_bullets` to `fire`). If not passed then
         default takes the default number of starburst bullets defined on
         the `control_sys`.
    **kwargs
        Passed to `Weapon` constructor.

    Attributes
    ----------
    margin
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: Firework,
        PlayerColor.RED: FireworkRed,
    }

    def __init__(
        self,
        *args,
        dflt_explosion_distance: int = 200,
        dflt_num_bullets: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._dflt_exp_dist = dflt_explosion_distance
        self._dflt_num_bullets = (
            dflt_num_bullets
            if dflt_num_bullets is not None
            else self.control_sys._dflt_num_starburst_bullets  # noqa: SLF001
        )

    @property
    def margin(self):
        """Minimum distance from centre of ship that firework can appear.

        Minimum distance, in pixels, from centre of associated ship that a
        `Firework` can appear without immediately colliding with ship.
        """
        return (self.control_sys.ship.width + Firework.img.width) // 2 + 1

    def _ammo_kwargs(self, **kwargs) -> dict:
        u = self.control_sys.bullet_initial_speed(factor=2)
        kwargs = self.control_sys.bullet_kwargs(
            initial_speed=u,
            margin=self.margin,
            **kwargs,
        )
        kwargs.setdefault("explosion_distance", self._dflt_exp_dist)
        kwargs.setdefault("num_starburst_bullets", self._dflt_num_bullets)
        kwargs.setdefault(
            "starburst_bullet_speed",
            self.control_sys.bullet_discharge_speed,
        )
        return kwargs

    def fire(self, **kwargs):
        """Fire one instance of ammunition or handle if unable to fire.

        Parameters
        ----------
        **kwargs
            Passed to `fire` method of base class. Can include:
            `explosion_distance`
                Distance, in pixels, the firework will travel before
                exploding naturally.
            `num_bullets`
                Number of bullets that the starburst will comprise of when
                the firework explodes.
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)


class SLD_Launcher(Weapon):  # noqa: N801
    """Super Laser Defence Launcher.

    Fires starbursts centered on the ship with the bullets first appearing
    at the ship's periphery. Has effect of bullets being fired from ship in
    'all directions'.

    Cannot be fired through shield.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    dflt_num_bullets
         Default for number of bullets that the super laser defence
         starburst will comprise of (can be overriden for any particular
         firing by passing `num_bullets` to `fire`). If not passed then
         default takes the default number of starburst bullets defined on
         the `control_sys`.
    **kwargs
        Passed to `Weapon` constructor.
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: SuperLaserDefence,
        PlayerColor.RED: SuperLaserDefenceRed,
    }

    def __init__(self, *args, dflt_num_bullets: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._dflt_num_bullets = (
            dflt_num_bullets
            if dflt_num_bullets is not None
            else self.control_sys._dflt_num_starburst_bullets  # noqa: SLF001
        )

    def _ammo_kwargs(self, **kwargs):
        kwargs = self.control_sys.ammo_base_kwargs()
        kwargs.setdefault("control_sys", self.control_sys)
        kwargs.setdefault("num_bullets", self._dflt_num_bullets)
        kwargs["distance_from_epi"] = self.control_sys.bullet_margin
        kwargs.setdefault("bullet_speed", self.control_sys.bullet_discharge_speed)
        return kwargs

    def fire(self, **kwargs):
        """Fire one instance of ammunition or handle if unable to fire.

        Parameters
        ----------
        **kwargs
            Passed to `fire` method of base class. Can include:
                `num_bullets`
                    Number of bullets that the super laser defence
                    starburst will comprise of. If not passed then will
                    take default value (see constructor documentation).
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)


class MineLayer(Weapon):
    """Lays mines.

    Mines can be laid whilst shield raised.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    dflt_fuse_length
        Default fuse length in seconds before mine will explode naturally
        (can be overriden for any particular mine by passing `fuse_length`
        to `fire`).
    dflt_num_bullets
        Default for number of bullets that the starburst will comprise of
        when a mine explodes (can be overriden for any particular mine by
        passing `num_starburst_bullets` to `fire`). If not passed then
        default takes the default number of starburst bullets defined on
        the `control_sys`.
    **kwargs
        Passed to `Weapon` constructor.
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: Mine,
        PlayerColor.RED: MineRed,
    }

    fire_when_shield_up = True

    def __init__(
        self,
        *args,
        dflt_fuse_length: int = 5,
        dflt_num_bullets: int | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._dflt_fuse_length = dflt_fuse_length
        self._dflt_num_bullets = (
            dflt_num_bullets
            if dflt_num_bullets is not None
            else self.control_sys._dflt_num_starburst_bullets  # noqa: SLF001
        )

    def _ammo_kwargs(self, **kwargs) -> dict:
        kwargs |= self.control_sys.ammo_base_kwargs()
        kwargs.setdefault("control_sys", self.control_sys)
        kwargs.setdefault("fuse_length", self._dflt_fuse_length)
        kwargs.setdefault("num_starburst_bullets", self._dflt_num_bullets)
        kwargs.setdefault("bullet_speed", self.control_sys.bullet_discharge_speed)
        return kwargs

    def fire(self, **kwargs):
        """Fire one instance of ammunition or handle if unable to fire.

        Parameters
        ----------
        **kwargs
            Passed to `fire` method of base class. Can include:
                `fuse_length`
                    Seconds after which mine will explode naturally.
                `num_starburst_bullets`
                    Number of bullets that will be fired out by exploding
                    mine.
        """
        # Executes inherited method. Only defined to provide documentation.
        super().fire(**kwargs)


class ShieldGenerator(Weapon):
    """Raises shield when fired.

    Only one shield can be generated at a time.

    Parameters
    ----------
    *args
        Passed to `Weapon` constructor.
    dflt_duration
        Default shield duration in seconds.
    **kwargs
        Passed to `Weapon` constructor.

    Attributes
    ----------
    shield_raised

    Methods
    -------
    lower_shield
        Lower any raised shield.
    """

    ammo_cls: ClassVar[dict[PlayerColor:Ammunition]] = {
        PlayerColor.BLUE: Shield,
        PlayerColor.RED: ShieldRed,
    }

    # fire_when_shield_up defined as False on base class. Ensures only one
    # shield can be raised at any time.

    def __init__(self, *args, dflt_duration: int = 5, **kwargs):
        self._dflt_duration = dflt_duration
        self._current_shield = None
        super().__init__(*args, **kwargs)

    def _ammo_kwargs(self, **kwargs) -> dict:
        kwargs |= self.control_sys.ammo_base_kwargs()
        kwargs.setdefault("ship", self.control_sys.ship)
        kwargs.setdefault("duration", self._dflt_duration)
        return kwargs

    def fire(self, **kwargs):
        """Fire one instance of ammunition or handle if unable to fire.

        Parameters
        ----------
        **kwargs
            Passed to `fire` method of base class. Can include:
                `duration`
                    Shield duaration in seconds. If not passed then
                    duration will take default value (see constructor
                    documentation).
        """
        funcs = [self._shield_lowered]
        if "on_die" in kwargs:
            funcs.append(copy(kwargs["on_die"]))
        kwargs["on_die"] = lambda: [f() for f in funcs]
        shield = super().fire(**kwargs)
        if shield:
            self._current_shield = shield

    @property
    def shield_raised(self) -> bool:
        """Query if shield raised."""
        return self._current_shield is not None

    def _shield_lowered(self):
        self._current_shield = None

    def lower_shield(self):
        """Lower any raised shield."""
        if self._current_shield is not None:
            self._current_shield.shield_down()


class RadiationGauge(Sprite):
    """8 stage colour radiation guage.

    Attributes
    ----------
    reading
    max_reading

    Methods
    -------
    reset
    """

    img_seq = load_image_sequence("rad_gauge_r2l_?.png", 8)

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
        """Current gauge reading (from 0 through 7)."""
        return self._reading

    @reading.setter
    def reading(self, value: int):
        """Set reading.

        Parameters
        ----------
        value
            From 0 (zero raditation detected) to 7 (maximum radiation
            level).
        """
        self._reading = min(floor(value), self._max_reading)
        self.image = self.img_seq[self._reading]

    def reset(self):
        """Reset gauge to 0."""
        self.reading = 0


class RadiationGaugeRed(RadiationGauge):
    """RadiationGauge for red ship."""

    img_seq = load_image_sequence("rad_gauge_l2r_?.png", 8)


class RadiationMonitor(StaticSourceMixin):
    """Monitors, displays and mangages a Ship's radiation exposure.

    Offers:
        Continuous evaluation of a ship's radiation exposure.
        Continuous updating of a RadiationGauge to display exposure.
        Radiation field definition as rectangular area of clean space
            with all other space considered dirty. Ship exposed to
            background radiation when in clean space, and high level
            radiation when in dirty space.
        Ship exposure limits can be set at any time.
        Audio warning when exposure reaches 70% of limit.
        On reaching exposure limit plays 'last words' then requests
            control system kill ship. Gives ship a last minute repreive
            if monitor reset before last words have finished being spoken.

    Class creates the radiation guage object which is assigned to attribute
    `gauge` Client is responsible for positioning gauge and attaching
    it to any batch and/or group. This can be done via the gauge's 'x',
    'y', 'batch' and 'group' attributes (gauge based on Sprite).

    Parameters
    ----------
    control_sys
        ControlSystem instance responsible for monitor.
    cleaner_space
        InRect representing clean space. All other space considered dirty.
        If not passed or None then all space assumed dirty. Can be
        subsequently set via `reset()`.
    nat_exp_limit
        Limit of continuous natural background radiation exposure, in
        seconds.
    high_exp_limit
        Limit of continuous high level radiation exposure, in seconds.

    Attributes
    ----------
    gauge
        RadiationGauge (Sprite).
    exposure
    """

    warning = load_static_sound("nn_radiation_warning.wav")
    last_words = load_static_sound("nn_too_much_radiation.wav")

    def __init__(
        self,
        control_sys: ControlSystem,
        cleaner_space: InRect | None = None,
        nat_exp_limit: int = 68,
        high_exp_limit: int = 20,
    ):
        super().__init__(sound=False)
        self.control_sys = control_sys
        self.gauge = self._get_gauge()

        self._exposure_level = 0
        self._exposure_limit = self.gauge.max_reading
        self._frequency = 0.5  # monitor update frequency

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

        Parameters
        ----------
        limit
            Limit of continuous background radiation exposure in seconds.
        """
        steps = limit / self._frequency
        self._nat_exposure_increment = self._exposure_limit / steps

    def set_high_exposure_limit(self, limit: int):
        """Set limit of high level radiation explosure.

        Parameters
        ----------
        limit
            Limit of continuous high level radiation exposure in seconds.
        """
        steps = limit / self._frequency
        self._high_exposure_increment = self._exposure_limit / steps

    def _warn(self):
        self.sound(self.warning)

    def _play_last_words(self):
        self.sound(self.last_words)

    def __kill_ship(self, _: float | None = None):
        self.control_sys.ship.kill()

    def _kill_ship(self):
        self._play_last_words()
        self._stop_monitoring()
        pyglet.clock.schedule_once(self.__kill_ship, self.last_words.duration)

    def _in_high_rad_zone(self) -> bool:
        """Query if ship in dirty space."""
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

        Parameters
        ----------
        value
            New exposure level. Will be adjusted to bounds of 0 through
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

    def _update(self, _: float | None = None):
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

    def _start_monitoring(self):
        pyglet.clock.schedule_interval(self._update, self._frequency)

    def halt(self):
        """Stop monitoring."""
        self._stop_monitoring()
        self.stop_sound()
        pyglet.clock.unschedule(self.__kill_ship)

    def reset(self, cleaner_space: InRect | None = None):
        """Stop existing processes and reset monitor.

        Parameters
        ----------
        cleaner_space
            InRect representing clean space. All other space considered
            dirty. If not passed or None then all space assumed dirty.
        """
        self.halt()
        self.exposure = 0
        self.gauge.reset()
        if cleaner_space is not None:
            self._cleaner_space = cleaner_space
        self._start_monitoring()


class RadiationMonitorRed(RadiationMonitor):
    """RadiationMonitor for red ship."""

    warning = load_static_sound("mr_radiation_warning.wav")
    last_words = load_static_sound("mr_too_much_radiation.wav")

    def _get_gauge(self):
        return RadiationGaugeRed()


class Explosion(OneShotAnimatedSprite):
    """One off animated explosion with sound."""

    img = anim("explosion.png", 1, 20, 0.1)
    snd = load_static_sound("nn_explosion.wav")


class Smoke(Explosion):
    """One off animated smoke cloud, with explosion sound."""

    img = anim("smoke.png", 1, 10, 0.2)


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

    Parameters
    ----------
    control_sys
        `ControlSystem` instance to control ship.
    cruise_speed
        Cruise speed in pixels/second.
    **kwargs
        Passed to `PhysicalSpriteInteractive` constructor.

    Methods
    -------
    set_controls
        Set ship controls (to alternative from default). Note that ship
        controls can also be set via configuration file.
    """

    img = load_image("ship_blue.png", anchor="center")
    img_flame = load_image("flame.png", anchor="center")
    img_flame.anchor_x -= 2
    snd_thrust = load_static_sound("thrusters.wav")

    controls: ClassVar[dict[str, int]] = {
        "THRUST_KEY": [pyglet.window.key.I],
        "ROTATE_LEFT_KEY": [pyglet.window.key.J],
        "ROTATE_RIGHT_KEY": [pyglet.window.key.L],
        "SHIELD_KEY": [pyglet.window.key.K],
        "FIRE_KEY": [pyglet.window.key.ENTER],
        "FIRE_FAST_KEY": [pyglet.window.key.BACKSPACE],
        "SLD_KEY": [pyglet.window.key.RCTRL],
        "FIREWORK_KEYS": OrderedDict(
            {
                pyglet.window.key._7: 200,  # noqa: SLF001
                pyglet.window.key._8: 500,  # noqa: SLF001
                pyglet.window.key._9: 900,  # noqa: SLF001
            },
        ),
        "MINE_KEYS": OrderedDict(
            {
                pyglet.window.key.M: 1,
                pyglet.window.key.COMMA: 3,
                pyglet.window.key.PERIOD: 6,
            },
        ),
    }

    @classmethod
    def set_controls(cls, controls: dict | None = None):
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

        Parameters
        ----------
        controls
            Dictionary with same keys as for the default above. Values
            define the keyboard key or keys that will result in the
            corresponding control being executed. A keyboard key is defined
            as the integer used by pyglet to represent that specific
            keyboard key and which can be defined as a corresponding,
            intelligibly named, constant of the pyglet.window.key module:
            https://pyglet.readthedocs.io/en/latest/modules/window_key.html
            Values take a List of these pyglet constants or an
            `OrderedDict` with keys as these pyglet constants.
            FIREWORK_KEYS and MINE_KEYS both take `OrderedDict` that
            provide for supplying an additional parameter for each keyboard
            key:
                Values of FIREWORK_KEYS `OrderedDict` represent the
                    distance, in pixels, that the firework will travel
                    before exploding.
                Values of MINE_KEYS `OrderedDict` represent the time, in
                    seconds, before the mine will explode.
        """
        if controls is None:
            return
        cls.controls.update(controls)

    def __init__(
        self,
        control_sys: ControlSystem,
        cruise_speed: int = 200,
        **kwargs,
    ):
        self.handlers = self._handlers()
        super().__init__(cruise_speed=cruise_speed, sound=False, **kwargs)
        self.control_sys = control_sys
        self.flame = Sprite(self.img_flame, batch=self.batch, group=self.group)
        self.flame.visible = False

    @property
    def _pick_up_cls(self):
        return PickUp

    def _handlers(self) -> dict:
        return {
            "THRUST_KEY": {
                "on_press": self._thrust_key_onpress_handler,
                "on_release": self._thrust_key_onrelease_handler,
                "while_pressed": self._thrust_key_pressed_handler,
            },
            "ROTATE_LEFT_KEY": {
                "on_press": self._rotate_left_key_onpress_handler,
                "on_release": self._rotate_key_onrelease_handler,
            },
            "ROTATE_RIGHT_KEY": {
                "on_press": self._rotate_right_key_onpress_handler,
                "on_release": self._rotate_key_onrelease_handler,
            },
            "SHIELD_KEY": {"on_press": self._shield_key_onpress_handler},
            "FIRE_KEY": {"on_press": self._fire_key_onpress_handler},
            "FIRE_FAST_KEY": {"on_press": self._fire_fast_key_onpress_handler},
            "SLD_KEY": {"on_press": self._sld_key_onpress_handler},
            "FIREWORK_KEYS": {"on_press": self._firework_key_onpress_handler},
            "MINE_KEYS": {"on_press": self._mine_key_onpress_handler},
        }

    def setup_keymod_handlers(self):
        """Set up keymod handlers.

        Notes
        -----
        Implements inherited method.
        """
        for key, keyboard_keys in self.controls.items():
            for keyboard_key in keyboard_keys:
                self.add_keymod_handler(key=keyboard_key, **self.handlers[key])

    def _thrust_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self._sound_thrust()
        self.flame.visible = True
        self.cruise_speed()

    def _thrust_key_onrelease_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.flame.visible = False
        self.speed_zero()
        self.stop_sound()

    def _thrust_key_pressed_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.flame.x = self.x
        self.flame.y = self.y
        self.flame.rotation = self.rotation

    def _rotate_right_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.cruise_rotation()

    def _rotate_key_onrelease_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.rotation_zero()

    def _rotate_left_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.cruise_rotation(clockwise=False)

    def _fire_fast_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.control_sys.fire(HighVelocityCannon)

    def _fire_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.control_sys.fire(Cannon)

    def _sld_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.control_sys.fire(SLD_Launcher)

    def _shield_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        self.control_sys.fire(ShieldGenerator)

    def _firework_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        dist = self.controls["FIREWORK_KEYS"][key]
        self.control_sys.fire(FireworkLauncher, explosion_distance=dist)

    def _mine_key_onpress_handler(self, key, modifier):  # noqa: ANN001 ARG002
        fuse_length = self.controls["MINE_KEYS"][key]
        self.control_sys.fire(MineLayer, fuse_length=fuse_length)

    def _sound_thrust(self):
        self.sound(self.snd_thrust, loop=True)

    def _explode(self):
        """Play 'explosion' animation.

        Plays explosion animtion at ship's position and scaled to ship size.
        """
        Explosion(x=self.x, y=self.y, scale_to=self, batch=self.batch, group=self.group)

    def stop(self):
        """Stop ship's movement and any sound."""
        super().stop()
        self.stop_sound()
        self.flame.visible = False

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        # take no action if 'collided with' ship's own shield
        if isinstance(other_obj, Shield) and other_obj.ship == self:
            return
        if isinstance(other_obj, (Asteroid, Bullet, Ship, Shield)):
            self.kill()
        elif type(other_obj) is self._pick_up_cls:
            self.control_sys.process_pickup(other_obj)

    def kill(self):
        """Implement ship destroyed."""
        self._explode()
        super().kill()

    def die(self):
        """Implement end-of-life."""
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

    img = load_image("ship_red.png", anchor="center")
    img_flame = load_image("flame.png", anchor="center")
    img_flame.anchor_x -= 2

    controls: ClassVar[dict[str, int]] = {
        "THRUST_KEY": [pyglet.window.key.W],
        "ROTATE_LEFT_KEY": [pyglet.window.key.A],
        "ROTATE_RIGHT_KEY": [pyglet.window.key.D],
        "SHIELD_KEY": [pyglet.window.key.S],
        "FIRE_KEY": [pyglet.window.key.TAB],
        "FIRE_FAST_KEY": [pyglet.window.key.ESCAPE],
        "SLD_KEY": [pyglet.window.key.LCTRL],
        "FIREWORK_KEYS": OrderedDict(
            {
                pyglet.window.key._1: 200,  # noqa: SLF001
                pyglet.window.key._2: 500,  # noqa: SLF001
                pyglet.window.key._3: 900,  # noqa: SLF001
            },
        ),
        "MINE_KEYS": OrderedDict(
            {
                pyglet.window.key.Z: 1,
                pyglet.window.key.X: 3,
                pyglet.window.key.C: 6,
            },
        ),
    }

    @property
    def _pick_up_cls(self):
        return PickUpRed


class Asteroid(PhysicalSprite):
    """Asteroid.

    Extends `PhysicalSprite` to define an Asteroid with spawning
    functionality such that asteroid spawn's `num_per_spawn` asteroids
    when object killed. Asteroid will spawn `spawn_limit` times and each
    spawned asteroid will be half the size of the asteroid that spawned it.
    Resolves collision with Bullets and Ships by considering asteroid
    to have been killed - plays smoke animation in the asteroid's last
    position, together with playing explosion auido.

    End-of-life handled via `kill` if killed in-game or .die if deceasing
    object out-of-game

    Parameters
    ----------
    spawn_level
        How many times the origin Asteroid has now spawned.
    spawn_limit
        How many times the origin Asteroid should spawn.
    num_per_spawn
        How many asteroids this asteroid should break up into when killed.
    at_boundary
        Behavior when asteroid reaches window boundary. Either 'bounce' or
        'wrap'. Deafaults to 'bounce'.
    **kwargs
        Passed to `PhysicalSprite` constructor.
    """

    img = load_image("pyroid.png", anchor="center")

    def __init__(
        self,
        spawn_level: int = 0,
        spawn_limit: int = 5,
        num_per_spawn: int = 3,
        at_boundary: Literal["bounce", "wrap"] = "bounce",
        **kwargs,
    ):
        super().__init__(at_boundary=at_boundary, sound=False, **kwargs)
        self._spawn_level = spawn_level
        self._spawn_limit = spawn_limit
        self._num_per_spawn = num_per_spawn

    def _spawn(self):
        """Spawn new asteroids if spawn level below spawn limit."""
        if self._spawn_level < self._spawn_limit:
            for _ in range(self._num_per_spawn):
                ast = Asteroid(
                    x=self.x,
                    y=self.y,
                    spawn_level=self._spawn_level + 1,
                    spawn_limit=self._spawn_limit,
                    num_per_spawn=self._num_per_spawn,
                    initial_speed=self.speed,
                    initial_rotation=random.randint(0, 359),  # noqa: S311
                    at_boundary=self._at_boundary,
                    batch=self.batch,
                    group=self.group,
                )
                scale_factor = 0.5 ** (self._spawn_level + 1)
                ast.scale = scale_factor

    def _explode(self):
        """Play 'smoke' animation in asteroid's current position."""
        Smoke(x=self.x, y=self.y, batch=self.batch, group=self.group, scale_to=self)

    def kill(self):
        """Implement end-of-life due to in-game collision."""
        self._spawn()
        self._explode()
        super().kill()

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        if isinstance(other_obj, (Bullet, Ship, Shield)):
            self.kill()


# GLOBALS
COLLECTABLE_IN = 2
COLLECTABLE_FOR = 10

PICKUP_AMMO_STOCKS = {
    HighVelocityCannon: (5, 9),
    FireworkLauncher: (3, 7),
    MineLayer: (3, 7),
    ShieldGenerator: (3, 5),
    SLD_Launcher: (3, 7),
}

settings = ["COLLECTABLE_IN", "COLLECTABLE_FOR", "PICKUP_AMMO_STOCKS"]
Config.import_config(vars(), settings)


class PickUp(PhysicalSprite):
    """Ammunition pickup for friendly ship (blue).

    Pickup offers the friendly ship a resupply of ammunition of a specific,
    albeit random, ammunition class. Pickup contains a random number of
    rounds within the minimum and maximum limits defined for each
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

    Attributes
    ----------
    color
        Pickup color (corresponding to color of ship / control
        system that can collect the pickup)
    stocks
        Dictionary defining possible weapons that a pickup can resupply
        and quantities of ammunition rounds that a pickup could contain.
        Keys take Weapon classes, one key for each weapon that a pickup
        could resupply. Values take a 2-tuple of integers representing the
        minimum and maximum rounds of ammunition that could be in a pickup
        for the corresponding weapon.
    collectable_in
        Seconds before a pickup can be collected.
    collectable_for
        Seconds that a pickup can be collected for before naturally
        deceasing.
    dropping
    """

    img = load_image("pickup_blue.png", anchor="center")  # Background
    snd = load_static_sound("supply_drop_blue.wav")
    snd_pickup = load_static_sound("nn_resupply.wav")

    color = PlayerColor.BLUE
    stocks = PICKUP_AMMO_STOCKS
    collectable_in = COLLECTABLE_IN
    collectable_for = COLLECTABLE_FOR
    final_secs = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position_randomly()
        self.Weapon = random.choice(list(self.stocks.keys()))  # noqa: S311
        self.number_rounds = random.randint(*self.stocks[self.Weapon])  # noqa: S311

        ammo_img = self.Weapon.ammo_cls[self.color].img_pickup
        # Place ammo sprite over the pickup background.
        self.ammo_sprite = Sprite(
            ammo_img,
            self.x,
            self.y,
            batch=self.batch,
            group=self.group,
        )

        self._killer_control_sys: ControlSystem

        self.flash_start(frequency=4)
        self._collectable = False
        self.schedule_once(self._now_collectable, self.collectable_in)

    @property
    def dropping(self):
        """Query if pickup is dropping (not yet collectable)."""
        return not self._collectable

    def _now_collectable(self, _: float | None = None):
        self.flash_stop()
        self._collectable = True
        self.schedule_once(self._dying, self.collectable_for - self.final_secs)

    def _dying(self, _: float | None = None):
        self.flash_start(frequency=8)
        self.schedule_once(self.die, self.final_secs)

    @property
    def _pick_up_ship_cls(self):
        return Ship

    def _play_pickup(self):
        self.sound(self.snd_pickup)

    def _starburst(self):
        Starburst(
            x=self.x,
            y=self.y,
            batch=self.batch,
            group=self.group,
            control_sys=self._killer_control_sys,
            num_bullets=self.number_rounds,
            bullet_speed=275,
        )

    def _explode(self):
        """Play explosion animation of pickup size in pickup position."""
        Explosion(x=self.x, y=self.y, scale_to=self, batch=self.batch, group=self.group)

    def kill(self):
        """Implement end-of-life due to being hit."""
        self._explode()
        if self.Weapon is not ShieldGenerator:
            self._starburst()
        super().kill()

    def die(self, _: float | None = None):
        """Decease pickup.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """
        self.ammo_sprite.delete()
        super().die(die_loudly=True)

    @property
    def _NotFriendlyShieldCls(self) -> type:  # noqa: N802
        return ShieldRed

    def collided_with(self, other_obj: Sprite):
        """Handle collision with another sprite."""
        if self.dropping:
            return
        if isinstance(other_obj, Bullet):
            self._killer_control_sys = other_obj.control_sys
            self.kill()
        elif type(other_obj) is self._NotFriendlyShieldCls:
            self._killer_control_sys = other_obj.ship.control_sys
            self.kill()
        elif type(other_obj) is self._pick_up_ship_cls:
            self._play_pickup()
            self.die()

    def refresh(self, _: float | None = None):
        """Remain stationary on refresh.

        Parameters
        ----------
        _
            Unused argument provides for accepting dt as seconds since
            function last called via scheduled event.
        """


class PickUpRed(PickUp):
    """Ammunition pickup for Red ship."""

    img = load_image("pickup_red.png", anchor="center")
    snd = load_static_sound("supply_drop_red.wav")
    snd_pickup = load_static_sound("mr_resupply.wav")
    color = PlayerColor.RED

    @property
    def _pick_up_ship_cls(self):
        return ShipRed

    @property
    def _NotFriendlyShieldCls(self) -> type:  # noqa: N802
        return Shield


# GLOBAL default values
SHIELD_DURATION = 8
HIGH_VELOCITY_BULLET_FACTOR = 5

INITIAL_AMMO_STOCKS = {
    Cannon: 9,
    HighVelocityCannon: 7,
    FireworkLauncher: 3,
    SLD_Launcher: 3,
    MineLayer: 3,
    ShieldGenerator: 2,
}

settings = ["SHIELD_DURATION", "INITIAL_AMMO_STOCKS", "HIGH_VELOCITY_BULLET_FACTOR"]
Config.import_config(vars(), settings)


class ControlSystem:
    """Control system for a player.

    Provides:
        Ship creation
        Weapons creation and management
        Shield Status
        Ammunition pickup management
        Radiation monitor creation and management

    Only one Ship can be associated with the control system at any time.
    Creation of a new ship results in managed systems being reset
    (radiation monitor, weapons' ammuntion stocks).

    Weapons available to control system:
        Cannon
        HighVelocityCannon
        FireworkLauncher
        SLD_Launcher
        MineLayer
        ShieldGenerator

    Class ATTRIUBTES
    ShipCls
        Associated Ship class.
    shield_duration
        Shield Duration
    hvb_factor
        High Velocity Bullet speed as multiple of standard bullet speed.
    initial_stock
        Dictionary representing initial ammuntion stocks.Each item
        represents initial ammunition stock for a specific weapon. Key
        takes a Weapon class. Value takes integer representing that
        weapon's initial stock of ammuntion.
    radiation_monitor
        Associated RadiationMonitor.
    weapons
    shield_up
    bullet_margin
    bullet_discharge_speed

    Methods
    -------
    new_ship
    fire
    process_pickup
    set_cannon_reload_rate
    cannon_full_reload

    bullet_initial_speed
    ammo_base_kwargs
    bullet_kwargs
    """

    ShipCls: ClassVar[dict[PlayerColor, Ship]] = {
        PlayerColor.BLUE: Ship,
        PlayerColor.RED: ShipRed,
    }

    _RadiationMonitorCls: ClassVar[dict[PlayerColor, RadiationMonitor]] = {
        PlayerColor.BLUE: RadiationMonitor,
        PlayerColor.RED: RadiationMonitorRed,
    }

    shield_duration = SHIELD_DURATION
    hvb_factor = HIGH_VELOCITY_BULLET_FACTOR
    initial_stock = INITIAL_AMMO_STOCKS

    def __init__(
        self,
        color: PlayerColor = PlayerColor.BLUE,
        bullet_discharge_speed: int = 200,
        dflt_num_starburst_bullets: int = 12,
    ):
        """Instantiate control system.

        Parameters
        ----------
        color
            Color of player who will use the control system.
        bullet_discharge_speed
            Default bullet speed. Can be subsequently set via property
            `bullet_discharge_speed`.
        dflt_num_starburst_bullets
            Default number of bullets that a starburst comprises of.
        """
        self.color = color
        self.ship: Ship  # set by --new_ship--
        self.radiation_monitor = self._RadiationMonitorCls[color](self)

        self._dflt_num_starburst_bullets = dflt_num_starburst_bullets
        self._bullet_discharge_speed = bullet_discharge_speed

        # --add_weapons()-- sets values to instance of corresponding Weapon
        self._weapons = {
            Cannon: None,
            HighVelocityCannon: None,
            FireworkLauncher: None,
            SLD_Launcher: None,
            MineLayer: None,
            ShieldGenerator: None,
        }

        self.add_weapons()

    def _set_initial_stocks(self):
        for Weapon, weapon in self._weapons.items():  # noqa: N806
            weapon.set_stock(self.initial_stock[Weapon])

    def _ship_killed(self):
        self.radiation_monitor.halt()
        self._weapons[ShieldGenerator].lower_shield()

    def new_ship(self, **kwargs) -> Ship:
        """Create new ship for player using control system."""
        funcs = [self._ship_killed]
        if "on_kill" in kwargs:
            funcs.append(copy(kwargs["on_kill"]))
        kwargs["on_kill"] = lambda: [f() for f in funcs]
        self.ship = self.ShipCls[self.color](control_sys=self, **kwargs)
        self._set_initial_stocks()
        self.radiation_monitor.reset()
        return self.ship

    @property
    def weapons(self) -> list[Weapon]:
        """List of controlled weapons."""
        return self._weapons.values()

    @property
    def bullet_margin(self):
        """Margin required between ship and bullet being fired.

        Minimum distance, in pixels, from center of associated ship to
        a point where a bullet can be instantiated without immediately
        colliding with ship.
        """
        return (self.ship.image.width + Bullet.img.width) // 2 + 2

    @property
    def shield_up(self) -> bool:
        """Query if shield is raised."""
        return self._weapons[ShieldGenerator].shield_raised

    @property
    def bullet_discharge_speed(self):
        """Component of Bullet speed from propulsion.

        Note that actual bullet speed will be this value plus the bullet's
        'own' speed.
        """
        return self._bullet_discharge_speed

    @bullet_discharge_speed.setter
    def bullet_discharge_speed(self, value: int):
        """Bullet discharge speed.

        Parameters
        ----------
        value
            New bullet discharge speed in pixels/second.
        """
        self._bullet_discharge_speed = max(value, self.ship._speed_cruise)  # noqa: SLF001

    def set_cannon_reload_rate(self, reload_rate: float):
        """Set cannon reload rate.

        Parameters
        ----------
        reload_rate
            Seconds to reload one round of ammunition.
        """
        self._weapons[Cannon].set_reload_rate(reload_rate)

    def cannon_full_reload(self):
        """Fully reload cannon."""
        self._weapons[Cannon].full_reload()

    def _add_weapon(self, weapon_cls: type, **kwargs):
        self._weapons[weapon_cls] = weapon_cls(self, **kwargs)

    def _add_cannon(self, **kwargs):
        self._add_weapon(Cannon, **kwargs)

    def _add_hv_cannon(self, **kwargs):
        kwargs.setdefault("bullet_speed_factor", self.hvb_factor)
        self._add_weapon(HighVelocityCannon, **kwargs)

    def _add_sld_launcher(self, **kwargs):
        self._add_weapon(SLD_Launcher, **kwargs)

    def _add_firework_launcher(self, **kwargs):
        self._add_weapon(FireworkLauncher, **kwargs)

    def _add_minelayer(self, **kwargs):
        self._add_weapon(MineLayer, **kwargs)

    def _add_shieldgenerator(self, **kwargs):
        kwargs.setdefault("dflt_duration", self.shield_duration)
        self._add_weapon(ShieldGenerator, **kwargs)

    def add_weapons(self):
        """Add all weapons to control system."""
        self._add_cannon()
        self._add_hv_cannon()
        self._add_sld_launcher()
        self._add_firework_launcher()
        self._add_minelayer()
        self._add_shieldgenerator()

    def fire(self, weapon: type[Weapon], **kwargs):
        """Attempt to fire one round of ammunition from specific weapon.

        Parameters
        ----------
        weapon
            Weapon class to fire.
        """
        self._weapons[weapon].fire(**kwargs)

    def process_pickup(self, pickup: PickUp):
        """Add ammunition in a `pickup` to corresponding weapon.

        Parameters
        ----------
        pickup
            Pickup of same color as control system.
        """
        self._weapons[pickup.Weapon].add_to_stock(pickup.number_rounds)

    def bullet_initial_speed(self, factor: int = 1) -> int:
        """Evaluate bullet speed if fired now.

        Parameters
        ----------
        factor
            Factor by which to multiply bullet discharge speed.
        """
        return self.ship.speed + (self.bullet_discharge_speed * factor)

    def ammo_base_kwargs(self) -> dict:
        """Return dictionary of options for an Ammunition class.

        Return can be passed as kwargs to ammunition class to set following
        options to same values as for associated ship:
            `x`
            `y`
            `batch`
            `group`
        """
        ship = self.ship
        return {"x": ship.x, "y": ship.y, "batch": ship.batch, "group": ship.group}

    def _bullet_base_kwargs(self, margin: int | None = None) -> dict:
        """Return dictionary of base options for Bullet class.

        Return can be passed as kwargs to a Bullet class constructor to
        set following options:
            `x`
            `y`
            `batch`
            `group`
            `control_sys`

        Parameters
        ----------
        margin
            Distance from centre of ship to point where bullet to first
            appear. Should be sufficient to ensure that bullet does not
            immediately collide with ship. If not passed then will use
            default margin.
        """
        margin = margin if margin is not None else self.bullet_margin
        x_, y_ = vector_anchor_to_rotated_point(margin, 0, self.ship.rotation)
        kwargs = self.ammo_base_kwargs()
        kwargs["control_sys"] = self
        kwargs["x"] += x_
        kwargs["y"] += y_
        return kwargs

    def bullet_kwargs(self, margin: int | None = None, **kwargs):
        """Options for Bullet class to fire bullet from nose of ship.

        Returned dictionary can be passed as kwags to Bullet class
        constructor.

        Parameters
        ----------
        margin
            Distance from centre of ship to point where bullet to first
            appear. Should be sufficient to ensure that bullet does not
            immediately collide with ship. If not passed then will use default
            margin.
        **kwargs
            Any option taken by Bullet class. Will be added to returned
            dictionary and override any option otherwise defined by method.
        """
        kwargs |= self._bullet_base_kwargs(margin=margin)
        kwargs.setdefault("initial_speed", self.bullet_initial_speed())
        kwargs.setdefault("initial_rotation", self.ship.rotation)
        return kwargs

    def die(self):
        """Implement end-of-life for control system."""
        self.radiation_monitor.halt()
        for weapon in self.weapons:
            weapon.die()
