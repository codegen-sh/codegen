<br />

<p align="center">
  <a href="https://docs.codegen.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  The SWE that Never Sleeps
</h2>

<div align="center">

[![PyPI](https://img.shields.io/badge/PyPi-codegen-gray?style=flat-square&color=blue)](https://pypi.org/project/codegen/)
[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com)
[![Slack Community](https://img.shields.io/badge/Slack-Join-4A154B?logo=slack&style=flat-square)](https://community.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)
[![Follow on X](https://img.shields.io/twitter/follow/codegen?style=social)](https://x.com/codegen)

</div>

<br />

# Codegen SDK

The Codegen SDK provides a programmatic interface to AI-powered code agents provided by [Codegen](https://codegen.com). It enables developers to integrate intelligent code generation, analysis, and transformation capabilities into their workflows and applications.

## Features

- **AI-Powered Code Generation**: Generate code based on natural language descriptions
- **Code Analysis**: Analyze codebases for patterns, issues, and insights
- **Code Transformation**: Refactor and transform code with intelligent understanding of context
- **Multi-Language Support**: Works with Python, JavaScript, TypeScript, and more
- **Integration with Development Workflows**: Seamlessly integrate with your existing tools
- **Extensible Architecture**: Build custom extensions and workflows

## Installation

Install the SDK using pip or uv:

```bash
pip install codegen
# or
uv pip install codegen
```

Requires Python 3.12 or newer.

## Quick Start

```python
from codegen.agents.agent import Agent

# Initialize the Agent with your organization ID and API token
agent = Agent(
    org_id="YOUR_ORG_ID",  # Find this at codegen.com/developer
    token="YOUR_API_TOKEN",  # Get this from codegen.com/developer
    # base_url="https://codegen-sh-rest-api.modal.run",  # Optional - defaults to production
)

# Run an agent with a prompt
task = agent.run(prompt="Implement a new feature to sort users by last login.")

# Check the initial status
print(task.status)

# Refresh the task to get updated status (tasks can take time)
task.refresh()

# Check the updated status
print(task.status)

# Once task is complete, you can access the result
if task.status == "completed":
    print(task.result)  # Result often contains code, summaries, or links
```

## Advanced Usage

### Working with Specific Files

```python
from codegen.agents.agent import Agent

agent = Agent(org_id="YOUR_ORG_ID", token="YOUR_API_TOKEN")

# Analyze a specific file
task = agent.run(
    prompt="Analyze this file for potential bugs and suggest improvements.",
    files=["path/to/your/file.py"]
)

# Wait for completion and get results
task.wait_until_complete()
print(task.result)
```

### Transforming Code

```python
from codegen.agents.agent import Agent

agent = Agent(org_id="YOUR_ORG_ID", token="YOUR_API_TOKEN")

# Transform code based on requirements
task = agent.run(
    prompt="Refactor this code to use async/await pattern instead of callbacks.",
    files=["path/to/your/file.js"]
)

# Wait for completion and get results
task.wait_until_complete()
print(task.result)
```

## Command Line Interface

The SDK includes a powerful CLI tool that allows you to interact with Codegen directly from your terminal:

```bash
# Get help
codegen --help

# Initialize configuration
codegen init

# Run an agent with a prompt
codegen run "Implement a function to calculate Fibonacci numbers"

# Analyze a file
codegen analyze path/to/file.py
```

## Integrations

Codegen integrates with popular development tools:

- **Slack**: Chat with your AI engineer in Slack
- **GitHub**: Get PR reviews and code suggestions
- **Linear**: Manage tasks and issues with AI assistance
- **Web Interface**: Use the web UI at [codegen.com](https://codegen.com)

## Resources

- [Documentation](https://docs.codegen.com)
- [Getting Started Guide](https://docs.codegen.com/introduction/getting-started)
- [API Reference](https://docs.codegen.com/api-reference)
- [Examples](https://github.com/codegen-sh/codegen-examples)
- [Contributing Guide](CONTRIBUTING.md)
- [Contact Us](https://codegen.com/contact)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to set up the development environment and submit contributions.

## Enterprise

For more information on enterprise engagements, please [contact us](https://codegen.com/contact) or [request a demo](https://codegen.com/request-demo).

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

