import functools
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, Union, overload

import wrapt

from codegen.sdk.core.autocommit.constants import AutoCommitState, OutdatedNodeError, enabled

P = ParamSpec("P")
T = TypeVar("T")


def is_outdated(c) -> bool:
    from codegen.sdk.core.interfaces.editable import Editable

    if isinstance(c, Editable):
        return c.is_outdated
    if isinstance(c, list):
        return any(is_outdated(i) for i in c)
    return False


@overload
def reader(wrapped: Callable[P, T]) -> Callable[P, T]: ...


@overload
def reader(wrapped: None = None, *, cache: bool | None = ...) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def reader(wrapped: Callable[P, T] | None = None, *, cache: bool | None = None) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Indicates this method is a read

    Args:
    ----
        cache (bool): Whether to cache the result of the function. By default enabled for functions without arguments

    """
    if wrapped is None:
        return functools.partial(reader, cache=cache)

    @wrapt.decorator(enabled=enabled)
    def wrapper(wrapped: Callable[P, T], instance: Union["Editable", None] = None, args: P.args = None, kwargs: P.kwargs = None) -> T:
        """Indicates this method is a reader and should be updated if there are any pending changes."""
        num_args = len(args) + len(kwargs)
        if instance is None:
            instance = args[0]
            num_args -= 1
        name = wrapped.__name__
        autocommit = instance.ctx._autocommit
        should_cache = cache

        def run_func():
            if should_cache and not instance.is_outdated:
                if cached := instance.autocommit_cache.get(name, None):
                    if not is_outdated(cached):
                        return cached
            ret = wrapped(*args, **kwargs)
            if should_cache:
                if is_outdated(ret):
                    raise OutdatedNodeError(instance)
                instance.autocommit_cache[name] = ret
            return ret

        if autocommit.state in (AutoCommitState.Special, AutoCommitState.Committing):
            return run_func()
        if num_args > 0:
            if cache:
                raise NotImplementedError("Cache doesn't support functions with arguments")
            should_cache = False
        elif cache is None:
            should_cache = True
        to_unlock = autocommit.try_lock_files({instance.filepath})
        old_state = autocommit.enter_state(AutoCommitState.Read)
        # logger.debug("Reading node %r, %r", instance, wrapped)
        try:
            autocommit.check_update(instance, lock=to_unlock, must_be_updated=False)
            ret = run_func()
        finally:
            autocommit.state = old_state
            autocommit.unlock_files(to_unlock)
        return ret

    wrapped._reader = True
    return wrapper(wrapped)


class AutoCommitMixin:
    """Support for autocommit"""

    _generation: int
    autocommit_cache: dict[str, Any]
    removed: bool = False

    def __init__(self, codebase_context: "CodebaseContext"):
        self._generation = codebase_context.generation
        self.autocommit_cache = {}

    def update_generation(self: "Editable", generation: int | None = None) -> None:
        if generation is None:
            generation = self.file._generation
        self._generation = generation

    @property
    def is_outdated(self: "Editable") -> bool:
        if file := self.file:
            return self._generation < file._generation
        return False

    def is_same_version(self, other: "AutoCommitMixin") -> bool:
        return self._generation == other._generation


def _delay_update(new_value) -> bool:
    if isinstance(new_value, AutoCommitMixin):
        return new_value.is_outdated
    elif isinstance(new_value, list):
        return any(v.is_outdated for v in new_value)
    return False


def update_dict(seen: set["Editable"], obj: "Editable", new_obj: "Editable"):
    from codegen.sdk.core.interfaces.editable import Editable

    if obj in seen or obj.removed:
        return
    if new_obj.is_outdated:
        raise OutdatedNodeError(new_obj)
    if new_obj.is_same_version(obj):
        return
    assert new_obj._generation > obj._generation
    seen.add(obj)

    def update_child(v, new_value):
        if isinstance(v, Editable):
            update_dict(seen, v, new_value)
        # elif isinstance(v, list):
        #     # This only will work for lists, as the others are non-ordered
        #     to_update = list(filter(lambda i: not i.removed, v))
        #     if len(to_update) == len(new_value):
        #         for old, new in zip(to_update, new_value):
        #             if isinstance(old, Editable):
        #                 update_dict(seen, old, new)

    for k, v in obj.__dict__.items():
        # Update all the detached symbols in the tree
        if k in new_obj.__dict__:
            new_value = new_obj.__dict__[k]
            # assert new_value is not None, f"{k=}, {v=}, {new_value=}"
            if new_value is not None:
                update_child(v, new_value)
    # If you put a breakpoint during this while loop, python may segfault
    for k, v in obj.autocommit_cache.items():
        new_value = getattr(new_obj, k)
        if isinstance(new_value, Callable) and not isinstance(new_value, Exception):
            new_value = new_value()
        update_child(v, new_value)
        if isinstance(new_value, Editable):
            new_obj.autocommit_cache[k] = v
    # # If you put a breakpoint during this while loop, python may segfault
    # while len(to_update) > 0:
    #     k = to_update.popleft()
    #     new_value = getattr(new_obj, k)
    #     if isinstance(new_value, Callable):
    #         new_value = new_value()
    #     if _delay_update(new_value):
    #         new_obj.autocommit_cache.clear()
    #         to_update.append(k)
    #     else:
    #         v = obj.autocommit_cache.get(k)
    #         update_child(v, new_value)
    assert new_obj.__class__ == obj.__class__
    obj.__dict__ = new_obj.__dict__
    assert new_obj.ts_node == obj.ts_node
    assert new_obj.is_same_version(obj)
    assert not obj.is_outdated


@overload
def commiter(wrapped: Callable[P, T]) -> Callable[P, T]: ...


@overload
def commiter(wrapped: None = None, *, reset: bool = ...) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def commiter(wrapped: Callable[P, T] | None = None, *, reset: bool = False) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Indicates this method is part of a commit. There should be no writes within this method and reads will not be updated

    Args:
    ----
        reset: Reset the autocommit state when done. Only useful in reset_graph()

    """
    if wrapped is None:
        return functools.partial(commiter, reset=reset)

    @wrapt.decorator(enabled=enabled)
    def wrapper(wrapped: Callable[P, T], instance: Union["Editable", "CodebaseContext", None] = None, args: P.args = None, kwargs: P.kwargs = None) -> T:
        if instance is None:
            instance = args[0]
        from codegen.sdk.codebase.codebase_context import CodebaseContext

        if isinstance(instance, CodebaseContext):
            autocommit = instance._autocommit
        else:
            autocommit = instance.ctx._autocommit
        old_state = autocommit.enter_state(AutoCommitState.Committing)
        try:
            ret = wrapped(*args, **kwargs)
        finally:
            autocommit.state = old_state
        if reset:
            autocommit.reset()
        return ret

    return wrapper(wrapped)
