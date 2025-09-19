#! /usr/bin/env python

"""Draw shapes and patterns from primative forms.

CLASSES
DrawingBase()  Base class to define drawable shapes and pattern.
AngledGrid(DrawingBase)  Grid of parallel lines angled to the vertical.
Rectangle(DrawingBase)  Filled Rectangle
"""

import math
from typing import Tuple, List, Optional

import pyglet


class DrawingBase(object):
    """Base class for defining drawable shapes and patterns.

    PROPERTIES
    --vertex_list--  VertexList that defines drawing.
    --count--  Number of vertices
    --mode--  Primative Open_GL mode, as represented by pyglet constant.
    --vertices_data--  Tuple of vertices data as passed to *data arguments
        of a VertexList.
    --color_data--  Tuple of color data as passed to *data arguments of a
        VertexList.

    METHODS
    Class offers two modes of operation which determine methods available.

    Direct Drawing. In this mode ++batch++ should not be passed/
        --draw()--  Draw drawing directly to the current window

    Add to batch. In this mode drawing will be immediately added to ++batch++.
        --remove_from_batch()--  Remove drawing from batch.
        --return_to_batch--  Return drawing to batch.


    --delete()--  Delete drawing.

    SUBCLASS INTERFACE
    Subclasses must implement the following methods:

    --mode()--  Should return the pyglet.gl constant that describes the
        GL_Open primative mode employed by the drawing, for example the
        primative mode for a rectangle would be pyglet.gl.GL_QUADS.

    --_coords()--  Should return a tuple of vertices co-ordinates. For
        example, to describe a 100x100 rectangle:
        (100, 100, 100, 200, 200, 200, 200, 100)
    """

    _shelf_batch = pyglet.graphics.Batch()

    def __init__(
        self,
        color=(255, 255, 255, 255),
        batch: Optional[pyglet.graphics.Batch] = None,
        group: Optional[pyglet.graphics.Group] = None,
    ):
        """
        ++color++  Drawing colour and, if applicable, fill. 3-tuple or
            4-tuple. First three elements integers that represent color's
            RGB components. Optional fourth element can take a further
            integer to define Alpha channel (255 fully opaque). If not
            passed defaults to White and fully opaque.
        ++batch++ Batch to which drawing is to be added. If not passed
            drawing can draw direct to window with --draw()--.
        ++group++ Any group that the batched drawing is to be added to.
            Only relevant if also pass ++batch++. Always optional.
        """
        self._color = color if len(color) == 4 else color + (255,)
        self._batch = batch
        self._current_batch: pyglet.graphics.Batch
        self._group = group

        self._count: int
        self._vertices_data: tuple
        self._color_data: tuple
        self._set_data()

        self._vertex_list: pyglet.graphics.vertexdomain.VertexList
        if batch is not None:
            self._add_to_batch()
        else:
            self._set_vertex_list()

    @property
    def vertex_list(self) -> pyglet.graphics.vertexdomain.VertexList:
        """VertexList that defines drawing."""
        return self._vertex_list

    @property
    def count(self) -> int:
        """Number of vertices."""
        return self._count

    @property
    def vertices_data(self) -> Tuple[str, tuple]:
        """Tuple of vertices data as passed to *data arguments of
        VertexList."""
        return self._vertices_data

    @property
    def color_data(self) -> Tuple[str, tuple]:
        """Tuple of color data as passed to *data arguments of VertexList."""
        return self._color_data

    @property
    def mode(self):
        """Not implemented. Implement on subclass.

        Return pyglet.gl constant that describes the GL_Open primative mode
        used by the drawing.
        """
        raise NotImplementedError("abstract")

    def _coords(self) -> tuple:
        """Not implemented. Implement on subclass"""
        raise NotImplementedError("abstract")

    def _set_vertices_data(self):
        coords = self._coords()
        self._count = len(coords) // 2
        self._vertices_data = ("v2i", coords)

    def _set_color_data(self):
        self._color_data = ("c4B", self._color * self.count)

    def _set_data(self):
        self._set_vertices_data()
        self._set_color_data()

    def _set_vertex_list(self):
        self._vertex_list = pyglet.graphics.vertex_list(
            self.count, self.vertices_data, self.color_data
        )

    def _add_to_batch(self):
        vl = self._batch.add(
            self.count, self.mode, self._group, self.vertices_data, self.color_data
        )
        self._vertex_list = vl
        self._current_batch = self._batch

    def _migrate(self, new_batch: pyglet.graphics.Batch):
        self._current_batch.migrate(
            self._vertex_list, self.mode, self._group, new_batch
        )
        self._current_batch = new_batch

    def remove_from_batch(self):
        """Remove vertex_list from batch.

        Move vertex_list to storage batch."""
        # Pyglet does not (seem to) provide for a way to simply remove a
        # vertex list from a batch. Documentation suggests VertexList.delete()
        # does the job although I can't get it to work in the way I would
        # expect.
        # Functionality provided for here by by migrating the vertex_list
        # to a 'shelf batch' where it sits in storage and from where can be
        # retrieved by --return_to_batch()--.
        assert self._batch is not None, (
            "Can only employ batch operations when ++batch++ is passed to constructor"
        )
        self._migrate(self._shelf_batch)

    def return_to_batch(self):
        """Return drawing to batch."""
        assert self._current_batch is self._shelf_batch, (
            "Can only return to"
            " batch after having previously removed from batch with"
            " --remove_from_batch()--"
        )
        self._migrate(self._batch)

    def delete(self):
        """Delete drawing."""
        try:
            self._vertex_list.delete()
        except AttributeError:
            pass

    def draw(self):
        """Draw to current window."""
        self.vertex_list.draw(self.mode)


