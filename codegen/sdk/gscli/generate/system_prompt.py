import json
from pathlib import Path

docs = Path("./docs")
mint = json.load(open(docs / "mint.json"))


def render_page(page_str: str):
    return open(docs / (page_str + ".mdx")).read()


def render_group(page_strs: list[str]):
    return "\n\n".join([render_page(x) for x in page_strs])


def get_group(name) -> list[str]:
    group = next((x for x in mint["navigation"] if x.get("group") == name), None)
    if group:
        return group["pages"]


def render_groups(group_names: list[str]) -> str:
    groups = [get_group(x) for x in group_names]
    return "\n\n".join([render_group(g) for g in groups])


def get_system_prompt() -> str:
    """Generates a string system prompt based on the docs"""
    return render_groups(["Introduction", "Building with Codegen", "Tutorials"])
