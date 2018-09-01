# Docker

## Important changes for the future
Note that the #develop refers to the develop branch. In the future, it is likely that we will instead be using the master branch, in which case we should remove the #develop
RUN git clone https://github.com/optimamodel/sciris.git#develop

## Installation of docker
https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce-1

## Installation of docker-compose
https://docs.docker.com/compose/install/
The installation command should look something like this
~~~
sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose
~~~

## Running locally
If you are running redis on your machine, you may have to stop it

~~~
/etc/init.d/redis-server stop
~~~
You can start it again later with 
~~~
/etc/init.d/redis-server start
~~~

Navigate to the atomica directory

~~~
sudo docker build --tag atomica:versionId .
~~~

The `.` represents the context of the dockerfile build. Don't forget it!

Use `-f DockerFile-cascade` as an option if not using the file called Dockerfile, e.g. using Dockerfile-cascade instead

To build (or rebuild) under docker-compose
~~~
sudo docker-compose build
~~~

To start the container(s) run
~~~
sudo docker-compose up
~~~

sudo docker run -d atomica:versionId


-d daemonize
-p map ports 8080 to 8080
sudo docker run -d -p 8080:8080 atomica:versionId .

## Useful functions
To see logs use 
~~~
sudo docker logs containerId
~~~

To see images use 
~~~
sudo docker images
~~~

To see running containers use 
~~~
sudo docker ps
~~~

To kill containers use 
~~~
sudo docker kill containerId
~~~

## Development triggers
At the moment, the platform is rebuilt whenever a push is made to `docker` or `develop` using the option `(docker|develop)`. 

You can see, and edit, these triggers in https://console.cloud.google.com/cloud-build/triggers.

You can create new instances using 
https://console.cloud.google.com/compute/instancesAdd



## Good videos
Docker Google Cloud
https://www.youtube.com/watch?v=WAPXaDpkytw

Docker compose up
https://www.youtube.com/watch?v=Qw9zlE3t8Ko
