from flask import Flask, render_template
from kafka import KafkaConsumer
from threading import Thread
import json
import time
import socket


app = Flask(__name__)
leaders = {}

@app.route('/')
def dashboard():
    top25 = sorted(leaders.values(), key=lambda leader: leader['stars'], reverse=True)[:24]
    return render_template('dashboard.html', popular=top25)

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
            return KafkaConsumer('leaderboard',
                bootstrap_servers=server,
                value_deserializer=lambda m: json.loads(m.decode('ascii')))
        except:
            print "failed, retrying in 1s"
            time.sleep(1)


def consume(consumer):
    for message in consumer:
        for leader in message.value['leaders']:
            leaders[leader['repo']] = leader


if __name__ == "__main__":
    consumer = connect('kafka:9092')
    print "connected"
    thread = Thread(target=consume, args = (consumer,))
    thread.start()
    app.run(host="0.0.0.0", debug=True)
