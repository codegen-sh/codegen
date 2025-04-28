from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType


def test_usages_max_depth_python(tmpdir) -> None:
    """Test the max_depth parameter in usages method for Python."""
    # language=python
    content = """
class A:
    def method_a(self):
        pass

class B(A):
    def method_b(self):
        self.method_a()

class C(B):
    def method_c(self):
        self.method_b()

# Usage of class C
c_instance = C()
c_instance.method_c()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        c_class = file.get_class("C")

        # Test depth 1 (direct usages only)
        usages_depth1 = c_class.usages(max_depth=1)
        assert len(usages_depth1) == 2

        # Test depth 2 (includes usages of B)
        usages_depth2 = c_class.usages(max_depth=2)
        assert len(usages_depth2) == 3

        # Test depth 3 (includes usages of A)
        usages_depth3 = c_class.usages(max_depth=3)
        assert len(usages_depth3) == 3


def test_usages_complex_scenarios(tmpdir) -> None:
    """Test more complex scenarios for the usages method."""
    # language=python
    content = """
class Base:
    def base_method(self):
        pass

class Mixin:
    def mixin_method(self):
        self.value = 42

class Child(Base, Mixin):
    def child_method(self):
        # Direct usage of base method
        self.base_method()
        # Direct usage of mixin method
        self.mixin_method()
        # Chained usage through property
        return self.value

# Multiple different types of usages
child = Child()  # Direct usage
child.child_method()  # Chained usage
indirect_child = child  # Indirect usage
child_instance = Child()  # Another direct usage

# Usage in type hints
def process_child(instance: Child) -> None:
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        child_class = file.get_class("Child")

        # Test without depth specified (should get all usages)
        all_usages = child_class.usages()
        # Should include: direct instantiations, chained method call, indirect usage, type hint usage
        assert len(all_usages) >= 5

        # Test with specific usage types
        direct_usages = child_class.usages(usage_types=UsageType.DIRECT)
        assert len(direct_usages) >= 2  # Direct instantiations and type hint usage

        chained_usages = child_class.usages(usage_types=UsageType.CHAINED)
        assert len(chained_usages) >= 1  # Method call

        indirect_usages = child_class.usages(usage_types=UsageType.INDIRECT)
        assert len(indirect_usages) >= 1  # Indirect assignment


def test_usages_edge_cases(tmpdir) -> None:
    """Test edge cases for the usages method."""
    # language=python
    content = """
class Parent:
    pass

class Child(Parent):
    @classmethod
    def factory(cls):
        return cls()

    @property
    def self_ref(self):
        return self

# Complex usage patterns
def create_child():
    # Multiple references in the same function
    child1 = Child()
    child2 = Child.factory()
    child3 = Child()
    return child1

# Usage in nested function
def outer():
    child = Child()
    def inner():
        return child
    return inner

# Multiple inheritance
class Mixin:
    pass

class MultiChild(Child, Mixin):
    pass
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        child_class = file.get_class("Child")

        # Test without depth
        all_usages = child_class.usages()
        # Should include: direct instantiations, factory calls, indirect usages
        assert len(all_usages) >= 6

        # Test with depth=1 but all usage types
        depth1_all_types = child_class.usages(max_depth=1, usage_types=None)
        # When max_depth=1, we should get the same or fewer usages than without depth
        assert len(depth1_all_types) <= len(all_usages)

        # Test with specific usage types but no depth
        method_usages = child_class.usages(usage_types=UsageType.DIRECT | UsageType.CHAINED)
        assert len(method_usages) >= 4  # Direct instantiations and method calls
