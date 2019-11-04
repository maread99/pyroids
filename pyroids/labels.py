#! /usr/bin/env python

from copy import copy
from typing import Optional, Tuple, Union, Iterable

import pyglet
from pyglet.sprite import Sprite
from pyglet.text import Label

from .lib.pyglet_lib.sprite_ext import load_image
from .lib.pyglet_lib.drawing import Rectangle

RED = (248, 81, 81, 255)
BLUE = (72, 190, 229, 255)
GREEN = (71, 245, 71, 255)
WHITE = (255, 255, 255, 255)

class ScreenLabels(object):
    """Base class to create a text screen comprising one or more labels all 
    of which will be included to ++batch++ and any passed ++group++.
    
    --_add_labels-- can be implemented on subclass to create one or more 
    labels using the following methods:
    --add_label-- to add a label
    --add_title-- to add a label formatted as the screen's main title
    
    --add_enter_for_inst_label-- to add a label towards the foot of the 
      screen advising user to press enter for instructions
    --add_escape_to_exit_label-- to add a label towards the foot of the 
      screen (and below and enter for inst label) advising user to press 
      escape to exit.

    Internals.
    By default the x-coordinate of each label is placed in the center of the 
    screen and the y-coordinate at --_y--'less' any +vert_spacing+ passed to 
    the --add_label--, with --_y-- upadated after each label is inserted to sit 
    at the bottom of the inseted label. NB this behaviour relies on 
    --add_label--'s setting the y_anchor of each added label to 'top'.
    
    To enter a label at the same height as the previous hold the --_y-- value 
    with _hold_y(move_on) before adding the first label to be displayed at 
    the same height. Can later release the --_y-- value with --_release_y--.

    --_display(label, bool)-- can be employed by subclasses to display, or not, 
    the passed +label+.
    """
    
    def __init__(self, window: pyglet.window.Window,
                 batch: pyglet.graphics.Batch,
                 group: Optional[pyglet.graphics.Group] = None):
        """Each label will be included to ++batch++ and ++group++"""
        self.win = window
        self.labels = []
        self.batch = batch
        self.group = group

        self._y = self.win.height
        self._x = self.win.width//2
        self._x_held = True
        self._y_held = False
        
        self._add_labels()

    def add_label(self, *args, vert_spacing=0, **kwargs) -> Label:
        kwargs['anchor_y'] = 'top'
        kwargs.setdefault('batch', self.batch)
        kwargs.setdefault('group', self.group)
        kwargs.setdefault('anchor_x', 'center')
        kwargs.setdefault('bold', False)
        kwargs.setdefault('font_size', 25)
        kwargs.setdefault('y', self._y - vert_spacing)
        kwargs.setdefault('x', self._x)
        lbl = Label(*args, **kwargs)
        self.labels.append(lbl)
        if not self._y_held:
            height = lbl.content_height if lbl.height is None else lbl.height
            self._y = lbl.y - height
        return lbl

    def add_title(self, *args, **kwargs):
        kwargs.setdefault('y', int(self.win.height*0.79))
        kwargs.setdefault('font_size', 100)
        kwargs.setdefault('bold', True)
        return self.add_label(*args, **kwargs)
    
    def add_enter_for_inst_label(self):
        return self.add_label('Enter for instructions', y=100, font_size=20)
        
    def add_escape_to_exit_label(self, alt_text: Optional[str] = None):
        text = alt_text if alt_text is not None else 'ESCAPE to exit'
        self._esc_lbl = self.add_label(text, y=55, font_size=15)
        return self._esc_lbl

    def _display(self, label: Label, show: bool = True):
        if show:
            label.batch = self.batch
        else:
            label.batch = None
            
    def _add_labels(self):
        """Implement on subclass to add any pre-defined labels"""
        pass

    def _hold_y(self, move_on):
        self._y_held = True
        self._y -= move_on

    def _release_y(self):
        self._y_held = False

class StartLabels(ScreenLabels):
    """Creates labels for an introduction screen.
    Title reads 'Asteroids' with subtitle underneath 'Press 1 or 2 to 
    start with 1 or 2 players'"""
    def _add_labels(self):
        self.add_title('PYROIDS')
        self.add_label('Press 1 or 2 to start with 1 or 2 players')
        self.add_enter_for_inst_label()
        self.add_escape_to_exit_label()
        
