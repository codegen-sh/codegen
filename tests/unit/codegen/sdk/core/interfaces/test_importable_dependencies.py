from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_dependencies_max_depth_python(tmpdir) -> None:
    """Test the max_depth parameter in dependencies property for Python."""
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

def use_c():
    c = C()
    c.method_c()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        use_c = file.get_function("use_c")
        c_class = file.get_class("C")
        b_class = file.get_class("B")
        a_class = file.get_class("A")

        # Test depth 1 (direct dependencies only)
        deps_depth1 = use_c.dependencies(max_depth=1)
        assert len(deps_depth1) == 1
        assert deps_depth1[0] == c_class

        # Test depth 2 (includes C's dependency on B)
        deps_depth2 = use_c.dependencies(max_depth=2)
        assert len(deps_depth2) == 2
        assert c_class in deps_depth2
        assert b_class in deps_depth2

        # Test depth 3 (includes full chain use_c -> C -> B -> A)
        deps_depth3 = use_c.dependencies(max_depth=3)
        assert len(deps_depth3) == 3
        assert c_class in deps_depth3
        assert b_class in deps_depth3
        assert a_class in deps_depth3

        # Test with both max_depth and usage_types
        deps_with_types = use_c.dependencies(max_depth=2, usage_types=UsageType.DIRECT)
        assert len(deps_with_types) == 2
        assert c_class in deps_with_types
        assert b_class in deps_with_types


def test_dependencies_max_depth_typescript(tmpdir) -> None:
    """Test the max_depth parameter in dependencies property for TypeScript."""
    # language=typescript
    content = """
interface IBase {
    baseMethod(): void;
}

class A implements IBase {
    baseMethod() {
        console.log('base');
    }
}

class B extends A {
    methodB() {
        this.baseMethod();
    }
}

class C extends B {
    methodC() {
        this.methodB();
    }
}

function useC() {
    const c = new C();
    c.methodC();
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        use_c = file.get_function("useC")
        c_class = file.get_class("C")
        b_class = file.get_class("B")
        a_class = file.get_class("A")
        ibase = file.get_interface("IBase")

        # Test depth 1 (direct dependencies only)
        deps_depth1 = use_c.dependencies(max_depth=1)
        assert len(deps_depth1) == 1
        assert deps_depth1[0] == c_class

        # Test depth 2 (includes C's dependency on B)
        deps_depth2 = use_c.dependencies(max_depth=2)
        assert len(deps_depth2) == 2
        assert c_class in deps_depth2
        assert b_class in deps_depth2

        # Test depth 3 (includes C -> B -> A)
        deps_depth3 = use_c.dependencies(max_depth=3)
        assert len(deps_depth3) == 3
        assert c_class in deps_depth3
        assert b_class in deps_depth3
        assert a_class in deps_depth3

        # Test depth 4 (includes interface implementation)
        deps_depth4 = use_c.dependencies(max_depth=4)
        assert len(deps_depth4) == 4
        assert c_class in deps_depth4
        assert b_class in deps_depth4
        assert a_class in deps_depth4
        assert ibase in deps_depth4

        # Test with both max_depth and usage_types
        deps_with_types = use_c.dependencies(max_depth=2)
        assert len(deps_with_types) == 2
        assert c_class in deps_with_types
        assert b_class in deps_with_types


def test_dependencies_max_depth_cyclic(tmpdir) -> None:
    """Test max_depth parameter with cyclic dependencies."""
    # language=python
    content = """
class A:
    def method_a(self):
        return B()

class B:
    def method_b(self):
        return A()

def use_both():
    a = A()
    b = B()
    return a.method_a(), b.method_b()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        use_both = file.get_function("use_both")
        a_class = file.get_class("A")
        b_class = file.get_class("B")

        # Test depth 1 (direct dependencies only)
        deps_depth1 = use_both.dependencies(max_depth=1)
        assert len(deps_depth1) == 2
        assert a_class in deps_depth1
        assert b_class in deps_depth1

        # Test depth 2 (should handle cyclic deps without infinite recursion)
        deps_depth2 = use_both.dependencies(max_depth=2)
        assert len(deps_depth2) == 2  # Still just A and B due to cycle
        assert a_class in deps_depth2
        assert b_class in deps_depth2

        # Test with both max_depth and usage_types
        deps_with_types = use_both.dependencies(max_depth=2)
        assert len(deps_with_types) == 2
        assert a_class in deps_with_types
        assert b_class in deps_with_types
