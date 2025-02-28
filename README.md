<br />

<p align="center">
  <a href="https://docs.codegen.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  Scriptable interface to a powerful, multi-lingual language server.
</h2>

<div align="center">

[![PyPI](https://img.shields.io/badge/PyPi-codegen-gray?style=flat-square&color=blue)](https://pypi.org/project/codegen/)
[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com)
[![Slack Community](https://img.shields.io/badge/Slack-Join-4A154B?logo=slack&style=flat-square)](https://community.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)
[![Follow on X](https://img.shields.io/twitter/follow/codegen?style=social)](https://x.com/codegen)

</div>

<br />

[Codegen](https://docs.codegen.com) is a python library for manipulating codebases.

```python
from codegen import Codebase

# Codegen builds a complete graph connecting
# functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.move_to_file("deprecated.py")
```

Write code that transforms code. Codegen combines the parsing power of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) with the graph algorithms of [rustworkx](https://github.com/Qiskit/rustworkx) to enable scriptable, multi-language code manipulation at scale.

## Installation and Usage

We support

- Running Codegen in Python 3.12 - 3.13 (recommended: Python 3.13+)
- macOS and Linux
  - macOS is supported
  - Linux is supported on x86_64 and aarch64 with glibc 2.34+
  - Windows is supported via WSL. See [here](https://docs.codegen.com/building-with-codegen/codegen-with-wsl) for more details.
- Python, Typescript, Javascript and React codebases

```
# Install inside existing project
uv pip install codegen

# Install global CLI
uv tool install codegen --python 3.13

# Create a codemod for a given repo
cd path/to/repo
codegen init
codegen create test-function

# Run the codemod
codegen run test-function

# Create an isolated venv with codegen => open jupyter
codegen notebook
```

## Usage

See [Getting Started](https://docs.codegen.com/introduction/getting-started) for a full tutorial.

```
from codegen import Codebase
```

## Troubleshooting

Having issues? Here are some common problems and their solutions:

- **I'm hitting an UV error related to `[[ packages ]]`**: This means you're likely using an outdated version of UV. Try updating to the latest version with: `uv self update`.
- **I'm hitting an error about `No module named 'codegen.sdk.extensions.utils'`**: The compiled cython extensions are out of sync. Update them with `uv sync --reinstall-package codegen`.
- **I'm hitting a `RecursionError: maximum recursion depth exceeded` error while parsing my codebase**: If you are using python 3.12, try upgrading to 3.13. If you are already on 3.13, try upping the recursion limit with `sys.setrecursionlimit(10000)`.

If you run into additional issues not listed here, please [join our slack community](https://community.codegen.com) and we'll help you out!

## Resources

- [Docs](https://docs.codegen.com)
- [Getting Started](https://docs.codegen.com/introduction/getting-started)
- [Contributing](CONTRIBUTING.md)
- [Contact Us](https://codegen.com/contact)

## Why Codegen?

Software development is fundamentally programmatic. Refactoring a codebase, enforcing patterns, or analyzing control flow - these are all operations that can (and should) be expressed as programs themselves.

We built Codegen backwards from real-world refactors performed on enterprise codebases. Instead of starting with theoretical abstractions, we focused on creating APIs that match how developers actually think about code changes:

- **Natural mental model**: Write transforms that read like your thought process - "move this function", "rename this variable", "add this parameter". No more wrestling with ASTs or manual import management.

- **Battle-tested on complex codebases**: Handle Python, TypeScript, and React codebases with millions of lines of code.

- **Built for advanced intelligences**: As AI developers become more sophisticated, they need expressive yet precise tools to manipulate code. Codegen provides a programmatic interface that both humans and AI can use to express complex transformations through code itself.

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to set up the development environment and submit contributions.

## Enterprise

For more information on enterprise engagements, please [contact us](https://codegen.com/contact) or [request a demo](https://codegen.com/request-demo).
