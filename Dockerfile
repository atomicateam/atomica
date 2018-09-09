FROM continuumio/anaconda:latest
ADD . /app
WORKDIR /app

ARG WHICH
ARG PORT
ARG REDIS_URL
ENV PORT $PORT
ENV REDIS_URL $REDIS_URL

# Set up apt-get
RUN apt-get update -qq && apt-get install -yqq gnupg curl libgl1-mesa-glx gcc supervisor

# Install nodejs
RUN curl -sL https://deb.nodesource.com/setup_9.x | bash
RUN apt-get install -yqq nodejs
RUN apt-get clean -y

# Install sciris
RUN git clone https://github.com/optimamodel/sciris.git
RUN cd sciris && python setup.py develop && python setup-web.py develop 

# Install mpld3
RUN git clone https://github.com/optimamodel/mpld3.git
RUN cd mpld3 && python setup.py submodule && python setup.py install

# Install atomica
RUN python setup.py develop

# Install clients common
WORKDIR clients
RUN python install_client.py

# Install app
WORKDIR ${WHICH}
RUN python build_client.py

# CMD python start_server.py
CMD PORT=80 supervisord 
