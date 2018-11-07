# Logging to a file

A common task is storing the log messages for a simulation run. This can be accomplished easily
through the logging module, by adding a file handler to the root logger. At the top of your script,
add the following snippet:

```
import logging
logger = logging.getLogger()
h = logging.FileHandler('output.log',mode='w')
logger.addHandler(h)
```

Then any messages logged by Atomica will be written to the specified file, in addition to being printed
in the console. If you run the commands above _before_ importing Atomica, then the version information
printed when Atomica is imported will be recorded as well (so it is recommended to initialize the
`FileHandler` at the start of your scripts).