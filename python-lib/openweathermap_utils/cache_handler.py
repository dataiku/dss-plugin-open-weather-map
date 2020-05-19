from diskcache import Cache


class CacheHandler(Cache):
    def __init__(self, *args, **kwargs):
        self._enabled = kwargs.get('enabled', True)

        if self._enabled:
            super(CacheHandler, self).__init__(*args, **kwargs)

    def set(self, *args, **kwargs):
        return super(CacheHandler, self).set(*args, **kwargs) if self._enabled else True

    __setitem__ = set

    def __exit__(self, *args):
        if self._enabled:
            super(CacheHandler, self).__exit__(*args)

    def __contains__(self, key):
        return super(CacheHandler, self).__contains__(key) if self._enabled else False

    def __getitem__(self, key):
        if self._enabled:
            return super(CacheHandler, self).__getitem__(key)
        raise KeyError(key)

    def __enter__(self):
        return super(CacheHandler, self).__enter__() if self._enabled else self