class NextLevelLabel(ScreenLabels):
    """Creates a single label that reads 'NEXT LEVEL' with around 70% 
    transparency
    """
    def _add_labels(self):
        self.add_title('NEXT ZONE', color=(255, 255, 255, 188))

class LevelLabel(ScreenLabels):
    """Creates a single label to display the level
    --update(new_level)-- to update the level label for a new level
    """
    def _add_labels(self):
        self.label = self.add_label(text="Zone  1", font_size=18, 
                                    y = self.win.height - 8, bold=False, 
                                    anchor_y='top')

    def update(self, new_level: Optional[int] = None):
        extra_space = ' ' if new_level < 10 else ''
        self.label.text = "Zone " + extra_space + str(new_level)

class EndLabels(ScreenLabels):
    """Creates labels for an Game Over screen.
    Title reads 'Game Over' with subtitle underneath 'Press 1 or 2 to start 
    again'. Provides for a further label indicating the winner.
    --display_winner_label(bool)-- to dispay the 'winner' label, or not, 
    at any particular time.
    --set_winner_label(text, color)-- to dynamically set the text and/or 
    color of the winner label.
    """
    def _add_labels(self):
        self._start_again_text = 'Press 1 or 2 to start again'
        
        self._title = self.add_title('placeholder', y = self.win.height - 200)
        self._sub1 = self.add_label('placeholder')
        self._sub2 = self.add_label('placeholder',
                                   vert_spacing=20)
        self.add_enter_for_inst_label()
        self.add_escape_to_exit_label()
        self._winner_lbl = self.add_label('placeholder', font_size=60,
                                          y=self.labels[0].y + 110, 
                                          bold=True)
            
    def display_winner_label(self, show: bool = True):
        super()._display(self._winner_lbl, show)
      
    def _set_winner_label(self, winner: Union['red', 'blue', bool, None]):
        """Will show a winner label unless +winner+ False.
        Text 'Draw!' if +winner+ is None, otherwise Red wins! or 'Blue wins!'.
        """
        if winner is False:
            text = ""
            color = (0, 0, 0, 255)
        elif winner is None:
            text = 'Draw!'
            color = GREEN
        else:
            text_start = 'BLUE' if winner == 'blue' else 'RED'
            text = text_start + ' wins!'
            color = BLUE if winner == 'blue' else RED
        self._winner_lbl.text = text
        self._winner_lbl.color = color

    def _set_title(self, completed: bool):
        self._title.text = 'WELL DONE!!' if completed else 'GAME OVER'
        
    def _set_sub1(self, completed: bool):
        self._sub1.text = 'ALL ASTEROIDS DESTROYED!' if completed\
            else self._start_again_text
        self._sub1.color = GREEN if completed else WHITE
        self._sub1.bold = True if completed else False

    def _set_sub2(self, completed: bool):
        self._sub2.text = self._start_again_text if completed else ''

    def set_labels(self, winner: Union['red', 'blue', bool, None],
                   completed=False):
        self._set_title(completed)
        self._set_sub1(completed)
        self._set_sub2(completed)
        self._set_winner_label(winner)

