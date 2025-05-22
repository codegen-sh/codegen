# Available Tools in Codegen

This document provides a comprehensive list of all tools available in Codegen, organized by category. These tools can be used in various contexts, including Slack interactions, GitHub integrations, and Linear workflows.

## Code Analysis & Navigation

| Tool                  | Description                                      |
| --------------------- | ------------------------------------------------ |
| `ripgrep_search`      | Search the codebase using regex pattern matching |
| `set_active_codebase` | Selects a codebase to be "active" for operations |

## File Operations

| Tool          | Description                                             |
| ------------- | ------------------------------------------------------- |
| `file_write`  | Create new files or completely overwrite existing files |
| `relace_edit` | Make targeted edits to existing files                   |

## Command Execution

| Tool          | Description                              |
| ------------- | ---------------------------------------- |
| `run_command` | Run a command in a sandboxed environment |

## Web Search & Browsing

| Tool                | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| `exa_web_search`    | Search the web and get content snippets from search results |
| `exa_web_view_page` | View the content of a specific webpage                      |

## GitHub Tools

| Tool                      | Description                                                 |
| ------------------------- | ----------------------------------------------------------- |
| `view_all_repos`          | View all repositories in the organization                   |
| `view_repo_history`       | View the recent commit history for the codebase             |
| `view_commit`             | View the details of a commit                                |
| `search_all_repos`        | Search for code across all repositories in the organization |
| `get_repo_default_branch` | Get the name of the default branch for the repository       |

## GitHub PR & Issue Management

| Tool                         | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| `create_pr`                  | Create a PR for the current branch                                   |
| `view_pr`                    | View the diff and associated context for a pull request              |
| `list_pr_checks`             | List the check suites for a PR                                       |
| `view_workflow_run`          | View a workflow run                                                  |
| `github_assign_pr_reviewers` | Assign a reviewer to a GitHub PR                                     |
| `edit_pr_meta`               | Edit a PR's title and/or body and/or state                           |
| `create_pr_comment`          | Create a general comment on a pull request                           |
| `create_pr_review_comment`   | Create an inline review comment on a specific line in a pull request |

## GitHub Issues

| Tool                   | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `github_create_issue`  | Create a new GitHub issue in the repository       |
| `view_issue`           | View the details of a GitHub issue                |
| `create_issue_comment` | Create a general comment on an issue              |
| `search_issues`        | Search for GitHub issues/PRs using a query string |

## Linear Issue Management

| Tool                           | Description                                              |
| ------------------------------ | -------------------------------------------------------- |
| `linear_create_issue`          | Create a new Linear issue                                |
| `linear_get_issue`             | Get details of a Linear issue by its ID                  |
| `linear_update_issue`          | Update an existing Linear issue                          |
| `linear_comment_on_issue`      | Add a comment to a Linear issue                          |
| `linear_get_issue_comments`    | Get all comments on a Linear issue                       |
| `linear_search_issues`         | Search for Linear issues with flexible filtering options |
| `linear_assign_issue_to_cycle` | Assign a Linear issue to a cycle                         |

## Linear Team & Project Management

| Tool                     | Description                                               |
| ------------------------ | --------------------------------------------------------- |
| `linear_get_teams`       | Get all Linear teams the authenticated user has access to |
| `linear_search_teams`    | Search for Linear teams using a search string             |
| `linear_search_projects` | Search for Linear projects using a search string          |
| `linear_get_assignees`   | Get all users who can be assigned to issues in a team     |
| `linear_search_users`    | Search for Linear users using a search string             |

## Linear Issue Metadata

| Tool                               | Description                         |
| ---------------------------------- | ----------------------------------- |
| `linear_get_issue_states`          | Get all states for issues in a team |
| `linear_get_issue_priority_values` | Get all issue priority values       |
| `linear_get_issue_labels`          | Get all labels for issues in a team |

## Linear Cycles

| Tool                      | Description                            |
| ------------------------- | -------------------------------------- |
| `linear_get_active_cycle` | Get the active cycle for a Linear team |
| `linear_get_cycles`       | Get all cycles for a Linear team       |
| `linear_get_cycle_issues` | Get all issues in a Linear cycle       |

## User Information

| Tool          | Description                                                 |
| ------------- | ----------------------------------------------------------- |
| `who_is_user` | Returns information about the user you are interacting with |

## Database & Visualization

| Tool           | Description                                                                 |
| -------------- | --------------------------------------------------------------------------- |
| `sql_query`    | Executes a SQL query against a pre-configured read-only PostgreSQL database |
| `plotly_chart` | Creates a Plotly chart visualization from SQL query results                 |

## Reflection & Planning

| Tool      | Description                                          |
| --------- | ---------------------------------------------------- |
| `reflect` | Reflect on current understanding and plan next steps |

## Communication

| Tool           | Description              |
| -------------- | ------------------------ |
| `send_message` | Send a message via Slack |

## Usage Examples

### Searching a Codebase

```python
# Search for a specific pattern in the codebase
ripgrep_search(query="function fetchUserData", file_extensions=[".js", ".ts"])
```

### Creating a PR

```python
# Create a PR for the current branch
create_pr(title="Add user authentication feature", body="This PR implements user authentication using OAuth.", head_branch="feature/user-auth")
```

### Assigning Reviewers to a PR

```python
# Assign reviewers to a PR
github_assign_pr_reviewers(pr_number=123, assignees=["username1", "username2"])
```

### Creating a Linear Issue

```python
# Create a new issue in Linear
linear_create_issue(title="Implement password reset functionality", description="Users need a way to reset their passwords when forgotten.")
```

## Tool Availability by Organization

Note that tool availability may vary by organization settings. Some organizations may have certain tools disabled, such as SQL database access or PR creation capabilities.

## Further Reading

For more detailed information about each tool, including all available parameters and return values, please refer to the [API Reference](./openapi3.json) documentation.
