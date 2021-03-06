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
    repos = []
    for partition in leaders.values():
        for repo in partition:
            repos.append(repo)
    top10 = sorted(repos, key=lambda repo: repo['stars'], reverse=True)[:10]
    return render_template('dashboard.html', popular=top10)

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
        leaders[message.value['partition']] = message.value['leaders']


if __name__ == "__main__":
    consumer = connect('kafka:9092')
    print "connected"
    thread = Thread(target=consume, args = (consumer,))
    thread.start()
    app.run(host="0.0.0.0", debug=True)