class AngledGrid(DrawingBase):
    """Grid of parallel lines angled to the vertical.

    Grid lines drawn both upwards and downwards over a rectangular area.

    Instance ATTRIBUTES
    --width--  Width of rectangular area being gridded.
    --height--  Height of rectangular area being gridded.
    --X_MIN--  Rectangular area left bound (++x_min++)
    --X_MAX--  Rectangular area right bound (++x_max++)
    --Y_MIN--  Rectangular area lower bound (++y_min++)
    --Y_MAX--  Rectangular area upper bound (++y_max++)

    METHODS
    --draw()--  Draw angled grid (inherited method).
    """

    def __init__(
        self,
        x_min: int,
        x_max: int,
        y_min: int,
        y_max: int,
        angle: int,
        vertical_spacing: int,
        color=(255, 255, 255, 255),
        **kwargs,
    ):
        """
        ++x_min++, ++x_max++, ++y_min++, ++y_max++ Bounds of rectangular area
            to be gridded.
        ++angle++ Angle of grid lines, in degrees from the horizontal. Limit
            90 which will draw horizontal lines that are NOT accompanied
            with vertical lines.
        ++vertical_spacing++ Vertical distance between parallel grid lines
            (horizonal spacing determined to keep lines parallel for given
            vertical spacing).
        """
        self.width = x_max - x_min
        self.X_MIN = x_min
        self.X_MAX = x_max
        self.height = y_max - y_min
        self.Y_MIN = y_min
        self.Y_MAX = y_max

        self._vertical_spacing = vertical_spacing
        angle = math.radians(angle)
        self._tan_angle = math.tan(angle)

        super().__init__(color=color, **kwargs)

    @property
    def mode(self):
        return pyglet.gl.GL_LINES

    def _left_to_right_coords(self) -> List[int]:
        """Return verticies for angled lines running downwards from left to
        right. Verticies returned as list of integers with each successive
        four integers describing a line:
        [line1_x1, line1_y1, line1_x2, line1_y2, line2_x1, line2_y1,
        line2_x2, line2_y2, line3_x1, line3_y1, line3_x2, line3_y2...].
        """
        spacing = self._vertical_spacing
        x1 = self.X_MIN
        y1 = self.Y_MAX
        vertices = []

        # Add vertices for lines running from left bound to earlier of right
        # bound or lower bound.
        while y1 > self.Y_MIN:
            vertices.extend([x1, y1])
            x2 = min(
                self.X_MAX, self.X_MIN + round((y1 - self.Y_MIN) * self._tan_angle)
            )
            y2 = (
                self.Y_MIN
                if x2 != self.X_MAX
                else y1 - round(self.width / self._tan_angle)
            )
            vertices.extend([x2, y2])
            y1 -= spacing

        # Add vertices for lines running from upper bound to earlier of right
        # bound or lower bound.
        spacing = round(spacing * self._tan_angle)
        y1 = self.Y_MAX
        x1 = self.X_MIN + spacing
        while x1 < self.X_MAX:
            vertices.extend([x1, y1])
            y2 = max(
                self.Y_MIN, self.Y_MAX - round((self.X_MAX - x1) / self._tan_angle)
            )
            x2 = (
                self.X_MAX
                if y2 != self.Y_MIN
                else x1 + round(self.height * self._tan_angle)
            )
            vertices.extend([x2, y2])
            x1 += spacing

        return vertices

    def _horizontal_flip(self, coords: List[int]) -> List[int]:
        """Return mirrored ++coords++ if mirror were placed vertically
        down the middle of the rectangular area being gridded."""
        flipped_coords = []
        x_mid = self.X_MIN + self.width // 2
        x_mid_por_dos = x_mid * 2
        for i in range(0, len(coords), 2):
            flipped_coords.append(x_mid_por_dos - coords[i])
            flipped_coords.append(coords[i + 1])
        return flipped_coords

    def _coords(self) -> Tuple:
        coords1 = self._left_to_right_coords()
        coords2 = self._horizontal_flip(coords1)
        return tuple(coords1 + coords2)


class Rectangle(DrawingBase):
    """Filled Rectangle.

    Instance ATTRIBUTES
    --X_MIN--  Left bound (++x_min++)
    --X_MAX--  Right bound (++x_max++)
    --Y_MIN--  Lower bound (++y_min++)
    --Y_MAX--  Upper bound (++y_max++)

    METHODS
    --draw()--  Draw filled Rectangle (inherited method).
    """

    def __init__(
        self,
        x_min: int,
        x_max: int,
        y_min: int,
        y_max: int,
        fill_color=(255, 255, 255, 255),
        **kwargs,
    ):
        """
        ++x_min++, ++x_max++, ++y_min++, ++y_max++ Rectangle's bounds.
        ++fill_color++  Fill color. 3-tuple or 4-tuple. First three elements
            as integers that represent color's RGB components. Optional
            fourth element can take a further integer to define Alpha channel
            (255 fully opaque). If not passed defaults to White and fully
            opaque.
        """
        self.X_MIN = x_min
        self.X_MAX = x_max
        self.Y_MIN = y_min
        self.Y_MAX = y_max

        super().__init__(color=fill_color, **kwargs)

    @property
    def mode(self):
        return pyglet.gl.GL_QUADS

    def _coords(self) -> tuple:
        return (
            self.X_MIN,
            self.Y_MIN,
            self.X_MIN,
            self.Y_MAX,
            self.X_MAX,
            self.Y_MAX,
            self.X_MAX,
            self.Y_MIN,
        )
