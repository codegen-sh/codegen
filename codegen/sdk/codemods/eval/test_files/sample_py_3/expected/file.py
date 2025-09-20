from decorators import decorator_function


@decorator_function
def foo_bar():
    return 1


@decorator_function
def foo_char():
    return 2


def bar():
    return 3
