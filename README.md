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

The Codegen SDK provides both AI-powered code agents and a comprehensive programmatic interface for codebase manipulation. Whether you need an AI agent to handle complex software engineering tasks or want to build custom code transformation tools, Codegen has you covered.

## Overview

Codegen serves three primary use cases:

**🤖 AI Code Agents** - Deploy intelligent agents that integrate with GitHub, Slack, and Linear to review PRs, implement features, fix bugs, and manage issues automatically.

**🔧 Codebase SDK** - Build custom tools for code analysis, refactoring, and transformation across Python, TypeScript, JavaScript, and React codebases with automatic import and dependency management.

**📊 SWE-Bench Evaluation** - Benchmark and evaluate code generation models against real-world software engineering tasks with automated evaluation pipelines.

### AI Agent API

Deploy intelligent agents for automated software engineering tasks:

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

### Codebase SDK

Programmatically analyze and transform your codebase:

```python
from codegen.sdk.codebase import Codebase

# Load a codebase for analysis and transformation
codebase = Codebase.from_repo("path/to/your/repo")

# Analyze code structure
for function in codebase.functions:
    print(f"Function: {function.name}")
    print(f"File: {function.file.path}")
    print(f"Usages: {len(function.usages)}")

# Find and modify specific patterns
for file in codebase.files:
    if file.path.endswith('.py'):
        # Analyze imports, dependencies, and symbols
        for import_stmt in file.imports:
            print(f"Import: {import_stmt}")
```

## Installation

**Requirements:** Python 3.12 - 3.13

Install the SDK using uv (recommended) or pip:

```bash
# Recommended: using uv
uv pip install codegen

# Alternative: using pip
pip install codegen
```

For development setup, see our [Contributing Guide](CONTRIBUTING.md).

## Getting Started

**For AI Agents:** Get started at [codegen.com](https://codegen.com) and get your API token at [codegen.com/developer](https://codegen.com/developer). You can interact with your AI engineer via API, or chat with it in Slack, Linear, GitHub, or on our website.

**For SDK Development:** Check out our comprehensive documentation and tutorials to start building with the Codebase SDK.

## Features

- **🤖 AI Code Agents** - Intelligent agents for automated software engineering
- **🔧 Multi-Language Support** - Python, TypeScript, JavaScript, and React
- **📊 Code Analysis** - Dependency graphs, symbol resolution, and usage tracking  
- **🔄 Code Transformation** - Safe, large-scale refactoring and modernization
- **🔗 Integrations** - GitHub, Slack, Linear, and MCP (Model Context Protocol)
- **📈 SWE-Bench Evaluation** - Benchmark code generation models
- **🛠️ Developer Tools** - CLI, Jupyter notebooks, and IDE extensions

## Resources

### Documentation
- [Documentation](https://docs.codegen.com) - Complete guides and API reference
- [Graph-sitter Getting Started](https://docs.codegen.com/graph-sitter/getting-started) - SDK tutorials and examples
- [API Reference](https://docs.codegen.com/api-reference/index) - Detailed API documentation

### Integrations
- [GitHub Integration](https://docs.codegen.com/integrations/github) - Automated PR reviews and issue management
- [Slack Integration](https://docs.codegen.com/integrations/slack) - Chat-based code assistance
- [Linear Integration](https://docs.codegen.com/integrations/linear) - Issue tracking integration
- [MCP Servers](https://docs.codegen.com/integrations/mcp) - Model Context Protocol support

### Community & Support
- [Slack Community](https://community.codegen.com) - Join our developer community
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Contact Us](https://codegen.com/contact) - Get in touch with our team

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to set up the development environment and submit contributions.

## Enterprise

For more information on enterprise engagements, please [contact us](https://codegen.com/contact) or [request a demo](https://codegen.com/request-demo).
