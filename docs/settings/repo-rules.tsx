---
title: "Repository Rules"
sidebarTitle: "Repo Rules"
icon: "shield-check"
---

Repository Rules in Codegen act as a persistent set of instructions or a "system prompt" for the AI agent whenever it operates on a specific repository. These rules are shown to the language model (LLM) every time it performs a task related to that repository, ensuring that certain guidelines, preferences, or constraints are consistently followed.

This feature is powerful for guiding the agent's behavior, enforcing coding standards, or reminding it of repository-specific conventions.

## How Repository Rules Work

When an agent is assigned a task on a repository with defined rules, those rules are automatically prepended or made available to the LLM as part of its context. This means the agent "sees" these rules alongside the actual task or prompt it receives.

For example, if you have a rule like "Always use tabs for indentation," the agent will be reminded of this preference before it starts writing or modifying code in that repository.

## Automatic Rule File Detection

In addition to manual repository rules, Codegen automatically discovers and includes agent rule files from your repository when the agent starts working on it. This discovery happens whenever the `set_active_codebase` tool initializes work on a repo.

### Supported Rule File Patterns

Codegen searches for the following patterns:

- **`.cursorrules`** (Cursor)
- **`.clinerules`** (Cline)
- **`.windsurfrules`** (Windsurf)
- **`**/*.mdc`** (any `.mdc` file in the repo)
- **`.cursor/rules/**/*.mdc`** (files under `.cursor/rules/`)
- **`CLAUDE.md`**, **`AGENTS.md`**, **`AGENT.md`** (top-level agent instruction docs)

### How it works

1. Discovery via `ripgrep`
2. Content is read and encoded to preserve formatting during transport, then decoded
3. A global size budget of **25,000 characters** is enforced across all discovered files
4. The resulting content is combined with your manual Repository Rules and provided to the agent

### Visibility in the UI

Discovered rule files are rendered in AgentTrace under the `SetActiveCodebase` tool card as "Repository Rules (Filesystem)". Expand entries to preview content and open the source on GitHub.

<Tip>
  Automatic rule files are merged with manual Repository Rules to give the agent repository-specific context.
</Tip>

<Warning>
  If discovered rule files exceed the global 25,000 character budget, content will be truncated. Keep files concise or split by area of concern.
</Warning>

## Accessing and Configuring Repository Rules

You can typically find and configure Repository Rules within the settings page for each specific repository in the Codegen web UI.

1.  Navigate to [codegen.com/repos](https://codegen.com/repos).
2.  Select the repository for which you want to set rules.
3.  Look for a section titled "Repository rules" or similar in the repository's settings.

<Frame caption="Configuring Repository Rules in the UI">
  <img src="/images/repo-rules-ui.png" alt="Repository Rules UI" />
</Frame>

In the text area provided (as shown in the image), you can specify any rules you want the agent to follow for this repository. Click "Save" to apply them.

## Common Use Cases and Examples

Repository rules are flexible and can be used for various purposes:

-   **Enforcing Linting/Formatting:**
    -   "Remember to run the linter with `npm run lint` before committing."
    -   "Ensure all Python code follows PEP 8 guidelines. Use `black` for formatting."
-   **Specifying Commit Message Conventions:**
    -   "All commit messages must follow the Conventional Commits specification."
    -   "Prefix commit messages with the related Linear issue ID (e.g., `ENG-123: ...`)."
-   **Highlighting Project-Specific Information:**
    -   "This repository uses TypeScript. All new backend code should be in the `/server/src` directory."
    -   "Avoid using deprecated function `old_function()`. Use `new_function()` instead."
-   **Code Style Preferences:**
    -   "Don't write super long strings, as this will break pre-commit. Do triple-quoted strings with newlines, non-indented, instead!" (As seen in your example image)
    -   "Prefer functional components over class components in React."
-   **Reminders for Testing:**
    -   "Ensure all new features have corresponding unit tests."
    -   "Run integration tests with `npm run test:integration` after significant changes."

<Tip>
  Keep your repository rules concise and clear. Overly complex or numerous rules might confuse the agent or lead to suboptimal performance. Focus on the most critical guidelines for each repository.
</Tip>

<Note>
  Repository Rules are applied *in addition* to any global prompting strategies or agent capabilities. They provide a repository-specific layer of instruction.
</Note>
