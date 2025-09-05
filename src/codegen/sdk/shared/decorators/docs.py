import bisect
import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar


@dataclass
class DocumentedObject:
    name: str
    module: str
    object: any

    def __lt__(self, other):
        return self.module < other.module

    def signature(self) -> str:
        return f"{self.name}"


apidoc_objects: list[DocumentedObject] = []


def apidoc(obj):
    """Decorator for objects that will be used as API documentation for AI-agent prompts."""
    obj._apidoc = True
    obj._api_doc_lang = "core"
    if doc_obj := get_documented_object(obj):
        bisect.insort(apidoc_objects, doc_obj)
    return obj


py_apidoc_objects: list[DocumentedObject] = []


def py_apidoc(obj):
    """Decorator for objects that will be used as Python API documentation for AI-agent prompts."""
    obj._py_apidoc = True
    obj._api_doc_lang = "python"
    if doc_obj := get_documented_object(obj):
        bisect.insort(py_apidoc_objects, doc_obj)
    return obj


ts_apidoc_objects: list[DocumentedObject] = []


def ts_apidoc(obj):
    """Decorator for objects that will be used as Typescript API documentation for AI-agent prompts."""
    obj._ts_apidoc = True
    obj._api_doc_lang = "typescript"
    if doc_obj := get_documented_object(obj):
        bisect.insort(ts_apidoc_objects, doc_obj)
    return obj


no_apidoc_objects: list[DocumentedObject] = []
no_apidoc_signatures: set[str] = set()

T = TypeVar("T", bound=Callable)


def noapidoc(obj: T) -> T:
    """Decorator for things that are hidden from the API documentation for AI-agent prompts."""
    obj._apidoc = False
    obj._api_doc_lang = None
    if doc_obj := get_documented_object(obj):
        bisect.insort(no_apidoc_objects, doc_obj)
        no_apidoc_signatures.add(doc_obj.signature())
    return obj


py_no_apidoc_objects: list[DocumentedObject] = []
py_no_apidoc_signatures: set[str] = set()


def py_noapidoc(obj: T) -> T:
    """Decorator for things that are hidden from the Python API documentation for AI-agent prompts."""
    obj._py_apidoc = False
    obj._api_doc_lang = "python"
    if doc_obj := get_documented_object(obj):
        bisect.insort(py_no_apidoc_objects, doc_obj)
        py_no_apidoc_signatures.add(doc_obj.signature())
    return obj


def get_documented_object(obj) -> DocumentedObject | None:
    module = inspect.getmodule(obj)
    module_name = module.__name__ if module else ""
    if module_name:
        return DocumentedObject(name=obj.__name__, module=module_name, object=obj)
