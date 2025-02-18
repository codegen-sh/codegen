from logging import getLogger
from typing import TYPE_CHECKING

from codegen.sdk.core.plugins.plugin import Plugin
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.codebase import PyCodebaseType

logger = getLogger(__name__)


class ModalApiFinder(Plugin):
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON

    def execute(self, codebase: "PyCodebaseType"):
        logger.info("Scanning for modal endpoints")
        endpoints = 0
        for func in codebase.functions:
            for decorator in func.decorators:
                if decorator.full_name == "web_endpoint":
                    value = decorator.call.get_arg_by_parameter_name("label").value.content
                    func.register_api(value)
                    endpoints += 1
        if endpoints > 0:
            logger.info(f"Found {endpoints} modal endpoints")
