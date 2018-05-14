import operator

class RepoMetadata(object):
    """
    This class is responsible for keeping tally of things
    like stars on a repo and recent events for the most
    popular repos.
    """

    def __init__(self):
        self.current_hour = None
        self.window = []
        self.repos = {}
        self.leaders = []
        self._window_cache = {}

    def set_current_hour(self, hour):
        """
        In order to keep a limited window of data, we need to
        group events into buckets and then remove the oldest
        bucket when we move beyond our window size. This
        method will check the current hour of the data we're
        processing to determine if we're ready to roll over the
        active bucket.
        """
        if self.current_hour != hour:
            self.window.append(self.repos)
            self._recalc_window_cache()
            self.repos = {}
            self.current_hour = hour
            self._trim_window()

    def add_star(self, name):
        """
        Keep a counter on all repositories to track which
        ones are popular. One call = one star event.
        """
        self._get_repo(name)['stars'] += 1

    def annotate_with_event(self, name, event):
        """
        Add an event to our current repo metadata. We keep at
        most 3 events to minimize size of the data stored.
        Trimming the event data to remove some of the fields
        may help keep the total size of the messages we publish
        to Kafka down.
        """
        events = self._get_repo(name)['events']
        events.append(event)
        if len(events) > 3:
            self._get_repo(name)['events'] = events[-3:]

    def changed_leaders(self, top):
        """
        Calculate our current leading repos by star count
        and return accumulated metadata if any have changed.
        If leaders have not changed since last run, return None.
        """
        stars = self._accumulate_stars()
        leaders = sorted(stars.iteritems(), key=operator.itemgetter(1), reverse=True)[:top]
        if self.leaders != leaders:
            self.leaders = leaders
            return [
                {
                    'repo': name,
                    'stars': stars,
                    'recent_events': self._get_repo(name)['events']
                }
                for (name, stars) in leaders
            ]

    def is_leader(self, name):
        """
        Check if our calculated leaderboard includes the given
        repo name or not. We could probably optimize the dict
        construct by storing it that way but it's nice to
        preserve ordering for output as well. We'll opt to keep
        it simple until we need to speed this up.
        """
        return name in dict(self.leaders)

    def _accumulate_stars(self):
        """
        Add together our running totals using the cache and
        our current repos bucket.
        """
        star_count = {}
        for repo in self.repos:
            star_count[repo] = self.repos[repo]['stars']
        for repo in self._window_cache:
            star_count[repo] = star_count.get(repo, 0) + self._window_cache[repo]['stars']
        return star_count

    def _default_repo(self):
        """
        When we need to record something new for a repository
        we expect it to already have a couple fields
        initialized. This could be moved to a class but we're
        keeping it simple for now and using a dict.
        """
        return {
            "stars": 0,
            "events": []
        }

    def _get_repo(self, name):
        """
        We need to dynamically populate our repo dictionary
        with a default repository. This acts as a simple
        accessor which will create a new dictionary for any
        missing repository.
        """
        if not name in self.repos:
            self.repos[name] = self._default_repo()
        return self.repos[name]

    def _recalc_window_cache(self):
        """
        To avoid summing all stars over each bucket every
        time we calculate the leaderboard, we keep a cache
        of the counts for all but our active bucket. This
        cuts down on the number of redundant iterations over
        our metadata for each star event.
        """
        cache = {}
        for hour in self.window:
            for repo in hour:
                data = hour[repo]
                cached = cache.get(repo)
                if cached:
                    cached['stars'] += data['stars']
                else:
                    cache[repo] = data
        self._window_cache = cache

    def _trim_window(self):
        """
        Trim our data if we have more than 23 hours of
        data plus our current hour. We could probably
        make this more fine-grained but it serves our
        needs well enough for now.
        """
        if len(self.window) > 23:
            self.window = self.window[-23:]
            self._recalc_window_cache()
