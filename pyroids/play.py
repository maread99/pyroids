#! /usr/bin/env python

"""Launch application from the command line.

    $ python -m pyroids.play

Application settings can be optionally customised by passing the name of a
configuration file located in the pyroids.config directory. Example:

    $ python -m pyroids.play novice

See pyroids\config\template.py for instructions on setting up configuration
files.
"""

import sys
import pyroids

if __name__ == "__main__":
    if len(sys.argv) is 2:
        config_file = sys.argv[1]
    else:
        config_file = None
    pyroids.launch(config_file)
