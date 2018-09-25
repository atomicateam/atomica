# Introduction

This explains how to set up the Cascade Analysis Tools client.

# Setting up the client

1. Ensure you have the Atomica and Sciris (sold separately) Python packages installed.

2. Change to this folder (you found it!).

3. Type `python install_client.py`. This will install the JavaScript node.js modules.

4. Type `python start_server.py`. This starts the Twisted/Flask server.

4a. If you want to run in "dev mode" (which auto-refreshes the webapp on changes), in a separate terminal, type `python dev_client.py`. This will serve the webapp on port 8080.

4b. If you want to run in "build mode" (which does not auto-refresh the webapp), in a separate terminal, type `python build_client.py`. This will serve the webapp on port 8094. Once the build is finished you can close the terminal.

# Troubleshooting

If you get weird server errors, you might want to reset the database. Use `python reset_database.py` for this. This will delete all data in the Cascade Tool database.