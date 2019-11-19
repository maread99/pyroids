# pyroids
Asteroidsesque game with various weapons, expendable ammunition, supply drops and 
radiation exposure. 1 or 2 player. Highly customisable via configuration file...you 
make the game!

TODO
	Reference instructions. NB how to pause game...or in game instructions sufficient?
	Include note on ease to hack the images, particularly the ships and asteroid images.
	INSTALLATION instructions
	
	MarkUp as applic, using reStructuredText or MarkDown (probably former, and save 
		README as .rst)


#TODO include where to report bugs

Play me
#TODO instructions to play game



#INCOPR FOLLOWING AS APPLIC...Use included configuration file as example:
Takes optional single argument as filename of a configuration file in 
..pyroids\config.  Configuration file should be based on 
..pyroids\config\template.py. If no configuration file is passed then 
game will use default settings.


Game Customisation

Settings that can be defined for each level include:
	Number of Asteroids
	Number of times each original asteroid will break up into smaller asteroids
	Number of smaller asteroids each asteroid will break up into when hit
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
	Min and Max ammunition stocks in each supply drop, per weapon
	Cannon reload rate
	High Velocity Bullet speed
	Shield duration
	Number of Levels
	Number of Lives
	Window dimensions
	
####REVIEW / REVISE...
Game can be customised by defining a configuration file and passing the 
filename as the first and only argument at the command line.

A configuration file can be created by making a copy of the template at
..\pyroids\config\template.py. The copy should be named appropriately and saved 
as a .py file to the same config folder, for example:
	..\pyroids\config\easy_peasy.py

The template includes instructions on how to customise game settings.

Only the name of the configuration file needs to be passed at the command 
line, for example:
###REVIEW FOR ACTUAL IMPLEMENTATION
python play_pyroids easy_peasy.py

As many configuration files can be saved to the config directory as required. 
The pyroids package includes the following configuration files:
##REVISE FOR ACTUAL IMPLEMENTATION
easy_peasy.py
bit_hard.py
wtf.py
wrap.py
alt_controls.py


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