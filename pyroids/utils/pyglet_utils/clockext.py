"""Clock extension."""

from __future__ import annotations

import pyglet


class ClockExt(pyglet.clock.Clock):
    """Extends standard default Clock to include pause functionality.

    Pausing clock has effect of delaying all scheduled calls by the time
    during which the clock is paused.

    Notes
    -----
    CHANGING THE CLOCK
    Use the following code to cahnge the standard pyglet clock to an
    instance of ClockExt. Note that This code must be executed by the
    application BEFORE any other import from pyglet:

    ```python
    from .utils.pyglet_utils_clockext import ClockExt
    import pyglet
    pyglet.clock.set_default(ClockExt())
    ```

    Methods
    -------
    pause
        Pause the clock
    resume
        Resume the clock
    """

    def __init__(self, *args, **kwargs):
        self._paused = False
        self._pause_ts: float | None = None
        self._paused_cumulative = 0

        super().__init__(*args, **kwargs)
        self._time_func = self.time  # stores original `time` function
        self.time = self._time  # assigns `time` to alternative function

    def _time(self):
        # Alternative time function as original save for subtracting
        # cumulative time over which clock has been paused.
        return self._time_func() - self._paused_cumulative

    def pause(self):
        """Pause the clock."""
        self._paused = True
        self._pause_ts = self._time_func()

    def resume(self):
        """Resume the clock."""
        time_paused = self._time_func() - self._pause_ts
        self._paused_cumulative += time_paused
        self._pause_ts = None
        self._paused = False

    def update_time(self, *args, **kwargs):
        """Get the elapsed time since the last call to `update_time`."""
        # Extends inherited method to not update time when paused.
        if self._paused:
            return 0
        return super().update_time(*args, **kwargs)

    def tick(self, *args, **kwargs):
        """Signify that one frame has passed."""
        # Extends inherited method to not tick when paused.
        if self._paused:
            return 0
        return super().tick(*args, **kwargs)
