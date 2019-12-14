from functools import partial
import time
from threading import Thread


class memoize:
    def __init__(self, timeout=0):
        self.cache = {}
        self.timeout = timeout

    def _flush(self, f, *args, **kwargs):
        now = time.time()
        for key,(ret,t) in list(self.cache.items()):
            if self.timeout and now - t > self.timeout:
                self.delete_entry(key, f, *args, **kwargs)

    def __call__(self, f):
        def func(*args, **kwargs):
            self._flush(f, *args, **kwargs)
            key = args, frozenset(kwargs.items())
            if key not in self.cache:
                r = f(*args,**kwargs)
                self.add_entry(key, r)
            ret,t = self.cache[key]
            return ret
        return func

    def add_entry(self, key, r):
        self.cache[key] = r, time.time()

    def delete_entry(self, key, f, *args, **kwargs):
        del self.cache[key]


class threaded_memoize(memoize):
    def delete_entry(self, key, f, *args, **kwargs):
        t = Thread(target=partial(self.post_run, f, *args, **kwargs))
        t.daemon = True
        t.start()

    def post_run(self, f, *args, **kwargs):
        key = args, frozenset(kwargs.items())
        r = f(*args,**kwargs)
        self.add_entry(key, r)
