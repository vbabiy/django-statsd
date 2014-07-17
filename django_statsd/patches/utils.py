import time
from django_statsd.clients import statsd
from functools import partial, wraps
from django_statsd.middleware import thread_locals


def wrapped(method, stat_name, *args, **kwargs):
    start = time.time()
    result = method(*args, **kwargs)
    duration = int((time.time() - start) * 1000)
    statsd.timing(stat_name, duration)

    try:
        request = thread_locals.request
        request.stats_timings["request.{}".format(stat_name)] += duration
        request.stats_counts["request.{}".format(stat_name)] += 1
    except AttributeError:
        pass

    return result


def wrap(method, key, *args, **kw):
    return partial(wrapped, method, key, *args, **kw)
