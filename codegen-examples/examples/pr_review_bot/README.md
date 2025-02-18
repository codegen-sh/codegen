# AI-Powered Pull Request Review Bot

This example demonstrates how to use Codegen to create an intelligent PR review bot that analyzes code changes and their dependencies to provide comprehensive code reviews. The bot uses GPT-4 to generate contextual feedback based on modified code and its relationships.

> [!NOTE]
> This codemod helps development teams by providing automated, context-aware code reviews that consider both direct and indirect code dependencies.

## How the PR Review Bot Works

The script analyzes pull requests in several key steps:

1. **Symbol Analysis**

   ```python
   modified_symbols = codebase.get_modified_symbols_in_pr(pr_number)
   for symbol in modified_symbols:
       deps = codebase.get_symbol_dependencies(symbol, max_depth=2)
       rev_deps = codebase.get_symbol_dependents(symbol, max_depth=2)
   ```

   - Identifies modified symbols in the PR
   - Analyzes dependencies up to 2 levels deep
   - Tracks reverse dependencies (symbols that depend on changes)

1. **Context Building**

   ```python
   context = {"pr_title": pr.title, "pr_body": pr.body, "modified_symbols": [...], "context_symbols": [...]}
   ```

   - Gathers PR metadata
   - Collects modified code content
   - Includes relevant dependency context

1. **AI Review Generation**

   ```python
   review = codebase.ai_client.llm_query_with_retry(messages=[...], model="gpt-4", max_tokens=2000)
   ```

   - Uses GPT-4 for analysis
   - Generates comprehensive review feedback
   - Considers full context of changes

## Why This Makes Code Review Better

1. **Context-Aware Analysis**

   - Understands code dependencies
   - Considers impact of changes
   - Reviews code in proper context

1. **Comprehensive Review**

   - Analyzes direct modifications
   - Evaluates dependency impact
   - Suggests improvements

1. **Consistent Feedback**

   - Structured review format
   - Thorough analysis every time
   - Scalable review process

## Review Output Format

The bot provides structured feedback including:

```
1. Overall Assessment
   - High-level review of changes
   - Impact analysis

2. Specific Code Feedback
   - Detailed code comments
   - Style suggestions
   - Best practices

3. Potential Issues
   - Security concerns
   - Performance impacts
   - Edge cases

4. Dependency Analysis
   - Impact on dependent code
   - Breaking changes
   - Integration considerations

```

## Key Benefits to Note

1. **Better Code Quality**

   - Thorough code analysis
   - Consistent review standards
   - Early issue detection

1. **Time Savings**

   - Automated initial review
   - Quick feedback loop
   - Reduced review burden

1. **Knowledge Sharing**

   - Educational feedback
   - Best practice suggestions
   - Team learning

## Configuration Options

You can customize the review by:

- Adjusting dependency depth
- Modifying the AI prompt
- Changing the review focus areas
- Tuning the GPT-4 parameters

## Learn More

- [Codegen Documentation](https://docs.codegen.com)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Codegen llm integration](https://docs.codegen.com/building-with-codegen/calling-out-to-llms)

## Contributing

Feel free to submit issues and enhancement requests! Contributions to improve the review bot's capabilities are welcome.
