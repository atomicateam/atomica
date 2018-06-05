#!/usr/bin/env python

'''
Small script to reset the user database -- WARNING, deletes everything!!!

Version: 2018jun04
'''

import sciris.web as sw
import nutrition as on
import os

webapp_dir = os.path.abspath(on.webapp.config.CLIENT_DIR)
redis_url = on.webapp.config.REDIS_URL
prompt = 'Are you sure you want to reset the database for the following?\n  %s\n  %s\nAnswer (y/[n]): ' % (webapp_dir, redis_url)
answer = raw_input(prompt)
if answer == 'y':
	theDataStore = sw.DataStore(redis_db_URL=redis_url)
	theDataStore.delete_all()
	print('Database reset.')
else:
	print('Database not reset.')