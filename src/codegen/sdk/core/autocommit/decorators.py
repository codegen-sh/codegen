from codegen.shared.logging.get_logger import get_logger
import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, ParamSpec, TypeVar, Union, overload

import wrapt

from codegen.sdk.core.autocommit.constants import AutoCommitState, enabled
from codegen.sdk.core.node_id_factory import NodeId

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.symbol import Symbol


logger = get_logger(__name__)
P = ParamSpec("P")
T = TypeVar("T")


@overload
def writer(wrapped: Callable[P, T]) -> Callable[P, T]: ...


@overload
def writer(
    wrapped: None = None, *, commit: bool = ...
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def writer(
    wrapped: Callable[P, T] | None = None, *, commit: bool = True
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """Indicates the method is a writer. This will automatically update if the original is out of
    date.

    Args:
    ----
        commit: Whether to commit if there is an update. Do not set this to False unless you are absolutely sure the method can be retried with commit as True safely.
    """
    if wrapped is None:
        return functools.partial(writer, commit=commit)

    @wrapt.decorator(enabled=enabled)
    def wrapper(wrapped: Callable[P, T], instance: "Editable", args, kwargs) -> T:
        if instance is None:
            instance = args[0]
        if instance.removed:
            logger.warning("Editing a removed node")
        autocommit = instance.ctx._autocommit
        logger.debug("Writing node %r,%r", instance, wrapped)
        with autocommit.write_state(instance, commit=commit):
            return wrapped(*args, **kwargs)

    return wrapper(wrapped)


@wrapt.decorator(enabled=enabled)
def remover(
    wrapped: Callable[P, T],
    instance: Union["Symbol", None] = None,
    args: P.args = None,
    kwargs: P.kwargs = None,
) -> Callable[P, T]:
    """Indicates the node will be removed at the end of this method.

    Further usage of the node will result in undefined behaviour and a warning.
    """
    if instance is None:
        instance = args[0]
    logger.debug("Removing node %r, %r", instance, wrapped)
    with instance.ctx._autocommit.write_state(instance):
        ret = wrapped(*args, **kwargs)
    # instance.ctx._autocommit.set_pending(instance, REMOVED)
    instance.removed = True
    return ret


@wrapt.decorator(enabled=enabled)
def repr_func(
    wrapped: Callable[P, T],
    instance: Union["Editable", None] = None,
    args: P.args = None,
    kwargs: P.kwargs = None,
) -> Callable[P, T]:
    """Indicates the method is use in debugging/logs."""
    if instance is None:
        instance = args[0]
    autocommit = instance.ctx._autocommit
    old_state = autocommit.enter_state(AutoCommitState.Special)
    try:
        ret = wrapped(*args, **kwargs)
    finally:
        autocommit.state = old_state
    return ret


@wrapt.decorator(enabled=enabled)
def mover(
    wrapped: Callable[P, tuple[NodeId, NodeId]],
    instance: Union["Symbol", None] = None,
    args: P.args = None,
    kwargs: P.kwargs = None,
) -> Callable[P, None]:
    """Indicates the Node will be moved by the end of this method.

    It should also return the node_id of itself and the new file
    """
    if instance is None:
        instance = args[0]
    with instance.ctx._autocommit.write_state(instance, move=True):
        file_node_id, node_id = wrapped(*args, **kwargs)
    instance.ctx._autocommit.set_pending(instance, node_id, file_node_id)
    instance.removed = False
    return None
