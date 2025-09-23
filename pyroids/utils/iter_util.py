"""Iterator-related utility functions.

Functions
---------
Functions return infinite interators defined from a passed sequence:
    repeat_last()  After exhausting sequences, repeats last value.
    increment_last()  After exhausting sequences, increments last value.
    factor_last()  After exhausting sequences, factors last value.
"""

from collections.abc import Iterator, Sequence
from itertools import chain, count, repeat


def repeat_last(seq: Sequence) -> Iterator:
    """Return a sequence as infinite iterator that repeats the last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the final value of `seq`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.
    """
    return chain(seq, repeat(seq[-1]))


def increment_last(seq: Sequence, increment: float) -> Iterator:
    """Return a sequence as infinite iterator that increments last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the prior value incremented by `increment`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.

    increment
        Value by which to increment last value of `seq` and subsequent
        values.
    """
    return chain(seq[:-1], count(seq[-1], increment))


def factor_last(
    seq: Sequence,
    factor: float,
    *,
    round_values: bool = False,
) -> Iterator:
    """Return a sequences as infinite iterator that factors last value.

    After exhausting values of `seq` further calls to returned iterator
    will return the prior value factored by `factor`.

    Parameters
    ----------
    seq
        Sequence of values from which to create iterator.

    factor
        Factor by which to augment last value of `seq` and subsequent
        values.

    round_values
        True to round returned values to nearest integer.
    """

    def series():
        cum = seq[-1]
        while True:
            cum *= factor
            yield round(cum) if round_values else cum

    return chain(seq, series())
