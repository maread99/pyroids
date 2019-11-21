#! /usr/bin/env python

"""Classes that create and maintain text to be displayed in the game window.

CLASSES

WindowLabels()  Base class to create a window display comprising labels
StartLabels(WindowLabels)  Introduction window.
NextLevelLabel(WindowLabels)  Next Level label.
LevelLabel(WindowLabels)  Current Level label.
EndLabels(WindowLabels)  Game over / Game completed window.
InstructionLabels(WindowLabels)  Instructions including key controls.

StockLabel(TextLayout)  image/text layout describing ammunition stock level.

InfoRow()  Row of player information including lives, score, ammunition stocks 
    and radiation gauge.
"""

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

class WindowLabels(object):
    """Base class to create a window display comprising one or more vertically 
    arranged labels.
    
    By default, labels are centered horiztonally and spaced vertically. The 
    first added label is positioned towards the top of the screen with each 
    subsequent label positioned under the one added immediately before.

    INSTANCE ATTRIBUTES
    --win--  Window in which labels are to be displayed (++window++)
    --batch--  Default label batch (++batch++)
    --group--  Default label group (++group++)
    --labels--  List of added labels.

    METHODS
    --add_label()--  Add a label.
    
    Convenience Methods to Add Labels:
    --add_title()--  Add a label formatted and positioned as the main title.
    --add_enter_for_inst_label()--  Add label 'Enter for instructions'
    --add_escape_to_exit_label()--  Add label 'ESCAPE to exit'

    Label management:
    --display()--  Display or hide a specific label.
    
    SUBCLASS INTERFACE
    Subclass should implement --add_lables()-- to create the required labels 
    via successive calls to --add_label()-- or a convenience method that 
    extends --add_label()--.

    The following methods can be used to customise behaviour for the vertical 
    vertical position of levels:
    --advance_y()--  Advance the current y position.
    --hold_y()--  Hold the current y position.
    --release_y()--  Release the current y position.
    """
    
    def __init__(self, window: pyglet.window.Window,
                 batch: pyglet.graphics.Batch,
                 group: Optional[pyglet.graphics.Group] = None):
        """
        ++window++ Window in which label to be displayed.
        ++batch++ Default batch to which labels to be included.
        ++group++ Default group to which labels to be included.
        """
        self.win = window
        self.labels = []
        self.batch = batch
        self.group = group

        self._y = self.win.height  # Current position of y
        self._x = self.win.width//2  # Current position of x
        #self._x_held = True ## DELETE IF NOT DOING ANYTHING!!
        self._y_held = False
        
        self.add_labels()

    def add_labels(self):
        """Not implemented. Implement on subclass"""
        pass

    def add_label(self, *args, vert_spacing=0, 
                  anchor_x='center', bold=False, font_size=25, 
                  **kwargs) -> Label:
        """Add a pyglet text label.
        
        Label will be created from +*args+ and +kwargs+ passed (as 
        parameters of pyglet.text.Label) together with defined parameters 
        +anchor_x+, +bold+ and +font_size+.
        
        If not passed within +kwargs+ then 'x' is defined to position the 
        label in the center of the screen.

        If not passed within +kwargs+ then 'y' is defined to position the
        label +vert_spacing+ pixels under the prior label, or under the 
        top of the window if this is the first label being added.
        """
        kwargs['anchor_y'] = 'top'  # To manage vertical separation
        kwargs['anchor_x'] = anchor_x
        kwargs['bold'] = bold
        kwargs['font_size'] = font_size
        kwargs.setdefault('batch', self.batch)
        kwargs.setdefault('group', self.group)
        kwargs.setdefault('y', self._y - vert_spacing)
        kwargs.setdefault('x', self._x)
        
        lbl = Label(*args, **kwargs)
        self.labels.append(lbl)
        
        # Set self._y to bottom of added label.
        if not self._y_held:
            height = lbl.content_height if lbl.height is None else lbl.height
            self._y = lbl.y - height
        
        return lbl

    def add_title(self, *args, font_size=100, bold=True, **kwargs) -> Label:
        """Add a Label formatted as the main title.
        
        Extends --add_label()-- by defining default values for a title label.

        If not passed within +kwargs+ then 'y' is defined to position the
        top of the label at 0.79 of the window height.
        """
        kwargs['bold'] = bold
        kwargs['font_size'] = font_size
        kwargs.setdefault('y', int(self.win.height*0.79))
        return self.add_label(*args, **kwargs)
    
    def add_enter_for_inst_label(self):
        """Add label advising user to press enter for instructions."""
        return self.add_label('Enter for instructions', y=100, font_size=20)
        
    def add_escape_to_exit_label(self, alt_text: Optional[str] = None):
        """Add label advising user to press escape to exit."""
        text = alt_text if alt_text is not None else 'ESCAPE to exit'
        self._esc_lbl = self.add_label(text, y=55, font_size=15)
        return self._esc_lbl

    def display(self, label: Label, show: bool = True):
        """Display or hide a label.
        
        +label+ Label to be hidden or displayed.
        +show+ True to display, False to hide.
        """
        if show:
            label.batch = self.batch
        else:
            label.batch = None
            
    def advance_y(advance: int):
        """Advance the current y position.
        
        +advance+ Number of pixels to advance the current y position. NB 
        pass a negative value to move the current y position 'back up' the 
        window.
        """
        self._y -= advance

    def hold_y(self, move_on: int = 0):
        """Hold current position of y.
        
        Next label added will be positioned at the same vertical level as 
        the previous added label.
        """
        self._y_held = True
        
    def release_y(self):
        """Release the current y position.
        
        If y level held, revert to default behaviour of positioning the next 
        added label under the previously added label.
        """
        self._y_held = False

