import pytest

from codegen.sdk.ai.helpers import count_tokens
from codegen.sdk.code_generation.doc_utils.generate_docs_json import generate_docs_json
from codegen.sdk.code_generation.prompts.api_docs import get_codegen_sdk_codebase, get_codegen_sdk_docs
from codegen.sdk.core.symbol import Symbol
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture(scope="module")
def codebase():
    return get_codegen_sdk_codebase()


@pytest.mark.xdist_group("codegen")
def test_basic_docs(codebase) -> None:
    # =====[ Grab codebase ]=====
    language = ProgrammingLanguage.PYTHON
    api_docs = get_codegen_sdk_docs(language=language, codebase=codebase)
    assert "class File" in api_docs
    assert "class PyFile" in api_docs
    assert "class Function" in api_docs
    assert "class PyFunction" in api_docs
    assert "class PyClass" in api_docs

    # =====[ Codebase class ]=====
    assert "class Codebase" in api_docs
    assert "def has_symbol" in api_docs
    assert "def create_file" in api_docs

    # =====[ "Behaviors" docstring ]====
    assert "class HasName" in api_docs
    assert "class HasValue" in api_docs


@pytest.mark.xdist_group("codegen")
@pytest.mark.parametrize("language", [ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT])
def test_api_doc_generation_sanity(codebase, language: ProgrammingLanguage) -> None:
    lang = "Py" if language == ProgrammingLanguage.PYTHON else "TS"
    other_lang = "TS" if language == ProgrammingLanguage.PYTHON else "Py"
    # =====[ Python ]=====
    docs = get_codegen_sdk_docs(language=language, codebase=codebase)
    assert count_tokens(docs) < 70000
    assert f"{lang}Function" in docs
    assert f"{lang}Class" in docs
    assert f"{other_lang}Function" not in docs
    # assert "InviteFactoryCreateParams" in docs # Canonicals aren't in docs


@pytest.mark.timeout(300)
@pytest.mark.xdist_group("codegen")
def test_mdx_api_doc_generation_sanity(codebase) -> None:
    docs_json = generate_docs_json(codebase, "HEAD", raise_on_missing_docstring=True)

    assert len(docs_json.classes) > 0


@pytest.mark.xdist_group("codegen")
@pytest.mark.parametrize("language", [ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT])
def test_get_codegen_sdk_codebase(codebase, language) -> None:
    """Make sure we can get the current codebase for GraphSitter, and that imports get resolved correctly"""
    cls = codebase.get_symbol("PyClass")
    assert cls is not None
    func = codebase.get_symbol("PyFunction")
    superclasses = func.superclasses()
    callable = [x for x in superclasses if isinstance(x, Symbol) and x.name == "Callable"]
    assert len(callable) == 1
