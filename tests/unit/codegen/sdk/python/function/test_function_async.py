from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_is_async_basic(tmpdir):
    # language=python
    content = """
def foo():
    pass

async def bar():
    pass

class MyClass:
    async def baz(self):
        pass

    def qux(self):
        pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        bar = file.get_function("bar")
        my_class = file.get_class("MyClass")
        baz = my_class.get_method("baz")
        qux = my_class.get_method("qux")

        assert not foo.is_async
        assert bar.is_async
        assert baz.is_async
        assert not qux.is_async

        foo.asyncify()
        bar.asyncify()
        baz.asyncify()
        qux.asyncify()

    # language=python
    assert (
        file.content
        == """
async def foo():
    pass

async def bar():
    pass

class MyClass:
    async def baz(self):
        pass

    async def qux(self):
        pass
    """
    )


def test_function_is_async_extended(tmpdir):
    # language=python
    content = """
@my_decorator
def foo():
    '''Docstring'''
    pass

@my_decorator
async def bar():
'''Docstring'''
    pass

@my_decorator
class MyClass:
    @my_decorator
    async def baz(self):
        '''Docstring'''
        pass

    @my_decorator
    def qux(self):
        '''Docstring'''
        pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        bar = file.get_function("bar")
        my_class = file.get_class("MyClass")
        baz = my_class.get_method("baz")
        qux = my_class.get_method("qux")

        assert not foo.is_async
        assert bar.is_async
        assert baz.is_async
        assert not qux.is_async

        foo.asyncify()
        bar.asyncify()
        baz.asyncify()
        qux.asyncify()

    # language=python
    assert (
        file.content
        == """
@my_decorator
async def foo():
    '''Docstring'''
    pass

@my_decorator
async def bar():
'''Docstring'''
    pass

@my_decorator
class MyClass:
    @my_decorator
    async def baz(self):
        '''Docstring'''
        pass

    @my_decorator
    async def qux(self):
        '''Docstring'''
        pass
    """
    )
