from statsd.client import StatsClient

try:
    from django.utils._threading_local import local
except ImportError:
    from threading import local

class StatsClient(StatsClient):
    aggregate_stats_per_request = True
    thread_locals = local()

    def timing(self, stat, delta, rate=1):
        super(self, StatsClient).timing(stat, delta, rate)
        try:
            request = thread_locals.request
            request.stats_timings[stat] += duration
            request.stats_counts[stat] += 1
        except AttributeError:
            pass
