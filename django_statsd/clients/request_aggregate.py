from statsd.client import StatsClient

try:
    from django.utils._threading_local import local
except ImportError:
    from threading import local

class AggregateStatsMixin(object):
    aggregate_request_stats = local()

    def timing(self, stat, delta, rate=1):
        super(self, AggregateStatsMixin).timing(stat, delta, rate)
        try:
            request = self.aggregate_request_stats.request
            request.stats_timings[stat] += duration
            request.stats_counts[stat] += 1
        except AttributeError:
            pass

class StatsClient(AggregateStatsMixin, StatsClient):
    pass
