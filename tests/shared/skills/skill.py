import inspect
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING

from codegen.sdk.core.codebase import Codebase, CodebaseType, PyCodebaseType, TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from tests.shared.skills.skill_implementation import SkillImplementation


class Skill(ABC):
    eval_skill: bool = False
    name: str = None
    python_skill_implementation: "SkillImplementation" = None
    typescript_skill_implementation: "SkillImplementation" = None
    prompt: str = None
    doc: str = None
    id: int | None = None
    guide: bool = False
    canonical: bool = False
    uid: str = None

    @staticmethod
    def python_skill_func(codebase: PyCodebaseType) -> callable: ...

    @staticmethod
    def typescript_skill_func(codebase: TSCodebaseType) -> callable: ...

    @staticmethod
    def skill_func(codebase: CodebaseType): ...

    def execute(self, codebase: Codebase) -> None: ...

    @classmethod
    def implementations(cls) -> list["SkillImplementation"]:
        return [impl for impl in [cls.python_skill_implementation, cls.typescript_skill_implementation] if impl is not None]

    @classmethod
    def language_to_skill_imp_dict(cls) -> dict[ProgrammingLanguage, "SkillImplementation"]:
        return {skill_imp.language: skill_imp for skill_imp in cls.implementations()}

    @staticmethod
    def languages() -> list[ProgrammingLanguage]:
        return [ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT]

    @classmethod
    def generate_snippet(cls, skill_doc=False) -> None | str:
        """Creates a mdx file with the source code of the skill that can be used in the docs."""
        skill_implementations = cls.implementations()
        snippet = ""
        match len(skill_implementations):
            case 0:
                return
            case 1:
                if skill_implementations[0].language == ProgrammingLanguage.PYTHON:
                    code_source = cls.python_skill_implementation.function_body
                    snippet = f"```python\n{cls.extract_code_snippet(code_source)}\n```"
                elif skill_implementations[0].language == ProgrammingLanguage.TYPESCRIPT:
                    code_source = cls.typescript_skill_implementation.function_body
                    snippet = f"```typescript\n{cls.extract_code_snippet(code_source)}\n```"
            case 2:
                snippet = f"""<CodeGroup>
```python python
{cls.extract_code_snippet(cls.python_skill_implementation.function_body)}
```

```python typescript
{cls.extract_code_snippet(cls.typescript_skill_implementation.function_body)}
```
</CodeGroup>"""

        if skill_doc:
            snippet = (
                f"""## {cls.name}

{cls.doc}
"""
                + "\n"
                + snippet
            )

        # ===== [Return Snippet Source] =====
        return snippet

    @classmethod
    def guide_path(cls) -> Path:
        # ===== [Path Where Skill is Defined] =====
        filepath = Path(inspect.getfile(cls).removesuffix(".py"))
        filepath_tuple = filepath.parts

        # ===== [Path from Guides] =====
        if "guides" not in filepath_tuple:
            msg = f"Skill {cls.name} is not in a guides directory"
            raise ValueError(msg)
        guides_index = filepath_tuple.index("guides")
        guides_path = Path("/".join(filepath.parts[guides_index:]))

        return guides_path

    @staticmethod
    def extract_code_snippet(source: str) -> str:
        """Extract the code snippet to be shown from the source code of a skill function."""
        if CODE_SNIPPET not in source:
            return source.strip()
        return source.split(CODE_SNIPPET)[1].strip()


CODE_SNIPPET = "# =====[ Code Snippet ]====="
