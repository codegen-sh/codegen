"""Main entry point for the code_smells command."""

import click

from codegen.cli.commands.code_smells import code_smells


@click.group(name="code-smells", help="Detect and refactor code smells in your codebase")
def code_smells_command():
    """Detect and refactor code smells in your codebase."""
    pass


code_smells_command.add_command(code_smells, name="detect")
