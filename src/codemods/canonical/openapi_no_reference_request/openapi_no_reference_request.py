from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.detached_symbols.decorator import Decorator
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that adds `@my_namespace.expect(None)` to all Flask route methods (GET, POST, PUT, PATCH, DELETE) in classes ending with
'Resource' that do not access the request object. Ensure that these methods do not already have an `expect` decorator or similar decorators like
`load_with`, `use_args`, or `use_kwargs`. The codemod should also check for the presence of a namespace decorator in the class to determine the
correct namespace to use.""",
    uid="5341d15f-92c7-4a3e-b409-416603dfa7f6",
)
@canonical
class OpenAPINoReferenceRequest(Codemod, Skill):
    """As part of the OpenAPI typing initiative for Flask endpoints, this codemod will add `@my_namespace.expect(None)` to all Flask routes that do not interact with the request object."""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        request_accesses = ["request_get_json", "request.json", "request.args", "request.form", "request.files", "request", "self.request"]

        def get_namespace_decorator(symbol: Symbol) -> Decorator | None:
            matches = [d for d in symbol.decorators if "_ns.route" in d.source]
            if len(matches) == 0:
                return None
            return matches[0]

        for cls in codebase.classes:
            if cls.name.endswith("Resource"):
                for method in cls.methods:
                    if method.name in ("get", "post", "put", "patch", "delete"):
                        # Check if it has any request accesses
                        if not any([access in method.source for access in request_accesses]):
                            # Check if it has an existing `expect`
                            decorators = method.decorators
                            if not any([x in decorator.source for decorator in decorators for x in ["load_with", "expect", "use_args", "use_kwargs"]]):
                                # Make sure it has `@xys_ns.route` on the class
                                ns_decorator = get_namespace_decorator(cls)
                                if ns_decorator is not None:
                                    ns_name = ns_decorator.source.split("@")[1].split(".")[0]
                                    # Add the decorator
                                    method.add_decorator(f"@{ns_name}.expect(None)")
