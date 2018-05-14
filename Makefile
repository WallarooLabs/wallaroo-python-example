
.PHONY: default build tail clean start stop

default:
	@echo "Usage: make {tail|clean|start|stop}"

tail:
	-docker-compose logs -f --tail=10

clean: stop
	docker-compose rm -f

build:
	docker-compose build
	docker-compose up --no-start

start: build
	@# Give Zookeeper a head-start to avoid Kafka issues
	docker-compose start zookeeper
	@echo "Waiting for zookeeper to start"
	@sleep 4
	@# Start the rest of the services
	docker-compose start

stop:
	docker-compose stop

# For users without an up-to-date docker-compose
env:
	virtualenv env
	. env/bin/activate; \
		pip install docker-compose
	@touch env # mark the "target" as up to date
