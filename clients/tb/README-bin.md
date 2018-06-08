# Bin folder

This folder contains the executable files for various tasks. On Mac/Linux, files have executable permission, so you can just type `./the-file.py`; you don't need to type `python the-file.py` (although that works too).

## Setup scripts

* `install_client.py` installs the node modules; it's simply a link to `npm install` in the client folder.

* `build_client.py` builds the client; it's a link to `npm run build` in the client folder.

## Run scripts

* `start_server.py` starts the main server. Note, this will only work after `build_client.py` has been run.

## Other

* `reset_database.py` deletes all data from the database: all users, projects, blobs, etc.
