from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_remove_unused_imports_basic(tmpdir) -> None:
    """Test basic unused import removal"""
    # language=python
    content = """
import os
import sys
from math import pi, sin
import json as jsonlib

print(os.getcwd())
sin(pi)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "import sys" not in file.content
    assert "import jsonlib" not in file.content
    assert "import os" in file.content
    assert "from math import pi, sin" in file.content


def test_remove_unused_imports_multiline(tmpdir) -> None:
    """Test removal of unused imports in multiline import statements"""
    # language=python
    content = """
from my_module import (
    used_func,
    unused_func,
    another_unused,
    used_class,
    unused_class
)

result = used_func()
obj = used_class()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "unused_func" not in file.content
    assert "another_unused" not in file.content
    assert "unused_class" not in file.content
    assert "used_func" in file.content
    assert "used_class" in file.content


def test_remove_unused_imports_with_aliases(tmpdir) -> None:
    """Test removal of unused imports with aliases"""
    # language=python
    content = """
from module import (
    long_name as short,
    unused as alias,
    used_thing as ut
)
import pandas as pd
import numpy as np

print(short)
result = ut.process()
data = pd.DataFrame()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "unused as alias" not in file.content
    assert "numpy as np" not in file.content
    assert "long_name as short" in file.content
    assert "used_thing as ut" in file.content
    assert "pandas as pd" in file.content


def test_remove_unused_imports_preserves_comments(tmpdir) -> None:
    """Test that removing unused imports preserves relevant comments"""
    # language=python
    content = """
# Important imports below
import os  # Used for OS operations
import sys  # Unused but commented
from math import (  # Math utilities
    pi,  # Circle constant
    e,   # Unused constant
    sin  # Trig function
)

print(os.getcwd())
print(sin(pi))
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "# Important imports below" in file.content
    assert "import os  # Used for OS operations" in file.content
    assert "import sys  # Unused but commented" not in file.content
    assert "e,   # Unused constant" not in file.content
    assert "pi,  # Circle constant" in file.content
    assert "sin  # Trig function" in file.content


def test_remove_unused_imports_relative_imports(tmpdir) -> None:
    """Test handling of relative imports"""
    # language=python
    content = """
from . import used_module
from .. import unused_module
from .subpackage import used_thing, unused_thing
from ..utils import helper

used_module.func()
used_thing.process()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "from . import used_module" in file.content
    assert "from .. import unused_module" not in file.content
    assert "unused_thing" not in file.content
    assert "from ..utils import helper" not in file.content
    assert "used_thing" in file.content


def test_remove_unused_imports_star_imports(tmpdir) -> None:
    """Test handling of star imports (should not be removed as we can't track usage)"""
    # language=python
    content = """
from os import *
from sys import *
from math import pi
from math import sqrt

getcwd()  # from os
print(pi)
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "from os import *" in file.content
    assert "from sys import *" in file.content
    assert "from math import pi" in file.content


def test_remove_unused_imports_type_hints(tmpdir) -> None:
    """Test handling of imports used in type hints"""
    # language=python
    content = """
from typing import List, Dict, Optional, Any
from custom_types import CustomType, UnusedType

def func(arg: List[int], opt: Optional[CustomType]) -> Dict[str, Any]:
    return {"result": arg}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert "List, Dict, Optional, Any" in file.content
    assert "CustomType" in file.content
    assert "UnusedType" not in file.content


def test_remove_unused_imports_empty_file(tmpdir) -> None:
    """Test handling of empty files"""
    # language=python
    content = """
# Empty file with imports
import os
import sys
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        file.remove_unused_imports()

    assert file.content.strip() == "# Empty file with imports"


def test_remove_unused_imports_multiple_removals(tmpdir) -> None:
    """Test multiple rounds of import removal"""
    # language=python
    content = """
import os
import sys
import json

def func():
    print(os.getcwd())
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # First removal
        file.remove_unused_imports()
        codebase.commit()
        file = codebase.get_file("test.py")

        assert "import sys" not in file.content
        assert "import json" not in file.content
        assert "import os" in file.content

        # Second removal (should not change anything)
        file.remove_unused_imports()
        codebase.commit()
        file = codebase.get_file("test.py")

        assert "import sys" not in file.content
        assert "import json" not in file.content
        assert "import os" in file.content


def test_file_complex_example_test_spliter(tmpdir) -> None:
    """Test splitting a test file into multiple files, removing unused imports"""
    # language=python
    content = """
from math import pi
from math import sqrt

def test_set_comparison():
    set1 = set("1308")
    set2 = set("8035")
    assert set1 == set2

def test_math_sqrt():
    assert sqrt(4) == 2
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        base_name = "test_utils"

        # Group tests by subpath
        test_groups = {}
        for test_function in file.functions:
            if test_function.name.startswith("test_"):
                test_subpath = "_".join(test_function.name.split("_")[:3])
                if test_subpath not in test_groups:
                    test_groups[test_subpath] = []
                test_groups[test_subpath].append(test_function)

        # Print and process each group
        for subpath, tests in test_groups.items():
            new_filename = f"{base_name}/{subpath}.py"

            # Create file if it doesn't exist
            if not codebase.has_file(new_filename):
                new_file = codebase.create_file(new_filename)
            file = codebase.get_file(new_filename)

            # Move each test in the group
            for test_function in tests:
                print(f"Moving function {test_function.name} to {new_filename}")
                test_function.move_to_file(new_file, strategy="update_all_imports", include_dependencies=True)
                original_file = codebase.get_file("test.py")

        # Force a commit to ensure all changes are applied
        codebase.commit()

        # Verify the results
        # Check that original test.py is empty of test functions
        original_file = codebase.get_file("test.py", optional=True)
        assert original_file is not None
        assert len([f for f in original_file.functions if f.name.startswith("test_")]) == 0

        # Verify test_set_comparison was moved correctly
        set_comparison_file = codebase.get_file("test_utils/test_set_comparison.py", optional=True)
        assert set_comparison_file is not None
        assert "test_set_comparison" in set_comparison_file.content
        assert 'set1 = set("1308")' in set_comparison_file.content

        # Verify test_math_sqrt was moved correctly
        math_file = codebase.get_file("test_utils/test_math_sqrt.py", optional=True)
        assert math_file is not None
        assert "test_math_sqrt" in math_file.content
        assert "assert sqrt(4) == 2" in math_file.content

        # Verify imports were preserved
        assert "from math import sqrt" in math_file.content
        assert "from math import pi" not in math_file.content  # Unused import should be removed
