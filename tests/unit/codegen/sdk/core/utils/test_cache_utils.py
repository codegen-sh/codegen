from threading import Event

from codegen.sdk.core.utils.cache_utils import cached_generator


def test_cached_generator():
    event = Event()

    @cached_generator()
    def cached_function():
        assert not event.is_set()
        event.set()
        yield from range(10)

    # First call
    result = cached_function()
    assert list(result) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Second call
    result = cached_function()
    assert list(result) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