class InstructionLabels(ScreenLabels):
    """Creates labels for an instructions screen which includes 
    key controls.

    --set_labels(paused: bool = False)-- will set the labels so as to 
    be appropriate for a pause screen, if +paused+ True, or a main 
    menu screen otherwise
    """
    
    class BGGroup(pyglet.graphics.OrderedGroup):
        def __init__(self):
            super().__init__(0)

        def set_state(self):
            pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
            
    _bg_group = BGGroup()
    _fg_group = pyglet.graphics.OrderedGroup(1)

    def __init__(self, blue_controls: dict, red_controls: dict, 
                 *args, **kwargs):
        self._blue_controls = blue_controls
        self._red_controls = red_controls
        kwargs['group'] = self._fg_group
        super().__init__(*args, **kwargs)
        
        self._inst_lbl: Label
        self._instructions = (
            "Shoot as many asteroids as you can! The ship can only carry "
            "limited ammo although command will drop supplies in from time to"
            " time. Pick them up. And don't hang around in any zone for too "
            "long...the ship can only be exposed to so much radiation "
            "before it fries! Radiation's EVERYWHERE although levels are "
            "highest in the field around the edge of each zone. GOOD LUCK!"
            )
        
        self._opaque_bg = self._add_screen_rect(color=(0, 0, 0, 255))
        self._trans_bg = self._add_screen_rect(color=(40, 40, 40, 125))
        self._trans_bg.remove_from_batch()
        self._opaque = True
        
    def _add_screen_rect(self, color: Tuple[int, int, int, int]):
        return Rectangle(0, self.win.width, 0, self.win.height,
                         fill_color=color, 
                         batch=self.batch, group=self._bg_group)

    def _set_transparent_bg(self):
        if not self._opaque:
            return
        self._trans_bg.return_to_batch()
        self._opaque_bg.remove_from_batch()
        self._opaque = False
        
    def _set_opaque_bg(self):
        if self._opaque:
            return
        self._trans_bg.remove_from_batch()
        self._opaque_bg.return_to_batch()
        self._opaque = True

    def _field(self, keys: Iterable):
        text = ''
        for i, key in enumerate(keys):
            sep = '' if i is 0 else ', '
            key_text = pyglet.window.key.symbol_string(key).strip('_')
            text = sep.join([text, key_text])
        return text

    def _row(self, first_col: str, control_key: str):
        blue_keys = self._blue_controls[control_key]
        red_keys = self._red_controls[control_key]
        return (first_col, self._field(blue_keys), self._field(red_keys))
        
    def _add_labels(self):
        self._inst_lbl = self.add_label("placeholder", vert_spacing=30,
                                        font_size=16, multiline=True,
                                        width=int(self.win.width*0.8),
                                        align='center', 
                                        color=(200, 200, 200, 255)) #GREEN
        
        self.add_label("CONTROLS", font_size=20, vert_spacing=105)

        controls = [self._row('Thrust', 'THRUST_KEY'),
                    self._row('Rotate Left', 'ROTATE_LEFT_KEY'),
                    self._row('Rotate Right', 'ROTATE_RIGHT_KEY'),
                    self._row('Fire Bullet', 'FIRE_KEY'),
                    self._row('Fire high Velocity Bullet', 'FIRE_FAST_KEY'),
                    self._row('Super Laser Defence', 'SLD_KEY'),
                    self._row('Launch Firework', 'FIREWORK_KEYS'),
                    self._row('Lay Mine', 'MINE_KEYS'),
                    self._row('Raise Shield', 'SHIELD_KEY')]

        options = [('Pause/Resume', 'F12', ''),
                   ('Exit Game', 'F12, ESCAPE', '')]

        blue_width = 270
        x_from_center = (blue_width//2) + 50
                
        center_kwargs = {'font_size': 20, 
                         'multiline': True,
                         'align': 'center',
                         'anchor_x': 'center',
                         'width':blue_width}
        
        left_kwargs = copy(center_kwargs)
        left_kwargs.update({'x': self._x - x_from_center,
                            'align': 'right',
                            'anchor_x': 'right',
                            'width': 290})

        right_kwargs = copy(center_kwargs)
        right_kwargs.update({'x': self._x + x_from_center,
                             'anchor_x': 'left',
                             'width': 150})

        self.add_label( ''.join([control[1] + '\n' for control in controls]),
                       color=BLUE, vert_spacing=20, **center_kwargs)

        y = self.labels[-1].y

        self.add_label( ''.join([option[1] + '\n' for option in options]),
                       vert_spacing=10, **center_kwargs)
        
        self.add_label( ''.join([control[0] + '\n' for control in controls]),
                       y=y, **left_kwargs)

        self.add_label( ''.join([option[0] + '\n' for option in options]),
                       vert_spacing=10, **left_kwargs)
        
        self.add_label( ''.join([control[2] + '\n' for control in controls]),
                       y=y, color=RED, **right_kwargs)

        self._to_rtrn = self.add_label("placeholder", font_size=20, y=145)
        self.add_escape_to_exit_label(alt_text="placeholder")
        self._esc_lbl.y = 70

    def _set_for_pause(self):
        self._inst_lbl.text = ""
        self._to_rtrn.text = 'Press F12 to return'
        self._esc_lbl.text = 'Press ESCAPE to end game'
        self._set_transparent_bg()

    def _set_for_main_menu(self):
        self._inst_lbl.text = self._instructions
        self._to_rtrn.text = 'Press any key to return'
        self._esc_lbl.text = ''
        self._set_opaque_bg()

    def set_labels(self, paused: bool = False):
        if paused:
            self._set_for_pause()
        else:
            self._set_for_main_menu()

class StockLabel(pyglet.text.layout.TextLayout):
    """Layout comprising an inline ++image++, of an ammunition stock, 
    followed by text that can be initialised (initial_stock) and 
    updated to reflect stock levels. Red X appears over the image if stock 
    level is 0.
    
    Internals.
      Defines StockLabelElement within the class to provide for an 
    InlineElement that horizontally aligns the centre of the image with the 
    centre of the subseqeunt text. Does this by the StockLabel constructor 
    setting the layout's content_valign to 'center' (such that the text sits 
    in the vertical centre) and anchor_y to 'bottom'. The in line element is 
    then simply placed so that it's own vertical centre is situated at the 
    layout's vertical centre.
      The cross through the image (when stock level is 0) draw to the same 
    batch as self albeit with a group that's one higher (so that cross drawn 
    on top). By default the drawing data is calculated on the first occasion 
    that a cross is drawn, with that same data then used for furture 
    drawings. Rather than evaluate the data when require the cross (likely 
    to be in game) the client can call --positioned()-- to evalute the data 
    at any earlier occasion, albeit only after the stocklabel's y and x 
    coordinates have been set as required.

    --set-- provides for styling the whole --document-- and setting layout 
    attributes
    --positioned-- can be optionally executed by client after stocklabel has 
    been positioned. If called then (minimally) reduces overhead on first 
    occasion that the ammunition image is crossed out.
    --update(stock)-- updates text to reflect +stock+
    """
    
    class StockLabelElement(pyglet.text.document.InlineElement):
        """Extends InlineElemnent to provide for an image of an 
        ammunition stock to appear as an inline element that's the 
        first character of a StockLabel
        Doesn't define ascent or descent values (leaves as 0) simply 
        because the best way I've come up with to later manipulate the 
        resulting StockLabel as required"""
        
        def __init__(self, image, separation=2):
            image = copy(image)
            image.anchor_x = 0
            image.anchor_y = 0
            
            self.image = image
            self.height = image.height
            super().__init__(ascent=0, descent=0, 
                             advance = image.width + separation)

        def place(self, layout, x, y):
            """Places sprite of --image-- in the element box in such a way 
            that the center of the image will line up with the mid-line of 
            the text that follows it.
            +layout+ receives the StockLabel layout object to which the 
            element was inserted.
            +x+ passed as left edge of element.
            +y+ passed as baseline level (on which text of the first line sits)
            NB Found the x useful, y representing the baseline is of no use 
            when require the image to be centered through the text mid-line, 
            which in turn *can be determined via +layout.y+ and 
            +layout.content_height+.   *assuming layout is y anchored at the 
            bottom and content_valign is 'center', both as provided for by the 
            StockLabel constructor.
            """
            y = layout.y + (layout.content_height//2) - ( self.image.anchor_y + (self.height//2) )
            self._sprite = Sprite(self.image, x, y, batch=layout.batch,
                                  group=layout.top_group)
            self._sprite.draw()
        
        def remove(self, layout):
            self._sprite.delete()

    class CrossOutGroup(pyglet.graphics.OrderedGroup):
        def set_state(self):
            pyglet.gl.glLineWidth(3)

    class BackgroundGroup(pyglet.graphics.OrderedGroup):
        def __init__(self):
            super().__init__(0)

    def __init__(self, image: pyglet.image.Texture, 
                 group: Optional[pyglet.graphics.OrderedGroup] = None,
                 initial_stock: int = 0, 
                 style_attrs = None, **kwargs):
        """++image++ image that represents the ammunition stock and will be 
        placed at the start of the StockLabel.
        ++style_attrs++ sytle attributes to apply to whole document.
        ++kwargs++ passed on to inherited construtor.
        """
        assert group is None or isinstance(group, 
                                           pyglet.graphics.OrderedGroup)
        group = group if group is not None else self.BackgroundGroup()
        text = self._label_text(initial_stock)
        doc = pyglet.text.document.FormattedDocument(text)
        doc.set_style(0, len(doc.text), style_attrs)
        self.img_element = self.StockLabelElement(image)
        doc.insert_element(0, self.img_element)
        super().__init__(doc, **kwargs)
        self.top_group = group
        self.content_valign = 'center'
        self.anchor_y='bottom'
        
        self._cross_out_data: Optional[List] = None
        self._cross_out_vertex_list: pyglet.graphics.vertexdomain.VertexList
        self._crossed_out = False

    def set(self, style_attrs: Optional[dict] = None, **kwargs):
        """Sets --document-- to reflect any passed style_attrs 
        and self to reflect layout properties passed as ++**kwargs++, 
        for example 'x', 'y', 'anchor_x', 'batch' etc.
        Attribute error unfortunately necessary to catch non-fatal error 
        which seems to occur when passing the 'color' attribute. Could 
        well be a pyglet but.
        """
        if style_attrs is not None:
            end = len(self.document.text)
            try:
                self.document.set_style(0, end, style_attrs)
            except AttributeError:
                pass
        if not kwargs:
            return
        self.begin_update()
        for kwarg, val in kwargs.items():
            setattr(self, kwarg, val)
        self.end_update()
        
    def positioned(self):
        self._setup_cross_out_data()

    def _label_text(self, stock: int) -> str:
        text = 'x' + str(stock)
        return text

    def _cross_out_vertices(self):
        x1 = self.x
        x2 = self.x + self.img_element.image.width
        y1 = self.img_element._sprite.y
        y2 = y1 + self.img_element.height
        return ('v2i', (x1, y1, x2, y2, x1, y2, x2, y1))

    def _setup_cross_out_data(self):
        group = self.CrossOutGroup(self.top_group.order + 1)
        count = 4
        mode = pyglet.gl.GL_LINES
        vertices = self._cross_out_vertices()
        color = ('c4B', (255, 0, 0, 255) * 4)
        self._cross_out_data = [count, mode, group, vertices, color]

    @property
    def cross_out_data(self):
        if self._cross_out_data is None:
            self._setup_cross_out_data()
        return self._cross_out_data

    def _cross_out(self):
        self._cross_out_vertex_list = self.batch.add(*self.cross_out_data)
        self._crossed_out = True

    def _delete_cross_out(self):
        self._cross_out_vertex_list.delete()
        self._crossed_out = False

    def delete(self):
        if self._crossed_out:
            self._delete_cross_out()
        super().delete()

    def update(self, stock: int):
        """Updates stock label to reflect current +stock+"""
        end = len(self.document.text)
        self.document.delete_text(1, end)
        self.document.insert_text(1, self._label_text(stock))
        if stock is 0:
            self._cross_out()
        elif self._crossed_out:
            self._delete_cross_out()

class InfoRow(object):
    """Creates and/or positions objects along a row at the top of the 
    screen, with those objects collectively providing a player with 
    information on remaining lives, ammunition stock levels, 
    radiation level and score. All items added to ++batch++.

    Places objects from right-to-left if ++control_sys++.color is blue, 
    or from left-to-right if red.

    Public Methods:
    --remove_a_life-- to remove one life sprite, will be removed from the 
      end furthest from the screen edge
    --update_score_label--
    --delete-- removes all inserted objects from the batch

    Internals.
    Player's ammunition stocks provided by StockLabels that are an 
    attribute of a weapon of the ++control_sys++. This class does not 
    create the StockLabels but rather is responsible only for their 
    positioning and assigning to ++batch++.

    Similarly, the class is not repsonsible for creating the radiation 
    gauge but rather positions the gauge associated with the ++control_sys++ 
    and adds this to ++batch++. Additionally places a ---radiation_symbol--- 
    alongside the gauge.
    
    All objects are allocated a y value as defined in the consturctor as 
    --_info_row_base-- such that objects sit above this level.

    Each object's position and batch is set by --_set_object-- which in turn 
    relies on --_advance_x-- and --_get_object_x--. Collectively works by 
    positioning the objects to the row one by one, working from the screen 
    edge towards the centre and updating --_x-- to reflect the current 
    position. NB requires all images and labels are anchored to origin, i.e. 
    left bottom.
    NB the Score Label isn't positioned according to the above but rather 
    is positioned relative to the ++game++'s level label.
    """
    
    text_colors = {'blue': BLUE,
                   'red': RED}
    
    radiation_symbol = load_image('radiation_20.png', anchor='origin')

    def __init__(self, window: pyglet.window.Window, 
                 batch: pyglet.graphics.Batch, 
                 control_sys,
                 num_lives: int, 
                 level_label: Label):
        """++batch++ takes batch to which all info row objects will be added.
        ++control_sys++ takes an instance of .sprites.ControlSystem"""
        self._win = window
        self._info_row_base = self._win.height - 30
        self._batch = batch
        self._control_sys = control_sys
        self._color = self._control_sys.color
        self.text_color = self.text_colors[self._color]
        self._num_lives = num_lives
        self._lives = []
        self._level_label = level_label

        self._x = self._win.width if self._color == 'blue' else 0
        self._set_lives()
        self._set_stocks_labels()
        self._set_radiation_gauge()
        self._create_score_label()

    def _advance_x(self, pixels: int):
        """Moves _x by +pixels+ pixels in the direction that labels are being 
        sequentially placed
        """
        pixels *= -1 if self._color == 'blue' else 1
        self._x += pixels
        
    def _get_object_x(self, obj: Union[Sprite, StockLabel]):
        """Return 'x' coordinate for obj which will place object at the 
        required separation on from the last object placed ASSUMING that 
        +obj+ is anchored to bottom left and --_x-- currently positioned 
        at the required spacing on from the last object placed.
        """
        if self._color == 'blue':
            width = obj.content_width if isinstance(obj, StockLabel) \
                else obj.width
            return self._x - width
        else:
            return self._x

    def _set_object(self, obj: Union[Sprite, StockLabel],
                   x: Optional[int] = None, y: Optional[int] = None,
                   batch: Optional[pyglet.graphics.Batch] = None, 
                   sep: int = 0):
        """NB ASSUMES obj anchored to bottom left corner.
        Sets passed obj to any attributes passed or defaults otherwise
        """
        if sep is not 0:
            self._advance_x(sep)
        obj.batch = self._batch if batch is None else batch
        obj.y = self._info_row_base if y is None else y
        obj.x = self._get_object_x(obj) if x is None else x
        width = obj.content_width if isinstance(obj, StockLabel)\
            else obj.width
        self._advance_x(width)

    def _set_lives(self):
        """Creates sprites (using the image of the Ship class associated with 
        ++control_sys++) to represent player's lives. Postions to the top 
        corner of the screen.
        Internals. Appends each to --_lives-- in reverse order, such that 
        first element to pop (by --remove_a_life-- is always that furthest 
        from the edge of the window
        """
        for i in range(self._num_lives):
            img = copy(self._control_sys.ShipCls[self._color].img)
            img.anchor_x = 0
            img.anchor_y = 0
            life = Sprite(img)
            life.scale = 0.36
            self._lives.append(life)
            self._set_object(life, sep=3)
             
    def remove_a_life(self):
        self._lives.pop()
        
    def _set_stocks_labels(self):
        for weapon in self._control_sys.weapons:
            label = weapon.stock_label
            label.set(style_attrs={'color': self.text_color, 'bold': True})
            self._set_object(label, sep=10)
            label.positioned()
                        
    def _set_radiation_gauge(self):
        self._set_object(self._control_sys.radiation_monitor.gauge, sep=15)
        self._rad_symbol = Sprite(self.radiation_symbol)
        self._set_object(self._rad_symbol, sep=5)

    def _score_label_x_coordinate(self) -> int:
        """Returns x coordinate for score label based on 
        score label lying to one side of the games's level label.
        """
        direction = 1 if self._color == 'blue' else -1
        dist = (self._level_label.content_width//2) + 34
        x = self._level_label.x + (dist * direction)
        return x
        
    def _create_score_label(self):
        """Creates a score lable to the side of the game's level label.
        Internals - Does not consider --_x--"""
        self._score_label = Label('0', x=self._score_label_x_coordinate(), 
                                 y=self._win.height,font_size=30, bold=True, 
                                 batch=self._batch,
                                 anchor_x='center', anchor_y='top')
        self._score_label.set_style('color', self.text_color)
    
    def update_score_label(self, score: int):
        """Updates score label to reflect +score+"""
        self._score_label.text = str(score)

    def delete(self):
        for life in self._lives:
            life.delete()
        for weapon in self._control_sys.weapons:
            weapon.stock_label.delete()
        self._score_label.delete()
        self._control_sys.radiation_monitor.gauge.delete()
        self._rad_symbol.delete()