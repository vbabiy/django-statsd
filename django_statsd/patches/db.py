from functools import wraps
import django
from django.db.backends import util
import time
from django_statsd.middleware import thread_locals
from django_statsd.patches.utils import wrap
from django_statsd.clients import statsd


def key(db, attr):
    return 'db.%s.%s.%s' % (db.client.executable_name, db.alias, attr)


def pre_django_1_6_cursorwrapper_getattr(self, attr):
    """
    The CursorWrapper is a pretty small wrapper around the cursor.
    If you are NOT in debug mode, this is the wrapper that's used.
    Sadly if it's in debug mode, we get a different wrapper.
    """
    if self.db.is_managed():
        self.db.set_dirty()
    if attr in self.__dict__:
        return self.__dict__[attr]
    else:
        if attr in ['execute', 'executemany', 'callproc']:
            return wrap(getattr(self.cursor, attr), key(self.db, attr))
        return getattr(self.cursor, attr)


def patched_timing(name):
    def outer(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            stat_name = key(self.db, name)
            start = time.time()

            result = func(self, *args, **kwargs)

            duration = int((time.time() - start) * 1000)
            statsd.timing(stat_name, duration)

            try:
                request = thread_locals.request
                request.stats_timings["request.{}".format(stat_name)] += duration
                request.stats_counts["request.{}".format(stat_name)] += 1
            except AttributeError:
                pass

            return result
        return wrapper
    return outer


def patch():
    """
    The CursorWrapper is a pretty small wrapper around the cursor.  If
    you are NOT in debug mode, this is the wrapper that's used.  Sadly
    if it's in debug mode, we get a different wrapper for version
    earlier than 1.6.
    """

    if django.VERSION > (1, 6):
        # In 1.6+ util.CursorDebugWrapper just makes calls to CursorWrapper
        # As such, we only need to instrument CursorWrapper.
        # Instrumenting both will result in duplicated metrics
        util.CursorWrapper.execute = patched_timing("execute")(
            util.CursorWrapper.execute)
        util.CursorWrapper.executemany = patched_timing("executemany")(
            util.CursorWrapper.executemany)
        util.CursorWrapper.callproc = patched_timing("callproc")(
            util.CursorWrapper.callproc)

    else:
        util.CursorWrapper.__getattr__ = pre_django_1_6_cursorwrapper_getattr
        util.CursorDebugWrapper.execute = patched_timing("execute")(
            util.CursorWrapper.execute)
        util.CursorDebugWrapper.executemany = patched_timing("executemany")(
            util.CursorWrapper.executemany)