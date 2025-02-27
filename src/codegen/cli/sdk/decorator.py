from collections.abc import Callable, Sequence
from functools import wraps
from typing import Literal, ParamSpec, TypeVar, get_type_hints

from codegen.shared.enums.programming_language import ProgrammingLanguage

P = ParamSpec("P")
T = TypeVar("T")
WebhookType = Literal["pr", "push", "issue", "release"]
WebhookEvent = Literal["created", "updated", "closed", "reopened", "synchronized"]


class DecoratedFunction:
    """Represents a Python function decorated with a codegen decorator."""

    def __init__(
        self,
        name: str,
        *,
        subdirectories: list[str] | None = None,
        language: ProgrammingLanguage | None = None,
        webhook_config: dict | None = None,
        lint_mode: bool = False,
        lint_user_whitelist: Sequence[str] | None = None,
    ):
        self.name = name
        self.subdirectories = subdirectories
        self.language = language
        self.func: Callable | None = None
        self.params_type = None
        self.webhook_config = webhook_config
        self.lint_mode = lint_mode
        self.lint_user_whitelist = list(lint_user_whitelist) if lint_user_whitelist else []

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        # Get the params type from the function signature
        hints = get_type_hints(func)
        if "params" in hints:
            self.params_type = hints["params"]

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)

        # Set the codegen name on the wrapper function
        wrapper.__codegen_name__ = self.name
        self.func = wrapper
        return wrapper


def function(name: str, subdirectories: list[str] | None = None, language: ProgrammingLanguage | None = None) -> DecoratedFunction:
    """Decorator for codegen functions.

    Args:
        name: The name of the function to be used when deployed

    Example:
        @codegen.function('my-function')
        def run(codebase):
            pass

    """
    return DecoratedFunction(name=name, subdirectories=subdirectories, language=language)


def webhook(
    label: str,
    *,
    type: WebhookType = "pr",
    event: WebhookEvent = "created",
    description: str | None = None,
    users: Sequence[str] | None = None,
) -> DecoratedFunction:
    """Decorator for webhook functions that run in response to events.

    Args:
        label: Unique identifier for this webhook
        type: Type of webhook ("pr", "push", "issue", "release")
        event: Event to trigger on ("created", "updated", "closed", etc.)
        description: Human-readable description of what this webhook does
        users: List of GitHub usernames to notify (with or without @ symbol)

    Example:
        @codegen.webhook(
            label="flag-customer-code",
            type="pr",
            event="created",
            description="Flags customer code",
        )
        def run(codebase, pr):
            pass

    """
    normalized_users = [user.lstrip("@") for user in users] if users else []

    webhook_config = {
        "type": type,
        "event": event,
        "description": description,
        "users": normalized_users,
    }

    return DecoratedFunction(
        name=label,
        webhook_config=webhook_config,
        lint_mode=True,
        lint_user_whitelist=normalized_users,
    )
