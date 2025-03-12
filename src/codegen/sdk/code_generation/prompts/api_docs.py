from codegen.sdk.code_generation.codegen_sdk_codebase import get_codegen_sdk_codebase
from codegen.sdk.code_generation.prompts.utils import get_api_classes_by_decorator, get_codegen_sdk_class_docstring
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# TODO: the agent in codegen-backend and codegen-frontend does not use any of this. we have api_docs.py in codegen-backend!!!

########################################################################################################################
# UTILS
########################################################################################################################


def get_docstrings_for_classes(codebase: Codebase, language: ProgrammingLanguage, classnames: list[str]) -> dict[str, str]:
    """Returns map of ClassName -> Docstring"""
    classes = get_api_classes_by_decorator(codebase=codebase, language=language)
    class_docstrings = {k: get_codegen_sdk_class_docstring(cls=v, codebase=codebase) for k, v in classes.items()}
    return {k: class_docstrings[k] for k in classnames}


########################################################################################################################
# API STUBS
########################################################################################################################
# This is like `PyFile` definition etc.


def get_codebase_docstring(codebase: Codebase, language: ProgrammingLanguage) -> str:
    """Returns the docstring for the `Codebase` class."""
    docstrings = get_docstrings_for_classes(codebase, language, ["Codebase"])
    docstring = docstrings["Codebase"]
    return f"""
The `Codebase` class is the main entrypoint to manipulating a codebase with GraphSitter. It implements the core methods that allow you to identify important symbols, make changes to the codebase, and commit those changes.

{docstring}
"""  # noqa: E501


def get_behavior_docstring(codebase: Codebase, language: ProgrammingLanguage) -> str:
    """These are the core classes in GraphSitter - they define things like `HasName` etc."""
    behavior_classnames = [
        "Editable",
        "Typeable",
        "HasBlock",
        "Name",
        "HasName",
        "Value",
        "HasValue",
        "Importable",
        "Exportable",
        "Callable",
        # "GraphSitterBase",
    ]
    docstrings = get_docstrings_for_classes(codebase, language, behavior_classnames)
    cls_sections = "\n\n".join([docstrings[cls] for cls in behavior_classnames])
    return f"""
The following classes represent "behaviors" in GraphSitter that apply to potentially many entities. For example, many types will inherit `HasName` and will then support `x.name`, `x.set_name(new_name)`, etc.

Look in the type inheritance of the core symbols to see which behaviors they support.

{cls_sections}
"""  # noqa: E501


########################################################################################################################
# CORE SYMBOLS
########################################################################################################################


def get_core_symbol_docstring(codebase: Codebase, language: ProgrammingLanguage) -> str:
    """This should return the docstrings for the symbol types in GraphSitter. Also should include the language-specific extensions."""
    symbol_types = [
        "File",
        "Statement",
        "CodeBlock",
        "AssignmentStatement",
        "ImportStatement",
        "Import",
        # "ImportResolution",
        "Export",
        "Symbol",
        "Usage",
        "Assignment",
        "Function",
        "Parameter",
        "Argument",
        "FunctionCall",
        "Class",
        "Attribute",
        "Decorator",
        "Comment",
        "ReturnStatement",
        "ExternalModule",
    ]
    if language == ProgrammingLanguage.TYPESCRIPT:
        symbol_types.extend(["JSXElement", "JSXExpression", "JSXProp"])

    docstrings = get_docstrings_for_classes(codebase, language, symbol_types)
    cls_sections = "\n\n".join([docstrings[cls] for cls in symbol_types])
    return f"""
The following classes represent the core symbol types in GraphSitter. These classes are used to represent the various entities in a codebase, such as files, functions, classes, etc.

Most codemods will begin by identifying the symbols in the codebase that need to be modified by searching and filtering through these symbol types, then calling various edit methods on them or their sub-components

{cls_sections}
"""  # noqa: E501


########################################################################################################################
# LANGUAGE SPECIFIC
########################################################################################################################


def get_language_specific_docstring(codebase: Codebase, language: ProgrammingLanguage) -> str:
    # =====[ Get language prefix ]=====
    if language == ProgrammingLanguage.PYTHON:
        prefix = "Py"
    else:
        prefix = "TS"

    # =====[ Grab docstrings ]=====
    classes = get_api_classes_by_decorator(codebase=codebase, language=language)
    class_docstrings = {k: get_codegen_sdk_class_docstring(cls=v, codebase=codebase) for k, v in classes.items()}
    docstrings = {k: v for k, v in class_docstrings.items() if k.startswith(prefix)}

    # =====[ Get mapping from e.g. File => PyFile and TFile => PyFile ]=====
    names = list(docstrings.keys())
    # stripped_names = [name.replace(prefix, "") for name in names]
    # inherit_mapping = {k: v for k, v in zip(stripped_names, names)}
    # type_mapping = {f"T{k}": v for k, v in inherit_mapping.items()}
    # name_mapping = {**inherit_mapping, **type_mapping}

    cls_docstrings = "\n\n".join([docstrings[name] for name in names])
    return f"""
Here are language-specific extensions of some of the classes above. Anywhere you see TFile as a type, that's the generic type that corresponds to these classes.

For example, all `File` that you encounter will be of type {prefix}File, {prefix}File inherits all methods from `File`.

{cls_docstrings}
"""


