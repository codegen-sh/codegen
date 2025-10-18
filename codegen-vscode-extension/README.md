# Codegen VSCode Extension

A VSCode extension for Codegen - AI-powered code generation and assistance.

## Features

- **Ask Questions**: Get answers to your programming questions directly in VSCode
- **Generate Code**: Generate code snippets based on your descriptions
- **Explain Code**: Get explanations for selected code
- **Improve Code**: Get suggestions to improve your code
- **Fix Code**: Get help fixing bugs in your code

## Requirements

- VSCode 1.78.0 or higher
- A Codegen API key (get one at [codegen.sh](https://codegen.sh))

## Installation

1. Install the extension from the VSCode Marketplace
1. Set your Codegen API key in the extension settings
1. Start using Codegen in your development workflow!

## Extension Settings

This extension contributes the following settings:

- `codegen.apiKey`: Your Codegen API key
- `codegen.endpoint`: The endpoint for the Codegen API (defaults to https://api.codegen.sh)

## Commands

The extension provides the following commands:

- `codegen.askQuestion`: Ask Codegen a question
- `codegen.generateCode`: Generate code with Codegen
- `codegen.explainCode`: Explain selected code
- `codegen.improveCode`: Improve selected code
- `codegen.fixCode`: Fix selected code

## Usage

### Ask a Question

1. Open the command palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS)
1. Type "Ask Codegen a Question" and press Enter
1. Enter your question and press Enter
1. View the response in the Codegen Chat view

### Generate Code

1. Open the command palette
1. Type "Generate Code with Codegen" and press Enter
1. Describe the code you want to generate
1. The generated code will be inserted at your cursor position

### Explain Code

1. Select the code you want to explain
1. Right-click and select "Explain Selected Code" from the context menu
1. View the explanation in the Codegen Chat view

### Improve Code

1. Select the code you want to improve
1. Right-click and select "Improve Selected Code" from the context menu
1. Review the suggested improvements and apply them if desired

### Fix Code

1. Select the code you want to fix
1. Right-click and select "Fix Selected Code" from the context menu
1. Optionally provide the error message you're getting
1. Review the suggested fixes and apply them if desired

## License

MIT
