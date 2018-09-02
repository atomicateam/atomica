# Docker

Note: the Dockerfile is currently set to use the `develop` branch in Sciris. `git checkout develop` should be removed from the line immediately following `git clone https://github.com/optimamodel/sciris.git` if this is not desired. 

# Installation
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

To build (or rebuild) under docker-compose
~~~
sudo docker-compose build
~~~

To start the container(s) run
~~~
sudo docker-compose up
~~~

# Google Cloud rebuild triggers
At the moment, the platform is rebuilt whenever a push is made to `docker` or `develop` using the option `(docker|develop)`. 

You can see, and edit, these triggers in https://console.cloud.google.com/cloud-build/triggers

You can create new instances using 
https://console.cloud.google.com/compute/instancesAdd


# Useful functions
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
To delete all the docker containers and images
sudo docker system prune -a


# Helpful information

## This website was used for inspiration on Dockerizing celery
https://nickjanetakis.com/blog/dockerize-a-flask-celery-and-redis-application-with-docker-compose

## Docker Google Cloud
https://www.youtube.com/watch?v=WAPXaDpkytw

## Docker compose
https://www.youtube.com/watch?v=Qw9zlE3t8Ko


**Notes:**
The following information may or may not be useful in the 

~~~
sudo docker build --tag atomica:versionId .
~~~

The `.` represents the context of the dockerfile build. Don't forget it!

Use `-f DockerFile-cascade` as an option if not using the file called Dockerfile, e.g. using Dockerfile-cascade instead

sudo docker run -d atomica:versionId

-d daemonize
-p map ports 8080 to 8080
sudo docker run -d -p 8080:8080 atomica:versionId .

