#!/usr/bin/env python

# Imports
import sys
import atomica_apps.apptasks_cascade as at

# If running on Windows, use eventlets
if 'win' in sys.platform: args = [__file__, '-l', 'info', '-P', 'eventlet']
else:                     args = [__file__, '-l', 'info']

# Run Celery
at.celery_instance.worker_main(args)