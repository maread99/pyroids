#! /usr/bin/env python

"""Physics Functions"""

import math
from typing import Tuple

def distance(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """Returns the direct distance from point1 to point2"""
    x_dist = abs(point1[0] - point2[0])
    y_dist = abs(point1[1] - point2[1])
    dist = math.sqrt(x_dist**2 + y_dist**2)
    return dist