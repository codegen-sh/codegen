import ast
import inspect
import textwrap
from collections.abc import Callable

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.compilation.string_to_code import create_execute_function_from_codeblock
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.skill_test import SkillTestCase
from tests.shared.skills.verify_skill_output import verify_skill_output


class SkillImplementation:
    """Represents a Skill."""

    name: str
    language: ProgrammingLanguage
    prompt: str = None
    test_cases: list[SkillTestCase]
    repo_id: int | None = None
    _skill_func: Callable[[CodebaseType], None]
    eval_skill: bool = False
    guide_skill: bool = False

    def __init__(
        self,
        test_cases: list[SkillTestCase],
        skill_func: Callable[[CodebaseType], None],
        language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
        name: str = "",
        repo_id: int | None = None,
        prompt: str | None = None,
        eval_skill: bool = False,
        skip_test: bool = False,
        si_id: int | None = None,
        from_app: bool = False,
        external: bool = False,
    ):
        self.name = name or skill_func.__name__
        self.language = language
        self.test_cases = [] if skip_test else test_cases
        if not (skip_test or from_app) and len(self.test_cases) == 0:
            msg = "Skill must have at least one test case"
            raise Exception(msg)
        self.repo_id = repo_id
        self._skill_func = skill_func
        self.eval_skill = eval_skill
        self.prompt = prompt
        self.doc = skill_func.__doc__
        self.external = external
        if si_id is not None:
            self.id = si_id

    def run_test_cases(self, tmpdir: str, get_diff: bool = False, snapshot=None) -> str | None:
        for test_case in self.test_cases:
            with get_codebase_session(tmpdir=tmpdir, programming_language=self.language, files=test_case.to_input_dict(), verify_output=False) as codebase:
                self._skill_func(codebase)
                codebase.commit()
                diff = verify_skill_output(codebase, self, test_case, get_diff, snapshot)
                if get_diff:
                    return diff
        return None

    @classmethod
    def from_source(cls, source: str, name: str, language: ProgrammingLanguage, test_cases: list[SkillTestCase], skip_test: bool = False) -> "SkillImplementation":
        """Create a new Skill instance from source code.

        :param source: The source code of the skill function.
        :param name: The name of the skill.
        :param language: The programming language of the skill.
        :param test_cases: The test cases for the skill.
        :return: A new Skill instance.
        """
        skill_func = create_execute_function_from_codeblock(codeblock=source, func_name="skill_func")

        # Create and return a new Skill instance
        return cls(test_cases=test_cases, skill_func=skill_func, name=name, language=language, skip_test=skip_test)

    @property
    def function_body(self) -> str:
        """Return the source code of the skill function, excluding the function declaration and docstring."""
        source = inspect.getsource(self._skill_func)

        try:
            tree = ast.parse(source)
        except SyntaxError:
            source = textwrap.dedent(source)
            tree = ast.parse(source)

        func_def = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))

        # Get the source lines
        source_lines = source.splitlines()

        # Find the start line of the function body
        start_line = func_def.body[0].lineno - 1  # -1 because lineno is 1-indexed

        # Find the end line of the function
        end_line = func_def.end_lineno if hasattr(func_def, "end_lineno") else len(source_lines)

        # Extract the function body
        body_lines = source_lines[start_line:end_line]

        # Remove docstring if it exists
        if body_lines and ast.get_docstring(func_def):
            docstring_node = func_def.body[0]
            docstring_end = docstring_node.end_lineno - func_def.lineno
            body_lines = body_lines[docstring_end:]

        # Remove any leading empty lines
        while body_lines and not body_lines[0].strip():
            body_lines = body_lines[1:]

        # Dedent the body
        body_source = textwrap.dedent("\n".join(body_lines))

        return body_source.strip()

    def __call__(self, codebase: CodebaseType):
        self._skill_func(codebase)

    def __str__(self):
        source = inspect.getsource(self._skill_func)
        return textwrap.dedent(source).strip()
