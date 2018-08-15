# Code structure

## Overall structure

* The **backend** code (`atomica/atomica`) runs simulations and manages and graphs the results.
* The **frontend** code (`atomica/clients`) is written in JavaScript using the Vue.js framework, which is a web application framework that lets you create HTML-template-based dynamic GUI components.  The frontend communicates with the server (webapp and backend) using RPCs (remote procedure calls).  These are implemented via HTTP requests (through the axios library).
* The **webapp** code (`atomica/atomica_apps`) manages user sessions, accounts, and data (including backend projects) and interfaces the frontend with the backend code. It is written in Python and uses Flask for managing server requests, and Twisted for serving the application in a quasi-multi-threaded way.
* The **database** used by the webapp to store its database to store backend- and user-related objects is Redis. Redis uses a lightweight key/value storage method (as opposed to databases like Postgres that use SQL).
* The **graphs** in the backend are created with Matplotlib.  A library called mpld3 is used, both on the server and client (frontend), to convert the Matplotlib graphs to D3.js, which is a very widely used standard for web-based data visualization.

### Client structure

* The top-level of the client contains `cascade`, `tb`, and `node_modules`. The first two are the two GUIs currently supported by Atomica. The third contains all of the JavaScript libraries (installed via Node Package Manager, a.k.a. `npm`) that are used by the client (including, for example, Vue itself).
* Within the tool-specific folders (e.g. `cascade`), the **build** folder contains all of the scripts for compiling the JavaScript code. Similarly, the **config** folder contains the basic settings for the client (e.g., which server port it will run on). Both of these are highly standardized and not specific to Atomica.
* The **dist** folder is where the compiled files are stored -- it is this folder which is actually made visible when the user logs into the tool.
* The **src** folder contains all of the source materials that the build scripts use to create the app (i.e., the `dist` folder). The key subfolder is `components`, which is where all of the code (HTML+JavaScript) is stored. There is one file per screen in the tool (e.g. `OptimizationsPage.vue`), and this file contains both the HTML (layout) and JavaScript (functionality) for that page.
* Other subfolders in the `src` folder include `assets`, which includes CSS stylings; `router`, which handles links within the app; `services`, which contains functions that are used on more than one page (e.g., handling RPCs); and `store`, which contains data that are used on more than one page (e.g., project definitions).
* Finally, there is a **static** folder that contains all of the files that are required for the app, but are used "as-is" (i.e. do not need to be compiled): this includes fonts, images, and external JavaScript libraries.
