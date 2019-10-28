#! python3

"""Iterator-related utility functions"""

if __name__ ==  "__main__":
	print("Module was run directly. Module is INTENDED TO BE IMPORTED")
	exit()

from itertools import chain, count, cycle, repeat
from typing import Iterator, Iterable, Union

def repeat_sequence(seq: Iterable) -> Iterator:
    """As itertools.cycle"""
    return cycle(seq)

def repeat_last(seq: Iterable) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ repeats the final value of +seq+"""
    return chain(seq, repeat(seq[-1]))

def increment_last(seq: Iterable, increment: Union[float, int]) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ returns the previous value incremented by +increment+"""
    return chain(seq[:-1], count(seq[-1], increment))

def factor_last(seq: Iterable, factor: Union[float, int], 
                round_values=False) -> Iterator:
    """Returns infinite iterator which after exhausting the values of 
    +seq+ returns the previous value factored by +factor+.
    Values rounded to the nearest integer if +round_values+ True.
    """
    def series():
        cum = seq[-1]
        while True:
            cum *= factor
            yield round(cum) if round_values else cum
    return chain(seq, series())