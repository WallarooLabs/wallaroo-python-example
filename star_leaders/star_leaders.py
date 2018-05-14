import simplejson
from datetime import datetime
import wallaroo
from repo_partitioner import RepoPartitioner
from repo_metadata import RepoMetadata

# Make this available to the state computation so
# we can tag leaders result with the partition.
REPO_PARTITIONER = RepoPartitioner()

def application_setup(args):
    """
    This is our application's entry point. We read in our
    command line arguments and describe our processing
    pipeline. We return a representation of that pipeline which
    is then started up my the Wallaroo runtime. Keep in mind
    that this application setup is run both on the primary
    worker as well as any secondary workers that you add to the
    cluster.
    """
    source_config = wallaroo.kafka_parse_source_options(args) + (decoder,)
    source = wallaroo.KafkaSourceConfig(*source_config)
    sink_config = wallaroo.kafka_parse_sink_options(args) + (encoder,)
    sink = wallaroo.KafkaSinkConfig(*sink_config)

    ab = wallaroo.ApplicationBuilder("GitHub Star Leaders")

    ab.new_pipeline("star count leaders", source)
    ab.to(filter_interesting_events)
    ab.to_state_partition(
        annotate_repos, RepoMetadata, "repo_metadata",
        REPO_PARTITIONER, REPO_PARTITIONER.partitions)
    ab.to_sink(sink)

    return ab.build()


@wallaroo.computation(name="filter interesting events")
def filter_interesting_events(event):
    """
    There are many event types. We only want ot process a subset,
    so we'll filter these out first.
    """
    if event['type'] in ['ForkEvent', 'PullRequestEvent', 'WatchEvent']:
        return event


@wallaroo.state_computation(name="count stars")
def annotate_repos(event, state):
    """
    Look at the event type and perform the expected annotation
    on our repository state.
    """
    time = datetime.strptime(event['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    state.set_current_hour(time.hour)
    repo = event['repo']['name']
    if event['type'] == 'WatchEvent':
        return calculate_leaders(event, state)
    elif state.is_leader(repo):
        # We only store this extra data on popular repos to avoid caching all
        # events in memory, which can total to many GBs.
        state.annotate_with_event(repo, event)
        return (None, True)
    else:
        # Wallaroo expects us to return a tuple here rather than just None.
        # False signifies that we haven't changed our state at all, so there
        # is nothing to checkpoint when running in resilient mode.
        return (None, False)


def calculate_leaders(event, state):
    """
    We recalculate the leaderboard after adding our new star
    event to our running tally. If we have a change in the
    leaders, we publish a new event.
    """
    repo = event['repo']['name']
    state.add_star(repo)
    changed = state.changed_leaders(top=10)
    part = REPO_PARTITIONER.partition(event)
    if changed:
        return ({"leaders": changed, "partition": part}, True)
    else:
        return (None, True)


@wallaroo.decoder(header_length=4, length_fmt=">I")
def decoder(data):
    """
    We're using JSON for our Kafka events. The decoder
    annotation above is currently required to be present,
    even if Kafka messages are already framed. It doesn't
    affect the contents of the Kafka messages. This
    requirement may change in the future to avoid confusion.
    """
    data = simplejson.loads(data)
    return data


@wallaroo.encoder
def encoder(data):
    """
    We're encoding our output as JSON. We currently leave the
    key as None here. If we wanted to make use of compaction
    in Kafka we could label the data here.
    """
    return (simplejson.dumps(data), None)
