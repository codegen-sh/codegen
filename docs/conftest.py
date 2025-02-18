from pathlib import Path
from typing import Any
import pytest
from sybil import Sybil
from sybil.parsers.rest import DocTestParser
from sybil.parsers.markdown import PythonCodeBlockParser
from doctest import ELLIPSIS

from codegen.sdk.code_generation.current_code_codebase import get_documented_objects
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.file import TSFile
from codegen.gscli.generate.runner_imports import EXTERNAL_IMPORTS

SAMPLE_FILENAME = {
    ProgrammingLanguage.PYTHON: "sample.py",
    ProgrammingLanguage.TYPESCRIPT: "sample.tsx",
}
SAMPLE_INPUT_PATH = {
    language: Path(__file__).parent / "samples" / name for language, name in SAMPLE_FILENAME.items()}
SAMPLE_INPUT = {language: path.read_text() for language, path in SAMPLE_INPUT_PATH.items()}
DEFAULT_LANGUAGE = ProgrammingLanguage.TYPESCRIPT

@pytest.fixture(scope="function")
def codebase(tmpdir):
    with get_codebase_session(tmpdir, programming_language=DEFAULT_LANGUAGE, files={SAMPLE_FILENAME[DEFAULT_LANGUAGE]: SAMPLE_INPUT[DEFAULT_LANGUAGE]}) as codebase:
        yield codebase

@pytest.fixture(scope="function")
def file(codebase):
    return codebase.get_file(SAMPLE_FILENAME[DEFAULT_LANGUAGE])

@pytest.fixture(scope="function")
def component(file: TSFile):
    name = "LoadingSpinner"
    component = file.get_class(name)
    if component is None:
        pytest.fail(f"Component {name} not found")
    return component

@pytest.fixture(scope="function")
def function(file: TSFile):
    name = "handleClick"
    function = file.get_function(name)
    if function is None:
        pytest.fail(f"Function {name} not found")
    return function

@pytest.fixture(scope="function")
def class_def(file: TSFile):
    name = "MyClass"
    class_def = file.get_class(name)
    if class_def is None:
        pytest.fail(f"Class {name} not found")
    return class_def

@pytest.fixture(scope="function")
def method(class_def: TSClass):
    name = "render"
    method = class_def.get_method(name)
    if method is None:
        pytest.fail(f"Method {name} not found")
    return method

@pytest.fixture(scope="function")
def element(file: TSFile):
    element = file.jsx_elements[0]
    if element is None:
        pytest.fail("Element not found")
    return element

@pytest.fixture(scope="function")
def symbol_to_modify(class_def: TSClass):
    return class_def

def setup(namespace: dict[str, Any]):
    for language_objects in get_documented_objects().values():
        for object in language_objects:
            namespace[object.name] = object.object
    exec(EXTERNAL_IMPORTS, namespace)
pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS),
        PythonCodeBlockParser(),

    ],
    fixtures=["codebase", "file", "component", "function", "method", "element", "class_def", "symbol_to_modify"],
    patterns=["*.mdx", "*.md", "*.py"],
    setup=setup
).pytest()