########################################################################################################################
# FULL DOCS
########################################################################################################################


def get_codegen_sdk_docs(language: ProgrammingLanguage = ProgrammingLanguage.PYTHON, codebase: Codebase | None = None) -> str:
    """Computes the GraphSitter docs from scratch"""
    codebase = codebase or get_codegen_sdk_codebase()
    with codebase.session(sync_graph=False, commit=False):
        return f"""
# Codegen SDK Docs

Codegen SDK is a Python SDK for writing powerful programs that operate on codebases. In essence, it is a scriptable, multi-language language server that is optimized for fast code transformations and analytics.

Consider the following:
```python
# Sets docstring to "hello world!" for all classes that end with `Resource`
num_edited = 0
for cls in codebase.classes:
    if cls.name.endswith("Resource"):
        cls.set_docstring("hello, world!")  # Handles all edge cases + formatting for properly setting docstrings
        num_edited += 1
# Provide developer-facing analytics on the output
print(f'⚡ Edited: {{num_edited}}')
```
As demonstrated, you can concisely express powerful transformations and analytics on codebases with GraphSitter.

## Motivation

Traditional "codemods" are difficult to write and maintain due to the complexities of parsing, import resolution, and more.

GraphSitter is specifically designed to enable AI agents to efficiently write code transformations and analytics. It enables agents to "act via code" and make powerful changes with guaranteed correctness and with minimal effort. Future additions to this library will enable agents to interact with other systems besides code via the GraphSitter API.

## Architecture Overview

GraphSitter enables manipulations of a codebase via a Python SDK.

The SDK provides a set of classes that represent the various entities in a codebase, such as files, directories, functions, types, etc. These classes are designed to be used in conjunction with the `Codebase` class, which is the entrypoint to most operations.

These classes and the `Codebase` object enable common transformations like `move_to_file`, `set_docstring`, `add_type_annotation`, etc.

A GraphSitter codemod is implemented as a Python script that operates on a global `Codebase`, such as the following:
```python
# Sets return type to `None` for all functions that do not have a return type. (This is on a Python Codebase)
file = codebase.get_file("src/app/main.py") # or .ts, if you are operating on a TypeScript codebase
for function in file.functions:
    if function.name != "main":
        if len(function.return_statements) == 0 and not function.return_type:
            function.set_return_type("None") # or `null` if you are operating on a TypeScript codebase
```

As you can see, a typical codemod will:
- Identify the symbols, files, etc. in a codebase that need to be modified (typically a set of for loops and nested conditionals)
- Make the necessary changes to the codebase by interacting with GraphSitter classes and methods (typically calling `.edit(...)` or other methods, that will call this under the hood.)

Given a Codemod like so, the Codegen infrastructure will:
- Run the codemod efficiently
- Visualise the diff, log or other artifacts created for the developer
- Split up the changes into logical PRs, e.g. by CODEOWNER or by file (according to the developer's request)
- Upload results to version control (e.g. GitHub)


## `Codebase` Class Documentation

{get_codebase_docstring(codebase=codebase, language=language)}

## Core Symbol Type Classes Documentation

{get_core_symbol_docstring(codebase=codebase, language=language)}

## Language-specific Extensions Documentation

{get_language_specific_docstring(codebase=codebase, language=language)}

## Behaviors and Common Classes Documentation

{get_behavior_docstring(codebase=codebase, language=language)}

## Best Practices
- Take inspiration on best practices from the provided, curated examples
    - These have been vetted by human experts and are known to be correct
- When applicable, include aesthetic and instructive logs for developers via the `print` statement, such as:
    - A title
    - Emoji
    - Hierarchical logging, with filenames in single quotes
- You do not need to explain to the developer the code you are going to write before calling CREATE_CODEMOD
    - This will just make the code
- You *DO NOT* need to import `codegen.sdk`, (this module does not exist) `codebase` or any types.
    - All types in the library are available in the global namespace and are automatically imported, as is the `codebase` object.
- You *DO NOT* need to do anything to parse the codebase.
    - This is done automatically by the Codegen infrastructure and pre-cached for fast execution. Just interact with the `codebase` object.
"""  # noqa: E501
