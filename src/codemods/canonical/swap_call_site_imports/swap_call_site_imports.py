from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that replaces all imports of a legacy function with its new replacement. The codemod should find all call sites of the
legacy function, update the import module to the new module, and handle the edge case where the legacy function is called within the same file it is
defined. In this case, the codemod should remove the legacy function and add an import for its replacement. The legacy function is located in
'redash/settings/helpers.py' and is named 'array_from_string'. The new import module is 'redash.settings.collections'. Include comments to explain
each step.""",
    uid="8fa00be7-adad-473d-8436-fc5f70e6ac6d",
)
@canonical
class SwapCallSiteImports(Codemod, Skill):
    """This codemod replaces all imports of a legacy function with it's new replacement.

    This involves:
    - Finding all the call sites of the old function
    - Updating the import module of the old function import to the new module
    - Edge case: legacy function is called within the same file it's defined in
        - There won't be an import to the legacy function in this file (b/c it's where it's defined)
        - For this case we have to both remove the legacy function and add an import to it's replacement.

    Example:
    Before:
        from mod import func

        func()

    After:
        from new_mode import func

        func()
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        legacy_func_file = codebase.get_file("redash/settings/helpers.py")
        legacy_function = legacy_func_file.get_function("array_from_string")

        # Find all call sites of the legacy function
        for call_site in legacy_function.call_sites:
            # Get the import of the legacy function in the call site file
            legacy_import = next((x for x in call_site.file.imports if x.resolved_symbol == legacy_function), None)

            # Update the import module of the old function import to the new module
            if legacy_import:
                legacy_import.set_import_module("redash.settings.collections")

            # Edge case: legacy function is called within the same file it's defined in
            if call_site.file == legacy_function.file:
                # Remove the legacy function
                legacy_function.remove()

                # Add import of the new function
                call_site.file.add_import_from_import_string(f"from settings.collections import {legacy_function.name}")
