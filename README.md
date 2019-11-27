# pyroids

Asteroids game with features including:
* 1 or 2 player
* Multiple weapons
* Expendable ammunition
* Supply drops
* Radiation exposure
* Highly customisable. You make the game!

## Installation

The simplest way to install pyroids is directly from PyPI:

	$ pip install --upgrade pyroids --user

#### Alternatively

Install from the source distribution on github:

	$ pip install git+https//github.com/maread99/pyroids.git#egg=pyroids

Install from a source distribution stored locally:

	$ python setup.py install --user

## Requirements

pyroids requires Python 3.6+ (employs annotation syntax).

The only dependency is pyglet 1.4 which, if not already installed, will be installed as part of the pyroids installation process.

## Play me!

Once installed, pyroids can be launched directly from the command line or by via the launch() function.

#### From the command line:

    $ python -m pyroids.play

To launch with settings as defined by a configuration file (see Game 
Customisation section), for example 'expert.py':

    $ python -m pyroids.play expert

If pyroids was installed via pip then the application \*may also launch with default settings with:

	$ pyroids

\* requires that the Scripts directory, of the python environment to which pyroids was installed, is included to the PATH environmental variable.

#### Using launch function:

    >>> import pyroids
    >>> pyroids.launch()

To launch with settings as defined by a configuration file (see Game Customisation section), for example 'novice.py':

    >>> pyroids.launch('novice')

## Game Customisation

Settings that can be defined for each level include:
* Number of Asteroids
* Number of times each original asteroid will break up into smaller asteroids
* Number of smaller asteroids each asteroid breaks up into
* Asteroid speed
* Ship Speed
* Radiation field
* Radiation exposure limits
* Number of supply drops

Settings that can be defined for duration of the application instance include:
* Ship Controls	
* Asteroid behaviour on reaching window border	
* Initial ammunition stocks per weapon
* Frequency and number of supply drops
* Min and Max ammunition stocks in each supply drop (per weapon)
* Cannon reload rate
* High Velocity Bullet speed
* Shield duration
* Number of Levels
* Number of Lives
* Window dimensions

Application settings can be customised by passing the name of a configuration file (see Play me! section). If no configuration file is passed then the game will use default settings.

Configuration files should:
* be based on the template at [pyroids\config\template.py](https://github.com/maread99/pyroids/blob/master/pyroids/config/template.py)
* be saved to the directory pyroids\config.
* have extension .py

See [pyroids\config\template.py](https://github.com/maread99/pyroids/blob/master/pyroids/config/template.py) documentation for instructions on setting up configuration files.

The following example configuration files are included as part of the pyroids 
package:
* [novice.py](https://github.com/maread99/pyroids/blob/master/pyroids/config/novice.py)
* [expert.py](https://github.com/maread99/pyroids/blob/master/pyroids/config/expert.py)

Aside from the configuration files, the ship and asteroid images can be changed with a little investigation of the source code and some minimal hacks.

## Licensing

#### Code
See [LICENSE.txt](https://github.com/maread99/pyroids/blob/master/LICENSE.txt).

#### Media
See [pyroids\resources\README.md](https://github.com/maread99/pyroids/blob/master/pyroids/resources/README.md).

## Code Documentation

Function and Method documentation:
* does not by default list all optional and keyword arguments, for which signature should be inspected.
* does not state argument types or return values, for which signature annotation should be inspected.

Names referenced in documentation are surrounded by symbols to identify the nature of the assigned object:

Name | Nature of assigned object
---- | -------------------------
+parameter_name+ | Parameter of documented function or method
++parameter_name++ | Parameter of class constructor method
-variable_name- | Variable local to code being documented
--attribute_name-- | Instance attribute
--method_name(args, kwargs)-- | Instance method. Only args / kwargs referred to in the 		subseqeunt documentation are noted. Signature should be inspected for full parameters
---classmethod_name()--- | Class method or static method
----global_constant_name---- | Global constant

## Issues

Please report any issues to the projects [issue page](https://github.com/maread99/pyroids/issues).

## Contact

[Marcus Read](mailto:marcusaread@gmail.com)