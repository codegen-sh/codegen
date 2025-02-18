import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING

import inflection

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.skill_implementation import SkillImplementation
from tests.shared.skills.skill_test import SkillTestCase
from tests.shared.skills.utils import skill_name_to_skill_implementations, skills

if TYPE_CHECKING:
    from tests.shared.skills.skill import Skill

ExecuteFuncType = Callable[[CodebaseType], None]


def skill_impl(
    test_cases: list[SkillTestCase],
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    eval_skill: bool = False,
    skip_test: bool = False,
    prompt: str | None = None,
    ignore: bool = False,
    si_id: int | None = None,
    from_app: bool = False,
    external: bool = False,
) -> Callable[[ExecuteFuncType], ExecuteFuncType]:
    """Decorator for Skill functions. Returns a Skill when you wrap a function with it."""

    def decorator(func: [ExecuteFuncType | type]) -> Callable[[CodebaseType], None]:
        if ignore:
            return func
        new_skill = SkillImplementation(
            test_cases=test_cases,
            skill_func=func,
            language=language,
            eval_skill=eval_skill,
            skip_test=skip_test,
            prompt=prompt,
            si_id=si_id,
            from_app=from_app,
            external=external,
        )

        # Set the language-specific implementation on the parent class
        if func is not None:
            qualname_as_array = func.__qualname__.split(".")
            if len(qualname_as_array) > 1:
                assert properly_named_function(name=func.__name__, language=language), skill_func_name_error(name=func.__name__, language=language)
                if language == ProgrammingLanguage.PYTHON:
                    if not hasattr(func, "python_skill_implementation"):
                        func.python_skill_implementation = new_skill
                elif language == ProgrammingLanguage.TYPESCRIPT:
                    if not hasattr(func, "typescript_skill_implementation"):
                        func.typescript_skill_implementation = new_skill
                return func

            elif inspect.isfunction(func):
                msg = "Please structure your skill as a Class."
                raise ValueError(msg)

            else:
                msg = f"Unsupported function type: {type(func)}"
                raise ValueError(msg)

    return decorator


def properly_named_function(name: str, language: ProgrammingLanguage):
    if language == ProgrammingLanguage.PYTHON:
        return name == "skill_func" or name == "python_skill_func" or name == "execute"
    elif language == ProgrammingLanguage.TYPESCRIPT:
        return name == "skill_func" or name == "typescript_skill_func" or name == "execute"
    else:
        return False


def skill_func_name_error(name: str, language: ProgrammingLanguage):
    if language == ProgrammingLanguage.PYTHON:
        return f"Function name must be 'skill_func', 'python_skill_func' or 'execute' for Python skills. Got {name}."
    elif language == ProgrammingLanguage.TYPESCRIPT:
        return f"Function name must be 'skill_func', 'typescript_skill_func' or 'execute' for TypeScript skills. Got {name}."
    else:
        return "Unsupported language."


def populate_skill_implementation(skill_imp: "SkillImplementation", sk: "Skill"):
    """Populate a SkillImplementation with the name and eval_skill attribute."""
    skill_imp.name = inflection.underscore(sk.__name__)
    skill_imp.eval_skill = sk.eval_skill
    skill_imp.guide_skill = sk.guide
    if skill_imp.prompt is None:
        if sk.prompt is None:
            msg = f"Prompt is not set for skill: {sk.__name__} ({skill_imp.language}). Prompt must be set in either skill or skill implementation."
            raise ValueError(msg)
        else:
            skill_imp.prompt = sk.prompt
    if skill_imp.doc is None:
        if sk.doc is None:
            msg = f"Docstring is not set for skill: {sk.__name__} ({skill_imp.language}). Docstring must be set in either skill or skill implementation."
            raise ValueError(msg)
        else:
            skill_imp.doc = sk.doc
    return skill_imp


def skill(uid: str, eval_skill: bool = False, prompt: str | None = None, s_id: int | None = None, guide: bool = False, canonical=True):
    """Decorator for Skill classes. Adds the class to the skills list."""

    def decorator(cls):
        cls.prompt = prompt
        cls.name = inflection.underscore(cls.__name__)
        cls.doc = cls.__doc__
        cls.eval_skill = eval_skill
        cls.id = s_id
        cls.guide = guide
        cls.canonical = canonical
        cls.uid = uid
        new_attributes = {}
        for name, method in cls.__dict__.items():
            if name not in ["python_skill_func", "typescript_skill_func", "skill_func", "execute"] or not callable(method):
                continue
            if hasattr(method, "__func__"):
                func = method.__func__
            else:
                func = method

            if hasattr(func, "python_skill_implementation"):
                skill_imp = func.python_skill_implementation
                new_attributes["python_skill_implementation"] = populate_skill_implementation(skill_imp, cls)
            if hasattr(func, "typescript_skill_implementation"):
                skill_imp = func.typescript_skill_implementation
                new_attributes["typescript_skill_implementation"] = populate_skill_implementation(skill_imp, cls)
        for name, value in new_attributes.items():
            setattr(cls, name, value)

        if cls.name not in skill_name_to_skill_implementations:
            skill_name_to_skill_implementations[cls.name] = cls.implementations()
            skills.append(cls)
        else:
            msg = f"Skill with name {cls.name} ({cls.__name__}) already exists. Please Rename the skill class."
            raise ValueError(msg)
        return cls

    return decorator
