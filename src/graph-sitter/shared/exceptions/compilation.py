class UserCodeException(Exception):
    """Custom exception for any issues in user code."""


class DangerousUserCodeException(UserCodeException):
    """Custom exception user code that has dangerous / not permitted operations."""


class InvalidUserCodeException(UserCodeException):
    """Custom exception for user code that can be compiled/executed. Ex: syntax errors, indentation errors, name errors etc."""
