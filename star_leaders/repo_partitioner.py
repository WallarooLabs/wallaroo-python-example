from hash_ring import HashRing

class RepoPartitioner(object):
    """
    This partitioner uses the hash_ring library to
    select a given partition key, in this case, a
    list of numbers from 0 up to but not including
    `size`. We hash the repository name to arrive
    at the proper partition. We don't currently
    change the partition count or weights here.
    Future versions of Wallaroo will support more
    advanced native partitioning capabilities so
    this may no longer be needed.
    """

    def __init__(self, size = 10):
        self.partitions = list(xrange(0, size))
        self.ring = HashRing(self.partitions)

    def partition(self, event):
        return self.ring.get_node(event['repo']['name'])
