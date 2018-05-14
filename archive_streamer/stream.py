from kafka import KafkaProducer
import requests

import gzip
# required since we aren't using Python 3 to decompress in-memory gzip data
from StringIO import StringIO

import calendar
from datetime import datetime
import json
import time
import sys


class Pacer(object):
    """
    Run archived recorded data through relative to realtime speeds
    given a timestamp. The speed up allows one to run faster than
    real-time. If a speed_up of 1 is passed, time will run at real-
    time (aka wall clock speed). If a time less than 1 is passed,
    it will run slower than real-time and greater than 1 will run
    it faster than real-time.
    """

    __slots__ = ['speed_up', '_start_time', '_start_period']

    def __init__(self, speed_up=1):
        self.speed_up = speed_up
        self._start_time = None
        self._start_period = None

    def pace(self, timestamp):
        """
        Delay a program till a given amount of time has passed based
        on the timestamp passed relative to the time this was first
        called and the speed up factor specified when constructing the
        Pacer.
        """
        epoch = self._timestamp_to_epoch(timestamp)
        if self._start_time is None:
            self._start_time = time.time()
            self._start_period = epoch
            return
        elapsed = time.time() - self._start_time
        target = self._start_period + (elapsed * self.speed_up)
        if epoch > target:
            time.sleep(epoch - target)

    # NB:
    # I'm sure there's a nicer way to do this but this seems
    # to work with Python 2.7's standard library and is good
    # enough for this application.
    def _timestamp_to_epoch(self, timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return calendar.timegm(dt.timetuple())


def gunzip(data):
    """
    Since we are writing Python 2.7 compatible code here, we
    should use StringIO to decompress in-memory data without
    writing out to disk.
    """
    stream = StringIO(data)
    with gzip.GzipFile(fileobj=stream, mode='rb') as gz:
        return gz.read()


def download(year, month, day, hour):
    """
    Download a compressed collection of JSON events from the
    github archive project on demand.
    """
    url = (
        "http://data.gharchive.org/%d-%02d-%02d-%d.json.gz" %
        (year, month, day, hour))
    resp = requests.get(url)
    entries = gunzip(resp.content)
    for entry in entries.splitlines():
        yield entry, json.loads(entry)


def range_from_time(year, month, day, hour):
    """
    Generate an unending sequence of year-month-day-hour
    tuples we can used for fetching our data. The given
    start time should be no earlier than 2015 given changes
    in the event data may not be compatible with our code.
    """
    while True:
        last_day = calendar.monthrange(year, month)[1]
        if hour > 23:
            hour = 0
            day += 1
        if day > last_day:
            day = 1
            month += 1
        if month > 12:
            month = 1
            year += 1
        yield (year, month, day, hour)
        hour += 1


def connect(server):
    """
    This utility function retries our connection logic. It's
    not meant for production applications but can be handy
    when developing against a docker-compose setup where boot
    time may be somewhat asynchronous.
    """
    while True:
        print("attempting to connecting to " + repr(server))
        try:
            return KafkaProducer(bootstrap_servers=server)
        except:
            print "failed, retrying in 1s"
            time.sleep(1)


def stream_to_kafka(start, speed, topic, broker):
    """
    This is our effective entry-point. For this application we're
    only interested in streaming past data for demonstration purposes.
    There are many other ways to get data into Kafka for processing
    and this one was built for demonstration purposes.
    """
    count = 0
    errors = 0
    pacer = Pacer(speed)
    producer = connect(broker)
    for period in range_from_time(*start):
        print("streaming from github archive %d-%02d-%02d %dh" % period)
        for json, data in download(*period):
            pacer.pace(data['created_at'])
            try:
                key = bytes(data['repo']['name'])
                producer.send(topic, key=key, value=json)
                count += 1
                if count % 100 == 0:
                    sys.stdout.write('.')
                if count % 2000 == 0:
                    # So we can see the output in docker-compose
                    sys.stdout.write('\n')
            except:
                # Ignore bad writes for now since it's just a
                # demonstration.
                errors += 1
                if errors % 100 == 0:
                    sys.stdout.write('x')
                pass
            sys.stdout.flush()
        print("published %d events" % count)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Kafka publisher for GHArchive.')
    parser.add_argument('--speedup',
        dest='speed_up', default=10,
        help='set the speed of the import, 1 = wall-clock speed'
    )
    parser.add_argument('--kafka',
        dest='broker', default='localhost:9092',
        help='set the address of the bootstrap kafka broker'
    )
    parser.add_argument('--topic',
        dest='topic', default='gharchive',
        help='set the kafka topic to write the github events to'
    )
    args = parser.parse_args()
    stream_to_kafka(
        # This start can be set anywhere back as far as 2015
        start=(2018, 2, 1, 0),
        speed=float(args.speed_up),
        topic=args.topic,
        broker=args.broker
    )
