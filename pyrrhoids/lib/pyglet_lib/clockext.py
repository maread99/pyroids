#! /usr/bin/env python

"""
Single class ClockExt which extends pyglet's 'Clock' class to provided for 
pause functionality.

NB The pyglet clock can be changed to an instance of ClockExt with the 
following code which should be executed by the application BEFORE any other 
import from pyglet:
    from .lib.pyglet_lib_clockext import ClockExt  # path to this file
    import pyglet
    CLOCK = ClockExt()  # 'CLOCK' - or name as required
    pyglet.clock.set_default(CLOCK)   # 'CLOCK' - or name as required
"""

import pyglet
class ClockExt(pyglet.clock.Clock):
    """Extends Clock to provide pyglet application with functionality to 
    pause the clock. All scheduled calls are delayed by the time the 
    clock is paused for.
    
    --pause-- to pause the clock
    --resume-- to resume the clock

    Internals. Reroutes calls to --time()--, which would usually reutrn the 
    time from the ++time_function++, such that the actual time returned is 
    the time as returned by the ++time_function++ less the cumulative time 
    during     which the application has been paused.
    Overrides both --tick-- and --update_time-- to return 0 in the event 
    paused (usually both methods would be expected to return the time 
    differnce (dt) since the time was last updated.
    Collective this has the effect of freezing the clock whilst paused
    """

    def __init__(self, *args, **kwargs):
        self._paused = False
        self._pause_ts: Optional[float] = None
        self._paused_cumulative = 0
        
        super().__init__(*args, **kwargs)
        self._time_func = self.time
        self.time = self._time

    def _time(self):
        """Internals - executed on calls to --time---. Extends the method 
        held by --time-- (the time_function) to account for time during
        which the application has been paused"""
        return self._time_func() - self._paused_cumulative

    def pause(self):
        self._paused = True
        self._pause_ts = self._time_func()


    def resume(self):
        time_paused = self._time_func() - self._pause_ts
        self._paused_cumulative += time_paused
        self._pause_ts = None
        self._paused = False

    def update_time(self, *args, **kwargs):
        if self._paused:
            return 0
        return super().update_time(*args, **kwargs)

    def tick(self, *args, **kwargs):
        if self._paused:
            return 0
        return super().tick(*args, **kwargs)