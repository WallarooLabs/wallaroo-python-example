# Troubleshooting Guide

There are a few gotchas that you might run into. We've documented the ones we are aware of here and will update

## Kafka fails to start

Occasionally, there is a race between docker-compose services. Zookeeper is required before Kafka can run but takes awhile to initialize. You may need to run `docker-compose start kafka` again after starting the main services. Usually this isn't a problem but if this still doesn't fix the issue, I'd suggest stopping all services and rebuilding them. Calling `make clean` should do the job.

## Docker Compose Version Error

Some systems support installing docker-compose from a package repository. These are not always kept up to date with upstream releases. If you encounter this issue, you've likely been using an old installation. You can install the latest version by using the virtualenv target in the make file like so:

```bash
$ make env
$ . env/bin/activate
```

The activation script may vary by which shell you use. Once that is run, the proper docker-compose executable should be used by default.


## Wallaroo Applications Fail To Start, Issue with /tmp

When running a cluster, it's possible to get an unclean shutdown. The quickest way to fix this is to rebuild the containers with `make clean build`. Shutting down the containers properly in the future can be done with `make stop`. See the Makefile for equivalent docker-compose commands.
