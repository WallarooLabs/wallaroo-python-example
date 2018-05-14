# Example Wallaroo Application with Python and Kafka

This application is meant to serve as an example of how to hook things into a more complete system (using Kafka) with containers. It can serve as a starting point for those developing new Wallaroo applications from scratch. The hope is that this removes some of the guesswork that goes into developing streaming applications.

The general mechanism for running this is all driven by docker-compose. This repository includes a Makefile for running specific docker-compose commands as well as setting up a virtualenv installation if you don't have the latest docker-compose version available on your host machine (see `make env`).

Much of the application itself is explained [this blog post](TODO). As Wallaroo us updated, we'll update this repository to work with the latest release as we refine our Python API and integration.

All works in this repository are available in the public domain, unless otherwise noted in the source file.

