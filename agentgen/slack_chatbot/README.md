# Codegen Slack Bot

<p align="center">
  <a href="https://docs.codegen.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  A Slack bot for answering questions about Codegen's implementation
</h2>

<div align="center">

[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)

</div>

This example demonstrates how to build a Slack chatbot that can answer questions about Codegen's implementation using VectorIndex for RAG. The bot:

1. Maintains an up-to-date index of Codegen's source code
1. Uses semantic search to find relevant code snippets
1. Generates detailed answers about Codegen's internals using GPT-4

## Quick Start

1. Install dependencies:

```bash
pip install modal-client codegen slack-bolt openai
```

2. Create a Slack app and get tokens:

   - Create a new Slack app at https://api.slack.com/apps
   - Add bot token scopes:
     - `app_mentions:read`
     - `chat:write`
     - `reactions:write`
   - Install the app to your workspace

1. Set up environment:

```bash
# Copy template and fill in your tokens
cp .env.template .env
```

4. Start the bot:

```bash
modal serve api.py
```

## Usage

Just mention the bot in any channel and ask your question about Codegen:

```
@your-bot-name How does the VectorIndex work?
@your-bot-name What's the implementation of semantic search?
@your-bot-name How does Codegen handle file operations?
```

The bot will:

1. Find the most relevant Codegen source code
1. Generate a detailed explanation
1. Show you links to the actual implementation

## Response Format

The bot responds with:

1. A detailed answer about Codegen's implementation
1. Links to relevant source files on GitHub
1. Error messages if something goes wrong

Example response:

```
*Answer:*
The VectorIndex class uses OpenAI's embeddings to create searchable vectors
for all files in a codebase. It handles chunking large files and maintains
a persistent index for faster subsequent queries.

*Relevant Files:*
• src/codegen/extensions/vector_index.py
• src/codegen/extensions/tools/semantic_search.py
```

## Environment Variables

Required environment variables (in `.env`):

- `SLACK_BOT_TOKEN`: Slack Bot User OAuth Token
- `SLACK_SIGNING_SECRET`: Slack Signing Secret
- `OPENAI_API_KEY`: OpenAI API key

## Development

The bot is built using:

- Modal for serverless deployment
- Codegen for codebase analysis
- Slack Bolt for the Slack integration
- OpenAI for embeddings and Q&A

To deploy changes:

```bash
modal deploy api.py
```

## Learn More

- [Codegen Documentation](https://docs.codegen.com)
- [Slack Bolt Python](https://slack.dev/bolt-python/concepts)
- [Modal Documentation](https://modal.com/docs)
- [VectorIndex Tutorial](https://docs.codegen.com/building-with-codegen/semantic-code-search)
