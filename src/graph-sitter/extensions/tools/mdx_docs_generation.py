import re

from codegen.sdk.code_generation.doc_utils.schemas import ClassDoc, MethodDoc, ParameterDoc
from codegen.sdk.code_generation.doc_utils.utils import sanitize_html_for_mdx, sanitize_mdx_mintlify_description


def render_mdx_page_for_class(cls_doc: ClassDoc) -> str:
    """Renders the MDX for a single class"""
    return f"""{render_mdx_page_title(cls_doc)}
{render_mdx_inheritence_section(cls_doc)}
{render_mdx_attributes_section(cls_doc)}
{render_mdx_methods_section(cls_doc)}
"""


def render_mdx_page_title(cls_doc: ClassDoc, icon: str | None = None) -> str:
    """Renders the MDX for the page title"""
    page_desc = cls_doc.description if hasattr(cls_doc, "description") else ""

    return f"""---
title: "{cls_doc.title}"
sidebarTitle: "{cls_doc.title}"
icon: "{icon if icon else ""}"
description: "{sanitize_mdx_mintlify_description(page_desc)}"
---
import {{Parameter}} from '/snippets/Parameter.mdx';
import {{ParameterWrapper}} from '/snippets/ParameterWrapper.mdx';
import {{Return}} from '/snippets/Return.mdx';
import {{HorizontalDivider}} from '/snippets/HorizontalDivider.mdx';
import {{GithubLinkNote}} from '/snippets/GithubLinkNote.mdx';
import {{Attribute}} from '/snippets/Attribute.mdx';

<GithubLinkNote link="{cls_doc.github_url}" />
"""


def render_mdx_inheritence_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the inheritence section"""
    # Filter on parents who we have docs for
    parents = cls_doc.inherits_from
    if not parents:
        return ""
    parents_string = ", ".join([parse_link(parent) for parent in parents])
    return f"""### Inherits from
{parents_string}
"""


def render_mdx_attributes_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the attributes section"""
    sorted_attributes = sorted(cls_doc.attributes + [method for method in cls_doc.methods if method.method_type == "property"], key=lambda x: x.name)
    if len(sorted_attributes) <= 0:
        return ""
    attributes_mdx_string = "\n".join([render_mdx_for_attribute(attribute) for attribute in sorted_attributes])

    return f"""## Attributes
<HorizontalDivider />
{attributes_mdx_string}
"""


def render_mdx_methods_section(cls_doc: ClassDoc) -> str:
    """Renders the MDX for the methods section"""
    sorted_methods = sorted(cls_doc.methods, key=lambda x: x.name)
    if len(sorted_methods) <= 0:
        return ""
    methods_mdx_string = "\n".join([render_mdx_for_method(method) for method in sorted_methods if method.method_type == "method"])

    return f"""## Methods
<HorizontalDivider />
{methods_mdx_string}
"""


def render_mdx_for_attribute(attribute: MethodDoc) -> str:
    """Renders the MDX for a single attribute"""
    attribute_docstring = sanitize_mdx_mintlify_description(attribute.description)
    if len(attribute.return_type) > 0:
        return_type = f"{resolve_type_string(attribute.return_type[0])}"
    else:
        return_type = ""
    if not attribute_docstring:
        attribute_docstring = "\n"
    return f"""### <span className="text-primary">{attribute.name}</span>
<HorizontalDivider light={{true}} />
<Attribute type={{ {return_type if return_type else "<span></span>"} }} description="{attribute_docstring}" />
"""


########################################################################################################################
# METHODS
########################################################################################################################


def format_parameter_for_mdx(parameter: ParameterDoc) -> str:
    type_string = resolve_type_string(parameter.type)
    return f"""
<Parameter
    name="{parameter.name}"
    type={{ {type_string} }}
    description="{sanitize_html_for_mdx(parameter.description)}"
    defaultValue="{sanitize_html_for_mdx(parameter.default)}"
/>
""".strip()


def format_parameters_for_mdx(parameters: list[ParameterDoc]) -> str:
    return "\n".join([format_parameter_for_mdx(parameter) for parameter in parameters])


def format_return_for_mdx(return_type: list[str], return_description: str) -> str:
    description = sanitize_html_for_mdx(return_description) if return_description else ""
    return_type = resolve_type_string(return_type[0])

    return f"""
<Return return_type={{ {return_type} }} description="{description}"/>
"""


def render_mdx_for_method(method: MethodDoc) -> str:
    description = sanitize_mdx_mintlify_description(method.description)
    # =====[ RENDER ]=====
    # TODO add links here
    # TODO add inheritence info here
    mdx_string = f"""### <span className="text-primary">{method.name}</span>
{description}
<GithubLinkNote link="{method.github_url}" />
"""
    if method.parameters:
        mdx_string += f"""
<ParameterWrapper>
{format_parameters_for_mdx(method.parameters)}
</ParameterWrapper>
"""
    if method.return_type:
        mdx_string += f"""
{format_return_for_mdx(method.return_type, method.return_description)}
"""

    return mdx_string


def get_mdx_route_for_class(cls_doc: ClassDoc) -> str:
    """Get the expected MDX route for a class
    split by /core, /python, and /typescript
    """
    lower_class_name = cls_doc.title.lower()
    if lower_class_name.startswith("py"):
        return f"codebase-sdk/python/{cls_doc.title}"
    elif lower_class_name.startswith(("ts", "jsx")):
        return f"codebase-sdk/typescript/{cls_doc.title}"
    else:
        return f"codebase-sdk/core/{cls_doc.title}"


def format_type_string(type_string: str) -> str:
    type_string = type_string.split("|")
    return " | ".join([type_str.strip() for type_str in type_string])


def resolve_type_string(type_string: str) -> str:
    if "<" in type_string:
        return f"<>{parse_link(type_string, href=True)}</>"
    else:
        return f'<code className="text-sm bg-gray-100 px-2 py-0.5 rounded">{format_type_string(type_string)}</code>'


def format_builtin_type_string(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([type_str.strip() for type_str in type_strings])
    return type_string


def span_type_string_by_pipe(type_string: str) -> str:
    if "|" in type_string:
        type_strings = type_string.split("|")
        return " | ".join([f"<span>{type_str.strip()}</span>" for type_str in type_strings])
    return type_string


def parse_link(type_string: str, href: bool = False) -> str:
    # Match components with angle brackets, handling nested structures

    parts = [p for p in re.split(r"(<[^>]+>)", type_string) if p]

    result = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            # Extract the path from between angle brackets
            path = part[1:-1]
            symbol = path.split("/")[-1]

            # Create a Link object
            link = f'<a href="/{path}" style={{ {{fontWeight: "inherit", fontSize: "inherit"}} }}>{symbol}</a>' if href else f"[{symbol}](/{path})"
            result.append(link)
        else:
            part = format_builtin_type_string(part)
            if href:
                result.append(f"<span>{part.strip()}</span>")
            else:
                result.append(part.strip())

    return " ".join(result)
