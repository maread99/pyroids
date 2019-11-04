#! /usr/bin/env python

"""Modules offers class to draw shapes and patterns from primative 
forms"""

import math
from typing import Tuple, List, Optional

import pyglet

class DrawingBase(object):
    """Base class for defining drawable shapes and patterns.
    
    Requires that subclass implement following properties and 
    methods (see method__doc__):
    --mode()--
    --_coords()--
    
    Provides for two modes of operation.
    If pass ++batch++ (and optionally ++group++) the the drawing will be 
        immediately added to ++batch++. In this case the drawing can be 
        removed from the batch with --remove_from_batch-- and subseqeuntly 
        returned to the batch with --return_to_batch--.
    If ++batch++ is not passed then drawing can be drawn directly to the 
        current window via --draw--.
    NB in either case all data is calcualted on instance instantiation such 
    that the actual drawing, via batch.draw or .draw(), does not carry this 
    overhead.

    Provides following properties:
    --vertex_list-- VertexList that defines drawing
    --count-- number of vertices
    --mode-- pyglet constant representing drawing's primative Open_GL mode
    --vertices_data-- tuple of vertices data as required by *data argumnents 
      of a VertexList
    --color_data-- tuple of color data as required by *data argumnents 
      of a VertexList

    Internals.
    Pyglet does not (seem to) provide for a way to simply remove a vertex 
    list from a batch! (the documentation claims VertexList.delete() does the 
    job but it eludes me). This class provides for such functionality, via 
    --remove_from_batch()-- by migrating the vertex_list from the passed 
    batch to a 'storeage batch' assigned to class attribute 
    ---_shelf_batch---. --return_to_batch()-- then simply migrates it back in 
    the other direction.
    """

    _shelf_batch = pyglet.graphics.Batch()

    def __init__(self, color = (255, 255, 255, 255), 
                 batch: Optional[pyglet.graphics.Batch] = None, 
                 group: Optional[pyglet.graphics.Group] = None):
        """++color++ defines drawing colour and, if applicable, 
        fill, passed as a Tuple[int, int, int] where int's determine 
        GB components respectively. Can pass a further int to define 
        Alpha channel if required. By default White and fully opaque.
        ++batch++ any batch that the drawing is to be added to
        ++group++ any group that the batched drawing is to be added to
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
    def vertex_list(self):
        return self._vertex_list

    @property
    def count(self) -> int:
        return self._count

    @property
    def vertices_data(self) -> Tuple[str, tuple]:
        return self._vertices_data

    @property
    def color_data(self) -> Tuple[str, tuple]:
        return self._color_data

    @property
    def mode(self):
        """Define on subclass to return pyglet.gl constant which 
        describes the GL_Open primative mode, for example for 
        a rectangle pyglet.gl.GL_QUADS"""
        raise NotImplementedError('abstract')

    def _coords(self) -> tuple:
        """Define on subclass to return a tuple of vertices co-ordinates.
        For example, to describe a 100x100 rectangle:
            (100, 100, 100, 200, 200, 200, 200, 100)"""
        raise NotImplementedError('abstract')
        
    def _set_vertices_data(self):
        coords = self._coords()
        self._count = len(coords)//2
        self._vertices_data = ('v2i', coords)
        
    def _set_color_data(self):
        self._color_data = ('c4B', self._color * self.count)

    def _set_data(self):
        self._set_vertices_data()
        self._set_color_data()

    def _set_vertex_list(self):
        self._vertex_list = pyglet.graphics.vertex_list(self.count,
                                                       self.vertices_data,
                                                       self.color_data)
        
    def _add_to_batch(self):
        vl = self._batch.add(self.count, self.mode, self._group, 
                             self.vertices_data, self.color_data)
        self._vertex_list = vl
        self._current_batch = self._batch

    def _migrate(self, new_batch: pyglet.graphics.Batch):
        self._current_batch.migrate(self._vertex_list, self.mode, 
                                    self._group, new_batch)
        self._current_batch = new_batch

    def remove_from_batch(self):
        assert self._batch is not None, "Can only employ batch operations"\
            " when ++batch++ is passed to constructor"
        self._migrate(self._shelf_batch)

    def return_to_batch(self):
        assert self._current_batch is self._shelf_batch, "Can only return to"\
            " batch after having previously removed from batch with"\
            " --remove_from_batch()--"
        self._migrate(self._batch)

    def draw(self):
        self.vertex_list.draw(self.mode)

    


class AngledGrid(DrawingBase):
    """--draw-- to a specified rectangular area a grid of lines angled 
    to the vertical. Lines drawn both left-to-right and right-to-left. 
    At limit, with ++angle++ = 90, will draw horizontal lines which are 
    not accompanied with vertical lines
    
    DrawingBase.__doc__ for further documentation"""
    
    def __init__(self, x_min: int, x_max: int, y_min: int, y_max: int,
                 angle: int,  vertical_spacing: int, 
                 color = (255, 255, 255, 255), **kwargs):
        """++x_min++, ++x_max++, ++y_min++, ++y_max++ define the borders 
        of the rectangular area to be gridded.
        ++angle++ describes the angle, in degrees, of the grid lines, from the 
        horizontal.
        ++vertical_spacing++ determines the vertical distance between 
        parallel grid lines (NB horizonal spacing determined so as to keep 
        lines parallel based on  ++vertical_spacing++
        """
        self.width = x_max - x_min
        self.X_MIN = x_min
        self.X_MAX = x_max
        self.height = y_max - y_min
        self.Y_MIN = y_min
        self.Y_MAX = y_max
        
        self.vertical_spacing = vertical_spacing
        angle = math.radians(angle)
        self.tan_angle = math.tan(angle)
        
        super().__init__(color=color, **kwargs)

    @property
    def mode(self):
        return pyglet.gl.GL_LINES
        
    def _left_to_right_coords(self) -> List[int]:
        spacing = self.vertical_spacing
        x1 = self.X_MIN
        y1 = self.Y_MAX
        vertices = []

        while y1 > self.Y_MIN:
            vertices.extend([x1, y1])
            x2 = min(self.X_MAX, 
                     self.X_MIN + round((y1 - self.Y_MIN) * self.tan_angle))
            y2 = self.Y_MIN if x2 != self.X_MAX \
                else y1 - round(self.width / self.tan_angle)
            vertices.extend([x2, y2]) 
            y1 -= spacing

        spacing = round(spacing * self.tan_angle)
        y1 = self.Y_MAX
        x1 = self.X_MIN + spacing
        while x1 < self.X_MAX:
            vertices.extend([x1, y1])
            y2 = max(self.Y_MIN, 
                     self.Y_MAX - round((self.X_MAX - x1)/self.tan_angle))
            x2 = self.X_MAX if y2 != self.Y_MIN else \
                x1 + round(self.height * self.tan_angle)
            vertices.extend([x2, y2])
            x1 += spacing

        return vertices

    def _horizontal_flip(self, coords: List[int]) -> List[int]:
        flipped_coords = []
        x_mid = self.X_MIN + self.width//2
        x_mid_por_dos = x_mid*2
        for i in range(0, len(coords), 2):
            flipped_coords.append(x_mid_por_dos-coords[i])
            flipped_coords.append(coords[i+1])
        return flipped_coords

    def _coords(self) -> Tuple:
        coords1 = self._left_to_right_coords()
        coords2 = self._horizontal_flip(coords1)
        return tuple(coords1 + coords2)


class Rectangle(DrawingBase):
    """--draw()-- draws a filled Rectangle"""
    
    def __init__(self, x_min: int, x_max: int, y_min: int, y_max: int,
                 fill_color = (255, 255, 255, 255), **kwargs):
        """++x_min++, ++x_max++, ++y_min++, ++y_max++ define the 
        rectangle's border.
        ++fill_color++ as defined on base class
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
        return (self.X_MIN, self.Y_MIN,
                self.X_MIN, self.Y_MAX,
                self.X_MAX, self.Y_MAX,
                self.X_MAX, self.Y_MIN)