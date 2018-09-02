#!/usr/bin/env python

print('Attempting to start the celery bash script (from python)')
import subprocess
subprocess.Popen(['source', 'start_celery.sh'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Run the server
import atomica_apps
atomica_apps.main.run(which='cascade')