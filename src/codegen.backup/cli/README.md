# Codegen CLI

A codegen module that handles all `codegen` CLI commands.

### Dependencies

- [codegen.sdk](https://github.com/codegen-sh/codegen-sdk/tree/develop/src/codegen/sdk)
- [codegen.shared](https://github.com/codegen-sh/codegen-sdk/tree/develop/src/codegen/shared)

## Best Practices

- Each folder in `cli` should correspond to a command group. The name of the folder should be the name of the command group. Ex: `task` for codegen task commands.
- The command group folder should have a file called `commands.py` where the CLI group (i.e. function decorated with `@click.group()`) and CLI commands are defined (i.e. functions decorated with ex: `@task.command()`) and if necessary a folder called `utils` (or a single `utils.py`) that holds any additional files with helpers/utilities that are specific to the command group.
- Store utils specific to a CLI command group within its folder.
- Store utils that can be shared across command groups in an appropriate file in cli/utils. If none exists, create a new appropriately named one!
