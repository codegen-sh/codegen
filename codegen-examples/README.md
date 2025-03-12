# Codegen Examples

[![Documentation](https://img.shields.io/badge/docs-docs.codegen.com-blue)](https://docs.codegen.com)

This is a collection of examples using [Codegen](https://codegen.com). You can use these examples to learn how to use Codegen and build custom code transformations.

## Setup

We recommend using [`uv`](https://github.com/astral-sh/uv) with Python 3.13 for the best experience.

To install Codegen, please follow the [official installation guide](https://docs.codegen.com/introduction/installation). Once Codegen is installed, use these steps to run the examples in this repository:

Install the Codegen CLI globally

```bash
uv tool install codegen
```

Initialize Codegen in your project

```bash
codegen init
```

Activate the virtual environment

```bash
source .codegen/.venv/bin/activate
```

Your environment is now ready to run example codemods.

### IDE Configuration (Optional)

To configure your IDE for optimal use with Codegen, follow our [IDE setup guide](https://docs.codegen.com/introduction/ide-usage#configuring-your-ide-interpreter).

## Examples

Within the examples folder, each subdirectory contains a self-contained example with:

- An explanation of the transformation (`README.md`)
- A Codegen script that performs the transformation (`run.py`)
- Sample code to transform, if not using a repository (`input_repo/`)

To see a transformation, simply run the `run.py` script within the desired directory.

## Learn More

- [Documentation](https://docs.codegen.com)
- [Getting Started Guide](https://docs.codegen.com/introduction/getting-started)
- [Tutorials](https://docs.codegen.com/tutorials/at-a-glance)
- [API Reference](https://docs.codegen.com/api-reference)

## Contributing

Have a useful example to share? We'd love to include it! Please see our [Contributing Guide](CONTRIBUTING.md) for instructions.

## License

The [Apache 2.0 license](LICENSE).
