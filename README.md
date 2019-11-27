# pyroids
Asteroids game with various weapons, expendable ammunition, supply drops and 
radiation exposure. 1 or 2 player. Highly customisable via configuration file...you 
make the game!

Installation

#TODO - REVIEW INSTALLATION SECTION

pyroids can be installed from PyPI
	pip install --upgrade pyroids --user

or from a source distribution
	python setup.py install --user

Requirements

pyroids requires Python 3.6+ (source code employs annotation syntax).

The only dependency is pyglet 1.4 which, if not otherwise available, will be 
installed by the pyroids installation process.

Play me

#TODO INCLUDE OPTION of 'pyroids' directly from the command line if the installed version will provide for executable via entry script...

The pyroids application can be launched directly from the command line or by 
the package's launch() function.

Command Line:

    $ python -m pyroids.play

To launch with settings as defined by a configuration file (see Game 
Customisation section), for example 'expert.py':

    $ python -m pyroids.play expert

Launch function:

    >>> import pyroids
    >>> pyroids.launch()

To launch with settings as defined by a configuration file (see Game 
Customisation section), for example 'novice.py':

    >>> pyroids.launch('novice')

Game Customisation

Settings that can be defined for each level include:
	Number of Asteroids
	Number of times each original asteroid will break up into smaller asteroids
	Number of smaller asteroids each asteroid breaks up into
	Asteroid speed
	Ship Speed
	Radiation field
	Radiation exposure limits
	Number of supply drops

Settings that can be defined for the duration of the application instance 
include:
	Ship Controls	
	Asteroid behaviour on reaching window border	
	Initial ammunition stocks per weapon
	Frequency and number of supply drops
	Min and Max ammunition stocks in each supply drop (per weapon)
	Cannon reload rate
	High Velocity Bullet speed
	Shield duration
	Number of Levels
	Number of Lives
	Window dimensions

Application settings can be customised by passing the name of a configuration 
file (see Play me section). If no configuration file is passed then the game 
will use default settings.

Configuration files should:
    be based on the template at pyroids\config.template.py
    be saved to the directory pyroids\config.
    have extension .py

See pyroids\config\template.py for instructions on setting up configuration 
files.

The following example configuration files are included as part of the pyroids 
package:
	novice.py
	expert.py

Aside from the configuration files, the ship and asteroid images can be 
changed with a little investigation of the source code and some minimal hacks.

Licensing

Code. As LICENSE.txt  (LINK TO github page holding LICENSE.txt)
Media. As \resources\README.md  (LINK TO github page holding resources README.md file!)

Code Documentation

Function/Method documention:
	does not by default list all optional and keyword arguments, for which 
		signature should be inspected.
	does not state argument types or return values, for which signature 
		annotation should be inspected.

When a variable is referenced in documentation, the name is enclosed with 
the following symbols to identify the variable's nature:
+parameter_name+   Parameter of documented function or method.
++parameter_name++   Parameter of class constructor method.
-variable_name-   Variable local to code being documented.
--attribute_name--   Instance attribute.
--method_name()--  Instance method.
	--method_name(args, kwargs)--  only args / kwargs referred to in the 
		subseqeunt documentation are noted. Signature should be inspected for 
		full parameters.
---classmethod_name()---   Class method or static method.
----global_constant_name----  Global constant.

Issues

Please report any issues to the projects issue page LINK TO https://github.com/maread99/pyroids/issues

Contact

[Marcus Read](mailto:marcusaread@gmail.com)