import re

from codegen.shared.exceptions.compilation import DangerousUserCodeException


def check_for_dangerous_operations(user_code: str) -> None:
    """If codeblock has dangerous operations (ex: exec, os.environ, etc) then raise an error and prevent the user from executing it."""
    dangerous_operation_patterns = [
        r"\b(os\.environ|locals|globals)\b",  # Environment variables and scope access
    ]
    pattern = "|".join(dangerous_operation_patterns)
    if re.search(pattern, user_code, re.IGNORECASE):
        msg = "The codeblock contains potentially dangerous operations that are not allowed."
        raise DangerousUserCodeException(msg)