class StartLabels(WindowLabels):
    """Labels for an introduction window.

    Text:
    'PYROIDS'
    'Press 1 or 2 to start with 1 or 2 players'
    'Enter for instructions'
    'ESCAPE to exit'
    """
    def add_labels(self):
        self.add_title('PYROIDS')
        self.add_label('Press 1 or 2 to start with 1 or 2 players')
        self.add_enter_for_inst_label()
        self.add_escape_to_exit_label()
        
class NextLevelLabel(WindowLabels):
    """Single semi-transparent Label to introduce next level.

    Text:
    'NEXT LEVEL'
    """
    def add_labels(self):
        self.add_title('NEXT ZONE', color=(255, 255, 255, 188))

class LevelLabel(WindowLabels):
    """Single label to display the current level.

    Text:
    "Zone 'xx'" where xx is a number. For numbers < 10 the first 'x' takes a 
        space.

    METHODS
    --update()-- to update label for a new level.
    """
    def add_labels(self):
        self.label = self.add_label(text="Zone  1", font_size=18, 
                                    y = self.win.height - 8, bold=False, 
                                    anchor_y='top')

    def update(self, new_level: Optional[int] = None):
        """Update label to reflect +new_level+."""
        extra_space = ' ' if new_level < 10 else ''
        self.label.text = "Zone " + extra_space + str(new_level)

class EndLabels(WindowLabels):
    """Labels for Game Over screen.

    Text:
    'Draw!' or 'BLUE wins!' or 'RED wins!' [Optional]
    'GAME OVER' or 'WELL DONE'
    'ALL ASTEROIDS DESTROYED' or 'Press 1 or 2 to start again'
    'Press 1 or 2 to start again' or ''
    'Enter for instructions'
    'ESCAPE to exit'
        
    METHODS
    --display_winner_label()--  Display or hide the 'winner' label
    --set_labels()--  Set labels according to who won and if game completed.
    """
    def add_labels(self):
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
        """Display or Hide 'winner' label.
        
        +show+ True to display, False to hide.
        """
        super().display(self._winner_lbl, show)
      
    def _set_winner_label(self, winner: Union['red', 'blue', bool, None]):
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
        """Set labels according to who won and whether game completed.
        
        +winner+ False to not define a result, None to define game as draw, 
        'red' or 'blue' to define winner a 'red' or 'blue' player.
        +completed+ True if player(s) completed the game.
        """
        self._set_title(completed)
        self._set_sub1(completed)
        self._set_sub2(completed)
        self._set_winner_label(winner)

