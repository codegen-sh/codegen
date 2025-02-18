from codegen.shared.enums.programming_language import ProgrammingLanguage


def canonical(codemod):
    """Decorator for canonical Codemods that will be used for AI-agent prompts."""
    codemod._canonical = True
    if not hasattr(codemod, "language") or codemod.language not in (ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT):
        msg = "Canonical codemods must have a `language` attribute (PYTHON or TYPESCRIPT)."
        raise AttributeError(msg)
    return codemod
