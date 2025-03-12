from threading import Event

import pytest

from codegen.sdk.extensions.utils import lru_cache, uncache_all


def test_lru_cache_with_uncache_all():
    event = Event()

    @lru_cache
    def cached_function():
        assert not event.is_set()
        event.set()
        return 42

    assert cached_function() == 42
    assert cached_function() == 42

    uncache_all()

    with pytest.raises(AssertionError):
        cached_function()


def test_lru_cache_args_with_uncache_all():
    event = [Event() for _ in range(2)]

    @lru_cache(maxsize=2)
    def cached_function(a):
        assert not event[a].is_set()
        event[a].set()
        return a

    for _ in range(2):
        for idx in range(2):
            assert cached_function(idx) == idx

    uncache_all()

    for idx in range(2):
        with pytest.raises(AssertionError):
            cached_function(idx)
