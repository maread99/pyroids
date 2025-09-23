"""Physics Functions.

Functions
---------
distance
    Length of line from point1 to point2.
"""

import math


def distance(point1: tuple[int, int], point2: tuple[int, int]) -> float:
    """Return length of line from point1 to point2."""
    x_dist = abs(point1[0] - point2[0])
    y_dist = abs(point1[1] - point2[1])
    return math.sqrt(x_dist**2 + y_dist**2)
