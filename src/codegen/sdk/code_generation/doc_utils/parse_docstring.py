import re

from codegen.sdk.code_generation.doc_utils.schemas import ParameterDoc

SECTION_PATTERN = re.compile(r"(Args|Returns|Raises|Note):\s*(.+?)(?=(?:Args|Returns|Raises|Note):|$)", re.DOTALL)
ARG_PATTERN = re.compile(r"\s*(\w+)\s*\(([^)]+)\):\s*([^\n]+)")


def parse_docstring(docstring: str) -> dict | None:
    """Parse a docstring into its components with optimized performance.

    Args:
        docstring (str): The docstring to parse

    Returns:
        dict | None: Parsed docstring components or None if parsing fails
    """
    # Strip once at the start
    docstring = docstring.strip().strip('"""').strip("'''")

    # Initialize result dictionary
    result = {"description": "", "arguments": [], "return_description": None, "raises": [], "note": None}

    # Find all sections
    sections = {match.group(1): match.group(2).strip() for match in SECTION_PATTERN.finditer(docstring)}

    # Get description (everything before first section)
    first_section = docstring.find(":")
    if first_section != -1:
        result["description"] = docstring[:first_section].split("\n")[0].strip()
    else:
        result["description"] = docstring.split("\n")[0].strip()

    # Parse Args section
    if "Args" in sections:
        args_text = sections["Args"]
        if args_text.lower() != "none":
            result["arguments"] = [ParameterDoc(name=m.group(1), type=m.group(2), description=m.group(3).strip()) for m in ARG_PATTERN.finditer(args_text)]

    # Parse Returns section
    if "Returns" in sections:
        returns_text = sections["Returns"]
        # Split on colon to separate type and description
        parts = returns_text.split(":", 1)
        if len(parts) > 1:
            # Only keep the description part after the colon
            result["return_description"] = " ".join(line.strip() for line in parts[1].split("\n") if line.strip())
        else:
            # If there's no colon, check if it's just a plain description without types
            # Remove any type-like patterns (words followed by brackets or vertical bars)
            cleaned_text = re.sub(r"^[^:]*?(?=\s*[A-Za-z].*:|\s*$)", "", returns_text)
            if cleaned_text:
                result["return_description"] = " ".join(line.strip() for line in cleaned_text.split("\n") if line.strip())

    # Parse Raises section
    if "Raises" in sections:
        raises_text = sections["Raises"]
        for line in raises_text.split("\n"):
            if ":" in line:
                exc_type, desc = line.split(":", 1)
                if exc_type.strip():
                    result["raises"].append({"type": exc_type.strip(), "description": desc.strip()})

    # Parse Note section
    if "Note" in sections:
        result["note"] = " ".join(line.strip() for line in sections["Note"].split("\n") if line.strip())

    return result
