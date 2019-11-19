#! python3

"""Iterator-related utility functions.

FUNCTIONS

Following functions return infinite interators defined from a passed sequence:
    repeat_sequence()  Iterator repeats passed sequence.
    repeat_last()  After exhausting sequences, repeats last value.
    increment_last()  After exhausting sequences, increments last value.
    factor_last()  After exhausting sequences, factors last value.
"""

if __name__ ==  "__main__":
	print("Module was run directly. Module is INTENDED TO BE IMPORTED")
	exit()

from itertools import chain, count, cycle, repeat
from typing import Iterator, Iterable, Union

def repeat_sequence(seq: Iterable) -> Iterator:
    """As itertools.cycle"""
    return cycle(seq)

def repeat_last(seq: Iterable) -> Iterator:
    """Return +seq+ as infinite iterator that repeats last value.
    
    After exhausting values of +seq+ further calls to iterator will return 
    the final value of +seq+.
    """
    return chain(seq, repeat(seq[-1]))

def increment_last(seq: Iterable, increment: Union[float, int]) -> Iterator:
    """Return +seq+ as infinite iterator that increments last value.
    
    After exhausting values of +seq+ further calls to iterator will return 
    the prior value incremented by +increment+.
    """
    return chain(seq[:-1], count(seq[-1], increment))

def factor_last(seq: Iterable, factor: Union[float, int], 
                round_values=False) -> Iterator:
    """Return +seq+ as infinite iterator that factors last value.
    
    After exhausting values of +seq+ further calls to iterator will return 
    the prior value factored by +factor+.
    +round_values+ True to round returned values to nearest integer.
    """
    def series():
        cum = seq[-1]
        while True:
            cum *= factor
            yield round(cum) if round_values else cum
    return chain(seq, series())