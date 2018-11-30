# Atomica

[![Build Status](https://travis-ci.com/atomicateam/atomica.svg?branch=develop)](https://travis-ci.com/atomicateam/atomica)
[![Documentation Status](https://readthedocs.org/projects/atomica/badge/?version=latest)](https://atomica.readthedocs.io/en/latest/?badge=latest)

Atomica is a simulation engine for compartmental models. It can be used to simulate disease epidemics, health care cascades, and many other things.

Atomica is still under development; please check back regularly for updates.

# Installation

Atomica is available for Python 3 only. Because we develop using Python 3.7, it is possible that dictionary order is
relevant (although we endeavour to use ordered dictionaries via `Sciris` in places where order matters). Therefore, we
only _officially_ support Python 3.7, as this is the first Python release that guarantees ordering of all dictionaries.

### Git installation

Use the Git installation method if you plan to make changes to the Atomica source code. First, you will need a Python
environment containing the `numpy`, `scipy` and `matplotlib`. In theory these can be installed automatically as
dependencies for `atomica`, but in practice, these packages can require system-level setup so it is usually easiest
to install them separately beforehand.

We recommend installing via Anaconda, which facilitates getting the binaries and dependencies like QT installed in a
platform-agnostic manner. We also recommend working within an Anaconda environment.

You may also wish to install `mkl` first, before installing `numpy` etc. to improve performance. So for example:

```
conda install mkl
conda install numpy scipy matplotlib
```

Then, you can install Atomica into the environment using:

```
git clone https://github.com/atomicateam/atomica.git
cd atomica
python setup.py develop
```

You can test with:

```
cd atomica/tests
python testworkflow.py
```

# Troubleshooting

### Installation fails due to missing `numpy`

If running `python setup.py develop` in a new environment, `numpy` must be installed prior to `scipy`. In some cases,
installing `numpy` may fail due to missing compiler options. In that case, you may wish to install `numpy` via Anaconda
(by installing Python through Anaconda, and using `conda install numpy scipy matplotlib`). In general, our experience
has been that it is easier to set up the C binaries for `numpy` and the QT dependencies for `matplotlib` via Anaconda
rather than doing this via the system, which involves different steps on every platform.

# Frontend installation

Note that these instructions are slated to be moved to a different repository.

### Initial installation
* Complete the backend installation instructions above.
* Ensure `import atomica_apps` works from a Python interpreter in the terminal. If not: (a) check our paths, (b) install any modules that are missing (we will soon have a `requirements.txt` file that solves this problem).
* Ensure `redis` is installed: https://redis.io/topics/quickstart
* Ensure `node.js` is installed: https://nodejs.org/en/download/
* Ensure `npm` is installed: https://www.npmjs.com/get-npm
* Change into the clients folder: `cd atomica/clients`
* Install the JavaScript modules: `python install_client.py`

### Running
* To use e.g. the `cascade` client, change into the tool folder: `cd cascade` (aside from this step, all the steps below are identical for the `tb` client)
* Start the development client: `python dev_client.py`
* In the same folder in a **separate** terminal window, start the server: `python start_server.py`
* The client should now be running on `localhost:8080`, which you can go to in your browser (if it doesn't open your browser automatically).
* By default, you can log into the client using the username/password `demo`/`demo`.

### Notes
* To run optimizations, you will also need Celery: `./start_celery.sh` (Mac/Linux) or `start_celery.cmd` (Windows) in the tool folder.
* Instead of `python dev_client.py`, which immediately recompiles the client if it detects a change in the source files, you can also run `python build_client.py`, which will compile the client only once. You can then serve it on its "official" port via the usual `python start_server.py` (e.g. `localhost:8094` for `cascade`, as opposed to `localhost:8080` when the client is compiled with `python dev_client.py`).
* If additional Node.js modules have been added, you will need to rerun `python install_client.py` before building the client. This will usually be the case if and only if the build fails (i.e. `python dev_client.py` gives an error).
* If the server crashes, the most likely cause is an old project that can't be unpickled. Run `python reset_database.py` to remove broken projects.

### Other FE troubleshooting


#### Restarting `redis`

Sometimes it might be necessary to restart the `redis` process. This can be system dependent. On Mac OS, if `redis` was installed using `brew`, first install brew services

```
brew tap homebrew/services
```

Then you can do something like 

```
brew services restart redis
```

#### Resetting everything

If there are general node errors and you are _not_ doing local FE development, a very simple brute-force solution is to

```
cd atomica
rm -rf clients
git checkout clients
cd clients
npm install
```

# Code structure

## Overall structure

* The **backend** code (`atomica/atomica`) runs simulations and manages and graphs the results.
* The **frontend** code (`atomica/clients`) is written in JavaScript using the Vue.js framework, which is a web application framework that lets you create HTML-template-based dynamic GUI components.  The frontend communicates with the server (webapp and backend) using RPCs (remote procedure calls).  These are implemented via HTTP requests (through the axios library).
* The **webapp** code (`atomica/atomica_apps`) manages user sessions, accounts, and data (including backend projects) and interfaces the frontend with the backend code. It is written in Python and uses Flask for managing server requests, and Twisted for serving the application in a quasi-multi-threaded way.
* The **database** used by the webapp to store its database to store backend- and user-related objects is Redis. Redis uses a lightweight key/value storage method (as opposed to databases like Postgres that use SQL).
* The **graphs** in the backend are created with Matplotlib.  A library called mpld3 is used, both on the server and client (frontend), to convert the Matplotlib graphs to D3.js, which is a very widely used standard for web-based data visualization.

### Client structure

* The top-level of the client contains `cascade`, `tb`, and `node_modules`. The first two are the two GUIs currently supported by Atomica. The third contains all of the JavaScript libraries (installed via Node Package Manager, a.k.a. `npm`) that are used by the client (including, for example, Vue itself).
* Within the tool-specific folders (e.g. `cascade`), the **build** folder contains all of the scripts for compiling the JavaScript code. Similarly, the **config** folder contains the basic settings for the client (e.g., which server port it will run on). Both of these are highly standardized for JavaScript webapps and are not specific to Atomica.
* The **dist** folder is where the compiled files are stored -- it is this folder which is actually made visible when the user logs into the tool.
* The **src** folder contains all of the source materials that the build scripts use to create the app (i.e., the `dist` folder). The key subfolder is `components`, which is where all of the code (HTML+JavaScript) is stored. There is one file per screen in the tool (e.g. `OptimizationsPage.vue`), and this file contains both the HTML (layout) and JavaScript (functionality) for that page.
* Other subfolders in the `src` folder include `assets`, which includes CSS stylings; `router`, which handles links within the app; `services`, which contains functions that are used on more than one page (e.g., handling RPCs); and `store`, which contains data that are used on more than one page (e.g., project definitions).
* Finally, there is a **static** folder that contains all of the files that are required for the app, but are used "as-is" (i.e. do not need to be compiled): this includes fonts, images, and precompiled JavaScript libraries.
