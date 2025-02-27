import ast
import os
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import astor

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class MethodRemover(ast.NodeTransformer):
    def __init__(self, conditions: list[Callable[[ast.FunctionDef], bool]]):
        self.conditions = conditions

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        body = []

        for child in node.body:
            if not self.should_remove(child):
                body.append(child)
            else:
                logger.debug("removing", child.name)
        node.body = body
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef | None:
        body = []
        for child in node.body:
            if not (isinstance(child, ast.FunctionDef) and any(cond(child) for cond in self.conditions)):
                body.append(child)
            else:
                logger.debug("removing", child.name)
        node.body = body
        return self.generic_visit(node)

    def should_remove(self, node: ast.FunctionDef | ast.AnnAssign) -> bool:
        if isinstance(node, ast.FunctionDef):
            return any(cond(node) for cond in self.conditions)

        return False


class FieldRemover(ast.NodeTransformer):
    def __init__(self, conditions: list[Callable[[ast.FunctionDef], bool]]):
        self.conditions = conditions

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        body = []
        for child in node.body:
            if not self.should_remove(child):
                body.append(child)
            else:
                if isinstance(child, ast.AnnAssign):
                    logger.debug("removing", child.target.id)
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        logger.debug("removing", target.id)
        node.body = body
        return self.generic_visit(node)

    def should_remove(self, node: ast.AnnAssign | ast.Assign) -> bool:
        if isinstance(node, ast.AnnAssign):
            return any(cond(node) for cond in self.conditions)

        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                # Check if it's a property annotation (e.g., var: property)
                return any(cond(node) for cond in self.conditions)
        return False


def _remove_methods(source: str, conditions: list[Callable[[ast.FunctionDef], bool]]) -> str:
    tree = ast.parse(source)
    transformer = MethodRemover(conditions)
    modified_tree = transformer.visit(tree)
    return astor.to_source(modified_tree)


def _remove_fields(source: str, conditions: list[Callable[[ast.FunctionDef], bool]]) -> str:
    tree = ast.parse(source)
    transformer = FieldRemover(conditions)
    modified_tree = transformer.visit(tree)
    return astor.to_source(modified_tree)


def _starts_with_underscore(node: ast.FunctionDef | ast.AnnAssign | ast.Assign) -> bool:
    if isinstance(node, ast.FunctionDef):
        return node.name.startswith("_") and (not node.name.startswith("__") and not node.name.endswith("__"))
    elif isinstance(node, ast.Assign):
        return node.targets[0].id.startswith("_")
    elif isinstance(node, ast.AnnAssign):
        return node.target.id.startswith("_")
    return False


def _has_decorator(decorator_name: str) -> Callable[[ast.FunctionDef], bool]:
    def test(node):
        has = any(isinstance(d, ast.Name) and d.id == decorator_name for d in node.decorator_list)
        # if (has):
        # logger.debug(node.name, 'has decorator', [d.id for d in node.decorator_list])
        return has

    return test


def _matches_regex(pattern: str) -> Callable[[ast.FunctionDef], bool]:
    return lambda node: re.match(pattern, node.name) is not None


def _strip_internal_symbols(file: str, root: str) -> None:
    if file.endswith(".pyi"):
        file_path = os.path.join(root, file)
        with open(file_path) as f:
            original_content = f.read()

        conditions = [
            _starts_with_underscore,
            _has_decorator("noapidoc"),
        ]

        modified_content = _remove_fields(original_content, [_starts_with_underscore])
        modified_content = _remove_methods(modified_content, conditions)

        if modified_content.strip().endswith(":"):
            modified_content += "    pass\n"
        with open(file_path, "w") as f:
            f.write(modified_content)
        logger.debug(f"Typestub file {file_path} has been modified.")


def strip_internal_symbols(typing_directory: str) -> None:
    with ThreadPoolExecutor() as exec:
        for root, _, files in os.walk(typing_directory):
            for file in files:
                exec.submit(_strip_internal_symbols, file, root)
