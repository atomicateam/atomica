



## Logging cookbook

The Atomica logger is named `'atomica'`. At any point, from anywhere, you can retrieve it using

	import logging
	logger = getLogger('atomica')

### Changing the amount of output

Once you have the logger object (e.g. in your own script) you can change the logging level to control the amount of output displayed. The most common levels are

Level | Command
--- | ---
Show warnings or worse only | `logger.setLevel('WARNING')`
**Default** - Show normal output | `logger.setLevel('INFO')`
Show extra detailed output | `logger.setLevel('DEBUG')`

When writing code for Atomica, set the level of the message accordingly e.g. in the code you are writing, use

	logger.warning('This should be displayed as a warning')
	logger.info('This is information that the user will normally see')
	logger.debug('This is extra-verbose output')

Note that the use of `logger.debug` means that you do not need to set `verbose` flags and `if` statements - instead, just set the logging level to `debug`.

Note also that the default logging level is set in `atomica/__init__.py` so normally you should set the logging level in your script _after_ importing Atomica e.g.

	import atomica.ui as au
	logger.setLevel('DEBUG')

If you instead do

	logger.setLevel('DEBUG')
	import atomica.ui as au

then the logging level will be reset to `INFO` so you won't see debug messages.

### Dumping output to a log file

A common task is storing the log messages for a simulation run. This can be accomplished easily
through the logging module, by adding a file handler to the root logger. At the top of your script,
add the following snippet:

    import logging
    logger = logging.getLogger()
    h = logging.FileHandler('output.log',mode='w')
    logger.addHandler(h)

Then any messages logged by Atomica will be written to the specified file, in addition to being printed
in the console. If you run the commands above _before_ importing Atomica, then the version information
printed when Atomica is imported will be recorded as well (so it is recommended to initialize the
`FileHandler` at the start of your scripts).
