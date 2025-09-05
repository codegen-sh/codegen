from enum import StrEnum


class DocumentationDecorators(StrEnum):
    PYTHON = "py_apidoc"
    TYPESCRIPT = "ts_apidoc"
    CODEMOD = "canonical"
    GENERAL_API = "apidoc"