class InstructionLabels(WindowLabels):
    """Labels that collectively offer instructions including key controls.

    General arrangement:
    Label offering instructions or ''
    Table of color coded labels describing Ship controls
    Table of labels offering Game Control keys.
    'Press F12 to return' or 'Press any key to return'
    'Press ESCAPE to end game' or ''

    Two modes, 'paused' or 'main menu'. Main menu will show labels over 
    an opaque black background whilst 'paused' shows labels over a 
    semi-transparent background such that existing window contents are 
    visible behind the labels.

    METHODS
    --set_labels()-- Set label for either paused or main menu mode.
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
        """+blue_controls+ Dictionary describing ship key controls for 
        blue player, for example as Ship.controls.
        +red_controls+ Dictionary describing ship key controls for red 
        player, for example as ShipRed.controls.
        """
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
            "highest in the area around the edge of each zone. GOOD LUCK!"
            )
        
        self._opaque_bg = self._add_window_rect(color=(0, 0, 0, 255))
        self._trans_bg = self._add_window_rect(color=(40, 40, 40, 125))
        self._trans_bg.remove_from_batch()
        self._opaque = True
        
    def _add_window_rect(self, color: Tuple[int, int, int, int]):
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

    def _field(self, keys: Iterable) -> str:
        """+keys+ Iterable of integers employed by pyglet to represent 
        the keyboard key(s) that serve(s) to action a specific ship control.
        """
        text = ''
        for i, key in enumerate(keys):
            sep = '' if i is 0 else ', '
            key_text = pyglet.window.key.symbol_string(key).strip('_')
            text = sep.join([text, key_text])
        return text

    def _row(self, first_col: str, control_key: str) -> Tuple[str, str, str]:
        """Return tuple of strings representing a table row that describes
        the keyboard keys to enact a specific ship control.

        +first_col+ String describing the specific control. Appears in the 
        row's first column.
        +control_key+ Internal key used to describe the specific control, i.e. 
        a key of ++blue_controls++.
        """
        blue_keys = self._blue_controls[control_key]
        red_keys = self._red_controls[control_key]
        return (first_col, self._field(blue_keys), self._field(red_keys))
        
    def add_labels(self):
        self._inst_lbl = self.add_label("placeholder", vert_spacing=30,
                                        font_size=16, multiline=True,
                                        width=int(self.win.width*0.8),
                                        align='center', 
                                        color=(200, 200, 200, 255)) # Green
        
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
        """Set labels for paused or main menu mode.
        
        +paused+ True to set labels for paused mode, otherwise False.
        """
        if paused:
            self._set_for_pause()
        else:
            self._set_for_main_menu()


class StockLabel(pyglet.text.layout.TextLayout):
    """image/text layout describing stock level for an ammunition type.

    Layout comprises:
        First character as an inline elelment containing an image that 
            represents a specific ammunition type
        Text to reflect stock level.
       
    Red 'X' appears over ammunition type image if stock level is 0.
    
    METHODS
    --set()--  Set document style and layout properties.
    --update()--  Update stock label text.
    --positioned--  Advise that client has positioned object (optional).
    """
    
    class StockLabelElement(pyglet.text.document.InlineElement):
        """Ammunition image representing first character of a StockLabel.

        Center of ammunition image will be vertically alligned with center 
        of the StockLabel's text that follows it.
        """
        
        def __init__(self, image: pyglet.image.Texture, separation=2):
            """
            ++image++ Image representing ammunition type.
            ++separation++ distance between edge of image and subsequent 
                text, in pixels.
            """
            image = copy(image)
            image.anchor_x = 0
            image.anchor_y = 0
            
            self.image = image
            self.height = image.height
            super().__init__(ascent=0, descent=0, 
                             advance = image.width + separation)

        def place(self, layout, x: int, y: int):
            """Position ammunition image.
            
            +layout+ StockLabel object to which this StockLabelElement was 
                inserted. Layout should have anchor_y set to 'bottom' and 
                'content_valign' set to 'center'.
            +x+ Left edge of box reserved for in-line element and in which 
                ammunition image is to be positioned.
            +y+ Baseline level, on which layout text sits.
            """
            # Defines y at level so center of in-line image alligns vertically
            # with center of subsequent text, for which requires:
            # layout.anchor_y is'bottom' and layout_content_valign is 'center'
            y = layout.y + (layout.content_height//2) - ( self.image.anchor_y + (self.height//2) )
            self._sprite = Sprite(self.image, x, y, batch=layout.batch,
                                  group=layout.top_group)
            self._sprite.draw()
        
        def remove(self, layout):
            """Remove image from in-line element."""
            self._sprite.delete()

    class CrossOutGroup(pyglet.graphics.OrderedGroup):
        def set_state(self):
            pyglet.gl.glLineWidth(3)

    class BackgroundGroup(pyglet.graphics.OrderedGroup):
        def __init__(self):
            super().__init__(0)

    def __init__(self, image: pyglet.image.Texture, 
                 initial_stock: int = 0, 
                 group: Optional[pyglet.graphics.OrderedGroup] = None,
                 style_attrs: dict = None, **kwargs):
        """
        ++image++ image representing ammunition type.
        ++initial_stock++ Number of rounds of ammunition stock to appear 
            next to ammunition type image.
        ++group++ OrderedGroup to which StockLabel is to be included, or None 
            if to be added to default BackgroundGroup.
        ++style_attrs++ Any style attributes to apply to whole layout 
            document, as passed to pyglet FormattedDoument().set_style().
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

        # Center text vertically
        self.content_valign = 'center'  
        # Allows StockLabelElement to locate vertical center.
        self.anchor_y='bottom'  
        
        self._cross_out_data: Optional[List] = None
        self._cross_out_vertex_list: pyglet.graphics.vertexdomain.VertexList
        self._crossed_out = False

    def set(self, style_attrs: Optional[dict] = None, **kwargs):
        """Set layout document.

        +style_attrs+ Any style attributes to apply to whole layout document, 
            as passed to pyglet FormattedDoument().set_style().
        +kwargs+ Layout properites to be set. For example, ''x', 'y', 
            'anchor_x', 'batch' etc.
        """
        if style_attrs is not None:
            end = len(self.document.text)
            try:
                self.document.set_style(0, end, style_attrs)
            # Ignore non-fatal error that occurs when pass 'color' attribute.
            # Suspect pyglet bug
            except AttributeError:
                pass
        if not kwargs:
            return
        self.begin_update()
        for kwarg, val in kwargs.items():
            setattr(self, kwarg, val)
        self.end_update()
        
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

    def positioned(self):
        """Advise that client has positioned object.

        Optional. Execution will minimally reduce overhead on first 
        occasion the ammunition image is crossed out.
        """
        self._setup_cross_out_data()

    def delete(self):
        if self._crossed_out:
            self._delete_cross_out()
        super().delete()

    def update(self, stock: int):
        """Update stock label text.
        
        +stock+ Updated stock level to display.
        """
        end = len(self.document.text)
        self.document.delete_text(1, end)
        self.document.insert_text(1, self._label_text(stock))
        if stock is 0:
            self._cross_out()
        elif self._crossed_out:
            self._delete_cross_out()


