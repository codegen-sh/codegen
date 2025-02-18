from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that transfers attributes from one class to another. The codemod should rename parameters of functions that use the first
class (GraphRagConfig) to use the second class (CacheConfig) instead. It should also handle variable renaming to avoid conflicts, update function
definitions, add necessary imports, and modify function call sites accordingly.""",
    uid="4a3569c2-cf58-4bdc-822b-7a5747f476ab",
)
@canonical
class SwapClassAttributeUsages(Codemod, Skill):
    """This codemod takes two classes (class A and class B) and transfers one class's attributes to the other.
    It does this by:
    - Renaming any parameters that are passing the class A and replaces it to take in class B instead
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        class_a_symb = codebase.get_symbol("GraphRagConfig")
        class_b_symb = codebase.get_symbol("CacheConfig")

        for function in codebase.functions:
            parameters = function.parameters
            if any(p.type == class_a_symb for p in parameters):
                # Rename existing instances of `cache_config`=> `cache_config_` (prevents mypy issue)
                name_conflict_vars = function.code_block.get_local_var_assignments("cache_config")
                for name_conflict_var in name_conflict_vars:
                    name_conflict_var.rename("cache_config_")

                # Get the parameter to update
                class_a_param = function.get_parameter_by_type(class_a_symb)

                # Update original function definition
                class_a_param.edit("cache_config: CacheConfig")

                # Add import of `CacheConfig` to function definition file
                function.file.add_symbol_import(class_b_symb)

                # Check if the function body is using `cache_config`
                if len(function.code_block.get_variable_usages(class_a_param.name)) > 0:
                    # Add "wrapper" inside the function
                    # This creates the `cache_config` variable internally
                    proxy_var_declaration = f"""{class_a_param.name} = cache_config.settings  # added by Codegen"""
                    function.prepend_statements(proxy_var_declaration)

                # Update all callsites of original function to take in `cache_config` instead of `graph_rag_config`
                fcalls = function.call_sites
                for fcall in fcalls:
                    arg = fcall.get_arg_by_parameter_name(class_a_param.name)
                    if not arg:
                        continue
                    if arg.is_named:
                        arg.edit(f"cache_config={arg.value}.cache_config")
                    else:
                        arg.edit(f"{arg.value}.cache_config")
