from logging import getLogger
from typing import TYPE_CHECKING

from codegen.sdk.core.plugins.plugin import Plugin
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.codebase import PyCodebaseType
logger = getLogger(__name__)


def is_flask_route(decorator):
    return (decorator.call and decorator.call.name in ["route", "get", "post", "put", "delete"]) or (decorator.call and "route" in decorator.call.name)


def extract_route(decorator):
    if decorator.call and decorator.call.args:
        return decorator.call.args[0].value
    return None


def extract_methods(decorator):
    if decorator.call and len(decorator.call.args) > 1:
        methods_arg = decorator.call.args[1]
        if isinstance(methods_arg, list):
            return [m.strip("'\"") for m in methods_arg.value.strip("[]").split(",")]
    return None


class FlaskApiFinder(Plugin):
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON

    def execute(self, codebase: "PyCodebaseType"):
        logger.info("Scanning for flask endpoints")
        endpoints = 0
        for func in codebase.functions:
            for decorator in func.decorators:
                if is_flask_route(decorator):
                    route = extract_route(decorator)
                    methods = extract_methods(decorator) or ["GET"]
                    if route:
                        func.register_api(route)
                        endpoints += 1

        for cls in codebase.classes:
            class_route = None
            for decorator in cls.decorators:
                if is_flask_route(decorator):
                    class_route = extract_route(decorator)
                    break

            for method in cls.methods:
                if method.name.lower() in ["get", "post", "put", "delete", "patch"]:
                    route = class_route or ""
                    for decorator in method.decorators:
                        if is_flask_route(decorator):
                            route += extract_route(decorator) or ""
                    if route:
                        method.register_api(route)
                        endpoints += 1

        if endpoints > 0:
            logger.info(f"Found {endpoints} modal endpoints")
