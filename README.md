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

The Codegen SDK provides a programmatic interface to code agents provided by [Codegen](https://codegen.com).

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

## Installation and Usage

Install the SDK using pip or uv:

```bash
pip install codegen
# or
uv pip install codegen
```

Get started at [codegen.com](https://codegen.com) and get your API token at [codegen.com/developer](https://codegen.com/developer).

You can interact with your AI engineer via API, or chat with it in Slack, Linear, Github, or on our website.

## Resources

- [Docs](https://docs.codegen.com)
- [Getting Started](https://docs.codegen.com/introduction/getting-started)
- [Contributing](CONTRIBUTING.md)
- [Contact Us](https://codegen.com/contact)

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to set up the development environment and submit contributions.

## Enterprise

For more information on enterprise engagements, please [contact us](https://codegen.com/contact) or [request a demo](https://codegen.com/request-demo).
