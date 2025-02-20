"""Tool for viewing PR contents and modified symbols."""

import re
from enum import StrEnum
from typing import Callable

from codegen.sdk.core.codebase import Codebase


class MessageChannel(StrEnum):
    LINEAR = "linear"
    MARKDOWN = "markdown"
    HTML = "html"
    SLACK = "slack"


def format_link_linear(name: str, url: str) -> str:
    return f"[{name}]({url})"


def format_link_markdown(name: str, url: str) -> str:
    return f"[{name}]({url})"


def format_link_html(name: str, url: str) -> str:
    return f"<a href='{url}'>{name}</a>"


def format_link_slack(name: str, url: str) -> str:
    return f"<{url}|{name}>"


LINK_FORMATS: dict[MessageChannel, Callable[[str, str], str]] = {
    "linear": format_link_linear,
    "markdown": format_link_markdown,
    "html": format_link_html,
    "slack": format_link_slack,
}


def clean_github_url(url: str) -> str:
    """Clean a GitHub URL by removing access tokens and standardizing format."""
    # Remove access token if present
    url = re.sub(r"https://[^@]+@", "https://", url)

    # Ensure it starts with standard github.com
    if not url.startswith("https://github.com"):
        url = "https://github.com" + url.split("github.com")[-1]

    return url


def format_link(name: str, url: str | None, format: MessageChannel = MessageChannel.SLACK) -> str:
    # Clean the URL if it's a GitHub URL
    if url is None:
        url = ""
    if "github.com" in url:
        url = clean_github_url(url)
    return LINK_FORMATS[format](name, url)


def extract_code_snippets(message: str) -> list[str]:
    """Find all text wrapped in single backticks, excluding content in code blocks.

    Args:
        message: The message to process

    Returns:
        List of strings found between single backticks, excluding those in code blocks
    """
    # First remove all code blocks (text between ```)
    code_block_pattern = r"```[^`]*```"
    message_without_blocks = re.sub(code_block_pattern, "", message)

    # Then find all text wrapped in single backticks
    matches = re.findall(r"`([^`]+)`", message_without_blocks)
    return matches


def is_likely_filepath(text: str) -> bool:
    """Check if a string looks like a filepath."""
    # Common file extensions we want to link
    extensions = [".py", ".ts", ".tsx", ".jsx", ".js", ".json", ".mdx", ".md", ".yaml", ".yml", ".toml"]

    # Check if it contains a slash (path separator)
    if "/" in text:
        return True

    # Check if it ends with a common file extension
    return any(text.endswith(ext) for ext in extensions)


def add_links_to_message(message: str, codebase: Codebase, channel: MessageChannel = MessageChannel.SLACK) -> str:
    """Add links to symbols and files in a message.

    This function:
    1. Links code snippets that match symbol names
    2. Links anything that looks like a filepath (files or directories)

    Args:
        message: The message to process
        codebase: The codebase to look up symbols and files in
        channel: The message channel format to use

    Returns:
        The message with appropriate links added
    """
    snippets = extract_code_snippets(message)
    for snippet in snippets:
        # Filepaths
        if is_likely_filepath(snippet):
            # Try as file first
            try:
                file = codebase.get_file(snippet, optional=True)
                if file:
                    link = format_link(snippet, file.github_url, channel)
                    message = message.replace(f"`{snippet}`", link)
                    continue
            except (IsADirectoryError, OSError):
                # Skip if there are any filesystem errors with file access
                pass

            # If not a file, try as directory
            try:
                directory = codebase.get_directory(snippet, optional=True)
                if directory:
                    # TODO: implement `Directory.github_url`
                    github_url = codebase.ctx.base_url
                    github_url = github_url or "https://github.com/your/repo/tree/develop/"  # Fallback URL
                    if github_url.endswith(".git"):
                        github_url = github_url.replace(".git", "/tree/develop/") + str(directory.dirpath)
                    else:
                        github_url = github_url + str(directory.dirpath)
                    print(github_url)
                    link = format_link(snippet, github_url, channel)
                    message = message.replace(f"`{snippet}`", link)
            except (IsADirectoryError, OSError):
                # Skip if there are any filesystem errors with directory access
                pass

        # Symbols
        else:
            symbols = codebase.get_symbols(snippet)
            # Only link if there's exactly one symbol
            if len(symbols) == 1:
                link = format_link(symbols[0].name, symbols[0].github_url, channel)
                message = message.replace(f"`{snippet}`", link)

    return message
