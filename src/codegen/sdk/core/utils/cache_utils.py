import functools
from collections.abc import Iterator
from typing import Callable, Generic, ParamSpec, TypeVar

from codegen.sdk.extensions.utils import lru_cache

ItemType = TypeVar("ItemType")
GenParamSpec = ParamSpec("GenParamSpec")


class LazyGeneratorCache(Generic[ItemType]):
    """A cache for a generator that is lazily evaluated."""

    _cache: list[ItemType]
    gen: Iterator[ItemType]

    def __init__(self, gen: Iterator[ItemType]):
        self._cache = []
        self.gen = gen

    def __iter__(self) -> Iterator[ItemType]:
        for item in self._cache:
            yield item

        for item in self.gen:
            self._cache.append(item)
            yield item


def cached_generator(maxsize: int = 16, typed: bool = False) -> Callable[[Callable[GenParamSpec, Iterator[ItemType]]], Callable[GenParamSpec, Iterator[ItemType]]]:
    """Decorator to cache the output of a generator function.

    The generator's output is fully consumed on the first call and stored as a list.
    Subsequent calls with the same arguments yield values from the cached list.
    """

    def decorator(func: Callable[GenParamSpec, Iterator[ItemType]]) -> Callable[GenParamSpec, Iterator[ItemType]]:
        @lru_cache(maxsize=maxsize, typed=typed)
        @functools.wraps(func)
        def wrapper(*args: GenParamSpec.args, **kwargs: GenParamSpec.kwargs) -> Iterator[ItemType]:
            return LazyGeneratorCache(func(*args, **kwargs))

        return wrapper

    return decorator
