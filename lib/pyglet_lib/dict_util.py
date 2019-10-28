#! python3

"""Dictionay-related utility functions and classes"""

if __name__ ==  "__main__":
	print("Module was run directly. Module is INTENDED TO BE IMPORTED")
	exit()

from typing import List

def print_rtrn_keys(dic: dict, output: bool = True) -> List[str]:
    """For advising of valid values where valid values comprise the keys 
    of a ++dic++.
    prints (by default) and returns list of ++dic++ keys.
    ++output++ if False does not ot print to standard output"""
    keys = list(dict.keys())
    if output:
        print(keys)
    return keys

def assert_key_in_dict(key, dic: dict):
    """Assertion statement that key must be in dic"""
    assert key in dic, str(key) + " must be in " +\
        str(print_rtrn_keys(dic, output=False))

def set_kwargs_from_dflt(passed: dict, dflt: dict) -> dict:
    """Updates ++passed++ dictionary to add any missing keys and 
    assign corresponding default values, with missing keys and 
    default values as defined by ++dflt++"""
    for key, val in dflt.items():
        passed.setdefault(key, val)
    return passed

def exec_kwargs(kwargs: dict) -> dict:
    """Calls any value of kwargs that represents a callable and updates
    value to the callable's return value"""
    for kw, val in kwargs.items():
        if callable(val):
            kwargs[kw] = val()
    return kwargs

def set_kwargs_from_dflt_exec(passed: dict, dflt: dict) -> dict:
    """Via function calls, Updates ++passed++ dictionary to add any missing 
    keys and assign corresponding default values (with missing keys and default 
    values as defined by ++dflt++), and sets value of any kwarg that 
    represents a callable to the callable's return value"""
    kwargs = set_kwargs_from_dflt(passed, dflt)
    return exec_kwargs(kwargs)

def set_kwargs(passed: dict, dflt: dict) -> dict:
    """Updates ++dflt++ dictionary to reflect any keys: value pairs 
    in ++passed++ dictionary"""
    for key, val in passed.items():
        dflt[key] = val
    return dflt

def set_exec_kwargs(passed: dict, dflt: dict) -> dict:
    """Via function calls, Updates ++dflt++ dictionary to reflect any keys: 
    value pairs in ++passed++ dictionary and the evaluated return of any 
    value that represents a callable"""
    kwargs = set_kwargs(passed, dflt)
    return exec_kwargs(kwargs)