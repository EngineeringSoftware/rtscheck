# docker build -t rtscheck .

# Pull base image
FROM ubuntu:16.04

# Install sofware properties common
RUN \
  apt-get update && \
  apt-get install -y software-properties-common

# Install oracleJDK8
RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer

# Use oracleJDK8 as default
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

# Verify java version
RUN java -version

# Install Maven 3.3.9
RUN \
  add-apt-repository universe && \
  apt-get update && \
  apt-get install -y maven && \
  mvn --version

# Install git
RUN \
  apt-get install -y git && \
  git --version

# Install python3
RUN \
  apt-get update && \
  apt-get install -y python3 python3-dev python3-pip python3-virtualenv


# Install pandas
RUN \
  pip3 install pandas

# Install matplotlib
RUN \
  pip3 install matplotlib

# Install zip
RUN \
  apt-get install -y zip && \
  rm -rf /var/lib/apt/lists/*

# Install sudo
RUN \
  apt-get update && \
  apt-get install -y sudo

# Install perl
RUN \
  apt-get update && \
  apt-get install -y perl && \
  perl -MCPAN -e 'install Bundle::DBI'

# Install some text editors
RUN \
  apt-get update && \
  apt-get install -y emacs vim && \
  rm -rf /var/lib/apt/lists/*

# Add new user
RUN useradd -ms /bin/bash -c "RTSCheck User" rtscheck && echo "rtscheck:docker" | chpasswd && adduser rtscheck sudo
USER rtscheck
WORKDIR /home/rtscheck/

# Configure git for new user
RUN git config --global user.email "rtscheck@email.com" && git config --global user.name "rtscheck"

# Set up working environment
COPY --chown=rtscheck:rtscheck . /home/rtscheck/
ENTRYPOINT /bin/bash
