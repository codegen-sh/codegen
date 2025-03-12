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
    prompt="""Generate a Python codemod that adds a `@xys_ns.response(200)` decorator to Flask Resource methods that lack return status codes. The codemod should
check for Flask Resource classes and their HTTP methods (GET, POST, PUT, PATCH, DELETE). If a method does not have any `@response` decorators and has
a valid return statement, the codemod should extract the namespace from the class's `@xys.route` decorator and add the `@xys_ns.response(200)`
decorator to the method.""",
    uid="c1596668-8169-44b4-9e0e-b244eb7671d9",
)
@canonical
class OpenAPIAddResponseNone(Codemod, Skill):
    """This one adds a `@xys_ns.response(200)` decorator to Flask Resource methods that do not contain any return status codes

    Before:

        @xyz_ns.route("/ping", methods=["GET"])
        class XYZResource(Resource):

            @decorator
            def get(self):
                return "pong"

    After:

        @xyz_ns.route("/ping", methods=["GET"])
        class XYZResource(Resource):

            @decorator
            @xyz_ns.response(200)
            def get(self):
                return "pong"
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase):
        def get_response_decorators(method: Symbol) -> list[Decorator]:
            """Returns a list of decorators that contain the string '.response' in the source code"""
            return [d for d in method.decorators if ".response" in d.source]

        def get_namespace_decorator(symbol: Symbol) -> Decorator | None:
            """Returns the first decorator that contains the string '.route' in the source code"""
            matches = [d for d in symbol.decorators if ".route" in d.source]
            if len(matches) == 0:
                return None
            return matches[0]

        for cls in codebase.classes:
            # Get Flask Resource classes
            if cls.superclasses and any("Resource" in sc.source for sc in cls.superclasses):
                for method in cls.methods:
                    # Filter to HTTP methods
                    if method.name in ("get", "post", "put", "patch", "delete"):
                        # Check if it has no `@response` decorators
                        response_decorators = get_response_decorators(method)
                        if len(response_decorators) == 0:
                            # Make sure it has `@xys.route` on the class
                            ns_decorator = get_namespace_decorator(cls)
                            if ns_decorator is not None:
                                # Check if returns a status code
                                if method.return_statements and not any(ret.value and ret.value.ts_node_type == "expression_list" for ret in method.return_statements):
                                    # Extract the namespace name
                                    ns_name = ns_decorator.source.split("@")[1].split(".")[0]
                                    # Add the decorator
                                    method.add_decorator(f"@{ns_name}.response(200)")