class InfoRow(object):
    """Row of Labels collectively providing player information.

    Provides information on:
        Lives, as images of player ship, one image per life remaining.
        Ammunition stock levels, as series of StockLabels associated with 
            each of player's weapons.
        Radiation level, as RadiationMonitor.gauge associated with player
        Score, as created score label.

    Information positioned right-to-left if player is blue, or from 
    left-to-right if red.

    METHODS
    --remove_a_life()--  Remove the life furthest from the screen edge.
    --update_score_label()--  Update score label
    --delete()--  Delete all objects that comprise InfoRow
    """
    
    _text_colors = {'blue': BLUE,
                   'red': RED}
    
    _radiation_symbol = load_image('radiation_20.png', anchor='origin')

    def __init__(self, window: pyglet.window.Window, 
                 batch: pyglet.graphics.Batch, 
                 control_sys,
                 num_lives: int, 
                 level_label: Label):
        """
        ++window++ Window to which InfoRow to be displayed.
        ++batch++ Batch to which InfoRow objects to be added.
        ++control_sys++ .game_objects.ControlSystem of player for whom 
            providing information.
        ++num_lives++ Number of lives player starts with.
        ++level_label++ Label that expresses current level.
        """
        self._win = window
        self._info_row_base = self._win.height - 30
        self._batch = batch
        self._control_sys = control_sys
        self._color = self._control_sys.color
        self._text_color = self._text_colors[self._color]
        self._num_lives = num_lives
        self._lives = []
        self._level_label = level_label

        # Current position of _x, updated --_advance_x()-- as set objects
        self._x = self._win.width if self._color == 'blue' else 0
        
        self._set_lives()
        self._set_stocks_labels()
        self._set_radiation_gauge()
        self._create_score_label()
        
    def _advance_x(self, pixels: int):
        """Move _x by +pixels+ pixels in the direction that labels are being 
        sequentially placed.
        """
        pixels *= -1 if self._color == 'blue' else 1
        self._x += pixels
        
    def _get_object_x(self, obj: Union[Sprite, StockLabel]):
        """Return 'x' coordinate to place object at required separation on 
        from last object placed ASSUMING +obj+ is anchored to bottom left 
        and --_x-- positioned at the required spacing on from the last 
        object placed.
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
        """Position and batch +obj+.
        
        Position and batch according to passed parameters, or according 
        to default behaviour otherwise. NB Default behaviour ASSUMES +obj+ 
        anchored to bottom left corner.
        """
        if sep is not 0:
            self._advance_x(sep)
        obj.batch = self._batch if batch is None else batch
        obj.y = self._info_row_base if y is None else y
        obj.x = self._get_object_x(obj) if x is None else x
        width = obj.content_width if isinstance(obj, StockLabel)\
            else obj.width
        self._advance_x(width) # Leave _x at end of info row

    def _set_lives(self):
        for i in range(self._num_lives):
            img = copy(self._control_sys.ShipCls[self._color].img)
            img.anchor_x = 0
            img.anchor_y = 0
            life = Sprite(img)
            life.scale = 0.36
            self._lives.append(life)
            self._set_object(life, sep=3)
             
    def remove_a_life(self):
        """Remove the life image furthest from the screen edge."""
        self._lives.pop()
        
    def _set_stocks_labels(self):
        for weapon in self._control_sys.weapons:
            label = weapon.stock_label
            label.set(style_attrs={'color': self._text_color, 'bold': True})
            self._set_object(label, sep=10)
            label.positioned()
                        
    def _set_radiation_gauge(self):
        self._set_object(self._control_sys.radiation_monitor.gauge, sep=15)
        self._rad_symbol = Sprite(self._radiation_symbol)
        self._set_object(self._rad_symbol, sep=5)

    def _score_label_x_coordinate(self) -> int:
        """Returns x coordinate for score label to position to side of level 
        label.
        """
        direction = 1 if self._color == 'blue' else -1
        dist = (self._level_label.content_width//2) + 34
        x = self._level_label.x + (dist * direction)
        return x
        
    def _create_score_label(self):
        self._score_label = Label('0', x=self._score_label_x_coordinate(), 
                                 y=self._win.height,font_size=30, bold=True, 
                                 batch=self._batch,
                                 anchor_x='center', anchor_y='top')
        self._score_label.set_style('color', self._text_color)
    
    def update_score_label(self, score: int):
        """Update score label to +score+."""
        self._score_label.text = str(score)

    def delete(self):
        """Delete all objects that comprise InfoRow."""
        for life in self._lives:
            life.delete()
        for weapon in self._control_sys.weapons:
            weapon.stock_label.delete()
        self._score_label.delete()
        self._control_sys.radiation_monitor.gauge.delete()
        self._rad_symbol.delete()