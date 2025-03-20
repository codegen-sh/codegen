# Sentry Integration for Codegen

This module provides integration with Sentry, allowing you to view Sentry issues and events directly from Codegen.

## Features

- View Sentry issues across organizations and projects
- Filter issues by query parameters and status
- View detailed information about specific issues
- View events associated with issues
- View detailed information about specific events, including stack traces

## Setup

### Environment Variables

The following environment variables need to be set:

- `SENTRY_AUTH_TOKEN`: Your Sentry auth token
- `SENTRY_CODEGEN_INSTALLATION_UUID`: The installation UUID for the Codegen Sentry account
- `SENTRY_RAMP_INSTALLATION_UUID`: The installation UUID for the Ramp Sentry account (if applicable)

### Usage

#### Direct Usage

```python
from codegen.extensions.tools.sentry.tools import (
    view_sentry_issues,
    view_sentry_issue_details,
    view_sentry_event_details,
)
from codegen.sdk.core.codebase import Codebase

# Initialize a codebase
codebase = Codebase.from_local("./")

# View issues
issues_result = view_sentry_issues(
    codebase=codebase,
    organization_slug="codegen-sh",
    status="unresolved",
    limit=5,
)
print(issues_result.render())

# View issue details
issue_result = view_sentry_issue_details(
    codebase=codebase,
    issue_id="ISSUE_ID",
    organization_slug="codegen-sh",
)
print(issue_result.render())

# View event details
event_result = view_sentry_event_details(
    codebase=codebase,
    event_id="EVENT_ID",
    organization_slug="codegen-sh",
    project_slug="codegen",
)
print(event_result.render())
```

#### Using LangChain Tools

```python
from codegen.extensions.langchain.sentry_tools import (
    ViewSentryIssuesTool,
    ViewSentryIssueDetailsTool,
    ViewSentryEventDetailsTool,
    ViewSentryTool,
)
from codegen.sdk.core.codebase import Codebase

# Initialize a codebase
codebase = Codebase.from_local("./")

# Initialize the tools
view_issues_tool = ViewSentryIssuesTool(codebase)
view_issue_tool = ViewSentryIssueDetailsTool(codebase)
view_event_tool = ViewSentryEventDetailsTool(codebase)
view_sentry_tool = ViewSentryTool(codebase)

# Use the tools
result = view_sentry_tool._run(
    action="view_issues",
    organization_slug="codegen-sh",
    status="unresolved",
    limit=5,
)
print(result)
```

#### Using the Combined Tool

The `ViewSentryTool` is a combined tool that can perform all Sentry operations:

```python
from codegen.extensions.langchain.sentry_tools import ViewSentryTool
from codegen.sdk.core.codebase import Codebase

# Initialize a codebase
codebase = Codebase.from_local("./")

# Initialize the tool
view_sentry_tool = ViewSentryTool(codebase)

# View issues
result = view_sentry_tool._run(
    action="view_issues",
    organization_slug="codegen-sh",
    status="unresolved",
    limit=5,
)
print(result)

# View issue details
result = view_sentry_tool._run(
    action="view_issue",
    issue_id="ISSUE_ID",
    organization_slug="codegen-sh",
)
print(result)

# View event details
result = view_sentry_tool._run(
    action="view_event",
    event_id="EVENT_ID",
    organization_slug="codegen-sh",
    project_slug="codegen",
)
print(result)
```

## Example Notebook

See the [example notebook](./example.ipynb) for a complete example of using the Sentry integration.
