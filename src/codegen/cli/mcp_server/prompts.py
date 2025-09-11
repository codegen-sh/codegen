"""Prompts and instructions for the Codegen MCP server."""

MCP_SERVER_INSTRUCTIONS = (
    "Codegen is an operating system for agents. "
    "It allows organizations to run Claude Code instances with superpowers, including unified observability, "
    "dynamic sandboxes, powerful MCP integrations, security and more.\n\n"
    "This MCP server provides permissioned access to integrations configured by your organization. "
    "All tools shown (GitHub, Linear, ClickUp, Notion, Sentry, etc.) are pre-configured and ready to use - "
    "they've been provisioned based on your organization's setup and your role permissions. "
    "You can confidently use any available tool without worrying about authentication or configuration.\n\n"
    "Learn more at https://codegen.com.\n"
    "For documentation, visit https://docs.codegen.com/integrations/mcp.\n"
    "To install and authenticate this server, run: `uv tool install codegen` then `codegen login`."
)
