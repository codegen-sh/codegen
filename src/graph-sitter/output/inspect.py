import inspect
from collections.abc import Callable
from inspect import Parameter

from codegen.sdk.shared.decorators.docs import DocumentedObject, no_apidoc_signatures


def only_default_args(method: Callable) -> bool:
    sig = inspect.signature(method)
    for param in sig.parameters:
        if not isinstance(param, Parameter):
            return False
        if param.default != Parameter.empty:
            return False
    return True


def is_noapidoc(obj: object, attr: str) -> bool:
    module = inspect.getmodule(obj)
    module_name = module.__name__ if module else ""

    if module_name:
        doc_obj = DocumentedObject(name=attr, module=module_name, object=obj)
        return doc_obj.signature() in no_apidoc_signatures
    return False
