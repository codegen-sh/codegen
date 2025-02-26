SYSTEM_PROMPT = '''
---
title: "Codegen"
sidebarTitle: "Overview"
icon: "code"
iconType: "solid"
---

[Codegen](https://github.com/codegen-sh/codegen-sdk) is a python library for manipulating codebases.

It provides a scriptable interface to a powerful, multi-lingual language server built on top of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/).

export const metaCode = `from codegen import Codebase

# Codegen builds a complete graph connecting
# functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.remove()

# Fast, in-memory code index
codebase.commit()
`

export const code = `def foo():
  pass

def bar():
  foo()

def baz():
  pass
`

<iframe
  width="100%"
  height="370px"
  scrolling="no"
  src={`https://codegen.sh/embedded/codemod/?code=${encodeURIComponent(
    metaCode
  )}&input=${encodeURIComponent(code)}`}
  style={{
    backgroundColor: "#15141b",
  }}
  className="rounded-xl"
></iframe>

<Note>
Codegen handles complex refactors while maintaining correctness, enabling a broad set of advanced code manipulation programs.
</Note>

<Tip>Codegen works with both Python and Typescript/JSX codebases. Learn more about language support [here](/building-with-codegen/language-support).</Tip>

## Installation

```bash
# Install CLI
uv tool install codegen

# Install inside existing project
pip install codegen
```

## What can I do with Codegen?

Codegen enables you to programmatically manipulate code with scale and precision.

<Frame caption="Call graph visualization for modal/modal-client/_Client">
<iframe
  width="100%"

  height="500px"
  scrolling="no"
  src={`https://codegen.sh/embedded/graph?id=66e2e195-ceec-4935-876a-ed4cfc1731c7&zoom=0.5&targetNodeName=_Client`}
  className="rounded-xl"
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>
</Frame>
<Info>
View source code on [modal/modal-client](https://github.com/modal-labs/modal-client/blob/cbac0d80dfd98588027ecd21850152776be3ab82/modal/client.py#L70). View codemod on [codegen.sh](https://www.codegen.sh/codemod/66e2e195-ceec-4935-876a-ed4cfc1731c7/public/diff)
</Info>

Common use cases include:

<CardGroup cols={2}>
  <Card
    title="Visualize Your Codebase"
    icon="diagram-project"
    href="/tutorials/codebase-visualization"
  >
    Generate interactive visualizations of your codebase's structure, dependencies, and relationships.
  </Card>
  <Card
    title="Mine Codebase Data"
    icon="robot"
    href="/tutorials/training-data"
  >
    Create high-quality training data for fine-tuning LLMs on your codebase.
  </Card>
  <Card
    title="Eliminate Feature Flags"
    icon="flag"
    href="/tutorials/manage-feature-flags"
  >
    Add, remove, and update feature flags across your application.
  </Card>
  <Card
    title="Organize Your Codebase"
    icon="folder-tree"
    href="/tutorials/organize-your-codebase"
  >
    Restructure files, enforce naming conventions, and improve project layout.
  </Card>
</CardGroup>


## Get Started

import {
  COMMUNITY_SLACK_URL,
  CODEGEN_SDK_GITHUB_URL,
} from "/snippets/links.mdx";

<CardGroup cols={2}>
  <Card
    title="Get Started"
    icon="graduation-cap"
    href="/introduction/getting-started"
  >
    Follow our step-by-step tutorial to start manipulating code with Codegen.
  </Card>
  <Card title="Tutorials" icon="diagram-project" href="/tutorials/at-a-glance">
    Learn how to use Codegen for common code transformation tasks.
  </Card>
  <Card title="View on GitHub" icon="github" href={CODEGEN_SDK_GITHUB_URL}>
    Star us on GitHub and contribute to the project.
  </Card>
  <Card title="Join our Slack" icon="slack" href={COMMUNITY_SLACK_URL}>
    Get help and connect with the Codegen community.
  </Card>
</CardGroup>

## Why Codegen?

Many software engineering tasks - refactors, enforcing patterns, analyzing control flow, etc. - are fundamentally programmatic operations. Yet the tools we use to express these transformations often feel disconnected from how we think about code.

Codegen was engineered backwards from real-world refactors we performed for enterprises at [Codegen, Inc.](/introduction/about). Instead of starting with theoretical abstractions, we built the set of APIs that map directly to how humans and AI think about code changes:

- **Natural Mental Model**: Express transformations through high-level operations that match how you reason about code changes, not low-level text or AST manipulation.
- **Clean Business Logic**: Let the engine handle the complexities of imports, references, and cross-file dependencies.
- **Scale with Confidence**: Make sweeping changes across large codebases consistently across Python, TypeScript, JavaScript, and React.

As AI becomes increasingly sophisticated, we're seeing a fascinating shift: AI agents aren't bottlenecked by their ability to understand code or generate solutions. Instead, they're limited by their ability to efficiently manipulate codebases. The challenge isn't the "brain" - it's the "hands."

We built Codegen with a key insight: future AI agents will need to ["act via code,"](/blog/act-via-code) building their own sophisticated tools for code manipulation. Rather than generating diffs or making direct text changes, these agents will:

1. Express transformations as composable programs
2. Build higher-level tools by combining primitive operations
3. Create and maintain their own abstractions for common patterns

This creates a shared language that both humans and AI can reason about effectively, making code changes more predictable, reviewable, and maintainable. Whether you're a developer writing a complex refactoring script or an AI agent building transformation tools, Codegen provides the foundation for expressing code changes as they should be: through code itself.


---
title: "Getting Started"
sidebarTitle: "Getting Started"
icon: "bolt"
iconType: "solid"
---

A quick tour of Codegen in a Jupyter notebook.

## Installation

Install [codegen](https://pypi.org/project/codegen/) on Pypi via [uv](https://github.com/astral-sh/uv):

```bash
uv tool install codegen
```

## Quick Start with Jupyter

The [codegen notebook](/cli/notebook) command creates a virtual environment and opens a Jupyter notebook for quick prototyping. This is often the fastest way to get up and running.

```bash
# Launch Jupyter with a demo notebook
codegen notebook --demo
```


<Tip>
  The `notebook --demo` comes pre-configured to load [FastAPI](https://github.com/fastapi/fastapi)'s codebase, so you can start
  exploring right away!
</Tip>

<Note>
  Prefer working in your IDE? See [IDE Usage](/introduction/ide-usage)
</Note>

## Initializing a Codebase

Instantiating a [Codebase](/api-reference/core/Codebase) will automatically parse a codebase and make it available for manipulation.

```python
from codegen import Codebase

# Clone + parse fastapi/fastapi
codebase = Codebase.from_repo('fastapi/fastapi')

# Or, parse a local repository
codebase = Codebase("path/to/git/repo")
```

<Note>
  This will automatically infer the programming language of the codebase and
  parse all files in the codebase. Learn more about [parsing codebases here](/building-with-codegen/parsing-codebases)
</Note>

## Exploring Your Codebase

Let's explore the codebase we just initialized.

Here are some common patterns for code navigation in Codegen:

- Iterate over all [Functions](/api-reference/core/Function) with [Codebase.functions](/api-reference/core/Codebase#functions)
- View class inheritance with [Class.superclasses](/api-reference/core/Class#superclasses)
- View function usages with [Function.usages](/api-reference/core/Function#usages)
- View inheritance hierarchies with [inheritance APIs](https://docs.codegen.com/building-with-codegen/class-api#working-with-inheritance)
- Identify recursive functions by looking at [FunctionCalls](https://docs.codegen.com/building-with-codegen/function-calls-and-callsites)
- View function call-sites with [Function.call_sites](/api-reference/core/Function#call-sites)

```python
# Print overall stats
print("🔍 Codebase Analysis")
print("=" * 50)
print(f"📚 Total Classes: {len(codebase.classes)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")

# Find class with most inheritance
if codebase.classes:
    deepest_class = max(codebase.classes, key=lambda x: len(x.superclasses))
    print(f"\n🌳 Class with most inheritance: {deepest_class.name}")
    print(f"   📊 Chain Depth: {len(deepest_class.superclasses)}")
    print(f"   ⛓️ Chain: {' -> '.join(s.name for s in deepest_class.superclasses)}")

# Find first 5 recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)][:5]
if recursive:
    print(f"\n🔄 Recursive functions:")
    for func in recursive:
        print(f"  - {func.name}")
```

## Analyzing Tests

Let's specifically drill into large test files, which can be cumbersome to manage.

```python
from collections import Counter

# Filter to all test functions and classes
test_functions = [x for x in codebase.functions if x.name.startswith('test_')]
test_classes = [x for x in codebase.classes if x.name.startswith('Test')]

print("🧪 Test Analysis")
print("=" * 50)
print(f"📝 Total Test Functions: {len(test_functions)}")
print(f"🔬 Total Test Classes: {len(test_classes)}")
print(f"📊 Tests per File: {len(test_functions) / len(codebase.files):.1f}")

# Find files with the most tests
print("\n📚 Top Test Files by Class Count")
print("-" * 50)
file_test_counts = Counter([x.file for x in test_classes])
for file, num_tests in file_test_counts.most_common()[:5]:
    print(f"🔍 {num_tests} test classes: {file.filepath}")
    print(f"   📏 File Length: {len(file.source)} lines")
    print(f"   💡 Functions: {len(file.functions)}")
```

## Splitting Up Large Test Files

Lets split up the largest test files into separate modules for better organization.

This uses Codegen's [codebase.move_to_file(...)](/building-with-codegen/moving-symbols), which will:
- update all imports
- (optionally) move dependencies
- do so very fast ⚡️

While maintaining correctness.

```python
filename = 'tests/test_path.py'
print(f"📦 Splitting Test File: {filename}")
print("=" * 50)

# Grab a file
file = codebase.get_file(filename)
base_name = filename.replace('.py', '')

# Group tests by subpath
test_groups = {}
for test_function in file.functions:
    if test_function.name.startswith('test_'):
        test_subpath = '_'.join(test_function.name.split('_')[:3])
        if test_subpath not in test_groups:
            test_groups[test_subpath] = []
        test_groups[test_subpath].append(test_function)

# Print and process each group
for subpath, tests in test_groups.items():
    print(f"\\n{subpath}/")
    new_filename = f"{base_name}/{subpath}.py"

    # Create file if it doesn't exist
    if not codebase.has_file(new_filename):
        new_file = codebase.create_file(new_filename)
    file = codebase.get_file(new_filename)

    # Move each test in the group
    for test_function in tests:
        print(f"    - {test_function.name}")
        test_function.move_to_file(new_file, strategy="add_back_edge")

# Commit changes to disk
codebase.commit()
```

<Warning>
  In order to commit changes to your filesystem, you must call
  [codebase.commit()](/api-reference/core/Codebase#commit). Learn more about
  [commit() and reset()](/building-with-codegen/commit-and-reset).
</Warning>

### Finding Specific Content

Once you have a general sense of your codebase, you can filter down to exactly what you're looking for. Codegen's graph structure makes it straightforward and performant to find and traverse specific code elements:

```python
# Grab specific content by name
my_resource = codebase.get_symbol('TestResource')

# Find classes that inherit from a specific base
resource_classes = [
    cls for cls in codebase.classes
    if cls.is_subclass_of('Resource')
]

# Find functions with specific decorators
test_functions = [
    f for f in codebase.functions
    if any('pytest' in d.source for d in f.decorators)
]

# Find files matching certain patterns
test_files = [
    f for f in codebase.files
    if f.name.startswith('test_')
]
```

## Safe Code Transformations

Codegen guarantees that code transformations maintain correctness. It automatically handles updating imports, references, and dependencies. Here are some common transformations:

```python
# Move all Enum classes to a dedicated file
for cls in codebase.classes:
    if cls.is_subclass_of('Enum'):
        # Codegen automatically:
        # - Updates all imports that reference this class
        # - Maintains the class's dependencies
        # - Preserves comments and decorators
        # - Generally performs this in a sane manner
        cls.move_to_file(f'enums.py')

# Rename a function and all its usages
old_function = codebase.get_function('process_data')
old_function.rename('process_resource')  # Updates all references automatically

# Change a function's signature
handler = codebase.get_function('event_handler')
handler.get_parameter('e').rename('event') # Automatically updates all call-sites
handler.add_parameter('timeout: int = 30')  # Handles formatting and edge cases
handler.add_return_type('Response | None')

# Perform surgery on call-sites
for fcall in handler.call_sites:
    arg = fcall.get_arg_by_parameter_name('env')
    # f(..., env={ data: x }) => f(..., env={ data: x or None })
    if isinstance(arg.value, Collection):
        data_key = arg.value.get('data')
        data_key.value.edit(f'{data_key.value} or None')
```

<Tip>
  When moving symbols, Codegen will automatically update all imports and
  references. See [Moving Symbols](/building-with-codegen/moving-symbols) to
  learn more.
</Tip>

## Leveraging Graph Relations

Codegen's graph structure makes it easy to analyze relationships between code elements across files:

```python
# Find dead code
for func in codebase.functions:
    if len(function.usages) == 0:
        print(f'🗑️ Dead code: {func.name}')
        func.remove()

# Analyze import relationships
file = codebase.get_file('api/endpoints.py')
print("\nFiles that import endpoints.py:")
for import_stmt in file.inbound_imports:
    print(f"  {import_stmt.file.path}")

print("\nFiles that endpoints.py imports:")
for import_stmt in file.imports:
    if import_stmt.resolved_symbol:
        print(f"  {import_stmt.resolved_symbol.file.path}")

# Explore class hierarchies
base_class = codebase.get_class('BaseModel')
if base_class:
    print(f"\nClasses that inherit from {base_class.name}:")
    for subclass in base_class.subclasses:
        print(f"  {subclass.name}")
        # We can go deeper in the inheritance tree
        for sub_subclass in subclass.subclasses:
            print(f"    └─ {sub_subclass.name}")
```

<Note>
  Learn more about [dependencies and
  references](/building-with-codegen/dependencies-and-usages) or [imports](/building-with-codegen/imports) and [exports](/building-with-codegen/exports).
</Note>

## What's Next?

<CardGroup cols={2}>
  <Card
    title="View Tutorials"
    icon="graduation-cap"
    href="/tutorials/at-a-glance"
  >
    Follow step-by-step tutorials for common code transformation tasks like
    modernizing React codebases or migrating APIs.
  </Card>
  <Card
    title="Learn Core Concepts"
    icon="book"
    href="/building-with-codegen/at-a-glance"
  >
    Understand key concepts like working with files, functions, imports, and the
    call graph to effectively manipulate code.
  </Card>
  <Card title="IDE Setup" icon="window" href="/introduction/ide-usage">
    Iterate locally with your favorite IDE, work with a debugger and build sophisticated codemods
  </Card>
  <Card
    title="Integrate with AI Tools"
    icon="microchip"
    href="/introduction/work-with-ai"
  >
    Learn how to use Codegen with Cursor, Devin, Windsurf, and more.
  </Card>

</CardGroup>


---
title: "Installation"
sidebarTitle: "Installation"
icon: "download"
iconType: "solid"
---

Install and set up Codegen in your development environment.

## Prerequisites

We recommend using [uv](https://github.com/astral-sh/uv) for installation. If you haven't installed `uv` yet:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installing Codegen

```bash
uv tool install codegen
```


<Note>
This makes the `codegen` command available globally in your terminal, while keeping its dependencies isolated.
</Note>

## Quick Start

Let's walk through a minimal example of using Codegen in a project:

1. Navigate to your repository:
   ```bash
   cd path/to/your/project
   ```

2. Initialize Codegen in your project with [codegen init](/cli/init):
   ```bash
   codegen init
   ```

   This creates a `.codegen/` directory with:
   ```bash
   .codegen/
   ├── .venv/            # Python virtual environment (gitignored)
   ├── codemods/         # Your codemod implementations
   ├── jupyter/          # Jupyter notebooks for exploration
   └── codegen-system-prompt.txt  # AI system prompt
   ```

3. Create your first codemod with [codegen create](/cli/create):
   ```bash
   codegen create organize-imports \
     -d "Sort and organize imports according to PEP8"
   ```
    <Note>
        The `-d` flag in `codegen create` generates an AI-powered implementation. This requires a Github account registered on [codegen.sh](https://codegen.sh)
    </Note>



4. Run your codemod with [codegen run](/cli/run):
   ```bash
   codegen run organize-imports
   ```

5. Reset any filesystem changes (excluding `.codegen/*`) with [codegen reset](/cli/reset):
   ```bash
   codegen reset
   ```

## Next Steps

<CardGroup cols={2}>
  <Card
    title="IDE Integration"
    icon="window"
    href="/introduction/ide-usage"
  >
    Learn how to use Codegen effectively in VSCode, Cursor, and other IDEs.
  </Card>
  <Card
    title="Tutorials"
    icon="graduation-cap"
    href="/tutorials/at-a-glance"
  >
    Follow step-by-step tutorials for common code transformation tasks.
  </Card>
  <Card
    title="Work with AI"
    icon="microchip"
    href="/introduction/work-with-ai"
  >
    Leverage AI assistants like Copilot, Cursor and Devin
    </Card>
  <Card
    title="Guides"
    icon="hammer"
    href="/building-with-codegen/at-a-glance"
  >
    Learn more about building with Codegen
    </Card>

</CardGroup>

<Note>
For more help, join our [community Slack](/introduction/community) or check the [FAQ](/introduction/faq).
</Note>

---
title: "Using Codegen in Your IDE"
sidebarTitle: "IDE Usage"
icon: "window"
iconType: "solid"
---

Get up and running with Codegen programs in IDEs like VSCode, Cursor and PyCharm.

<Tip>Make sure to [install and initialize](/introduction/installation) Codegen with `codegen init`</Tip>

## Configuring your IDE Interpreter

Codegen creates a custom Python environment in `.codegen/.venv`. Configure your IDE to use this environment for the best development experience.

<AccordionGroup>
  <Accordion title="VSCode, Cursor and Windsurf" icon="window-maximize">
    1. Install the VSCode Python Extensions for LSP and debugging support. We recommend Python, Pylance and Python Debugger for the best experience.
      <img src="/images/python-extensions.png" />
    2. Open the Command Palette (Cmd/Ctrl + Shift + P)
    3. Type "Python: Select Interpreter"
    <img src="/images/set-interpreter.png" />
    4. Choose "Enter interpreter path"
    5. Navigate to and select:
       ```bash
       .codegen/.venv/bin/python
       ```

    Alternatively, create a `.vscode/settings.json`:
        ```json
        {
          "python.defaultInterpreterPath": "${workspaceFolder}/.codegen/.venv/bin/python",
          "python.analysis.extraPaths": [
            "${workspaceFolder}/.codegen/.venv/lib/python3.12/site-packages"
          ]
        }
        ```
  </Accordion>

  <Accordion title="PyCharm" icon="python">
    1. Open PyCharm Settings/Preferences
    2. Navigate to "Project > Python Interpreter"
    3. Click the gear icon ⚙️ and select "Add"
    4. Choose "Existing Environment"
    5. Set interpreter path to:
       ```bash
       .codegen/.venv/bin/python
       ```
  </Accordion>

</AccordionGroup>


## Create a New Codemod

Generate the boilerplate for a new code manipulation program using [codegen create](/cli/create):

```bash
codegen create organize-types \
  -d "Move all TypeScript types to \
      into a centralized types.ts file"
```

<Tip>
    Passing in `-d --description` will get an LLM expert to compose an initial version for you. This requires a Github account registered on [codegen.sh](https://codegen.sh)
</Tip>

This will:
1. Create a new codemod in `.codegen/codemods/organize_types/`
2. Generate a custom `system-prompt.txt` based on your task
3. Set up the basic structure for your program

<Note>
The generated codemod includes type hints and docstrings, making it easy to get IDE autocompletion and documentation.
</Note>

## Iterating with Chat Assistants

When you do `codegen init`, you will receive a [system prompt optimized for AI consumption](/introduction/work-with-ai) at `.codegen/codegen-system-prompt.txt`.

If you reference this file in "chat" sessions with Copilot, Cursor, Cody, etc., the assistant will become fluent in Codegen.

<Frame>
    <img src="/images/system-prompt.png" />
    Collaborating with Cursor's assistant and the Codegen system prompt
</Frame>

In addition, when you [create](/cli/create) a codemod with "-d", Codegen generates an optimized system prompt in `.codegen/codemods/{name}/{name}-system-prompt.txt`. This prompt contains:
- Relevant Codegen API documentation
- Examples of relevant transformations
- Context about your specific task

<Tip>
You can also drag and drop the system prompt ([available here](/introduction/work-with-ai))file directly into chat windows like ChatGPT or Claude for standalone help.
</Tip>

## Running and Testing Codemods

```bash
# Run => write changes to disk
codegen run organize-types

# Reset changes on disk
codegen reset
```

<Tip>You can also run the program directly via `.codegen/.venv/bin/python path/to/codemod.py` or via your editor's debugger</Tip>

## Viewing Changes

We recommend viewing changes in your IDE's native diff editor.


## What's Next

<CardGroup cols={2}>
  <Card
    title="Explore Tutorials"
    icon="graduation-cap"
    href="/tutorials/at-a-glance"
  >
    See real-world examples of codemods in action.
  </Card>
  <Card
    title="Codegen Guides"
    icon="book"
    href="/building-with-codegen/at-a-glance"
  >
    Learn about Codegen's core concepts and features
  </Card>
</CardGroup>


---
title: "Working with AI"
sidebarTitle: "AI Integration"
icon: "microchip"
iconType: "solid"
---

Codegen is designed to be used with AI assistants. This document describes how to use Codegen with common AI tools, including Copilot, Cursor, Devin and more.

## System Prompt

Codegen provides a `.txt` file that you can drag-and-drop into any chat assistant. This is roughly 60k tokens and will enable chat assistants like, ChatGPT, Claude 3.5 etc. to build effectively with Codegen.

import {
  CODEGEN_SYSTEM_PROMPT
} from "/snippets/links.mdx";

<Card title="Download System Prompt" href={CODEGEN_SYSTEM_PROMPT} icon="download">
  Download System Prompt
</Card>

<Tip>Learn about leveraging this in IDE chat assistants like Cursor [here](/introduction/ide-usage#iterating-with-chat-assistants)</Tip>

## Generating System Prompts

The [Codegen CLI](/cli/about) provides commands to generate `.md` files that can be fed to any AI assistant for more accurate and contextual help.

When you create a new codemod via [`codegen create`](/cli/create):

```bash
codegen create delete-dead-imports --description "Delete unused imports"
```

Codegen automatically generates an optimized ["system prompt"](https://news.ycombinator.com/item?id=37880023) that includes:

- An introduction to Codegen
- Codegen API documentation
- Examples of relevant transformations

You can find this generated prompt in the `.codegen/prompts/<codemod-name>-system-prompt.md` file.

<Note>
  All contents of the `.codegen/prompts` directory are by default ignored the
  `.gitignore` file. after running [`codegen init`](/cli/init)
</Note>

This `.md` file can be used with any AI assistant (Claude, GPT-4, etc.) to get more accurate and contextual help.

## Example Workflow

<Steps>
  <Step title="Create a codemod with description">
    Use the [`create` command](/cli/create) with a detailed description of what you want to accomplish:
    ```bash
    codegen create modernize-components --description "Convert class components to functional components with hooks"
    ```
  </Step>
  <Step title="Review the generated system prompt">
    Check the AI context that Codegen generated for your transformation: ```bash
    cat codegen-sh/codemods/modernize-components/prompt.md ```
  </Step>

<Step title="Iterate in Copilot, Cursor or Windsurf">
  Reference your codemod when asking questions to get contextual help: ```
  @codegen-sh/codemods/modernize-components How should I handle
  componentDidMount? ```
</Step>

  <Step title="Get contextual help">
    The AI will understand you're working on React modernization and provide relevant suggestions about using useEffect hooks and other modern React patterns.
  </Step>
</Steps>

## Copilot, Cursor and Windsurf (IDEs)

When using IDE chat assistants, you can leverage Codegen's context by mentioning your codemod in composer mode:

```bash
@.codegen/codemods/upgrade-react18 @.codegen/prompts/system-prompt.md
```

This will ensure that the IDE's native chat model is aware of the APIs and common patterns for Codegen.

## Devin, OpenHands and Semi-autonomous Code Agents

<Warning>Coming soon!</Warning>


---
title: "Under the Hood"
sidebarTitle: "How it Works"
icon: "gear"
iconType: "solid"
subtitle: "How Codegen's codebase graph works"
---

Codegen performs advanced static analysis to build a rich graph representation of your codebase. This pre-computation step analyzes dependencies, references, types, and control flow to enable fast and reliable code manipulation operations.

<Note>
  Codegen is built on top of
  [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) and
  [rustworkx](https://github.com/Qiskit/rustworkx) and has implemented most
  language server features from scratch.
</Note>
<Info>
  Codegen is open source. Check out the [source
  code](https://github.com/codegen-sh/codegen-sdk) to learn more!
</Info>

## The Codebase Graph

At the heart of Codegen is a comprehensive graph representation of your code. When you initialize a [Codebase](/api-reference/core/Codebase), it performs static analysis to construct a rich graph structure connecting code elements:

```python
# Initialize and analyze the codebase
from codegen import Codebase
codebase = Codebase("./")

# Access pre-computed relationships
function = codebase.get_symbol("process_data")
print(f"Dependencies: {function.dependencies}")  # Instant lookup
print(f"Usages: {function.usages}")  # No parsing needed
```

### Building the Graph

Codegen's graph construction happens in two stages:

1. **AST Parsing**: We use [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) as our foundation for parsing code into Abstract Syntax Trees. Tree-sitter provides fast, reliable parsing across multiple languages.

2. **Multi-file Graph Construction**: Custom parsing logic, implemented in [rustworkx](https://github.com/Qiskit/rustworkx) and Python, analyzes these ASTs to construct a more sophisticated graph structure. This graph captures relationships between [symbols](/building-with-codegen/symbol-api), [files](/building-with-codegen/files-and-directories), [imports](/building-with-codegen/imports), and more.

### Performance Through Pre-computation

Pre-computing a rich index enables Codegen to make certain operations very fast that that are relevant to refactors and code analysis:

- Finding all usages of a symbol
- Detecting circular dependencies
- Analyzing the dependency graphs
- Tracing call graphs
- Static analysis-based code retrieval for RAG
- ...etc.

<Tip>
  Pre-parsing the codebase enables constant-time lookups rather than requiring
  re-parsing or real-time analysis.
</Tip>

## Multi-Language Support

One of Codegen's core principles is that many programming tasks are fundamentally similar across languages.

Currently, Codegen supports:

- [Python](/api-reference/python)
- [TypeScript](/api-reference/typescript)
- [React & JSX](/building-with-codegen/react-and-jsx)

<Note>
  Learn about how Codegen handles language specifics in the [Language
  Support](/building-with-codegen/language-support) guide.
</Note>

We've started with these ecosystems but designed our architecture to be extensible. The graph-based approach provides a consistent interface across languages while handling language-specific details under the hood.

## Build with Us

Codegen is just getting started, and we're excited about the possibilities ahead. We enthusiastically welcome contributions from the community, whether it's:

- Adding support for new languages
- Implementing new analysis capabilities
- Improving performance
- Expanding the API
- Adding new transformations
- Improving documentation

Check out our [community guide](/introduction/community) to get involved!


---
title: "Guiding Principles"
sidebarTitle: "Principles"
icon: "compass"
iconType: "solid"
---

Codegen was developed by working backwards from real-world, large-scale codebase migrations. Instead of starting with abstract syntax trees and parser theory, we started with the question: "How do developers actually think about code changes?"

This practical origin led to four core principles that shape Codegen's design:

## Intuitive APIs

Write code that reads like natural language, without worrying about abstract syntax trees or parser internals. Codegen provides high-level APIs that map directly to the transformations developers want to perform:

```python
# Methods that read like English
function.rename("new_name")  # Not ast.update_node(function_node, "name", "new_name")
function.move_to_file("new_file.py")  # Not ast.relocate_node(function_node, "new_file.py")

# Clean, readable properties
if function.is_async:  # Not ast.get_node_attribute(function_node, "async")
    print(function.name)  # Not ast.get_node_name(function_node)

# Natural iteration patterns
for usage in function.usages:  # Not ast.find_references(function_node)
    print(f"Used in {usage.file.name}")
```

## No Sharp Edges

Focus on your high-level intent while Codegen handles the intricate details.

Codegen operations handle the edge cases - it should be hard to break lint.

```python
# Moving a function? Codegen handles:
function.move_to_file("new_file.py")
# ✓ Updating all import statements
# ✓ Preserving dependencies
# ✓ Maintaining references
# ✓ Fixing relative imports
# ✓ Resolving naming conflicts

# Renaming a symbol? Codegen manages:
class_def.rename("NewName")
# ✓ Updating all usages
# ✓ Handling string references
# ✓ Preserving docstrings
# ✓ Maintaining inheritance
```

## Performance through Pre-Computation

Codegen frontloads as much as possible to enable fast, efficient transformations.

It is built with the insight that each codebase only needs to be parsed once per commit.

<Tip>
  Learn more about parsing the codebase graph in the [How it
  Works](/introduction/how-it-works) guide.
</Tip>

## Python-First Composability

Codegen embraces Python's strength as a "glue language" - its ability to seamlessly integrate different tools and APIs. This makes it natural to compose Codegen with your existing toolchain:

- Build complex transforms by combining simpler operations
- Integrate Codegen with your existing tools (linters, type checkers, test frameworks, AI tools)

<Note>
  Python's rich ecosystem makes it ideal for code manipulation tasks. Codegen is
  designed to be one tool in your toolbox, not a replacement for your entire
  workflow.
</Note>


---
title: "Community & Contributing"
sidebarTitle: "Community"
icon: "people-group"
iconType: "solid"
---

import {
  COMMUNITY_SLACK_URL,
  CODEGEN_SDK_GITHUB_URL,
} from "/snippets/links.mdx";

Join the growing Codegen community! We're excited to have you be part of our journey to make codebase manipulation and transformation more accessible.

<CardGroup cols={2}>
  <Card title="Join our Slack" icon="slack" href={COMMUNITY_SLACK_URL}>
    Connect with the community, get help, and share your Codegen projects in our
    active Slack workspace.
  </Card>
  <Card title="GitHub" icon="github" href={CODEGEN_SDK_GITHUB_URL}>
    Star us on GitHub, report issues, submit PRs, and contribute to the project.
  </Card>
  <Card title="Twitter (X)" icon="twitter" href="https://twitter.com/codegen">
    Follow us for updates, tips, and community highlights.
  </Card>
  <Card
    title="Documentation"
    icon="book-open"
    href="/introduction/getting-started"
  >
    Learn how to use Codegen effectively with our comprehensive guides.
  </Card>
</CardGroup>

<Tip>
  Please help us improve this library and documentation by submitting a PR!
</Tip>

## Contributing

We welcome contributions of all kinds! Whether you're fixing a typo in documentation, reporting a bug, or implementing a new feature, we appreciate your help in making Codegen better.

Check out our [Contributing Guide](https://github.com/codegen-sh/codegen-sdk/blob/develop/CONTRIBUTING.md) on GitHub to learn how to:

- Set up your development environment
- Submit pull requests
- Report issues
- Contribute to documentation


---
title: "Codegen, Inc."
sidebarTitle: "About Us"
icon: "building"
iconType: "solid"
---

<Card
  img="/images/codegen.jpeg"
  title="Codegen, Inc."
  href="https://codegen.com"
/>

## Our Mission

Our mission is to build fully-autonomous software engineering - the equivalent of self-driving cars for code.

We believe the highest leverage path to autonomous development is enabling AI agents to "act via code."

Just as self-driving cars need sophisticated sensors and controls to navigate the physical world, AI agents need powerful, precise tools to manipulate codebases. We're building that foundational layer: a programmatic interface that lets AI agents express complex code transformations through code itself.

This approach creates a shared language that both humans and AI can use to:

- Express powerful changes with precision and predictability
- Build sophisticated tools from primitive operations
- Create and maintain their own abstractions
- Scale transformations across massive codebases

## The Team

Based in San Francisco, we're a team of engineers and researchers passionate about:

- Making large-scale code changes more accessible
- Building tools that work the way developers think
- Creating the infrastructure for AI-powered code manipulation
- Advancing the state of the art in program transformation

## Open Source

We believe in the power of open source software. Our core library, [codegen](https://github.com/codegen-sh/codegen-sdk), is freely available and open to contributions from the community.

## Join Us

<CardGroup cols={2}>
  <Card title="Careers" icon="briefcase" href="https://codegen.com/careers">
    We're hiring! Join us in building the future of code transformation.
  </Card>
  <Card title="Community" icon="people-group" href="/introduction/community">
    Connect with other developers and share your Codegen experiences.
  </Card>
</CardGroup>

## Connect with Us

<CardGroup cols={2}>
  <Card title="X (Twitter)" icon="twitter" href="https://x.com/codegen">
    Follow us for updates and announcements
  </Card>
  <Card
    title="LinkedIn"
    icon="linkedin"
    href="https://linkedin.com/company/codegen-dot-com"
  >
    Connect with our team and stay updated on company news
  </Card>
</CardGroup>

<Note>
  Want to learn more about what we're building? Check out our [getting started
  guide](/introduction/getting-started) or join our [community
  Slack](https://community.codegen.com).
</Note>


---
title: "Frequently Asked Questions"
sidebarTitle: "FAQ"
icon: "square-question"
iconType: "solid"
---

<AccordionGroup>
  <Accordion title="What languages does Codegen support?" icon="code">
    Codegen currently parses two languages:
    - [Python](/api-reference/python)
    - [TypeScript](/api-reference/typescript)

    We're actively working on expanding language support based on community needs.
    <Tip>
      Learn more about how Codegen handles language specifics in the [Language
      Support](/building-with-codegen/language-support) guide.
    </Tip>
    <Note>
      Interested in adding support for your language? [Let us know](https://x.com/codegen) or [contribute](/introduction/community)!
    </Note>

  </Accordion>
    <Accordion title="Is Codegen exact?" icon="scale-balanced">
    Pretty much! Codegen is roughly on par with `mypy` and `tsc`. There are always edge cases in static analysis that are provably impossible to get (for example doing `eval()` on a string), but all of Codegen's APIs are intended to be exact unless otherwise specified. Please reach out if you find an edge case and we will do our best to patch it.
  </Accordion>
  <Accordion title="Is Codegen suitable for large codebases?" icon="database">
    Yes! Codegen was developed on multmillion-line Python and Typescript codebases
    and includes optimizations for handling large-scale transformations.
    <Tip>
      For enterprise support, please reach out to [team@codegen.com](mailto:team@codegen.com)
    </Tip>
  </Accordion>
  <Accordion title="Can I use Codegen with my existing tools?" icon="screwdriver-wrench">
    Yes - [by design](/introduction/guiding-principles#python-first-composability).

    Codegen works like any other python package. It works alongside your IDE, version control system, and other development tools.
  </Accordion>
  <Accordion
    title="How can I contribute if I'm new to the project?"
    icon="hand-holding-heart"
  >
    Start by trying out Codegen, joining our [Slack community](https://community.codegen.com), and looking for
    issues labeled "good first issue" on [GitHub](https://github.com/codegen-sh/codegen-sdk). We welcome contributions to
    documentation, examples, and code improvements.
  </Accordion>
  <Accordion title="Is Codegen free to use?" icon="scale-balanced">
    Yes, Codegen is [open source](https://github.com/codegen-sh/codegen-sdk) and free to use under the [Apache 2.0
    license](https://github.com/codegen-sh/codegen-sdk?tab=Apache-2.0-1-ov-file).
    You can use it for both personal and commercial projects.
  </Accordion>
  <Accordion title="Where can I get help if I'm stuck?" icon="life-ring">
    The best places to get help are:
    1. Our community [Slack channel](https://community.codegen.com)
    2. [GitHub issues](https://github.com/codegen-sh/codegen-sdk) for bug reports
    3. Reach out to us on [Twitter](https://x.com/codegen)
  </Accordion>
</AccordionGroup>


---
title: "Building with Codegen"
sidebarTitle: "At a Glance"
icon: "book"
iconType: "solid"
---

Learn how to use Codegen's core APIs to analyze and transform code.

## Core Concepts

<CardGroup cols={2}>
  <Card
    title="Parsing Codebases"
    icon="code"
    href="/building-with-codegen/parsing-codebases"
  >
    Understand how Codegen parses and analyzes different programming languages.
  </Card>
  <Card
    title="Files & Directories"
    icon="folder-tree"
    href="/building-with-codegen/files-and-directories"
  >
    Learn how to work with files, directories, and navigate the codebase
    structure.
  </Card>
  <Card
    title="The Editable API"
    icon="wand-magic-sparkles"
    href="/building-with-codegen/the-editable-api"
  >
    Learn how to safely modify code while preserving formatting and comments.
  </Card>
  <Card
    title="Symbols, Functions and Classes"
    icon="pen-to-square"
    href="/building-with-codegen/the-editable-api"
  >
    Master the core abstractions for manipulating code safely and effectively.
  </Card>

</CardGroup>

## Navigating the Code Graph

<CardGroup cols={2}>
  <Card
    title="Dependencies & Usages"
    icon="diagram-project"
    href="/building-with-codegen/dependencies-and-usages"
  >
    Analyze relationships between code elements and track symbol references.
  </Card>
  <Card
    title="Function Calls & Callsites"
    icon="arrow-right-arrow-left"
    href="/building-with-codegen/function-calls-and-callsites"
  >
    Understand function call patterns and manipulate call sites.
  </Card>
  <Card
    title="Imports"
    icon="file-import"
    href="/building-with-codegen/imports"
  >
    Work with module imports and manage dependencies.
  </Card>
  <Card
    title="Traversing the Call Graph"
    icon="share-nodes"
    href="/building-with-codegen/traversing-the-call-graph"
  >
    Navigate function call relationships and analyze code flow.
  </Card>
</CardGroup>

## Code Manipulation

<CardGroup cols={2}>
  <Card
    title="Moving Symbols"
    icon="arrows-up-down-left-right"
    href="/building-with-codegen/moving-symbols"
  >
    Relocate functions, classes, and other symbols while updating references.
  </Card>
  <Card
    title="Statements & Code Blocks"
    icon="brackets-curly"
    href="/building-with-codegen/statements-and-code-blocks"
  >
    Work with code blocks, control flow, and statement manipulation.
  </Card>
  <Card
    title="Variable Assignments"
    icon="equals"
    href="/building-with-codegen/variable-assignments"
  >
    Handle variable declarations, assignments, and scope.
  </Card>
  <Card
    title="Collections"
    icon="layer-group"
    href="/building-with-codegen/collections"
  >
    Work with groups of related code elements like functions, classes, and
    imports.
  </Card>
</CardGroup>

## Special Features

<CardGroup cols={2}>
  <Card
    title="React & JSX"
    icon="react"
    href="/building-with-codegen/react-and-jsx"
  >
    Work with React components, JSX syntax, and component transformations.
  </Card>
  <Card
    title="Local Variables"
    icon="cube"
    href="/building-with-codegen/local-variables"
  >
    Analyze and manipulate local variable usage and scope.
  </Card>
  <Card
    title="Calling Out to LLMs"
    icon="robot"
    href="/building-with-codegen/calling-out-to-llms"
  >
    Integrate AI assistance into your code transformations.
  </Card>
  <Card
    title="Codebase Visualization"
    icon="chart-network"
    href="/building-with-codegen/codebase-visualization"
  >
    Visualize code relationships and dependencies.
  </Card>
</CardGroup>

<Note>
  Each guide includes practical examples and best practices. Start with core
  concepts or jump directly to the topics most relevant to your needs.
</Note>


---
title: "Parsing Codebases"
sidebarTitle: "Parsing Codebases"
icon: "power-off"
iconType: "solid"
---

The primary entrypoint to programs leveraging Codegen is the [Codebase](/api-reference/core/Codebase) class.

## Local Codebases

Construct a Codebase by passing in a path to a local `git` repository or any subfolder within it. The path must be within a git repository (i.e., somewhere in the parent directory tree must contain a `.git` folder).

```python
from codegen import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Parse from a git repository root
codebase = Codebase("path/to/repository")

# Parse from a subfolder within a git repository
codebase = Codebase("path/to/repository/src/subfolder")

# Parse from current directory (must be within a git repo)
codebase = Codebase("./")

# Specify programming language (instead of inferring from file extensions)
codebase = Codebase("./", programming_language=ProgrammingLanguage.TYPESCRIPT)
```

<Note>
  By default, Codegen will automatically infer the programming language of the codebase and
  parse all files in the codebase. You can override this by passing the `programming_language` parameter
  with a value from the `ProgrammingLanguage` enum.
</Note>

<Tip>
  The initial parse may take a few minutes for large codebases. This
  pre-computation enables constant-time operations afterward. [Learn more
  here.](/introduction/how-it-works)
</Tip>

## Remote Repositories

To fetch and parse a repository directly from GitHub, use the `from_repo` function.

```python
import codegen
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Fetch and parse a repository (defaults to /tmp/codegen/{repo_name})
codebase = codegen.from_repo('fastapi/fastapi')

# Customize temp directory, clone depth, specific commit, or programming language
codebase = codegen.from_repo(
    'fastapi/fastapi',
    tmp_dir='/custom/temp/dir',  # Optional: custom temp directory
    commit='786a8ada7ed0c7f9d8b04d49f24596865e4b7901',  # Optional: specific commit
    shallow=False,  # Optional: full clone instead of shallow
    programming_language=ProgrammingLanguage.PYTHON  # Optional: override language detection
)
```

<Note>
  Remote repositories are cloned to the `/tmp/codegen/{repo_name}` directory by
  default. The clone is shallow by default for better performance.
</Note>

## Configuration Options

You can customize the behavior of your Codebase instance by passing a `CodebaseConfig` object. This allows you to configure secrets (like API keys) and toggle specific features:

```python
from codegen import Codebase
from codegen.configs.models.codebase import CodebaseConfig
from codegen.configs.models.secrets import SecretsConfig

codebase = Codebase(
    "path/to/repository",
    config=CodebaseConfig(
        sync_enabled=True,   # Enable graph synchronization
        ...  # Add other feature flags as needed
    ),
    secrets=SecretsConfig(openai_api_key="your-openai-key")     # For AI-powered features
)
```

- `CodebaseConfig` and `SecretsConfig` allow you to configure
  - `config`: Toggle specific features like language engines, dependency management, and graph synchronization
  - `secrets`: API keys and other sensitive information needed by the codebase

For a complete list of available feature flags and configuration options, see the [source code on GitHub](https://github.com/codegen-sh/codegen-sdk/blob/develop/src/codegen/sdk/codebase/config.py).

## Advanced Initialization

For more complex scenarios, Codegen supports an advanced initialization mode using `ProjectConfig`. This allows for fine-grained control over:

- Repository configuration
- Base path and subdirectory filtering
- Multiple project configurations

Here's an example:

```python
from codegen import Codebase
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage

codebase = Codebase(
    projects = [
        ProjectConfig(
            repo_operator=RepoOperator(
                repo_config=RepoConfig(name="codegen-sdk"),
                bot_commit=True
            ),
            programming_language=ProgrammingLanguage.TYPESCRIPT,
            base_path="src/codegen/sdk/typescript",
            subdirectories=["src/codegen/sdk/typescript"]
        )
    ]
)
```

For more details on advanced configuration options, see the [source code on GitHub](https://github.com/codegen-sh/codegen-sdk/blob/develop/src/codegen/sdk/core/codebase.py).

## Supported Languages

Codegen currently supports:

- [Python](/api-reference/python)
- [TypeScript/JavaScript](/api-reference/typescript)
- [React/JSX](/building-with-codegen/react-and-jsx)


---
title: "Reusable Codemods"
sidebarTitle: "Reusable Codemods"
icon: "arrows-rotate"
iconType: "solid"
---

Codegen enables you to create reusable code transformations using Python functions decorated with `@codegen.function`. These codemods can be shared, versioned, and run by your team.

## Creating Codemods

The easiest way to create a new codemod is using the CLI [create](/cli/create) command:

```bash
codegen create rename-function
```

This creates a new codemod in your `.codegen/codemods` directory:

```python
import codegen
from codegen import Codebase

@codegen.function("rename-function")
def run(codebase: Codebase):
    """Add a description of what this codemod does."""
    # Add your code here
    pass
```

<Note>
  Codemods are stored in `.codegen/codemods/name/name.py` and are tracked in Git for easy sharing.
</Note>

### AI-Powered Generation with `-d`

You can use AI to generate an initial implementation by providing a description:

```bash
codegen create rename-function -d "Rename the getUserData function to fetchUserProfile"
```

This will:
1. Generate an implementation based on your description
2. Create a custom system prompt that you can provide to an IDE chat assistant (learn more about [working with AI](/introduction/work-with-ai))
3. Place both files in the codemod directory

## Running Codemods

Once created, run your codemod using:

```bash
codegen run rename-function
```

The execution flow:
1. Codegen parses your codebase into a graph representation
2. Your codemod function is executed against this graph
3. Changes are tracked and applied to your filesystem
4. A diff preview shows what changed


## Codemod Structure

A codemod consists of three main parts:

1. The `@codegen.function` decorator that names your codemod
2. A `run` function that takes a `Codebase` parameter
3. Your transformation logic using the Codebase API

```python
import codegen
from codegen import Codebase

@codegen.function("update-imports")
def run(codebase: Codebase):
    """Update import statements to use new package names."""
    for file in codebase.files:
        for imp in file.imports:
            if imp.module == "old_package":
                imp.rename("new_package")
    codebase.commit()
```

## Arguments

Codemods can accept arguments using Pydantic models:

```python
from pydantic import BaseModel

class RenameArgs(BaseModel):
    old_name: str
    new_name: str

@codegen.function("rename-function")
def run(codebase: Codebase, arguments: RenameArgs):
    """Rename a function across the codebase."""
    old_func = codebase.get_function(arguments.old_name)
    if old_func:
        old_func.rename(arguments.new_name)
    codebase.commit()
```

Run it with:
```bash
codegen run rename-function --arguments '{"old_name": "getUserData", "new_name": "fetchUserProfile"}'
```

## Directory Structure

Your codemods live in a dedicated directory structure:

```
.codegen/
└── codemods/
    └── rename_function/
        ├── rename_function.py       # The codemod implementation
        └── rename_function_prompt.md  # System prompt (if using AI)
```

---
title: "The .codegen Directory"
sidebarTitle: ".codegen Directory"
icon: "folder"
iconType: "solid"
---

The `.codegen` directory contains your project's Codegen configuration, codemods, and supporting files. It's automatically created when you run `codegen init`.

## Directory Structure

```bash
.codegen/
├── .venv/            # Python virtual environment (gitignored)
├── .env              # Project configuration
├── codemods/         # Your codemod implementations
├── jupyter/          # Jupyter notebooks for exploration
└── codegen-system-prompt.txt  # AI system prompt
```

## Initialization

The directory is created and managed using the `codegen init` command:

```bash
codegen init [--fetch-docs] [--repo-name NAME] [--organization-name ORG]
```

<Note>
The `--fetch-docs` flag downloads API documentation and examples specific to your project's programming language.
</Note>

## Virtual Environment

Codegen maintains its own virtual environment in `.codegen/.venv/` to ensure consistent package versions and isolation from your project's dependencies. This environment is:

- Created using `uv` for fast, reliable package management
- Initialized with Python 3.13
- Automatically managed by Codegen commands
- Used for running codemods and Jupyter notebooks
- Gitignored to avoid committing environment-specific files

The environment is created during `codegen init` and used by commands like `codegen run` and `codegen notebook`.

<Note>To debug codemods, you will need to set the python virtual environment in your IDE to `.codegen/.venv`</Note>

### Configuration

The `.env` file stores your project settings:

```env
REPOSITORY_OWNER = "your-org"
REPOSITORY_PATH = "/root/git/your-repo"
REPOSITORY_LANGUAGE = "python"  # or other supported language
```

This configuration is used by Codegen to provide language-specific features and proper repository context.

## Git Integration

Codegen automatically adds appropriate entries to your `.gitignore`:

```gitignore
# Codegen
.codegen/.venv/
.codegen/docs/
.codegen/jupyter/
.codegen/codegen-system-prompt.txt
```

<Info>
- While most directories are ignored, your codemods in `.codegen/codemods/` are tracked in Git
- The virtual environment and Jupyter notebooks are gitignored to avoid environment-specific issues
</Info>

## Working with Codemods

The `codemods/` directory is where your transformation functions live. You can create new codemods using:

```bash
codegen create my-codemod [--description "what it does"]
```

This will:
1. Create a new file in `.codegen/codemods/`
2. Generate a system prompt in `.codegen/prompts/` (if using `--description`)
3. Set up the necessary imports and decorators

<Tip>
Use `codegen list` to see all codemods in your project.
</Tip>

## Jupyter Integration

The `jupyter/` directory contains notebooks for interactive development:

```python
from codegen import Codebase

# Initialize codebase
codebase = Codebase('../../')

# Print stats
print(f"📚 Total Files: {len(codebase.files)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
```

<Note>
A default notebook is created during initialization to help you explore your codebase.
</Note>

## Next Steps

After initializing your `.codegen` directory:

1. Create your first codemod:
```bash
codegen create my-codemod -d "describe what you want to do"
```

2. Run it:
```bash
codegen run my-codemod --apply-local
```

3. Deploy it for team use:
```bash
codegen deploy my-codemod
```


---
title: Function Decorator
sidebarTitle: "@codegen.function"
icon: "at"
iconType: "solid"
---

# Function Decorator

The `function` decorator is used to define codegen functions within your application. It allows you to specify a name for the function that will be ran making it easier to run specific codemods

## Usage

To use the `function` decorator, simply annotate your function with `@codegen.function` and provide a name as an argument.

### Example

```python
@codegen.function('my-function')
def run(codebase):
    pass
```

In this example, the function `run` is decorated with `@codegen.function` and given the name `'my-function'`. This name will be used when the function is ran.

## Parameters

- `name` (str): The name of the function to be used when ran.

## Description

The `function` decorator is part of the codegen SDK CLI and is used to mark functions that are intended to be ran as part of a code generation process. It ensures that the function is properly registered and can be invoked with the specified name.


## CLI Examples

### Running a Function

To run a deployed function using the CLI, use the following command:

```bash
codegen run my-function
```

This command runs the function named `my-function`.

## See Also

- [Webhook Decorator](./webhook-decorator.mdx): For handling webhook events with decorators.
- [Codebase Visualization](./codebase-visualization.mdx): For visualizing codebases in your application.
- [CLI Init Command](../cli/init.mdx): For initializing projects or environments related to the function decorator.
- [CLI Create Command](../cli/create.mdx): For creating new functions or projects using the CLI.
- [CLI Run Command](../cli/run.mdx): For running code or scripts using the CLI.


---
title: "Language Support"
sidebarTitle: "Language Support"
icon: "binary"
iconType: "solid"
---

Codegen provides first-class support for both Python and TypeScript codebases. The language is automatically inferred when you initialize a codebase.

## Language Detection

When you create a new `Codebase` instance, Codegen automatically detects the programming language:

```python
from codegen import Codebase

# Automatically detects Python or TypeScript
codebase = Codebase("./")

# View language with `codebase.language`
print(codebase.language)  # "python" or "typescript"
```

<Tip>
  Learn more about codebase initialization options in [Parsing
  Codebases](/building-with-codegen/parsing-codebases).
</Tip>

## Type System

Codegen uses specialized types for each language. These are defined as type aliases:

```python
# Python codebases use PyCodebaseType
PyCodebaseType = Codebase[
    PyFile, Directory, PySymbol, PyClass, PyFunction,
    PyImport, PyAssignment, Interface, TypeAlias,
    PyParameter, PyCodeBlock
]

# TypeScript codebases use TSCodebaseType
TSCodebaseType = Codebase[
    TSFile, Directory, TSSymbol, TSClass, TSFunction,
    TSImport, TSAssignment, TSInterface, TSTypeAlias,
    TSParameter, TSCodeBlock
]
```

Every code element has both a Python and TypeScript implementation that inherits from a common base class. For example:

- [`Function`](/api-reference/core/Function)
  - [`PyFunction`](/api-reference/python/PyFunction)
  - [`TSFunction`](/api-reference/typescript/TSFunction)
- [`Class`](/api-reference/core/Class)
  - [`PyClass`](/api-reference/python/PyClass)
  - [`TSClass`](/api-reference/typescript/TSClass)
- [`Import`](/api-reference/core/Import)
  - [`PyImport`](/api-reference/python/PyImport)
  - [`TSImport`](/api-reference/typescript/TSImport)

...

```python
# Base class (core/function.py)
class Function:
    """Abstract representation of a Function."""
    pass

# Python implementation (python/function.py)
class PyFunction(Function):
    """Extends Function for Python codebases."""
    pass

# TypeScript implementation (typescript/function.py)
class TSFunction(Function):
    """Extends Function for TypeScript codebases."""
    pass
```

This inheritance pattern means that most Codegen programs can work with either Python or TypeScript without modification, since they share the same API structure.

```python
# Works for both Python and TypeScript
for function in codebase.functions:
    print(f"Function: {function.name}")
    print(f"Parameters: {[p.name for p in function.parameters]}")
    print(f"Return type: {function.return_type}")
```

## TypeScript-Specific Features

Some features are only available in TypeScript codebases:

- **Types and Interfaces**: TypeScript's rich type system ([`TSTypeAlias`](/api-reference/typescript/TSTypeAlias), [`TSInterface`](/api-reference/typescript/TSInterface))
- **Exports**: Module exports and re-exports ([`TSExport`](/api-reference/typescript/TSExport))
- **JSX/TSX**: React component handling (see [React and JSX](/building-with-codegen/react-and-jsx))

Example of TypeScript-specific features:

```python
# Only works with TypeScript codebases
if isinstance(codebase, TSCodebaseType):
    # Work with TypeScript interfaces
    for interface in codebase.interfaces:
        print(f"Interface: {interface.name}")
        print(f"Extends: {[i.name for i in interface.parent_interfaces]}")

    # Work with type aliases
    for type_alias in codebase.type_aliases:
        print(f"Type alias: {type_alias.name}")
```


---
title: "Commit and Reset"
sidebarTitle: "Commit and Reset"
icon: "arrows-rotate"
iconType: "solid"
---

Codegen requires you to explicitly commit changes by calling [codebase.commit()](/api-reference/core/Codebase#commit).

<Tip>
  Keeping everything in memory enables fast, large-scale writes. See the [How it
  Works](/introduction/how-it-works) guide to learn more.
</Tip>

You can manage your codebase's state with two core APIs:

- [Codebase.commit()](/api-reference/core/Codebase#commit) - Commit changes to disk
- [Codebase.reset()](/api-reference/core/Codebase#reset) - Reset the `codebase` and filesystem to its initial state

## Committing Changes

When you make changes to your codebase through Codegen's APIs, they aren't immediately written to disk. You need to explicitly commit them with [codebase.commit()](/api-reference/core/Codebase#commit):

```python
from codegen import Codebase

codebase = Codebase("./")

# Make some changes
file = codebase.get_file("src/app.py")
file.before("# 🌈 hello, world!")

# Changes aren't on disk yet
codebase.commit()  # Now they are!
```

This transaction-like behavior helps ensure your changes are atomic and consistent.

## Resetting State

The [codebase.reset()](/api-reference/core/Codebase#reset) method allows you to revert the codebase to its initial state:

```python
# Make some changes
codebase.get_file("src/app.py").remove()
codebase.create_file("src/new_file.py", "x = 1")

# Check the changes
assert codebase.get_file("src/app.py", optional=True) is None
assert codebase.get_file("src/new_file.py") is not None

# Reset everything
codebase.reset()

# Changes are reverted
assert codebase.get_file("src/app.py") is not None
assert codebase.get_file("src/new_file.py", optional=True) is None
```

<Note>
  `reset()` reverts both the in-memory state and any uncommitted filesystem
  changes. However, it preserves your codemod implementation in `.codegen/`.
</Note>


---
title: "Git Operations"
sidebarTitle: "Git Operations"
icon: "code-branch"
---

Many workflows require Git operations. Codegen provides a high-level API for common Git operations through the [`Codebase`](/api-reference/core/Codebase) class, including:

- [`Codebase.git_commit(...)`](/api-reference/core/Codebase#git_commit)
- [`Codebase.checkout(...)`](/api-reference/core/Codebase#checkout)

## Committing Changes to Git

You can commit changes to Git using the [`Codebase.git_commit(...)`](/api-reference/core/Codebase#git_commit):

```python
# Make some changes and call `commit()` to sync them to disk
codebase.functions[0].rename('foo')
codebase.commit()

# Commit all staged changes to git with a message
commit = codebase.git_commit("feat: update function signatures")

# You can also verify the commit (runs pre-commit hooks)
commit = codebase.git_commit("feat: update signatures", verify=True)

# The method returns the commit object if changes were committed, None otherwise
if commit:
    print(f"Created commit: {commit.hexsha}")
```

<Note>
  `git_commit` will only commit changes that have been synced to the filesystem
  by calling [`Codebase.commit()`](/api-reference/core/Codebase#commit). See
  [`Commit and Reset`](/building-with-codegen/commit-and-reset) for more
  details.
</Note>

## Checking Current Git State

Codegen provides properties to check the current Git state:

```python
# Get the default branch (e.g. 'main' or 'master')
default = codebase.default_branch
print(f"Default branch: {default}")

# Get the current commit
current = codebase.current_commit
if current:
    print(f"Current commit: {current.hexsha}")
```

## Checking Out Branches and Commits

The [`Codebase.checkout(...)`](/api-reference/core/Codebase#checkout) method allows you to switch between branches and commits.

This will automatically re-parse the codebase to reflect the new state.

```python
# Checkout a branch
result = codebase.checkout(branch="feature/new-api")

# Create a new branch if it doesn't exist
result = codebase.checkout(branch="feature/new-api", create_if_missing=True)

# Checkout a specific commit
result = codebase.checkout(commit="abc123")

# Checkout and pull from remote
result = codebase.checkout(branch="main", remote=True)
```


---
title: "Files and Directories"
sidebarTitle: "Files & Directories"
icon: "folder-tree"
iconType: "solid"
---

Codegen provides three primary abstractions for working with your codebase's file structure:

- [File](/api-reference/core/File) - Represents a file in the codebase (e.g. README.md, package.json, etc.)
- [SourceFile](/api-reference/core/SourceFile) - Represents a source code file (e.g. Python, TypeScript, React, etc.)
- [Directory](/api-reference/core/Directory) - Represents a directory in the codebase

<Info>
  [SourceFile](/api-reference/core/SourceFile) is a subclass of [File](/api-reference/core/File) that provides additional functionality for source code files.
</Info>


## Accessing Files and Directories

You typically access files from the [codebase](/api-reference/core/Codebase) object with two APIs:

- [codebase.get_file(...)](/api-reference/core/Codebase#get-file) - Get a file by its path
- [codebase.files](/api-reference/core/Codebase#files) - Enables iteration over all files in the codebase

```python
# Get a file from the codebase
file = codebase.get_file("path/to/file.py")

# Iterate over all files in the codebase
for file in codebase.files:
    pass

# Check if a file exists
exists = codebase.has_file("path/to/file.py")

```


These APIs are similar for [Directory](/api-reference/core/Directory), which provides similar methods for accessing files and subdirectories.

```python
# Get a directory
dir = codebase.get_directory("path/to/dir")

# Iterate over all files in the directory
for file in dir.files:
    pass

# Get the directory containing a file:
dir = file.directory

# Check if a directory exists
exists = codebase.has_directory("path/to/dir")
```

## Differences between SourceFile and File

- [File](/api-reference/core/File) - a general purpose class that represents any file in the codebase including non-code files like README.md, .env, .json, image files, etc.
- [SourceFile](/api-reference/core/SourceFile) - a subclass of [File](/api-reference/core/File) that provides additional functionality for source code files written in languages supported by the [codegen-sdk](/introduction/overview) (Python, TypeScript, JavaScript, React).

The majority of intended use cases involve using exclusively [SourceFile](/api-reference/core/SourceFile) objects as these contain code that can be parsed and manipulated by the [codegen-sdk](/introduction/overview). However, there may be cases where it will be necessary to work with non-code files. In these cases, the [File](/api-reference/core/File) class can be used.

By default, the `codebase.files` property will only return [SourceFile](/api-reference/core/SourceFile) objects. To include non-code files the `extensions='*'` argument must be used.

```python
# Get all source files in the codebase
source_files = codebase.files

# Get all files in the codebase (including non-code files)
all_files = codebase.files(extensions="*")
```


When getting a file with `codebase.get_file`, files ending in `.py, .js, .ts, .jsx, .tsx` are returned as [SourceFile](/api-reference/core/SourceFile) objects while other files are returned as [File](/api-reference/core/File) objects.

Furthermore, you can use the `isinstance` function to check if a file is a [SourceFile](/api-reference/core/SourceFile):

```python
py_file = codebase.get_file("path/to/file.py")
if isinstance(py_file, SourceFile):
    print(f"File {py_file.filepath} is a source file")

# prints: `File path/to/file.py is a source file`

mdx_file = codebase.get_file("path/to/file.mdx")
if not isinstance(mdx_file, SourceFile):
    print(f"File {mdx_file.filepath} is a non-code file")

# prints: `File path/to/file.mdx is a non-code file`
```

<Note>
  Currently, the codebase object can only parse source code files of one language at a time. This means that if you want to work with both Python and TypeScript files, you will need to create two separate codebase objects.
</Note>

## Accessing Code

[SourceFiles](/api-reference/core/SourceFile) and [Directories](/api-reference/core/Directory) provide several APIs for accessing and iterating over their code.

See, for example:

- `.functions` ([SourceFile](/api-reference/core/SourceFile#functions) / [Directory](/api-reference/core/Directory#functions)) - All [Functions](/api-reference/core/Function) in the file/directory
- `.classes` ([SourceFile](/api-reference/core/SourceFile#classes) / [Directory](/api-reference/core/Directory#classes)) - All [Classes](/api-reference/core/Class) in the file/directory
- `.imports` ([SourceFile](/api-reference/core/SourceFile#imports) / [Directory](/api-reference/core/Directory#imports)) - All [Imports](/api-reference/core/Import) in the file/directory
- `.get_function(...)` ([SourceFile](/api-reference/core/SourceFile#get-function) / [Directory](/api-reference/core/Directory#get-function)) - Get a specific function by name
- `.get_class(...)` ([SourceFile](/api-reference/core/SourceFile#get-class) / [Directory](/api-reference/core/Directory#get-class)) - Get a specific class by name
- `.get_global_var(...)` ([SourceFile](/api-reference/core/SourceFile#get-global-var) / [Directory](/api-reference/core/Directory#get-global-var)) - Get a specific global variable by name


```python
# Get all functions in a file
for function in file.functions:
    print(f"Found function: {function.name}")
    print(f"Parameters: {[p.name for p in function.parameters]}")
    print(f"Return type: {function.return_type}")

# Get all classes
for cls in file.classes:
    print(f"Found class: {cls.name}")
    print(f"Methods: {[m.name for m in cls.methods]}")
    print(f"Attributes: {[a.name for a in cls.attributes]}")

# Get imports (can also do `file.import_statements`)
for imp in file.imports:
    print(f"Import from: {imp.module}")
    print(f"Imported symbol: {[s.name for s in imp.imported_symbol]}")

# Get specific symbols
main_function = file.get_function("main")
user_class = file.get_class("User")
config = file.get_global_var("CONFIG")

# Access code blocks
if main_function:
    for statement in main_function.code_block.statements:
        print(f"Statement type: {statement.statement_type}")

# Get local variables in a function
if main_function:
    local_vars = main_function.code_block.get_local_var_assignments()
    for var in local_vars:
        print(f"Local var: {var.name} = {var.value}")
```

## Working with Non-Code Files (README, JSON, etc.)

By default, Codegen focuses on source code files (Python, TypeScript, etc). However, you can access all files in your codebase, including documentation, configuration, and other non-code [files](/api-reference/core/File) like README.md, package.json, or .env:

```python
# Get all files in the codebase (including README, docs, config files)
files = codebase.files(extensions="*")

# Print files that are not source code (documentation, config, etc)
for file in files:
    if not file.filepath.endswith(('.py', '.ts', '.js')):
        print(f"📄 Non-code file: {file.filepath}")
```

You can also filter for specific file types:

```python
# Get only markdown documentation files
docs = codebase.files(extensions=[".md", ".mdx"])

# Get configuration files
config_files = codebase.files(extensions=[".json", ".yaml", ".toml"])
```

These APIs are similar for [Directory](/api-reference/core/Directory), which provides similar methods for accessing files and subdirectories.

## Raw Content and Metadata

```python
# Grab raw file string content
content = file.content # For text files
print('Length:', len(content))
print('# of functions:', len(file.functions))

# Access file metadata
name = file.name # Base name without extension
extension = file.extension # File extension with dot
filepath = file.filepath # Full relative path
dir = file.directory # Parent directory

# Access directory metadata
name = dir.name # Base name without extension
path = dir.path # Full relative path from repository root
parent = dir.parent # Parent directory
```

## Editing Files Directly

Files themselves are [`Editable`](/api-reference/core/Editable.mdx) objects, just like Functions and Classes.

<Tip>
  Learn more about the [Editable API](/building-with-codegen/the-editable-api).
</Tip>

This means they expose many useful operations, including:

- [`File.search`](/api-reference/core/File#search) - Search for all functions named "main"
- [`File.edit`](/api-reference/core/File#edit) - Edit the file
- [`File.replace`](/api-reference/core/File#replace) - Replace all instances of a string with another string
- [`File.insert_before`](/api-reference/core/File#insert-before) - Insert text before a specific string
- [`File.insert_after`](/api-reference/core/File#insert-after) - Insert text after a specific string
- [`File.remove`](/api-reference/core/File#remove) - Remove a specific string

```python
# Get a file
file = codebase.get_file("path/to/file.py")

# Replace all instances of a string
file.replace("name", "new_name")
file.replace("name", "new_name", include_comments=False) # Don't edit comments

# Replace entire text of the file
file.edit('hello, world!')

# Get + delete all instances of a string
for editable in file.search("foo"):
    editable.remove()

# Insert text at the top of the file
file.insert_before("def main():\npass")
# ... or at the bottom
file.insert_after("def end():\npass")

# Delete the file
file.remove()
```

You can frequently do bulk modifictions via the [`.edit(...)`](/api-reference/core/Editable#edit) method or [`.replace(...)`](/api-reference/core/File#replace) method.

<Note>
  Most useful operations will have bespoke APIs that handle edge cases, update
  references, etc.
</Note>

## Moving and Renaming Files

Files can be manipulated through methods like [`File.update_filepath()`](/api-reference/core/File#update-filepath), [`File.rename()`](/api-reference/core/File#rename), and [`File.remove()`](/api-reference/core/File#remove):

```python
# Move/rename a file
file.update_filepath("/path/to/foo.py")  # Move to new location
file.rename("bar")  # Rename preserving extension, e.g. `bar.py`

# Remove a file (potentially destructive)
file.remove()

# Move all tests to a tests directory
for file in codebase.files:
    if 'test_' in file.name:
        # This will handle updating imports and other references
        file.update_filepath('tests/' + file.filepath.replace("test_", ""))
```

<Warning>
  Removing files is a potentially breaking operation. Only remove files if they
  have no external usages.
</Warning>

## Directories

[`Directories`](/api-reference/core/Directory) expose a similar API to the [File](/api-reference/core/File.mdx) class, with the addition of the `subdirectories` property.

```python
# Get a directory
dir = codebase.get_directory("path/to/dir")

# Iterate over all directories in the codebase
for directory in codebase.directories:
    print(f"Found directory: {directory.path}")

# Check directory existence
exists = codebase.has_directory("path/to/dir")

# Access metadata
name = dir.name  # Directory name
path = dir.path  # Full path
parent = dir.parent  # Parent directory

# Get specific items
file = dir.get_file("file.py")
subdir = dir.get_subdirectory("subdir")

# Get all ancestor subdirectories
subdirs = dir.subdirectories

# Get the parent directory
parent_dir = dir.parent

# Find all child directories
for subdir in dir.subdirectories:
    if dir.parent == subdir:
        print(f"Found child subdirectory: {subdir.path}")

# Move to new location
dir.update_filepath("new/path")

# Rename directory in place
dir.rename("new_name")

# Remove a directory and all contents (potentially destructive)
dir.remove()
```

<Warning>
  Removing directories is a potentially destructive operation. Only remove
  directories if they have no external usages.
</Warning>


---
title: "The Editable API"
sidebarTitle: "Editables"
icon: "pencil"
iconType: "solid"
---

Every code element in Codegen is an [Editable](../api-reference/core/Editable) - meaning it can be manipulated while maintaining correctness.

All higher-level code manipulation APIs are built on top of the atomic Editable API.

## Core Concepts

Every Editable provides:

- Information about the source code:
  - [source](../api-reference/core/Editable#source) - the text content of the Editable
  - [extended_source](../api-reference/core/Editable#extended_source) - includes relevant content like decorators, comments, etc.
- Information about the file that contains the Editable:
  - [file](../api-reference/core/Editable#file) - the [SourceFile](../api-reference/core/SourceFile) that contains this Editable
- Relationship tracking
  - [parent_class](../api-reference/core/Editable#parent-class) - the [Class](../api-reference/core/Class) that contains this Editable
  - [parent_function](../api-reference/core/Editable#parent-function) - the [Function](../api-reference/core/Function) that contains this Editable
  - [parent_statement](../api-reference/core/Editable#parent-statement) - the [Statement](../api-reference/core/Statement) that contains this Editable
- Safe modification operations

## Basic Editing

There are several fundamental ways to modify code with Editables:

```python
# 1. edit() - Replace entire source with new content
function = codebase.get_function("process_data")
function.edit("""
def process_data(input_data: dict) -> dict:
    return transform(input_data)
""")

# 2. Replace - Substitute text while preserving context
class_def = codebase.get_class("UserModel")
class_def.replace("user_id", "account_id")  # Updates all occurrences

# 3. Remove - Safely delete code with proper cleanup
unused_import = file.get_import("from utils import deprecated_func")
unused_import.remove()  # Handles formatting, commas, etc

# 4. Insert - Add code before or after an element
function.insert_before("# Process user input")  # Adds comment before function
function.insert_after("""
def validate_data(data: dict) -> bool:
    return all(required in data for required in REQUIRED_FIELDS)
""")  # Adds new function after
```

## Finding and Searching

Editables provide powerful search capabilities:

```python
# Find string literals
results = function.find_string_literals(["error", "warning"])
results = function.find_string_literals(["error"], fuzzy_match=True)

# Search with regex
matches = function.search(r"data\\['[^']*'\\]")  # Find dict access
matches = function.search("TODO:", include_comments=True)

# Find specific patterns
variables = function.get_variable_usages("config")
function_calls = function.function_calls  # All function calls within this node
```

## Smart Formatting

Codegen handles formatting details automatically:

```python
# Adding to import statements
import_stmt = file.get_import("from mylib import func1")
import_stmt.add_symbol("func2")  # Handles comma placement
import_stmt.add_symbol("func3")  # Maintains proper formatting

# Multi-line formatting is preserved
from mylib import (
    func1,
    func2,    # New imports maintain
    func3     # existing style
)
```

## Safe Removals

Removing code elements is safe and clean:

```python
# Remove a function and its decorators
function.remove()  # Removes associated comments and formatting

# Remove imports cleanly
import_stmt.remove()  # Handles commas and whitespace
```

## Working with References

Editables track their relationships to other code elements:

```python
# Find and update all references
function = codebase.get_function("old_name")
function.rename("new_name")  # Updates all usages

# Navigate relationships
print(function.parent_function)  # Containing function
print(function.parent_class)    # Containing class
print(function.parent_statement)  # Containing statement
```

## Understanding Context

Editables provide rich information about their location and context in the code:

### Parent Relationships

```python
# Get containing elements
function = codebase.get_function("process_data")
print(function.parent_class)     # Class containing this function
print(function.parent_function)  # Function containing this function (for nested functions)
print(function.parent_statement) # Statement containing this function

# Check if top-level
is_top_level = function.parent_class is None and function.parent_function is None
```

### Statement Containment

The `is_wrapped_in` method lets you check if an Editable is contained within specific types of statements:

```python
# Check containment in statement types
is_in_try = function.is_wrapped_in("try")
is_in_if = function.is_wrapped_in("if")
is_in_while = function.is_wrapped_in("while")

# Get the first parent statements of a certain type
if_block = function.parent_of_type(IfStatement)

# Common patterns
if function.is_wrapped_in(IfStatement):
    print("This is in an IfBlock")

if variable.is_wrapped_in(WithStatement):
    print("Variable used in WithStatement")
```

### Common Use Cases

```python
# Move nested functions to module level
for func in file.functions:
    if func.parent_function:  # This is a nested function
        func.parent_function.insert_before(func.source) # Move to module level
        func.remove() # Remove the nested function

# Find variables defined in unsafe blocks
for var in function.code_block.get_local_var_assignments():
    if var.is_wrapped_in(TryStatement):
        print(f"Warning: {var.name} defined in try block")
```



---
title: "The Symbol API"
sidebarTitle: "Symbols"
icon: "shapes"
iconType: "solid"
---

The [Symbol](/api-reference/core/Symbol) is the primary way developers interact with code in Codegen. It maps to how developers think about code - as functions, classes, variables, and other named entities.

Both the [Function](/api-reference/core/Function) and [Class](/api-reference/core/Class) symbols are subclasses of the [Symbol](/api-reference/core/Symbol) class.

## Accessing Symbols

The [Codebase](/api-reference/core/Codebase) class provides getters and iterators for functions, classes and symbols:

```python
# Core symbol types
symbol = codebase.get_symbol("process_data") # will return a Function, Class, etc.
function = codebase.get_function("process_data")
class_def = codebase.get_class("DataProcessor")

# Iterate over all symbols (includes functions + classes)
for symbol in codebase.symbols:
    print(symbol.name)

# Iterate over all functions and classes
for symbol in codebase.functions + codebase.classes:
    print(symbol.name)
```

## Shared APIs

All symbols share common APIs for manipulation:

- The [Editable](/api-reference/core/Editable) API
- Metadata
  - [symbol.name](/api-reference/core/Symbol#name)
  - [symbol.source](/api-reference/core/Symbol#source)
  - [symbol.docstring](/api-reference/core/Symbol#docstring)
- Edit operations
  - [symbol.set_docstring](/api-reference/core/Symbol#set-docstring)
  - [symbol.move_to_file](/api-reference/core/Symbol#move-to-file) (see [Moving Symbols](/building-with-codegen/moving-symbols))
- Graph relations (See [Usages and Dependencies](/building-with-codegen/dependencies-and-usages))
  - [symbol.usages](/api-reference/core/Symbol#usages)
  - [symbol.dependencies](/api-reference/core/Symbol#dependencies)

## Name operations

```python
# Name operations
print(symbol.name)
symbol.rename("new_name")

# Source code
print(symbol.source)  # Get source code
symbol.edit("new source code")  # Modify source

# Documentation
print(symbol.docstring)  # Get docstring
symbol.set_docstring("New documentation")

# Move symbol to new file
symbol.move_to_file(new_file)

# Add before/after other symbols
symbol.insert_before("# deprecated")
symbol.insert_after("# end deprecated")
```

## Function Statement Manipulation

Functions provide special APIs for adding statements to their body:

- [Function.prepend_statements](/api-reference/core/Function#prepend_statements) - add statements to the start of the function body
- [Function.add_statements](/api-reference/core/Function#add_statements) - add statements to the end of the function body

```python
# Add statements at the start of a function
function.prepend_statements("print('Starting function')")
method.prepend_statements("self.validate_input()")

# Add statements at the end of a function
function.add_statements("print('Done')")
method.add_statements("return self.result")
```

<Note>
  The statement manipulation APIs (`prepend_statements` and `add_statements`)
  are only available on Function objects. For other symbols, use the general
  Editable APIs like `insert_before` and `insert_after`.
</Note>

## Common Patterns

Most Codegen programs focus on finding and manipulating symbols:

```python
# Find and modify functions
for function in codebase.functions:
    if function.name.startswith("old_"):
        # Rename function
        function.rename(function.name.replace("old_", "new_"))
        # Update docstring
        function.set_docstring("Updated version of function")

# Update class methods
for method in class_def.methods:
    # Add logging
    method.prepend_statements("logger.info('Called {}'".format(method.name))
```

<Note>
  The Symbol API is designed to be intuitive and match how developers think
  about code. Most transformations start with finding relevant symbols and then
  applying changes to them.
</Note>


---
title: "The Class API"
sidebarTitle: "Classes"
icon: "cube"
iconType: "solid"
---

The [Class](/api-reference/core/Class) API extends the [Symbol](/building-with-codegen/symbol-api) API to support methods, attributes, and inheritance hierarchies.

## Methods and Method Usages

Classes provide access to their methods and method [usages](/building-with-codegen/dependencies-and-usages) through an intuitive API:

```python
# Access methods
for method in class_def.methods:
    print(f"Method: {method.name}")
    # Find all usages of this method
    for usage in method.usages:
        print(f"Used in {usage.file.name}")

# Get specific methods
init_method = class_def.constructor  # Get __init__ method
process_method = class_def.get_method("process_data")

# Filter methods
public_methods = class_def.methods(private=False)  # Exclude private methods
regular_methods = class_def.methods(magic=False)   # Exclude magic methods
```

<Info>
  Methods are typed as [Function](/api-reference/core/Function) objects.
</Info>

## Class Attributes

[Attributes](/api-reference/core/Attribute) can be accessed and modified easily:

```python
# Access all attributes
for attr in class_def.attributes:
    print(f"Attribute: {attr.name}")

# Add new attributes
class_def.add_attribute_from_source("count: int = 0")

# Get specific attribute
name_attr = class_def.get_attribute("name")

# Add attribute from another class
other_class = codebase.get_class("OtherClass")
class_def.add_attribute(
    other_class.get_attribute("config"),
    include_dependencies=True  # Also adds required imports
)
```

### Manipulating Attributes

[Attributes](/api-reference/core/Attribute) expose their own API for modification and analysis:

```python
# Modify attribute values and types
attr = class_def.get_attribute("count")
attr.set_value("42")  # Change value
attr.assignment.set_type_annotation("float")  # Change type
attr.assignment.type.remove()  # Remove type annotation

# Find attribute usages
for usage in attr.usages:
    print(f"Used in {usage.file.name}")

# Find local usages (within the class)
for usage in attr.local_usages:
    print(f"Used in method: {usage.parent_function.name}")

# Rename attributes (updates all references)
attr.rename("new_name")  # Also updates self.count -> self.new_name

# Remove attributes
attr.remove()  # Removes the attribute definition

# Check attribute properties
if attr.is_private:  # Starts with underscore
    print("Private attribute")
if attr.is_optional:  # Optional[Type] or Type | None
    print("Optional attribute")

# Access underlying value
if attr.value:  # The expression assigned to the attribute
    print(f"Default value: {attr.value.source}")
```

<Note>
  Attribute operations automatically handle all references, including
  `self.attribute` usages in methods and string references.
</Note>

### Working with Inheritance

You can navigate inheritance hierarchies with APIs including:

- [Class.superclasses](/api-reference/core/Class#superclasses)
- [Class.subclasses](/api-reference/core/Class#subclasses)
- [Class.is_subclass_of](/api-reference/core/Class#is-subclass-of)

```python
class_def = codebase.get_class("Cube")

# View ancestors
all_ancestors = class_def.superclasses # All classes inherited
immediate_parents = class_def.superclasses(max_depth=1)  # Direct parents only

# Inheritance-aware method lookup
method = class_def.get_method("process")  # Searches up inheritance chain
if method.parent_class != class_def:
    print(f"Method inherited from {method.parent_class.name}")

# Handle external dependencies
if class_def.is_subclass_of("Enum"):  # Works with stdlib/external classes
    print("This is an enum class")
```

Likewise, you can modify inheritance by accessing:

- [Class.parent_class_names](/api-reference/core/Class#parent-class-names)
- [Class.get_parent_class(cls_name)](/api-reference/core/Class#get-parent-class)

Which return lists of [Name](/api-reference/core/Name) objects.

```python
# Modify inheritance
parent_names = class_def.parent_class_names
if parent_names[0] == 'BaseClass':
    parent_names[0].edit("NewBaseClass")  # Change parent class

# Get specific parent class
parent_class = class_def.get_parent_class("BaseClass")
if parent_class:
    parent_class.edit("NewBaseClass")  # Change parent class
```

<Tip>
  When working with inheritance, use `max_depth` to control how far up the
  inheritance chain to look. `max_depth=0` means current class only,
  `max_depth=None` means traverse entire hierarchy.
</Tip>

<Note>
  Codegen handles both internal and external parent classes (like stdlib
  classes). The `superclasses` property follows the language's MRO rules for
  method resolution.
</Note>

## Method Resolution Order (MRO)

Codegen follows the target language's method resolution order (MRO) for inheritance:

```python
# Access superclasses
for parent in class_def.superclasses:
    print(f"Parent: {parent.name}")

# Check inheritance
if class_def.is_subclass_of("BaseClass"):
    print("This is a subclass of BaseClass")

# Get all subclasses
for child in class_def.subclasses:
    print(f"Child class: {child.name}")

# Access inherited methods/attributes
all_methods = class_def.methods(max_depth=None)  # Include inherited methods
all_attrs = class_def.attributes(max_depth=None)  # Include inherited attributes
```


---
title: "The Import API"
sidebarTitle: "Imports"
icon: "file-import"
iconType: "solid"
---

The [Import](/api-reference/core/Import) API provides tools for working with imports and managing dependencies between files.

## Accessing Imports

You can access these through [File.imports](/api-reference/core/File#imports) and [File.import_statements](/api-reference/core/File#import-statements):

```python
# Direct access to imports via file
for imp in file.imports:
    ...

# Grab by name of symbol being imported
imp = file.get_import('math')

# Grab and filter from a codebase
from codegen.sdk import ExternalModule

external_imports = [i for i in codebase.imports if isinstance(i, ExternalModule)]
```

## Common Operations

The Import API provides several methods for modifying imports:

```python
# Get a specific import
import_stmt = file.get_import("MyComponent")

# Change import source
import_stmt.set_module("./new/path")

# Add/update alias
import_stmt.set_alias("MyAlias")  # import X as MyAlias

# TypeScript-specific operations
import_stmt.make_type_import()  # Convert to 'import type'
import_stmt.make_value_import() # Remove 'type' modifier

# Update multiple properties
import_stmt.update(
    module="./new/path",
    alias="NewAlias",
    is_type=True
)
```

## Import Resolution

Imports can be traced to their original symbols:

```python
# Follow import chain to source
import_stmt = file.get_import("MyComponent")
original = import_stmt.resolved_symbol

if original:
    print(f"Defined in: {original.file.filepath}")
    print(f"Original name: {original.name}")

# Get file relationships
print(f"From file: {import_stmt.from_file.filepath}")
print(f"To file: {import_stmt.to_file.filepath}")
```

<Note>
With Python one can specify the `PYTHONPATH` environment variable which is then considered when resolving
packages.
</Note>

## Working with External Modules

You can determine if an import references an [ExternalModule](/api-reference/core/ExternalModule) by checking the type of [Import.imported_symbol](/api-reference/core/Import#imported-symbol), like so:

```python
# Check if import is from external package
for imp in file.imports:
    if isinstance(imp.imported_symbol, ExternalModule):
        print(f"External import: {imp.name} from {imp.module}")
    else:
        print(f"Local import: {imp.name}")
```

<Tip>Learn more about [external modules here](/building-with-codegen/external-modules)</Tip>


## Bulk Operations

Here are patterns for working with multiple imports:

```python
# Update imports from a specific module
old_path = "./old/path"
new_path = "./new/path"

for imp in file.imports:
    if imp.module == old_path:
        imp.set_module(new_path)

# Remove unused imports (excluding external)
for imp in file.imports:
    if not imp.usages and not isinstance(imp.resolved_symbol, ExternalModule):
        print(f"Removing: {imp.name}")
        imp.remove()

# Consolidate duplicate imports
from collections import defaultdict

module_imports = defaultdict(list)
for imp in file.imports:
    module_imports[imp.module].append(imp)

for module, imports in module_imports.items():
    if len(imports) > 1:
        # Create combined import
        symbols = [imp.name for imp in imports]
        file.add_import(
            f"import {{ {', '.join(symbols)} }} from '{module}'"
        )
        # Remove old imports
        for imp in imports:
            imp.remove()
```

<Note>
Always check if imports resolve to external modules before modification to avoid breaking third-party package imports.
</Note>

## Import Statements vs Imports

Codegen provides two levels of abstraction for working with imports:

- [ImportStatement](/api-reference/core/ImportStatement) - Represents a complete import statement
- [Import](/api-reference/core/Import) - Represents individual imported symbols

<CodeGroup>
```python Python
# One ImportStatement containing multiple Import objects
from math import sin, cos as cosine
# Creates:
# - Import for 'sin'
# - Import for 'cos' with alias 'cosine'
```

```typescript Typescript
// One ImportStatement containing multiple Import objects
import { sin, cos as cosine } from 'math';
// Creates:
// - Import for 'sin'
// - Import for 'cos' with alias 'cosine'
```
</CodeGroup>

You can access these through [File.imports](/api-reference/core/File#imports) and [File.import_statements](/api-reference/core/File#import-statements):

```python
# Direct access to imports
for imp in file.imports:
    ...

# Access to imports via statements
for stmt in file.import_statements:
    for imp in stmt.imports:
        ...
```

<Note>
ImportStatement inherits from [Statement](/building-with-codegen/statements-and-code-blocks), providing operations like `remove()` and `insert_before()`.
</Note>

---
title: "The Export API"
sidebarTitle: "Exports"
icon: "file-export"
iconType: "solid"
---

The [Export](/api-reference/core/Export) API provides tools for managing exports and module boundaries in TypeScript codebases.

<Note>Exports are a TS-only language feature</Note>

## Export Statements vs Exports

Similar to imports, Codegen provides two levels of abstraction for working with exports:

- [ExportStatement](/api-reference/core/ExportStatement) - Represents a complete export statement
- [Export](/api-reference/core/Export) - Represents individual exported symbols

```typescript
// One ExportStatement containing multiple Export objects
export { foo, bar as default, type User };
// Creates:
// - Export for 'foo'
// - Export for 'bar' as default
// - Export for 'User' as a type

// Direct exports create one ExportStatement per export
export const value = 42;
export function process() {}
```

You can access these through your file's collections:

```python
# Access all exports in the codebase
for export in codebase.exports:
    ...

# Access all export statements
for stmt in file.export_statements:
    for exp in stmt.exports:
        ...
```

<Note>
ExportStatement inherits from [Statement](/building-with-codegen/statements-and-code-blocks), providing operations like `remove()` and `insert_before()`. This is particularly useful when you want to manipulate the entire export declaration.
</Note>

## Common Operations

Here are common operations for working with exports:

```python
# Add exports from source code
file.add_export_from_source("export { MyComponent };")
file.add_export_from_source("export type { MyType } from './types';")

# Export existing symbols
component = file.get_function("MyComponent")
file.add_export(component)  # export { MyComponent }
file.add_export(component, alias="default")  # export { MyComponent as default }

# Convert to type export
export = file.get_export("MyType")
export.make_type_export()

# Remove exports
export = file.get_export("MyComponent")
export.remove()  # Removes export but keeps the symbol

# Remove multiple exports
for export in file.exports:
    if not export.is_type_export():
        export.remove()

# Update export properties
export.update(
    name="NewName",
    is_type=True,
    is_default=False
)

# Export from another file
other_file = codebase.get_file("./components.ts")
component = other_file.get_class("Button")
file.add_export(component, from_file=other_file)  # export { Button } from './components';

# Analyze symbols being exported
for export in file.exports:
    if isinstance(export.exported_symbol, ExternalModule):
        print('Exporting ExternalModule')
    else:
        ...
```

<Note>
When adding exports, you can:
- Add from source code with `add_export_from_source()`
- Export existing symbols with `add_export()`
- Re-export from other files by specifying `from_file`

The export will automatically handle adding any required imports.
</Note>

## Export Types

Codegen supports several types of exports:

```typescript
// Direct exports
export const value = 42;                     // Value export
export function myFunction() {}              // Function export
export class MyClass {}                      // Class export
export type MyType = string;                 // Type export
export interface MyInterface {}              // Interface export
export enum MyEnum {}                        // Enum export

// Re-exports
export { foo, bar } from './other-file';     // Named re-exports
export type { Type } from './other-file';    // Type re-exports
export * from './other-file';                // Wildcard re-exports
export * as utils from './other-file';       // Namespace re-exports

// Aliased exports
export { foo as foop };                      // Basic alias
export { foo as default };                   // Default export alias
export { bar as baz } from './other-file';   // Re-export with alias
```

## Identifying Export Types

The Export API provides methods to identify and filter exports:
- [.is_type_export()](/api-reference/typescript/TSExport#is-type-export)
- [.is_default_export()](/api-reference/typescript/TSExport#is-default-export)
- [.is_wildcard_export()](/api-reference/typescript/TSExport#is-wildcard-export)


```python
# Check export types
for exp in file.exports:
    if exp.is_type_export():
        print(f"Type export: {exp.name}")
    elif exp.is_default_export():
        print(f"Default export: {exp.name}")
    elif exp.is_wildcard_export():
        print(f"Wildcard export from: {exp.from_file.filepath}")
```

## Export Resolution

You can trace exports to their original symbols:

```python
for exp in file.exports:
    if exp.is_reexport():
        # Get original and current symbols
        current = exp.exported_symbol
        original = exp.resolved_symbol

        print(f"Re-exporting {original.name} from {exp.from_file.filepath}")
        print(f"Through: {' -> '.join(e.file.filepath for e in exp.export_chain)}")
```

## Managing Re-exports

You can manage re-exports with the [TSExport.is_reexport()](/api-reference/typescript/TSExport#is-reexport) API:

```python
# Create public API
index_file = codebase.get_file("index.ts")

# Re-export from internal files
for internal_file in codebase.files:
    if internal_file.name != "index":
        for symbol in internal_file.symbols:
            if symbol.is_public:
                index_file.add_export(
                    symbol,
                    from_file=internal_file
                )

# Convert default to named exports
for exp in file.exports:
    if exp.is_default_export():
        exp.make_named_export()

# Consolidate re-exports
from collections import defaultdict

file_exports = defaultdict(list)
for exp in file.exports:
    if exp.is_reexport():
        file_exports[exp.from_file].append(exp)

for from_file, exports in file_exports.items():
    if len(exports) > 1:
        # Create consolidated re-export
        names = [exp.name for exp in exports]
        file.add_export_from_source(
            f"export {{ {', '.join(names)} }} from '{from_file.filepath}'"
        )
        # Remove individual exports
        for exp in exports:
            exp.remove()
```

<Note>
When managing exports, consider the impact on your module's public API. Not all symbols that can be exported should be exported.
</Note>

---
title: "Inheritable Behaviors"
sidebarTitle: "Inheritable Behaviors"
icon: "puzzle-piece"
iconType: "solid"
---

Codegen uses a set of core behaviors that can be inherited by code elements. These behaviors provide consistent APIs across different types of symbols.


## Core Behaviors

- [HasName](/api-reference/core/HasName): For elements with [Names](/api-reference/core/Name) (Functions, Classes, Assignments, etc.)
- [HasValue](/api-reference/core/HasValue): For elements with [Values](/api-reference/core/Value) (Arguments, Assignments, etc.)
- [HasBlock](/api-reference/core/HasBlock): For elements containing [CodeBlocks](/api-reference/core/CodeBlock) (Files, Functions, Classes)
- [Editable](/api-reference/core/Editable): For elements that can be safely modified ([learn more](/building-with-codegen/the-editable-api))

<Note>These "behaviors" are implemented as inherited classes.</Note>

## Working with Names

The [HasName](/api-reference/core/HasName) behavior provides APIs for working with named elements:

```python
# Access the name
print(function.name)  # Base name without namespace
print(function.full_name)  # Full qualified name with namespace

# Modify the name
function.set_name("new_name")  # Changes just the name
function.rename("new_name")    # Changes name and updates all usages

# Get the underlying name node
name_node = function.get_name()
```

## Working with Values

The [HasValue](/api-reference/core/HasValue) behavior provides APIs for elements that have values:

```python
# Access the value
value = variable.value  # Gets the value Expression node
print(value.source)     # Gets the string content

# Modify the value
variable.set_value("new_value")

# Common patterns
if variable.value is not None:
    print(f"{variable.name} = {variable.value.source}")
```

## Working with Code Blocks

The [HasBlock](/api-reference/core/HasBlock) behavior provides APIs for elements containing code:

```python
# Access the code block
block = function.code_block
print(len(block.statements))  # Number of statements
printS(block.source)
```

<Info>
  Learn more about [CodeBlocks and Statements
  here](/building-with-codegen/statements-and-code-blocks)
</Info>

## Working with Attributes

The [get_attribute](/api-reference/core/Class#get-attribute) method provides APIs for attribute access:

```python
# Common patterns
class_attr = class_def.get_attribute("attribute_name")
if class_attr:
    print(f"Class variable value: {class_attr.value.source}")
```

<Info>
  Learn more about [working with Attributes
  here](/building-with-codegen/class-api#class-attributes).
</Info>

## Behavior Combinations

Many code elements inherit multiple behaviors. For example, a function typically has:

```python
# Functions combine multiple behaviors
function = codebase.get_function("process_data")

# HasName behavior
print(function.name)
function.rename("process_input")

# HasBlock behavior
print(len(function.code_block.statements))
function.add_decorator("@timer")

# Editable behavior
function.edit("def process_input():\n    pass")
```


---
title: "Statements and Code Blocks"
sidebarTitle: "Statements and Code Blocks"
icon: "code"
iconType: "solid"
---

Codegen uses two classes to represent code structure at the highest level:

- [Statement](../api-reference/core/Statement): Represents a single line or block of code

  - Can be assignments, imports, loops, conditionals, etc.
  - Contains source code, dependencies, and type information
  - May contain nested code blocks (like in functions or loops)

- [CodeBlock](../api-reference/core/CodeBlock): A container for multiple Statements
  - Found in files, functions, classes, and control flow blocks
  - Provides APIs for analyzing and manipulating statements
  - Handles scope, variables, and dependencies

Codegen provides rich APIs for working with code statements and blocks, allowing you to analyze and manipulate code structure at a granular level.

## Working with Statements

### Basic Usage

Every file, function, and class in Codegen has a [CodeBlock](../api-reference/core/CodeBlock) that contains its statements:

```python
# Access statements in a file
file = codebase.get_file("main.py")
for statement in file.code_block.statements:
    print(f"Statement type: {statement.statement_type}")

# Access statements in a function
function = file.get_function("process_data")
for statement in function.code_block.statements:
    print(f"Statement: {statement.source}")
```

### Filtering Statements

Filter through statements using Python's builtin `isinstance` function.

```python
# Filter statements by type
for stmt in file.code_block.statements:
    if isinstance(stmt, ImportStatement):
        print(stmt)
```

### Adding Statements

Functions and Files support [.prepend_statement(...)](../api-reference/core/Symbol#prepend-statement) and [.add_statement(...)](../api-reference/core/Function#add-statement) to add statements to the symbol.

<Tip>
  See [Adding
  Statements](/building-with-codegen/symbol-api#function-statement-manipulation)
  for details.
</Tip>

### Working with Nested Structures

Frequently you will want to check if a statement is nested within another structure, for example if a statement is inside an `if` block or a `try/catch` statement.

Codegen supports this functionality with the [Editable.is_wrapped_in(...)](../api-reference/core/Editable#is-wrapped-in) method.

```python
func = codebase.get_function("process_data")
for usage in func.local_variable_usages:
    if usage.is_wrapped_in(IfStatement):
        print(f"Usage of {usage.name} is inside an if block")
```

Similarly, all Editable objects support the `.parent_statement`, which can be used to navigate the statement hierarchy.

```python
func = codebase.get_function("process_data")
for usage in func.local_variable_usages:
    if isinstance(usage.parent_statement, IfStatement):
        print(f"Usage of {usage.name} is directly beneath an IfStatement")
```

### Wrapping and Unwrapping Statements

[CodeBlocks](../api-reference/core/CodeBlock) support wrapping and unwrapping with the following APIs:

- [.wrap(...)](../api-reference/core/CodeBlock#wrap) - allows you to wrap a statement in a new structure.
- [.unwrap(...)](../api-reference/core/CodeBlock#unwrap) - allows you to remove the wrapping structure while preserving the code block's contents.

```python
# Wrap code blocks with new structures
function.code_block.wrap("with open('test.txt', 'w') as f:")
# Result:
#   with open('test.txt', 'w') as f:
#       original_code_here...

# Wrap code in a function
file.code_block.wrap("def process_data(a, b):")
# Result:
#   def process_data(a, b):
#       original_code_here...

# Unwrap code from its container
if_block.code_block.unwrap()  # Removes the if statement but keeps its body
while_loop.code_block.unwrap()  # Removes the while loop but keeps its body
```

<Warning>
  Both `wrap` and `unwrap` are potentially unsafe changes and will modify
  business logic.
</Warning>

<Note>
  The `unwrap()` method preserves the indentation of the code block's contents
  while removing the wrapping structure. This is useful for refactoring nested
  code structures.
</Note>

## Statement Types

Codegen supports various statement types, each with specific APIs:

### [Import Statements](../api-reference/core/ImportStatement) / [Export Statements](../api-reference/core/ExportStatement)

<Tip>
  See [imports](/building-with-codegen/imports) and [exports](../building-with-codegen/exports) for
  more details.
</Tip>

```python
# Access import statements
for import_stmt in file.import_statements:
    print(f"Module: {import_stmt.module}")
    for imported in import_stmt.imports:
        print(f"  Imported: {imported.name}")

# Remove specific imports
import_stmt = file.import_statements[0]
import_stmt.imports[0].remove()  # Remove first import

# Remove entire import statement
import_stmt.remove()
```

### [If/Else Statements](../api-reference/core/IfBlockStatement)

If/Else statements provide rich APIs for analyzing and manipulating conditional logic:

```python
# Access if/else blocks
if_block = file.code_block.statements[0]
print(f"Condition: {if_block.condition.source}")

# Check block types
if if_block.is_if_statement:
    print("Main if block")
elif if_block.is_elif_statement:
    print("Elif block")
elif if_block.is_else_statement:
    print("Else block")

# Access alternative blocks
for elif_block in if_block.elif_statements:
    print(f"Elif condition: {elif_block.condition.source}")

if else_block := if_block.else_statement:
    print("Has else block")

# Access nested code blocks
for block in if_block.nested_code_blocks:
    print(f"Block statements: {len(block.statements)}")
```

If blocks also support condition reduction, which can simplify conditional logic:

```python
# Reduce if condition to True
if_block.reduce_condition(True)
# Before:
#   if condition:
#       print("a")
#   else:
#       print("b")
# After:
#   print("a")

# Reduce elif condition to False
elif_block.reduce_condition(False)
# Before:
#   if a:
#       print("a")
#   elif condition:
#       print("b")
#   else:
#       print("c")
# After:
#   if a:
#       print("a")
#   else:
#       print("c")
```

<Note>
  When reducing conditions, Codegen automatically handles the restructuring of
  elif/else chains and preserves the correct control flow.
</Note>

### [Switch](../api-reference/core/SwitchStatement)/[Match](../api-reference/python/PyMatchStatement) Statements

```python
# TypeScript switch statements
switch_stmt = file.code_block.statements[0]
for case_stmt in switch_stmt.cases:
    print(f"Case condition: {case_stmt.condition}")
    print(f"Is default: {case_stmt.default}")

    # Access statements in each case
    for statement in case_stmt.code_block.statements:
        print(f"Statement: {statement.source}")

# Python match statements
match_stmt = file.code_block.statements[0]
for case in match_stmt.cases:
    print(f"Pattern: {case.pattern}")
    for statement in case.code_block.statements:
        print(f"Statement: {statement.source}")
```

### [While Statements](../api-reference/core/WhileStatement)

```python
while_stmt = file.code_block.statements[0]
print(f"Condition: {while_stmt.condition}")

# Access loop body
for statement in while_stmt.code_block.statements:
    print(f"Body statement: {statement.source}")

# Get function calls within the loop
for call in while_stmt.function_calls:
    print(f"Function call: {call.source}")
```

### [Assignment Statements](../api-reference/core/AssignmentStatement)

```python
# Access assignments in a code block
for statement in code_block.statements:
    if statement.statement_type == StatementType.ASSIGNMENT:
        for assignment in statement.assignments:
            print(f"Variable: {assignment.name}")
            print(f"Value: {assignment.value}")
```

## Working with Code Blocks

Code blocks provide several ways to analyze and manipulate their content:

### Statement Access

```python
code_block = function.code_block

# Get all statements
all_statements = code_block.statements

# Get statements by type
if_blocks = code_block.if_blocks
while_loops = code_block.while_loops
try_blocks = code_block.try_blocks

# Get local variables
local_vars = code_block.get_local_var_assignments()
```

### Statement Dependencies

```python
# Get dependencies between statements
function = file.get_function("process")
for statement in function.code_block.statements:
    deps = statement.dependencies
    print(f"Statement {statement.source} depends on: {[d.name for d in deps]}")
```

### Parent-Child Relationships

```python
# Access parent statements
function = file.get_function("main")
parent_stmt = function.parent_statement

# Access nested symbols
class_def = file.get_class("MyClass")
for method in class_def.methods:
    parent = method.parent_statement
    print(f"Method {method.name} is defined in {parent.source}")
```

## Common Operations

### Finding Statements

```python
# Find specific statements
assignments = [s for s in code_block.statements
              if s.statement_type == StatementType.ASSIGNMENT]

# Find statements by content
matching = [s for s in code_block.statements
           if "specific_function()" in s.source]
```

### Analyzing Flow Control

```python
# Analyze control flow
for statement in code_block.statements:
    if statement.statement_type == StatementType.IF_BLOCK:
        print("Condition:", statement.condition)
        print("Then:", statement.consequence_block.statements)
        if statement.alternative_block:
            print("Else:", statement.alternative_block.statements)
```

### Working with Functions

```python
# Analyze function calls in statements
for statement in code_block.statements:
    for call in statement.function_calls:
        print(f"Calls function: {call.name}")
        print(f"With arguments: {[arg.source for arg in call.arguments]}")
```


---
title: "Dependencies and Usages"
sidebarTitle: "Dependencies and Usages"
icon: "share-nodes"
iconType: "solid"
---

Codegen pre-computes dependencies and usages for all symbols in the codebase, enabling constant-time queries for these relationships.

## Overview

Codegen provides two main ways to track relationships between symbols:

- [`.dependencies`](/api-reference/core/Symbol#dependencies) / [`.get_dependencies(...)`](/api-reference/core/Symbol#get-dependencies) - What symbols does this symbol depend on?
- [`.usages`](/api-reference/core/Symbol#usages) / [`.usages(...)`](/api-reference/core/Symbol#usages) - Where is this symbol used?

Dependencies and usages are inverses of each other. For example, given the following input code:

```python
# Input code
from module import BaseClass

class MyClass(BaseClass):
    pass
```

The following assertions will hold in the Codegen API:

```python
base = codebase.get_symbol("BaseClass")
my_class = codebase.get_symbol("MyClass")

# MyClass depends on BaseClass
assert base in my_class.dependencies

# BaseClass is used by MyClass
assert my_class in base.usages
```

If `A` depends on `B`, then `B` is used by `A`. This relationship is tracked in both directions, allowing you to navigate the codebase from either perspective.

```mermaid

flowchart LR
    B(BaseClass)



    A(MyClass)
    B ---| used by |A
    A ---|depends on |B

    classDef default fill:#fff,stroke:#000,color:#000;
```

- `MyClass.dependencies` answers the question: *"which symbols in the codebase does MyClass depend on?"*

- `BaseClass.usages` answers the question: *"which symbols in the codebase use BaseClass?"*

## Usage Types

Both APIs use the [UsageType](../api-reference/core/UsageType) enum to specify different kinds of relationships:

```python
class UsageType(IntFlag):
    DIRECT = auto()    # Direct usage within the same file
    CHAINED = auto()   # Usage through attribute access (module.symbol)
    INDIRECT = auto()  # Usage through a non-aliased import
    ALIASED = auto()   # Usage through an aliased import
```

### DIRECT Usage

A direct usage occurs when a symbol is used in the same file where it's defined, without going through any imports or attribute access.

```python
# Define MyClass
class MyClass:
    def __init__(self):
        pass

# Direct usage of MyClass in same file
class Child(MyClass):
    pass
```

### CHAINED Usage

A chained usage occurs when a symbol is accessed through module or object attribute access, using dot notation.

```python
import module

# Chained usage of ClassB through module
obj = module.ClassB()
# Chained usage of method through obj
result = obj.method()
```

### INDIRECT Usage

An indirect usage happens when a symbol is used through a non-aliased import statement.

```python
from module import BaseClass

# Indirect usage of BaseClass through import
class MyClass(BaseClass):
  pass
```

### ALIASED Usage

An aliased usage occurs when a symbol is used through an import with an alias.

```python
from module import BaseClass as AliasedBase

# Aliased usage of BaseClass
class MyClass(AliasedBase):
  pass
```

## Dependencies API

The dependencies API lets you find what symbols a given symbol depends on.

### Basic Usage

```python
# Get all direct dependencies
deps = my_class.dependencies  # Shorthand for get_dependencies(UsageType.DIRECT)

# Get dependencies of specific types
direct_deps = my_class.get_dependencies(UsageType.DIRECT)
chained_deps = my_class.get_dependencies(UsageType.CHAINED)
indirect_deps = my_class.get_dependencies(UsageType.INDIRECT)
```

### Combining Usage Types

You can combine usage types using the bitwise OR operator:

```python
# Get both direct and indirect dependencies
deps = my_class.get_dependencies(UsageType.DIRECT | UsageType.INDIRECT)

# Get all types of dependencies
deps = my_class.get_dependencies(
    UsageType.DIRECT | UsageType.CHAINED |
    UsageType.INDIRECT | UsageType.ALIASED
)
```

### Common Patterns

1. Finding dead code (symbols with no usages):

```python
# Check if a symbol is unused
def is_dead_code(symbol):
    return not symbol.usages

# Find all unused functions in a file
dead_functions = [f for f in file.functions if not f.usages]
```

<Tip>
  See [Deleting Dead Code](/tutorials/deleting-dead-code) to learn more about finding
  unused code.
</Tip>

2. Finding all imports that a symbol uses:

```python
# Get all imports a class depends on
class_imports = [dep for dep in my_class.dependencies if isinstance(dep, Import)]

# Get all imports used by a function, including indirect ones
all_function_imports = [
    dep for dep in my_function.get_dependencies(UsageType.DIRECT | UsageType.INDIRECT)
    if isinstance(dep, Import)
]
```


---
title: "Function Calls and Call Sites"
sidebarTitle: "Function Calls"
icon: "function"
iconType: "solid"
---

Codegen provides comprehensive APIs for working with function calls through several key classes:

- [FunctionCall](../api-reference/core/FunctionCall) - Represents a function invocation
- [Argument](../api-reference/core/Argument) - Represents arguments passed to a function
- [Parameter](../api-reference/core/Parameter) - Represents parameters in a function definition

<Tip>
  See [Migrating APIs](/tutorials/migrating-apis) for relevant tutorials and
  applications.
</Tip>

## Navigating Function Calls

Codegen provides two main ways to navigate function calls:

1. From a function to its call sites using [call_sites](../api-reference/core/Function#call-sites)
2. From a function to the calls it makes (within it's [CodeBlock](../api-reference/core/CodeBlock)) using [function_calls](../api-reference/core/Function#function-calls)

Here's how to analyze function usage patterns:

```python
# Find the most called function
most_called = max(codebase.functions, key=lambda f: len(f.call_sites))
print(f"\nMost called function: {most_called.name}")
print(f"Called {len(most_called.call_sites)} times from:")
for call in most_called.call_sites:
    print(f"  - {call.parent_function.name} at line {call.start_point[0]}")

# Find function that makes the most calls
most_calls = max(codebase.functions, key=lambda f: len(f.function_calls))
print(f"\nFunction making most calls: {most_calls.name}")
print(f"Makes {len(most_calls.function_calls)} calls to:")
for call in most_calls.function_calls:
    print(f"  - {call.name}")

# Find functions with no callers (potential dead code)
unused = [f for f in codebase.functions if len(f.call_sites) == 0]
print(f"\nUnused functions:")
for func in unused:
    print(f"  - {func.name} in {func.filepath}")

# Find recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)]
print(f"\nRecursive functions:")
for func in recursive:
    print(f"  - {func.name}")
```

This navigation allows you to:

- Find heavily used functions
- Analyze call patterns
- Map dependencies between functions

## Arguments and Parameters

The [Argument](../api-reference/core/Argument) class represents values passed to a function, while [Parameter](../api-reference/core/Parameter) represents the receiving variables in the function definition:

Consider the following code:

```python
# Source code:
def process_data(input_data: str, debug: bool = False):
    pass

process_data("test", debug=True)
```

You can access and modify the arguments and parameters of the function call with APIs detailed below.

### Finding Arguments

The primary APIs for finding arguments are:

- [FunctionCall.args](/api-reference/core/FunctionCall#args)
- [FunctionCall.get_arg_by_parameter_name(...)](/api-reference/core/FunctionCall#get-arg-by-parameter-name)
- [FunctionCall.get_arg_by_index(...)](/api-reference/core/FunctionCall#get-arg-by-index)

```python
# Get the function call
call = file.function_calls[0]

# Working with arguments
for arg in call.args:
    print(f"Arg {arg.index}: {arg.value}")  # Access argument value
    print(f"Is named: {arg.is_named}")      # Check if it's a kwarg
    print(f"Name: {arg.name}")              # For kwargs, e.g. "debug"

    # Get corresponding parameter
    if param := arg.parameter:
        print(f"Parameter type: {param.type}")
        print(f"Is optional: {param.is_optional}")
        print(f"Has default: {param.default}")

# Finding specific arguments
debug_arg = call.get_arg_by_parameter_name("debug")
first_arg = call.get_arg_by_index(0)
```

### Modifying Arguments

There are two ways to modify function call arguments:

1. Using [FunctionCall.set_kwarg(...)](/api-reference/core/FunctionCall#set-kwarg) to add or modify keyword arguments:

```python
# Modifying keyword arguments
call.set_kwarg("debug", "False")  # Modifies existing kwarg
call.set_kwarg("new_param", "value", create_on_missing=True)  # Adds new kwarg
call.set_kwarg("input_data", "'new_value'", override_existing=True)  # Converts positional to kwarg
```

2. Using [FuncionCall.args.append(...)](/api-reference/core/FunctionCall#args) to add new arguments:
   <Tip>
     [FunctionCall.args](/api-reference/core/FunctionCall#args) is a
     [Collection](/building-with-codegen/collections) of
     [Argument](/api-reference/core/Argument) objects, so it supports
     [.append(...)](/api-reference/core/List#append),
     [.insert(...)](/api-reference/core/List#insert) and other collection
     methods.
   </Tip>

```python
# Adding new arguments
call.args.append('cloud="aws"')  # Add a new keyword argument
call.args.append('"value"')      # Add a new positional argument

# Real-world example: Adding arguments to a decorator
@app.function(image=runner_image)
def my_func():
    pass

# Add cloud and region if not present
if "cloud=" not in decorator.call.source:
    decorator.call.args.append('cloud="aws"')
if "region=" not in decorator.call.source:
    decorator.call.args.append('region="us-east-1"')
```

The `set_kwarg` method provides intelligent argument manipulation:

- If the argument exists and is positional, it converts it to a keyword argument
- If the argument exists and is already a keyword, it updates its value (if override_existing=True)
- If the argument doesn't exist, it creates it (if create_on_missing=True)
- When creating new arguments, it intelligently places them based on parameter order

Arguments and parameters support safe edit operations like so:

```python
# Modifying arguments
debug_arg.edit("False")              # Change argument value
first_arg.add_keyword("input_data")  # Convert to named argument

# modifying parameters
param = codebase.get_function('process_data').get_parameter('debug')
param.rename('_debug') # updates all call-sites
param.set_type_annotation('bool')
```

## Finding Function Definitions

Every [FunctionCall](../api-reference/core/FunctionCall) can navigate to its definition through [function_definition](../api-reference/core/FunctionCall#function-definition) and [function_definitions](../api-reference/core/FunctionCall#function-definitions):

```python
function_call = codebase.files[0].function_calls[0]
function_definition = function_call.function_definition
print(f"Definition found in: {function_definition.filepath}")
```

## Finding Parent (Containing) Functions

FunctionCalls can access the function that invokes it via [parent_function](../api-reference/core/FunctionCall#parent-function).

For example, given the following code:

```python
# Source code:
def outer():
    def inner():
        helper()
    inner()
```

You can find the parent function of the helper call:

```python
# Manipulation code:
# Find the helper() call
helper_call = file.get_function("outer").function_calls[1]

# Get containing function
parent = helper_call.parent_function
print(f"Call is inside: {parent.name}")  # 'inner'

# Get the full call hierarchy
outer = parent.parent_function
print(f"Which is inside: {outer.name}")  # 'outer'
```

## Method Chaining

Codegen enables working with chained method calls through [predecessor](../api-reference/core/FunctionCall#predecessor) and related properties:

For example, for the following database query:

```python
# Source code:
query.select(Table)
    .where(id=1)
    .order_by("name")
    .limit(10)
```

You can access the chain of calls:

```python
# Manipulation code:
# Get the `limit` call in the chain
limit_call = next(f for f in file.function.function_calls if f.name == "limit", None)

# Navigate backwards through the chain
order_by = limit_call.predecessor
where = order_by.predecessor
select = where.predecessor

# Get the full chain at once
chain = limit_call.call_chain  # [select, where, order_by, limit]

# Access the root object
base = limit_call.base  # Returns the 'query' object

# Check call relationships
print(f"After {order_by.name}: {limit_call.name}")
print(f"Before {where.name}: {select.name}")
```


---
title: "Variable Assignments"
sidebarTitle: "Variable Assignments"
icon: "equals"
iconType: "solid"
---

Codegen's enables manipulation of variable assignments via the following classes:

- [AssignmentStatement](../api-reference/core/AssignmentStatement) - A statement containing one or more assignments
- [Assignment](../api-reference/core/Assignment) - A single assignment within an AssignmentStatement


### Simple Value Changes

Consider the following source code:

```typescript
const userId = 123;
const [userName, userAge] = ["Eve", 25];
```

In Codegen, you can access assignments with the [get_local_var_assignment](../api-reference/core/CodeBlock#get-local-var-assignment) method.

You can then manipulate the assignment with the [set_value](../api-reference/core/Assignment#set-value) method.

```python
id_assignment = file.code_block.get_local_var_assignment("userId")
id_assignment.set_value("456")

name_assignment = file.code_block.get_local_var_assignment("name")
name_assignment.rename("userName")
```

<Note>
  Assignments inherit both [HasName](/api-reference/core/HasName) and
  [HasValue](/api-reference/core/HasValue) behaviors. See [Inheritable
  Behaviors](/building-with-codegen/inheritable-behaviors) for more details.
</Note>

### Type Annotations

Similarly, you can set type annotations with the [set_type_annotation](../api-reference/core/Assignment#set-type-annotation) method.

For example, consider the following source code:

```typescript
let status;
const data = fetchData();
```

You can manipulate the assignments as follows:

```python
status_assignment = file.code_block.get_local_var_assignment("status")
status_assignment.set_type_annotation("Status")
status_assignment.set_value("Status.ACTIVE")

data_assignment = file.code_block.get_local_var_assignment("data")
data_assignment.set_type_annotation("ResponseData<T>")

# Result:
let status: Status = Status.ACTIVE;
const data: ResponseData<T> = fetchData();
```

## Tracking Usages and Dependencies

Like other symbols, Assignments support [usages](/api-reference/core/Assignment#usages) and [dependencies](/api-reference/core/Assignment#dependencies).

```python
assignment = file.code_block.get_local_var_assignment("userId")

# Get all usages of the assignment
usages = assignment.usages

# Get all dependencies of the assignment
dependencies = assignment.dependencies
```

<Tip>
  See [Dependencies and Usages](/building-with-codegen/dependencies-and-usages)
  for more details.
</Tip>


---
title: "Local Variables"
sidebarTitle: "Local Variables"
icon: "cube"
iconType: "solid"
---

This document explains how to work with local variables in Codegen.

## Overview

Through the [CodeBlock](../api-reference/core/CodeBlock) class, Codegen exposes APIs for analyzing and manipulating local variables within code blocks.

- [local_var_assignments](../api-reference/core/CodeBlock#local-var-assignments): find all [Assignments](../api-reference/core/Assignment) in this scope
- [get_local_var_assignment(...)](../api-reference/core/CodeBlock#get-local-var-assignment): get specific [Assignments](../api-reference/core/Assignment) by name
- [rename_local_variable(...)](../api-reference/core/CodeBlock#rename-local-variable): rename variables safely across the current scope

## Basic Usage

Every code block (function body, loop body, etc.) provides access to its local variables:

```python
# Get all local variables in a function
function = codebase.get_function("process_data")
local_vars = function.code_block.local_var_assignments
for var in local_vars:
    print(var.name)

# Find a specific variable
config_var = function.code_block.get_local_var_assignment("config")
config_var.rename("settings")  # Updates all references safely

# Rename a variable used in this scope (but not necessarily declared here)
function.rename_local_variable("foo", "bar")
```

## Fuzzy Matching

Codegen supports fuzzy matching when searching for local variables. This allows you to find variables whose names contain a substring, rather than requiring exact matches:

```python
# Get all local variables containing "config"
function = codebase.get_function("process_data")

# Exact match - only finds variables named exactly "config"
exact_matches = function.code_block.get_local_var_assignments("config")
# Returns: config = {...}

# Fuzzy match - finds any variable containing "config"
fuzzy_matches = function.code_block.get_local_var_assignments("config", fuzzy_match=True)
# Returns: config = {...}, app_config = {...}, config_settings = {...}

# Fuzzy matching also works for variable usages
usages = function.code_block.get_variable_usages("config", fuzzy_match=True)

# And for renaming variables
function.code_block.rename_variable_usages("config", "settings", fuzzy_match=True)
# Renames: config -> settings, app_config -> app_settings, config_settings -> settings_settings
```

<Note>
  Be careful with fuzzy matching when renaming variables, as it will replace the
  matched substring in all variable names. This might lead to unintended renames
  like `config_settings` becoming `settings_settings`.
</Note>


---
title: "Comments and Docstrings"
sidebarTitle: "Comments & Docstrings"
icon: "comment"
iconType: "solid"
---

Codegen enables reading, modifying, and manipulating comments and docstrings while preserving proper formatting.

This guide describes proper usage of the following classes:

- [Comment](/api-reference/core/Comment) - Represents a single comment.
- [CommentGroup](/api-reference/core/CommentGroup) - Represents a group of comments.

## Accessing with Comments

Comments can be accessed through any symbol or directly from code blocks. Each comment is represented by a `Comment` object that provides access to both the raw source and parsed text:

```python
# Find all comments in a file
file = codebase.get_file("my_file.py")
for comment in file.code_block.comments:
    print(comment.text)

# Access comments associated with a symbol
symbol = file.get_symbol("my_function")
if symbol.comment:
    print(symbol.comment.text)  # Comment text without delimiters
    print(symbol.comment.source)  # Full comment including delimiters

# Access inline comments
if symbol.inline_comment:
    print(symbol.inline_comment.text)

# Accessing all comments in a function
for comment in symbol.code_block.comments:
    print(comment.text)
```

### Editing Comments

Comments can be modified using the `edit_text()` method, which handles formatting and delimiters automatically:

```python
# Edit a regular comment
symbol.comment.edit_text("Updated comment text")

# Edit an inline comment
symbol.set_inline_comment("New inline comment")
```

### Comment Groups

Multiple consecutive comments are automatically grouped into a `CommentGroup`, which can be edited as a single unit:

```python
# Original comments:
# First line
# Second line
# Third line

comment_group = symbol.comment
print(comment_group.text)  # "First line\nSecond line\nThird line"

# Edit the entire group at once
comment_group.edit_text("New first line\nNew second line")
```

## Working with Docstrings

Docstrings are special comments that document functions, classes, and modules. Codegen provides similar APIs for working with docstrings:

```python
function = file.get_symbol("my_function")
if function.docstring:
    print(function.docstring.text)  # Docstring content
    print(function.docstring.source)  # Full docstring with delimiters
```

### Adding Docstrings

You can add docstrings to any symbol that supports them:

```python
# Add a single-line docstring
function.set_docstring("A brief description")

# Add a multi-line docstring
function.set_docstring("""
    A longer description that
    spans multiple lines.

    Args:
        param1: Description of first parameter
""")
```

### Language-Specific Formatting

Codegen automatically handles language-specific docstring formatting:

```python
# Python: Uses triple quotes
def my_function():
    """Docstring is formatted with triple quotes."""
    pass
```

```typescript
// TypeScript: Uses JSDoc style
function myFunction() {
  /** Docstring is formatted as JSDoc */
}
```

### Editing Docstrings

Like comments, docstrings can be modified while preserving formatting:

```python
# Edit a docstring
function.docstring.edit_text("Updated documentation")

# Edit a multi-line docstring
function.docstring.edit_text("""
    Updated multi-line documentation
    that preserves indentation and formatting.
""")
```

## Comment Operations

Codegen provides utilities for working with comments at scale. For example, you can update or remove specific types of comments across your codebase:

```python
# Example: Remove eslint disable comments for a specific rule
for file in codebase.files:
    for comment in file.code_block.comments:
        if "eslint-disable" in comment.source:
            # Check if comment disables specific rule
            if "@typescript-eslint/no-explicit-any" in comment.text:
                comment.remove()
```

<Note>
  When editing multi-line comments or docstrings, Codegen automatically handles
  indentation and maintains the existing comment style.
</Note>

## Special APIs and AI Integration

### Google Style Docstrings

Codegen supports Google-style docstrings and can handle their specific formatting, using the [CommentGroup.to_google_docstring(...)](/api-reference/core/CommentGroup#to-google-docstring) method.

```python
# Edit while preserving Google style
symbol_a = file.get_symbol("SymbolA")
func_b = symbol_a.get_method("funcB")
func_b.docstring.to_google_docstring(func_b)
```

### Using AI for Documentation

Codegen integrates with LLMs to help generate and improve documentation. You can use the [Codebase.ai(...)](/api-reference/core/Codebase#ai) method to:

- Generate comprehensive docstrings
- Update existing documentation
- Convert between documentation styles
- Add parameter descriptions

```python
# Generate a docstring using AI
function = codebase.get_function("my_function")

new_docstring = codebase.ai(
    "Generate a comprehensive docstring in Google style",
    target=function
    context={
        # provide additional context to the LLM
        'usages': function.usages,
        'dependencies': function.dependencies
    }
)
function.set_docstring(new_docstring)
```

<Tip>
  Learn more about AI documentation capabilities in our [Documentation
  Guide](/tutorials/creating-documentation) and [LLM Integration
  Guide](/building-with-codegen/calling-out-to-llms).
</Tip>

### Documentation Coverage

You can analyze and improve documentation coverage across your codebase:

```python
# Count documented vs undocumented functions
total = 0
documented = 0
for function in codebase.functions:
    total += 1
    if function.docstring:
        documented += 1

coverage = (documented / total * 100) if total > 0 else 0
print(f"Documentation coverage: {coverage:.1f}%")
```

<Note>
  Check out the [Documentation Guide](/tutorials/creating-documentation) for
  more advanced coverage analysis and bulk documentation generation.
</Note>


---
title: "External Modules"
sidebarTitle: "External Modules"
icon: "box-archive"
iconType: "solid"
---

Codegen provides a way to handle imports from external packages and modules through the [ExternalModule](/api-reference/core/ExternalModule) class.

```python
# Python examples
import datetime
from requests import get

# TypeScript/JavaScript examples
import React from 'react'
import { useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import axios from 'axios'
```

## What are External Modules?

When writing code, you often import from packages that aren't part of your project - like `datetime` and `requests` in Python, or `react` and `axios` in TypeScript. In Codegen, these are represented as [ExternalModule](/api-reference/core/ExternalModule) instances.

```python
for imp in codebase.imports:
    if isinstance(imp.symbol, ExternalModule):
        print(f"Importing from external package: {imp.resolved_symbol.source}")
```

<Note>
  External modules are read-only - you can analyze them but can't modify their
  implementation. This makes sense since they live in your project's
  dependencies!
</Note>

## Working with External Modules

The most common use case is handling external modules differently from your project's code:

### Identifying Function Calls as External Modules

For [FunctionCall](/api-reference/core/FunctionCall) instances, you can check if the function definition is an [ExternalModule](/api-reference/core/ExternalModule) via the [FunctionCall.function_definition](/api-reference/core/FunctionCall#function-definition) property:

```python
for fcall in file.function_calls:
    definition = fcall.function_definition
    if isinstance(definition, ExternalModule):
        # Skip external functions
        print(f'External function: {definition.name}')
    else:
        # Process local functions...
        print(f'Local function: {definition.name}')
```

### Import Resolution

Similarly, when working with imports, you can determine if they resolve to external modules by checking the [Import.resolved_symbol](/api-reference/core/Import#resolved-symbol) property:

```python
for imp in file.imports:
    resolved = imp.resolved_symbol
    if isinstance(resolved, ExternalModule):
        print(f"Import from external package: from {imp.module} import {imp.name}")
```

<Tip>
  Use `isinstance(symbol, ExternalModule)` to reliably identify external
  modules. This works better than checking names or paths since it handles all
  edge cases.
</Tip>

## Properties and Methods

External modules provide several useful properties:

```python
# Get the module name
module_name = external_module.name  # e.g. "datetime" or "useState"

# Check if it's from node_modules (TypeScript/JavaScript)
if external_module.filepath == "":
    print("This is an external package from node_modules")
```

## Common Patterns

Here are some typical ways you might work with external modules:

### Skip External Processing:

When modifying function calls or imports, skip external modules since they can't be changed:

```python
# Example from a codemod that adds type hints
def add_type_hints(function):
    if isinstance(function.definition, ExternalModule):
        return  # Can't add type hints to external modules like React.FC
    # Add type hints to local functions...
```

### Analyze Dependencies

Track which external packages your code uses:

```python
# Find all external package dependencies
external_deps = set()
for imp in codebase.imports:
    if isinstance(imp.resolved_symbol, ExternalModule):
        external_deps.add(imp.resolved_symbol.source)
        # Will find things like 'react', 'lodash', 'datetime', etc.
```

<Note>
  When working with imports, always handle external modules as a special case.
  This ensures your codemods work correctly with both local and external code.
</Note>


---
title: "Working with Type Annotations"
sidebarTitle: "Type Annotations"
icon: "code"
iconType: "solid"
---

This guide covers the core APIs and patterns for working with type annotations in Codegen.

## Type Resolution

Codegen builds a complete dependency graph of your codebase, connecting functions, classes, imports, and their relationships. This enables powerful type resolution capabilities:

```python
from codegen import Codebase

# Initialize codebase with dependency graph
codebase = Codebase("./")

# Get a function with a type annotation
function = codebase.get_file("path/to/file.py").get_function("my_func")

# Resolve its return type to actual symbols
return_type = function.return_type
resolved_symbols = return_type.resolved_types  # Returns the actual Symbol objects

# For generic types, you can resolve parameters
if hasattr(return_type, "parameters"):
    for param in return_type.parameters:
        resolved_param = param.resolved_types  # Get the actual type parameter symbols

# For assignments, resolve their type
assignment = codebase.get_file("path/to/file.py").get_assignment("my_var")
resolved_type = assignment.type.resolved_types
```

<Tip>
    Type resolution follows imports and handles complex cases like type aliases, forward references, and generic type parameters.
</Tip>

## Core Interfaces

Type annotations in Codegen are built on two key interfaces:

- [Typeable](/api-reference/core/Typeable) - The base interface for any node that can have a type annotation (parameters, variables, functions, etc). Provides `.type` and `.is_typed`.
- [Type](/api-reference/core/Type) - The base class for all type annotations. Provides type resolution and dependency tracking.

Any node that inherits from `Typeable` will have a `.type` property that returns a `Type` object, which can be used to inspect and modify type annotations.

<Tip>Learn more about [inheritable behaviors](/building-with-codegen/inheritable-behaviors) like Typeable here</Tip>

## Core Type APIs

Type annotations can be accessed and modified through several key APIs:

### Function Types

The main APIs for function types are [Function.return_type](/api-reference/python/PyFunction#return-type) and [Function.set_return_type](/api-reference/python/PyFunction#set-return-type):

```python
# Get return type
return_type = function.return_type  # -> TypeAnnotation
print(return_type.source)  # "List[str]"
print(return_type.is_typed)  # True/False

# Set return type
function.set_return_type("List[str]")
function.set_return_type(None)  # Removes type annotation
```

### Parameter Types

Parameters use [Parameter.type](/api-reference/core/Parameter#type) and [Parameter.set_type_annotation](/api-reference/core/Parameter#set-type-annotation):

```python
for param in function.parameters:
    # Get parameter type
    param_type = param.type  # -> TypeAnnotation
    print(param_type.source)  # "int"
    print(param_type.is_typed)  # True/False

    # Set parameter type
    param.set_type("int")
    param.set_type(None)  # Removes type annotation
```

### Variable Types

Variables and attributes use [Assignment.type](/api-reference/core/Assignment#type) and [Assignment.set_type_annotation](/api-reference/core/Assignment#set-type-annotation). This applies to:
- Global variables
- Local variables
- Class attributes (via [Class.attributes](/api-reference/core/Class#attributes))

```python
# For global/local assignments
assignment = file.get_assignment("my_var")
var_type = assignment.type  # -> TypeAnnotation
print(var_type.source)  # "str"

# Set variable type
assignment.set_type("str")
assignment.set_type(None)  # Removes type annotation

# For class attributes
class_def = file.get_class("MyClass")
for attr in class_def.attributes:
    # Each attribute has an assignment property
    attr_type = attr.assignment.type  # -> TypeAnnotation
    print(f"{attr.name}: {attr_type.source}")  # e.g. "x: int"

    # Set attribute type
    attr.assignment.set_type("int")

# You can also access attributes directly by index
first_attr = class_def.attributes[0]
first_attr.assignment.set_type("str")
```

## Working with Complex Types

### Union Types

Union types ([UnionType](/api-reference/core/UnionType)) can be manipulated as collections:

```python
# Get union type
union_type = function.return_type  # -> A | B
print(union_type.symbols)  # ["A", "B"]

# Add/remove options
union_type.append("float")
union_type.remove("None")

# Check contents
if "str" in union_type.options:
    print("String is a possible type")
```
<Tip>Learn more about [working with collections here](/building-with-codegen/collections)</Tip>

### Generic Types

Generic types ([GenericType](/api-reference/core/GenericType)) expose their parameters as collection of [Parameters](/api-reference/core/Parameter):

```python
# Get generic type
generic_type = function.return_type  # -> GenericType
print(generic_type.base)  # "List"
print(generic_type.parameters)  # ["str"]

# Modify parameters
generic_type.parameters.append("int")
generic_type.parameters[0] = "float"

# Create new generic
function.set_return_type("List[str]")
```
<Tip>Learn more about [working with collections here](/building-with-codegen/collections)</Tip>

### Type Resolution

Type resolution uses [`Type.resolved_value`](/api-reference/core/Type#resolved-value) to get the actual symbols that a type refers to:

```python
# Get the actual symbols for a type
type_annotation = function.return_type  # -> Type
resolved_types = type_annotation.resolved_value  # Returns an Expression, likely a Symbol or collection of Symbols

# For generic types, resolve each parameter
if hasattr(type_annotation, "parameters"):
    for param in type_annotation.parameters:
        param_types = param.resolved_value # Get symbols for each parameter

# For union types, resolve each option
if hasattr(type_annotation, "options"):
    for option in type_annotation.options:
        option_types = option.resolved_value # Get symbols for each union option
```


---
title: "Moving Symbols"
sidebarTitle: "Moving Symbols"
icon: "arrows-up-down-left-right"
iconType: "solid"
---

Codegen provides fast, configurable and safe APIs for moving symbols (functions, classes, variables) between files while automatically handling imports and dependencies.

The key API is [`Symbol.move_to_file(...)`](/api-reference/core/Symbol#move-to-file).

## Basic Symbol Movement

Simply call [`Symbol.move_to_file(...)`](/api-reference/core/Symbol#move-to-file) to move a symbol to a new file.

```python
# Manipulation code:
file1 = codebase.get_file("file1.py")
file2 = codebase.get_file("file2.py")

helper_func = file1.get_symbol("helper")

# Ensure the destination file exists
if not file2.exists():
    file2 = codebase.create_file('file2.py')

# Move the symbol
helper_func.move_to_file(file2)
```

<Note>
  By default, this will move any dependencies, including imports, to the new
  file.
</Note>

## Moving Strategies

The [`Symbol.move_to_file(...)`](/api-reference/core/Symbol#move-to-file) method accepts a `strategy` parameter, which can be used to control how imports are updated.

Your options are:

- `"update_all_imports"`: Updates all import statements across the codebase (default)
- `"add_back_edge"`: Adds import and re-export in the original file

`"add_back_edge"` is useful when moving a symbol that is depended on by other symbols in the original file, and will result in smaller diffs.

<Warning>
  `"add_back_edge"` will result in circular dependencies if the symbol has
  non-import dependencies in it's original file.
</Warning>

## Moving Symbols in Bulk

Make sure to call [`Codebase.commit(...)`](/api-reference/core/Codebase#commit) _after_ moving symbols in bulk for performant symbol movement.

```python
# Move all functions with a specific prefix
for file in codebase.files:
    for function in file.functions:
        if function.name.startswith("pylsp_"):
            function.move_to_file(
                shared_file,
                include_dependencies=True,
                strategy="update_all_imports"
            )

# Commit the changes once, at the end
codebase.commit()
```


---
title: "Collections"
sidebarTitle: "Collections"
icon: "layer-group"
iconType: "solid"
---

Codegen enables traversing and manipulating collections through the [List](/api-reference/core/List) and [Dict](/api-reference/core/Dict) classes.

These APIs work consistently across Python and TypeScript while preserving formatting and structure.

## Core Concepts

The [List](/api-reference/core/List) and [Dict](/api-reference/core/Dict) classes provide a consistent interface for working with ordered sequences of elements. Key features include:

- Standard sequence operations (indexing, length, iteration)
- Automatic formatting preservation
- Safe modification operations
- Language-agnostic behavior
- Comment and whitespace preservation

Collections handle:

- Proper indentation
- Delimiters (commas, newlines)
- Multi-line formatting
- Leading/trailing whitespace
- Nested structures

## List Operations

Lists in both Python and TypeScript can be manipulated using the same APIs:

```python
# Basic operations
items_list = file.get_symbol("items").value  # Get list value
first = items_list[0]        # Access elements
length = len(items_list)     # Get length
items_list[0] = "new"       # Modify element
items_list.append("d")      # Add to end
items_list.insert(1, "x")   # Insert at position
del items_list[1]           # Remove element

# Iteration
for item in items_list:
    print(item.source)

# Bulk operations
items_list.clear()          # Remove all elements
```

### Single vs Multi-line Lists

Collections automatically preserve formatting:

```python
# Source code:
items = [a, b, c]
config = [
    "debug",
    "verbose",
    "trace",
]

# Manipulation code:
items_list = file.get_symbol("items").value
items_list.append("d")    # Adds new element

config_list = file.get_symbol("config").value
config_list.append("info")  # Adds with formatting

# Result:
items = [a, b, c, d]
config = [
    "debug",
    "verbose",
    "trace",
    "info",
]
```

## Dictionary Operations

Dictionaries provide a similar consistent interface:

```python
# Basic operations
settings = file.get_symbol("settings").value  # Get dict value
value = settings["key"]     # Get value
settings["key"] = "value"   # Set value
del settings["key"]         # Remove key
has_key = "key" in settings # Check existence

# Iteration
for key in settings:
    print(f"{key}: {settings[key]}")

# Bulk operations
settings.clear()           # Remove all entries
```


---
title: "Traversing the Call Graph"
sidebarTitle: "Call Graph"
icon: "sitemap"
iconType: "solid"
---

Codegen provides powerful capabilities for analyzing and visualizing function call relationships in your codebase. This guide will show you how to traverse the call graph and create visual representations of function call paths.

## Understanding Call Graph Traversal

At the heart of call graph traversal is the [.function_calls](/api-reference/core/Function#function-calls) property, which returns information about all function calls made within a function:

```python
def example_function():
    result = helper_function()
    process_data()
    return result

# Get all calls made by example_function
successors = example_function.function_calls
for successor in successors:
    print(f"Call: {successor.source}")  # The actual function call
    print(f"Called: {successor.function_definition.name}")  # The function being called
```

## Building a Call Graph

Here's how to build a directed graph of function calls using NetworkX:

```python
import networkx as nx
from codegen.sdk.core.interfaces.callable import FunctionCallDefinition
from codegen.sdk.core.function import Function

def create_call_graph(start_func, end_func, max_depth=5):
    G = nx.DiGraph()

    def traverse_calls(parent_func, current_depth):
        if current_depth > max_depth:
            return

        # Determine source node
        if isinstance(parent_func, Function):
            src_call = src_func = parent_func
        else:
            src_func = parent_func.function_definition
            src_call = parent_func

        # Skip external modules
        if isinstance(src_func, ExternalModule):
            return

        # Traverse all function calls
        for call in src_func.function_calls:
            func = call.function_definition

            # Skip recursive calls
            if func.name == src_func.name:
                continue

            # Add nodes and edges
            G.add_node(call)
            G.add_edge(src_call, call)

            # Check if we reached the target
            if func == end_func:
                G.add_edge(call, end_func)
                return

            # Continue traversal
            traverse_calls(call, current_depth + 1)

    # Initialize graph
    G.add_node(start_func, color="blue")  # Start node
    G.add_node(end_func, color="red")     # End node

    # Start traversal
    traverse_calls(start_func, 1)
    return G

# Usage example
start = codebase.get_function("create_skill")
end = codebase.get_function("auto_define_skill_description")
graph = create_call_graph(start, end)
```

## Filtering and Visualization

You can filter the graph to show only relevant paths and visualize the results:

```python
# Find all paths between start and end
all_paths = nx.all_simple_paths(graph, source=start, target=end)

# Create subgraph of only the nodes in these paths
nodes_in_paths = set()
for path in all_paths:
    nodes_in_paths.update(path)
filtered_graph = graph.subgraph(nodes_in_paths)

# Visualize the graph
codebase.visualize(filtered_graph)
```

## Advanced Usage

### Example: Finding Dead Code

You can use call graph analysis to find unused functions:

```python
def find_dead_code(codebase):
    dead_functions = []
    for function in codebase.functions:
        if not any(function.function_calls):
            # No other functions call this one
            dead_functions.append(function)
    return dead_functions
```

### Example: Analyzing Call Chains

Find the longest call chain in your codebase:

```python
def get_max_call_chain(function):
    G = nx.DiGraph()

    def build_graph(func, depth=0):
        if depth > 10:  # Prevent infinite recursion
            return
        for call in func.function_calls:
            called_func = call.function_definition
            G.add_edge(func, called_func)
            build_graph(called_func, depth + 1)

    build_graph(function)
    return nx.dag_longest_path(G)
```

<Note>
The `.function_calls` property is optimized for performance and uses Codegen's internal graph structure to quickly traverse relationships. It's much faster than parsing the code repeatedly.
</Note>

<Warning>
When traversing call graphs, be mindful of:
- Recursive calls that could create infinite loops
- External module calls that might not be resolvable
- Dynamic/runtime function calls that can't be statically analyzed
</Warning>


---
title: "React and JSX"
sidebarTitle: "React and JSX"
icon: "react"
iconType: "brands"
---

GraphSitter exposes several React and JSX-specific APIs for working with modern React codebases.

Key APIs include:

- [Function.is_jsx](/api-reference/typescript/TSFunction#is-jsx) - Check if a function contains JSX elements
- [Class.jsx_elements](/api-reference/typescript/TSClass#jsx-elements) - Get all JSX elements in a class
- [Function.jsx_elements](/api-reference/typescript/TSFunction#jsx-elements) - Get all JSX elements in a function
- [JSXElement](/api-reference/typescript/JSXElement) - Manipulate JSX elements
- [JSXProp](/api-reference/typescript/JSXProp) - Manipulate JSX props

<Tip>
  See [React Modernization](/tutorials/react-modernization) for tutorials and
  applications of the concepts described here
</Tip>

## Detecting React Components with `is_jsx`

Codegen exposes a `is_jsx` property on both classes and functions, which can be used to check if a symbol is a React component.

```python
# Check if a function is a React component
function = file.get_function("MyComponent")
is_component = function.is_jsx  # True for React components

# Check if a class is a React component
class_def = file.get_class("MyClassComponent")
is_component = class_def.is_jsx  # True for React class components
```

## Working with JSX Elements

Given a React component, you can access its JSX elements using the [jsx_elements](/api-reference/typescript/TSFunction#jsx-elements) property.

You can manipulate these elements by using the [JSXElement](/api-reference/typescript/JSXElement) and [JSXProp](/api-reference/typescript/JSXProp) APIs.

```python
# Get all JSX elements in a component
for element in component.jsx_elements:
    # Access element name
    if element.name == "Button":
        # Wrap element in a div
        element.wrap("<div className='wrapper'>", "</div>")

    # Get specific prop
    specific_prop = element.get_prop("className")

    # Iterate over all props
    for prop in element.props:
        if prop.name == "className":
            # Set prop value
            prop.set_value('"my-classname"')

    # Modify element
    element.set_name("NewComponent")
    element.add_prop("newProp", "{value}")

    # Get child JSX elements
    child_elements = element.jsx_elements

    # Wrap element in a JSX expression (preserves whitespace)
    element.wrap("<div className='wrapper'>", "</div>")
```

## Common React Operations

<Tip>See [React Modernization](/tutorials/react-modernization) for more</Tip>

### Refactoring Components into Separate Files

Split React components into individual files:

```python
# Find (named) React components
react_components = [
    func for func in codebase.functions
    if func.is_jsx and func.name is not None
]

# Filter out those that are not the default export
non_default_components = [
    comp for comp in react_components
    if not comp.export or not comp.export.is_default_export()
]

# Move these non-default components to new files
for component in react_components:
    if component != default_component:
        # Create new file
        new_file_path = '/'.join(component.filepath.split('/')[:-1]) + f"{component.name}.tsx"
        new_file = codebase.create_file(new_file_path)

        # Move component and update imports
        component.move_to_file(new_file, strategy="add_back_edge")
```

<Note>
  See [Moving Symbols](/building-with-codegen/moving-symbols) for more details
  on moving symbols between files.
</Note>

### Updating Component Names and Props

Replace components throughout the codebase with prop updates:

```python
# Find target component
new_component = codebase.get_symbol("NewComponent")

for function in codebase.functions:
    if function.is_jsx:
        # Update JSX elements
        for element in function.jsx_elements:
            if element.name == "OldComponent":
                # Update name
                element.set_name("NewComponent")

                # Edit props
                needs_clsx = not file.has_import("clsx")
                for prop in element.props:
                    if prop.name == "className":
                        prop.set_value('clsx("new-classname")')
                        needs_clsx = True
                    elif prop.name == "onClick":
                        prop.set_name('handleClick')

                # Add import if needed
                if needs_clsx:
                    file.add_import_from_import_source("import clsx from 'clsx'")

                # Add import if needed
                if not file.has_import("NewComponent"):
                    file.add_import(new_component)
```


---
title: "Codebase Visualization"
sidebarTitle: "Visualization"
icon: "share-nodes"
iconType: "solid"
---

Codegen provides the ability to create interactive graph visualizations via the [codebase.visualize(...)](/api-reference/core/Codebase#visualize) method.

These visualizations have a number of applications, including:

- Understanding codebase structure
- Monitoring critical code paths
- Analyzing dependencies
- Understanding inheritance hierarchies

This guide provides a basic overview of graph creation and customization. Like the one below which displays the call_graph for the [modal/client.py](https://github.com/modal-labs/modal-client/blob/v0.72.49/modal/client.py) module.

<iframe
  width="100%"
  height="600px"
  scrolling="no"
  src={`https://codegen.sh/embedded/graph?id=299beefe-0207-43b6-bff3-6ca9036f62eb&zoom=0.5`}
  className="rounded-xl "
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>

<Note>
  Codegen visualizations are powered by [NetworkX](https://networkx.org/) and
  rendered using [d3](https://d3js.org/what-is-d3).
</Note>

## Basic Usage

The [Codebase.visualize](/api-reference/core/Codebase#visualize) method operates on a NetworkX [DiGraph](https://networkx.org/documentation/stable/reference/classes/graph.DiGraph.html).

```python
import networkx as nx

# Basic visualization
G = nx.grid_2d_graph(5, 5)
# Or start with an empty graph
# G = nx.DiGraph()
codebase.visualize(G)

```

It is up to the developer to add nodes and edges to the graph.

### Adding Nodes and Edges

When adding nodes to your graph, you can either add the symbol directly or just its name:

```python
import networkx as nx
G = nx.DiGraph()
function = codebase.get_function("my_function")

# Add the function object directly - enables source code preview
graph.add_node(function)  # Will show function's source code on click

# Add just the name - no extra features
graph.add_node(function.name)  # Will only show the name
```

<Tip>
  Adding symbols to the graph directly (as opposed to adding by name) enables
  automatic type information, code preview on hover, and more.
</Tip>

## Common Visualization Types

### Call Graphs

Visualize how functions call each other and trace execution paths:

```python
def create_call_graph(entry_point: Function):
    graph = nx.DiGraph()

    def add_calls(func):
        for call in func.call_sites:
            called_func = call.resolved_symbol
            if called_func:
                # Add function objects for rich previews
                graph.add_node(func)
                graph.add_node(called_func)
                graph.add_edge(func, called_func)
                add_calls(called_func)

    add_calls(entry_point)
    return graph

# Visualize API endpoint call graph
endpoint = codebase.get_function("handle_request")
call_graph = create_call_graph(endpoint)
codebase.visualize(call_graph, root=endpoint)
```

<Tip>
  Learn more about [traversing the call graph
  here](/building-with-codegen/traversing-the-call-graph).
</Tip>

### React Component Trees

Visualize the hierarchy of React components:

```python
def create_component_tree(root_component: Class):
    graph = nx.DiGraph()

    def add_children(component):
        for usage in component.usages:
            if isinstance(usage.parent, Class) and "Component" in usage.parent.bases:
                graph.add_edge(component.name, usage.parent.name)
                add_children(usage.parent)

    add_children(root_component)
    return graph

# Visualize component hierarchy
app = codebase.get_class("App")
component_tree = create_component_tree(app)
codebase.visualize(component_tree, root=app)
```

### Inheritance Graphs

Visualize class inheritance relationships:

```python
import networkx as nx

G = nx.DiGraph()
base = codebase.get_class("BaseModel")

def add_subclasses(cls):
    for subclass in cls.subclasses:
        G.add_edge(cls, subclass)
        add_subclasses(subclass)

add_subclasses(base)

codebase.visualize(G, root=base)
```

### Module Dependencies

Visualize dependencies between modules:

```python
def create_module_graph(start_file: File):
    G = nx.DiGraph()

    def add_imports(file):
        for imp in file.imports:
            if imp.resolved_symbol and imp.resolved_symbol.file:
                graph.add_edge(file, imp.resolved_symbol.file)
                add_imports(imp.resolved_symbol.file)

    add_imports(start_file)
    return graph

# Visualize module dependencies
main = codebase.get_file("main.py")
module_graph = create_module_graph(main)
codebase.visualize(module_graph, root=main)
```

### Function Modularity

Visualize function groupings by modularity:

```python
def create_modularity_graph(functions: list[Function]):
    graph = nx.Graph()

    # Group functions by shared dependencies
    for func in functions:
        for dep in func.dependencies:
            if isinstance(dep, Function):
                weight = len(set(func.dependencies) & set(dep.dependencies))
                if weight > 0:
                    graph.add_edge(func.name, dep.name, weight=weight)

    return graph

# Visualize function modularity
funcs = codebase.functions
modularity_graph = create_modularity_graph(funcs)
codebase.visualize(modularity_graph)
```

## Customizing Visualizations

You can customize your visualizations using NetworkX's attributes while still preserving the smart node features:

```python
def create_custom_graph(codebase):
    graph = nx.DiGraph()

    # Add nodes with custom attributes while preserving source preview
    for func in codebase.functions:
        graph.add_node(func,
            color='red' if func.is_public else 'blue',
            shape='box' if func.is_async else 'oval'
        )

    # Add edges between actual function objects
    for func in codebase.functions:
        for call in func.call_sites:
            if call.resolved_symbol:
                graph.add_edge(func, call.resolved_symbol,
                    style='dashed' if call.is_conditional else 'solid',
                    weight=call.count
                )

    return graph
```

## Best Practices

1. **Use Symbol Objects for Rich Features**

   ```python
   # Better: Add symbol objects for rich previews
   # This will include source code previews, syntax highlighting, type information, etc.
   for func in api_funcs:
       graph.add_node(func)

   # Basic: Just names, no extra features
   for func in api_funcs:
       graph.add_node(func.name)
   ```

2. **Focus on Relevant Subgraphs**

   ```python
   # Better: Visualize specific subsystem
   api_funcs = [f for f in codebase.functions if "api" in f.filepath]
   api_graph = create_call_graph(api_funcs)
   codebase.visualize(api_graph)

   # Avoid: Visualizing entire codebase
   full_graph = create_call_graph(codebase.functions)  # Too complex
   ```

3. **Use Meaningful Layouts**

   ```python
   # Group related nodes together
   graph.add_node(controller_class, cluster="api")
   graph.add_node(service_class, cluster="db")
   ```

4. **Add Visual Hints**
   ```python
   # Color code by type while preserving rich previews
   for node in codebase.functions:
       if "Controller" in node.name:
           graph.add_node(node, color="red")
       elif "Service" in node.name:
           graph.add_node(node, color="blue")
   ```

## Limitations

- Large graphs may become difficult to read
- Complex relationships might need multiple views
- Some graph layouts may take time to compute
- Preview features only work when adding symbol objects directly



---
title: "Calling Out to LLMs"
sidebarTitle: "LLM Integration"
icon: "brain"
iconType: "solid"
---

Codegen natively integrates with LLMs via the [codebase.ai(...)](../api-reference/core/Codebase#ai) method, which lets you use large language models (LLMs) to help generate, modify, and analyze code.

## Configuration

Before using AI capabilities, you need to provide an OpenAI API key via [codebase.set_ai_key(...)](../api-reference/core/Codebase#set-ai-key):

```python
# Set your OpenAI API key
codebase.set_ai_key("your-openai-api-key")
```

## Calling Codebase.ai(...)

The [Codebase.ai(...)](../api-reference/core/Codebase#ai) method takes three key arguments:

```python
result = codebase.ai(
    prompt="Your instruction to the AI",
    target=symbol_to_modify,  # Optional: The code being operated on
    context=additional_info   # Optional: Extra context from static analysis
)
```

- **prompt**: Clear instruction for what you want the AI to do
- **target**: The symbol (function, class, etc.) being operated on - its source code will be provided to the AI
- **context**: Additional information you want to provide to the AI, which you can gather using GraphSitter's analysis tools

<Note>
  Codegen does not automatically provide any context to the LLM by default. It
  does not "understand" your codebase, only the context you provide.
</Note>

The context parameter can include:

- A single symbol (its source code will be provided)
- A list of related symbols
- A dictionary mapping descriptions to symbols/values
- Nested combinations of the above

### How Context Works

The AI doesn't automatically know about your codebase. Instead, you can provide relevant context by:

1. Using GraphSitter's static analysis to gather information:

```python
function = codebase.get_function("process_data")
context = {
    "call_sites": function.call_sites,      # Where the function is called
    "dependencies": function.dependencies,   # What the function depends on
    "parent": function.parent,              # Class/module containing the function
    "docstring": function.docstring,        # Existing documentation
}
```

2. Passing this information to the AI:

```python
result = codebase.ai(
    "Improve this function's implementation",
    target=function,
    context=context  # AI will see the gathered information
)
```

## Common Use Cases

### Code Generation

Generate new code or refactor existing code:

```python
# Break up a large function
function = codebase.get_function("large_function")
new_code = codebase.ai(
    "Break this function into smaller, more focused functions",
    target=function
)
function.edit(new_code)

# Generate a test
my_function = codebase.get_function("my_function")
test_code = codebase.ai(
    f"Write a test for the function {my_function.name}",
    target=my_function
)
my_function.insert_after(test_code)
```

### Documentation

Generate and format documentation:

```python
# Generate docstrings for a class
class_def = codebase.get_class("MyClass")
for method in class_def.methods:
    docstring = codebase.ai(
        "Generate a docstring describing this method",
        target=method,
        context={
            "class": class_def,
            "style": "Google docstring format"
        }
    )
    method.set_docstring(docstring)
```

### Code Analysis and Improvement

Use AI to analyze and improve code:

```python
# Improve function names
for function in codebase.functions:
    if codebase.ai(
        "Does this function name clearly describe its purpose? Answer yes/no",
        target=function
    ).lower() == "no":
        new_name = codebase.ai(
            "Suggest a better name for this function",
            target=function,
            context={"call_sites": function.call_sites}
        )
        function.rename(new_name)
```

### Contextual Modifications

Make changes with full context awareness:

```python
# Refactor a class method
method = codebase.get_class("MyClass").get_method("target_method")
new_impl = codebase.ai(
    "Refactor this method to be more efficient",
    target=method,
    context={
        "parent_class": method.parent,
        "call_sites": method.call_sites,
        "dependencies": method.dependencies
    }
)
method.edit(new_impl)
```

## Best Practices

1. **Provide Relevant Context**

   ```python
   # Good: Providing specific, relevant context
   summary = codebase.ai(
       "Generate a summary of this method's purpose",
       target=method,
       context={
           "class": method.parent,              # Class containing the method
           "usages": list(method.usages),       # How the method is used
           "dependencies": method.dependencies,  # What the method depends on
           "style": "concise"
       }
   )

   # Bad: Missing context that could help the AI
   summary = codebase.ai(
       "Generate a summary",
       target=method  # AI only sees the method's code
   )
   ```

2. **Gather Comprehensive Context**

   ```python
   # Gather relevant information before AI call
   def get_method_context(method):
       return {
           "class": method.parent,
           "call_sites": list(method.call_sites),
           "dependencies": list(method.dependencies),
           "related_methods": [m for m in method.parent.methods
                             if m.name != method.name]
       }

   # Use gathered context in AI call
   new_impl = codebase.ai(
       "Refactor this method to be more efficient",
       target=method,
       context=get_method_context(method)
   )
   ```

3. **Handle AI Limits**

   ```python
   # Set custom AI request limits for large operations
   codebase.set_session_options(max_ai_requests=200)
   ```

4. **Review Generated Code**
   ```python
   # Generate and review before applying
   new_code = codebase.ai(
       "Optimize this function",
       target=function
   )
   print("Review generated code:")
   print(new_code)
   if input("Apply changes? (y/n): ").lower() == 'y':
       function.edit(new_code)
   ```

## Limitations and Safety

- The AI doesn't automatically know about your codebase - you must provide relevant context
- AI-generated code should always be reviewed
- Default limit of 150 AI requests per codemod execution
  - Use [set_session_options(...)](../api-reference/core/Codebase#set-session-options) to adjust limits:
  ```python
  codebase.set_session_options(max_ai_requests=200)
  ```
<Note>
  You can also use `codebase.set_session_options` to increase the execution time and the number of operations allowed in a session. This is useful for handling larger tasks or more complex operations that require additional resources. Adjust the `max_seconds` and `max_transactions` parameters to suit your needs:
  ```python
  codebase.set_session_options(max_seconds=300, max_transactions=500)
  ```
</Note>

---
title: "Reducing Conditions"
sidebarTitle: "Reducing Conditions"
icon: "code-branch"
iconType: "solid"
---

Codegen provides powerful APIs for reducing conditional logic to constant values. This is particularly useful for removing feature flags, cleaning up dead code paths, and simplifying conditional logic.

## Overview

The `reduce_condition()` method is available on various conditional constructs:

- [If/else statements](/api-reference/core/IfBlockStatement#reduce-condition)
- [Ternary expressions](/api-reference/core/TernaryExpression#reduce-condition)
- [Binary expressions](/api-reference/core/BinaryExpression#reduce-condition)
- [Function calls](/api-reference/core/FunctionCall#reduce-condition)

When you reduce a condition to `True` or `False`, Codegen automatically:

1. Evaluates which code path(s) to keep
2. Removes unnecessary branches
3. Preserves proper indentation and formatting

### Motivating Example

For example, consider the following code:

```python
flag = get_feature_flag('MY_FEATURE')
if flag:
    print('MY_FEATURE: ON')
else:
    print('MY_FEATURE: OFF')
```

`.reduce_condition` allows you to deterministically reduce this code to the following:

```python
print('MY_FEATURE: ON')
```

This is useful when a feature flag is fully "rolled out".

## Implementations

### [IfBlockStatements](/api-reference/core/IfBlockStatement#reduce-condition)

You can reduce if/else statements to either their "true" or "false" branch.

For example, in the code snippet above:

```python
# Grab if statement
if_block = file.code_block.statements[1]

# Reduce to True branch
if_block.reduce_condition(True)
```

This will remove the `else` branch and keep the `print` statement, like so:

```python
flag = get_feature_flag('MY_FEATURE')
print('MY_FEATURE: ON')
```

### Handling Elif Chains

Codegen intelligently handles elif chains when reducing conditions:

```python
# Original code
if condition_a:
    print("A")
elif condition_b:
    print("B")
else:
    print("C")

# Reduce first condition to False
if_block.reduce_condition(False)
# Result:
if condition_b:
    print("B")
else:
    print("C")

# Reduce elif condition to True
elif_block.reduce_condition(True)
# Result:
print("B")
```

## Ternary Expressions

Ternary expressions (conditional expressions) can also be reduced:

```python
# Original code
result = 'valueA' if condition else 'valueB'

# Reduce to True
ternary_expr.reduce_condition(True)
# Result:
result = 'valueA'

# Reduce to False
ternary_expr.reduce_condition(False)
# Result:
result = 'valueB'
```

### Nested Ternaries

Codegen handles nested ternary expressions correctly:

```python
# Original code
result = 'A' if a else 'B' if b else 'C'

# Reduce outer condition to False
outer_ternary.reduce_condition(False)
# Result:
result = 'B' if b else 'C'

# Then reduce inner condition to True
inner_ternary.reduce_condition(True)
# Result:
result = 'B'
```

## Binary Operations

Binary operations (and/or) can be reduced to simplify logic:

```python
# Original code
result = (x or y) and b

# Reduce x to True
x_assign.reduce_condition(True)
# Result:
result = b

# Reduce y to False
y_assign.reduce_condition(False)
# Result:
result = x and b
```

## Function Calls

[Function calls](/api-reference/core/FunctionCall#reduce-condition) can also be reduced, which is particularly useful when dealing with hooks or utility functions that return booleans:

```typescript
// Original code
const isEnabled = useFeatureFlag("my_feature");
return isEnabled ? <NewFeature /> : <OldFeature />;

// After reducing useFeatureFlag to True
return <NewFeature />;
```

### Feature Flag Hooks

A common use case is reducing feature flag hooks to constants. Consider the following code:

```typescript
// Original code
function MyComponent() {
  const showNewUI = useFeatureFlag("new_ui_enabled");

  if (showNewUI) {
    return <NewUI />;
  }
  return <OldUI />;
}
```

We can reduce the `useFeatureFlag` hook to a constant value like so, with [FunctionCall.reduce_condition](/api-reference/core/FunctionCall#reduce-condition):

```python
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages():
    if isinstance(usage.match, FunctionCall):
        fcall = usage.match
        if fcall.args[0].value.content == 'new_ui_enabled':
            # This will automatically reduce any conditions using the flag
            fcall.reduce_condition(True)
```

This produces the following code:

```typescript
function MyComponent() {
  return <NewUI />;
}
```

### Comprehensive Example

Here's a complete example of removing a feature flag from both configuration and usage:

```python
feature_flag_name = "new_ui_enabled"
target_value = True

# 1. Remove from config
config_file = codebase.get_file("src/featureFlags/config.ts")
feature_flag_config = config_file.get_symbol("FEATURE_FLAG_CONFIG").value
feature_flag_config.pop(feature_flag_name)

# 2. Find and reduce all usages
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages():
    fcall = usage.match
    if isinstance(fcall, FunctionCall):
        # Check if this usage is for our target flag
        first_arg = fcall.args[0].value
        if isinstance(first_arg, String) and first_arg.content == feature_flag_name:
            print(f'Reducing in: {fcall.parent_symbol.name}')
            # This will automatically reduce:
            # - Ternary expressions using the flag
            # - If statements checking the flag
            # - Binary operations with the flag
            fcall.reduce_condition(target_value)

# Commit changes to disk
codebase.commit()
```

This example:

1. Removes the feature flag from configuration
2. Finds all usages of the feature flag hook
3. Reduces each usage to a constant value
4. Automatically handles all conditional constructs using the flag

<Note>
  When reducing a function call, Codegen automatically handles all dependent
  conditions. This includes: - [If/else
  statements](/api-reference/core/IfBlockStatement#reduce-condition) - [Ternary
  expressions](/api-reference/core/TernaryExpression#reduce-condition) - [Binary
  operations](/api-reference/core/BinaryExpression#reduce-condition)
</Note>

## TypeScript and JSX Support

Condition reduction works with TypeScript and JSX, including conditional rendering:

```typescript
// Original JSX
const MyComponent: React.FC = () => {
  let isVisible = true;
  return (
    <div>
      {isVisible && <span>Visible</span>}
      {!isVisible && <span>Hidden</span>}
    </div>
  );
};

// After reducing isVisible to True
const MyComponent: React.FC = () => {
  return (
    <div>
      <span>Visible</span>
    </div>
  );
};
```

<Tip>
  Condition reduction is particularly useful for cleaning up feature flags in
  React components, where conditional rendering is common.
</Tip>


---
title: "Learn by Example"
sidebarTitle: "At a Glance"
icon: "graduation-cap"
iconType: "solid"
---

Explore our tutorials to learn how to use Codegen for various code transformation tasks.

## Featured Tutorials

<CardGroup cols={2}>
  <Card
    title="Visualize Your Codebase"
    icon="diagram-project"
    href="/tutorials/codebase-visualization"
  >
    Generate interactive visualizations of your codebase's structure, dependencies, and relationships.
  </Card>
  <Card
    title="Mine Training Data"
    icon="robot"
    href="/tutorials/training-data"
  >
    Create high-quality training data for LLM pre-training similar to word2vec or node2vec
  </Card>
  <Card
    title="Manage Feature Flags"
    icon="flag"
    href="/tutorials/manage-feature-flags"
  >
    Add, remove, and update feature flags across your application.
  </Card>
  <Card
    title="Delete Dead Code"
    icon="broom"
    href="/tutorials/deleting-dead-code"
  >
    Remove unused imports, functions, and variables with confidence.
  </Card>
</CardGroup>

## API Migrations

<CardGroup cols={2}>
  <Card
    title="API Migration Guide"
    icon="arrow-right-arrow-left"
    href="/tutorials/migrating-apis"
  >
    Update API calls, handle breaking changes, and manage bulk updates across your codebase.
  </Card>
  <Card
    title="SQLAlchemy 1.4 to 2.0"
    icon="layer-group"
    href="/tutorials/sqlalchemy-1.4-to-2.0"
  >
    Update SQLAlchemy code to use the new 2.0-style query interface and patterns.
  </Card>
  <Card
    title="Flask to FastAPI"
    icon="bolt"
    href="/tutorials/flask-to-fastapi"
  >
    Convert Flask applications to FastAPI, updating routes and dependencies.
  </Card>
  <Card
    title="Python 2 to 3"
    icon="snake"
    href="/tutorials/python2-to-python3"
  >
    Migrate Python 2 code to Python 3, updating syntax and modernizing APIs.
  </Card>
</CardGroup>

## Code Organization

<CardGroup cols={2}>
  <Card
    title="Organize Your Codebase"
    icon="folder-tree"
    href="/tutorials/organize-your-codebase"
  >
    Restructure files, enforce naming conventions, and improve project layout.
  </Card>
  <Card
    title="Improve Modularity"
    icon="cubes"
    href="/tutorials/modularity"
  >
    Split large files, extract shared logic, and manage dependencies.
  </Card>
  <Card
    title="Manage TypeScript Exports"
    icon="file-export"
    href="/tutorials/managing-typescript-exports"
  >
    Organize and optimize TypeScript module exports.
  </Card>
  <Card
    title="Convert Default Exports"
    icon="file-import"
    href="/tutorials/converting-default-exports"
  >
    Convert between default and named exports in TypeScript/JavaScript.
  </Card>
</CardGroup>

## Testing & Types

<CardGroup cols={2}>
  <Card
    title="unittest to pytest"
    icon="vial"
    href="/tutorials/unittest-to-pytest"
  >
    Convert unittest test suites to pytest's modern testing style.
  </Card>
  <Card
    title="Increase Type Coverage"
    icon="shield-check"
    href="/tutorials/increase-type-coverage"
  >
    Add TypeScript types, infer types from usage, and improve type safety.
  </Card>
</CardGroup>

## Documentation & AI

<CardGroup cols={2}>
  <Card
    title="Create Documentation"
    icon="book"
    href="/tutorials/creating-documentation"
  >
    Generate JSDoc comments, README files, and API documentation.
  </Card>
  <Card
    title="Prepare for AI"
    icon="robot"
    href="/tutorials/preparing-your-codebase-for-ai"
  >
    Generate system prompts, create hierarchical documentation, and optimize for AI assistance.
  </Card>
</CardGroup>

<Note>
  Each tutorial includes practical examples, code snippets, and best practices.
  Follow them in order or jump to the ones most relevant to your needs.
</Note>


---
title: "Migrating APIs"
sidebarTitle: "API Migrations"
icon: "webhook"
iconType: "solid"
---

API migrations are a common task in large codebases. Whether you're updating a deprecated function, changing parameter names, or modifying return types, Codegen makes it easy to update all call sites consistently.

## Common Migration Scenarios

### Renaming Parameters

When updating parameter names across an API, you need to update both the function definition and all call sites:

```python
# Find the API function to update
api_function = codebase.get_function("process_data")

# Update the parameter name
old_param = api_function.get_parameter("input")
old_param.rename("data")

# All call sites are automatically updated:
# process_data(input="test") -> process_data(data="test")
```

<Info>See [dependencies and usages](/building-with-codegen/dependencies-and-usages) for more on updating parameter names and types.</Info>

### Adding Required Parameters

When adding a new required parameter to an API:

```python
# Find all call sites before modifying the function
call_sites = list(api_function.call_sites)

# Add the new parameter
api_function.add_parameter("timeout: int")

# Update all existing call sites to include the new parameter
for call in call_sites:
    call.add_argument("timeout=30")  # Add with a default value
```

<Info>See [function calls and callsites](/building-with-codegen/function-calls-and-callsites) for more on handling call sites.</Info>

### Changing Parameter Types

When updating parameter types:

```python
# Update the parameter type
param = api_function.get_parameter("user_id")
param.type = "UUID"  # Change from string to UUID

# Find all call sites that need type conversion
for call in api_function.call_sites:
    arg = call.get_arg_by_parameter_name("user_id")
    if arg:
        # Convert string to UUID
        arg.edit(f"UUID({arg.value})")
```

<Info>See [working with type annotations](/building-with-codegen/type-annotations) for more on changing parameter types.</Info>

### Deprecating Functions

When deprecating an old API in favor of a new one:

```python
old_api = codebase.get_function("old_process_data")
new_api = codebase.get_function("new_process_data")

# Add deprecation warning
old_api.add_decorator('@deprecated("Use new_process_data instead")')

# Update all call sites to use the new API
for call in old_api.call_sites:
    # Map old arguments to new parameter names
    args = [
        f"data={call.get_arg_by_parameter_name('input').value}",
        f"timeout={call.get_arg_by_parameter_name('wait').value}"
    ]

    # Replace the old call with the new API
    call.replace(f"new_process_data({', '.join(args)})")
```

## Bulk Updates to Method Chains

When updating chained method calls, like database queries or builder patterns:

```python
# Find all query chains ending with .execute()
for execute_call in codebase.function_calls:
    if execute_call.name != "execute":
        continue

    # Get the full chain
    chain = execute_call.call_chain

    # Example: Add .timeout() before .execute()
    if "timeout" not in {call.name for call in chain}:
        execute_call.insert_before("timeout(30)")
```

## Handling Breaking Changes

When making breaking changes to an API, it's important to:
1. Identify all affected call sites
2. Make changes consistently
3. Update related documentation
4. Consider backward compatibility

Here's a comprehensive example:

```python
def migrate_api_v1_to_v2(codebase):
    old_api = codebase.get_function("create_user_v1")

    # Document all existing call patterns
    call_patterns = {}
    for call in old_api.call_sites:
        args = [arg.source for arg in call.args]
        pattern = ", ".join(args)
        call_patterns[pattern] = call_patterns.get(pattern, 0) + 1

    print("Found call patterns:")
    for pattern, count in call_patterns.items():
        print(f"  {pattern}: {count} occurrences")

    # Create new API version
    new_api = old_api.copy()
    new_api.rename("create_user_v2")

    # Update parameter types
    new_api.get_parameter("email").type = "EmailStr"
    new_api.get_parameter("role").type = "UserRole"

    # Add new required parameters
    new_api.add_parameter("tenant_id: UUID")

    # Update all call sites
    for call in old_api.call_sites:
        # Get current arguments
        email_arg = call.get_arg_by_parameter_name("email")
        role_arg = call.get_arg_by_parameter_name("role")

        # Build new argument list with type conversions
        new_args = [
            f"email=EmailStr({email_arg.value})",
            f"role=UserRole({role_arg.value})",
            "tenant_id=get_current_tenant_id()"
        ]

        # Replace old call with new version
        call.replace(f"create_user_v2({', '.join(new_args)})")

    # Add deprecation notice to old version
    old_api.add_decorator('@deprecated("Use create_user_v2 instead")')

# Run the migration
migrate_api_v1_to_v2(codebase)
```

## Best Practices

1. **Analyze First**: Before making changes, analyze all call sites to understand usage patterns
   ```python
   # Document current usage
   for call in api.call_sites:
       print(f"Called from: {call.parent_function.name}")
       print(f"With args: {[arg.source for arg in call.args]}")
   ```

2. **Make Atomic Changes**: Update one aspect at a time
   ```python
   # First update parameter names
   param.rename("new_name")

   # Then update types
   param.type = "new_type"

   # Finally update call sites
   for call in api.call_sites:
       # ... update calls
   ```

3. **Maintain Backwards Compatibility**:
   ```python
   # Add new parameter with default
   api.add_parameter("new_param: str = None")

   # Later make it required
   api.get_parameter("new_param").remove_default()
   ```

4. **Document Changes**:
   ```python
   # Add clear deprecation messages
   old_api.add_decorator(\'\'\\@deprecated(
       "Use new_api() instead. Migration guide: docs/migrations/v2.md"
   )\'\'\\)
   ```

<Note>
Remember to test thoroughly after making bulk changes to APIs. While Codegen ensures syntactic correctness, you'll want to verify the semantic correctness of the changes.
</Note>

---
title: "Codebase Visualization"
sidebarTitle: "Visualization"
description: "This guide will show you how to create codebase visualizations using [codegen](/introduction/overview)."
icon: "share-nodes"
iconType: "solid"
---

<Frame caption="Blast radius visualization of the `export_asset` function. Click and drag to pan, scroll to zoom.">
  <iframe
  width="100%"
  height="600px"
  scrolling="no"
  loading="lazy"
  src={`https://codegen.sh/embedded/graph?id=347d349e-263b-481a-9601-1cd205b332b9&zoom=1&targetNodeName=export_asset`}
  className="rounded-xl "
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>
</Frame>

## Overview

To demonstrate the visualization capabilities of the codegen we will generate three different visualizations of PostHog's open source [repository](https://github.com/PostHog/posthog).
 - [Call Trace Visualization](#call-trace-visualization)
 - [Function Dependency Graph](#function-dependency-graph)
 - [Blast Radius Visualization](#blast-radius-visualization)


## Call Trace Visualization

Visualizing the call trace of a function is a great way to understand the flow of a function and for debugging. In this tutorial we will create a call trace visualization of the `patch` method of the `SharingConfigurationViewSet` class. View the source code [here](https://github.com/PostHog/posthog/blob/c2986d9ac7502aa107a4afbe31b3633848be6582/posthog/api/sharing.py#L163).


### Basic Setup
First, we'll set up our codebase, graph and configure some basic parameters:

```python
import networkx as nx
from codegen import Codebase

# Initialize codebase
codebase = Codebase("path/to/posthog/")

# Create a directed graph for representing call relationships
G = nx.DiGraph()

# Configuration flags
IGNORE_EXTERNAL_MODULE_CALLS = True  # Skip calls to external modules
IGNORE_CLASS_CALLS = False           # Include class definition calls
MAX_DEPTH = 10

COLOR_PALETTE = {
    "StartFunction": "#9cdcfe",     # Light blue - Start Function
    "PyFunction": "#a277ff",        # Soft purple/periwinkle - PyFunction
    "PyClass": "#ffca85",           # Warm peach/orange - PyClass
    "ExternalModule": "#f694ff"     # Bright magenta/pink - ExternalModule
}
```

### Building the Visualization
We'll create a function that will recursively traverse the call trace of a function and add nodes and edges to the graph:

```python
def create_downstream_call_trace(src_func: Function, depth: int = 0):
    """Creates call graph by recursively traversing function calls

    Args:
        src_func (Function): Starting function for call graph
        depth (int): Current recursion depth
    """
    # Prevent infinite recursion
    if MAX_DEPTH <= depth:
        return

    # External modules are not functions
    if isinstance(src_func, ExternalModule):
        return

    # Process each function call
    for call in src_func.function_calls:
        # Skip self-recursive calls
        if call.name == src_func.name:
            continue

        # Get called function definition
        func = call.function_definition
        if not func:
            continue

        # Apply configured filters
        if isinstance(func, ExternalModule) and IGNORE_EXTERNAL_MODULE_CALLS:
            continue
        if isinstance(func, Class) and IGNORE_CLASS_CALLS:
            continue

        # Generate display name (include class for methods)
        if isinstance(func, Class) or isinstance(func, ExternalModule):
            func_name = func.name
        elif isinstance(func, Function):
            func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name

        # Add node and edge with metadata
        G.add_node(func, name=func_name,
                  color=COLOR_PALETTE.get(func.__class__.__name__))
        G.add_edge(src_func, func, **generate_edge_meta(call))

        # Recurse for regular functions
        if isinstance(func, Function):
            create_downstream_call_trace(func, depth + 1)
```

### Adding Edge Metadata
We can enrich our edges with metadata about the function calls:

```python
def generate_edge_meta(call: FunctionCall) -> dict:
    """Generate metadata for call graph edges

    Args:
        call (FunctionCall): Function call information

    Returns:
        dict: Edge metadata including name and location
    """
    return {
        "name": call.name,
        "file_path": call.filepath,
        "start_point": call.start_point,
        "end_point": call.end_point,
        "symbol_name": "FunctionCall"
    }
```
### Visualizing the Graph
Finally, we can visualize our call graph starting from a specific function:
```python
# Get target function to analyze
target_class = codebase.get_class('SharingConfigurationViewSet')
target_method = target_class.get_method('patch')

# Add root node
G.add_node(target_method,
           name=f"{target_class.name}.{target_method.name}",
           color=COLOR_PALETTE["StartFunction"])

# Build the call graph
create_downstream_call_trace(target_method)

# Render the visualization
codebase.visualize(G)
```


### Take a look
<iframe
  width="100%"
  height="600px"
  scrolling="no"
  loading="lazy"
  src={`https://codegen.sh/embedded/graph?id=6a34b45d-c8ad-422e-95a8-46d4dc3ce2b0&zoom=1&targetNodeName=SharingConfigurationViewSet.patch`}
  className="rounded-xl "
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>
<Info>
View on [codegen.sh](https://www.codegen.sh/codemod/6a34b45d-c8ad-422e-95a8-46d4dc3ce2b0/public/diff)
</Info>

### Common Use Cases
The call graph visualization is particularly useful for:
 - Understanding complex codebases
 - Planning refactoring efforts
 - Identifying tightly coupled components
 - Analyzing critical paths
 - Documenting system architecture

## Function Dependency Graph

Understanding symbol dependencies is crucial for maintaining and refactoring code. This tutorial will show you how to create visual dependency graphs using Codegen and NetworkX. We will be creating a dependency graph of the `get_query_runner` function. View the source code [here](https://github.com/PostHog/posthog/blob/c2986d9ac7502aa107a4afbe31b3633848be6582/posthog/hogql_queries/query_runner.py#L152).

### Basic Setup
<Info>
We'll use the same basic setup as the [Call Trace Visualization](/tutorials/codebase-visualization#call-trace-visualization) tutorial.
</Info>

### Building the Dependency Graph
The core function for building our dependency graph:
```python
def create_dependencies_visualization(symbol: Symbol, depth: int = 0):
    """Creates visualization of symbol dependencies

    Args:
        symbol (Symbol): Starting symbol to analyze
        depth (int): Current recursion depth
    """
    # Prevent excessive recursion
    if depth >= MAX_DEPTH:
        return

    # Process each dependency
    for dep in symbol.dependencies:
        dep_symbol = None

        # Handle different dependency types
        if isinstance(dep, Symbol):
            # Direct symbol reference
            dep_symbol = dep
        elif isinstance(dep, Import):
            # Import statement - get resolved symbol
            dep_symbol = dep.resolved_symbol if dep.resolved_symbol else None

        if dep_symbol:
            # Add node with appropriate styling
            G.add_node(dep_symbol,
                      color=COLOR_PALETTE.get(dep_symbol.__class__.__name__,
                                            "#f694ff"))

            # Add dependency relationship
            G.add_edge(symbol, dep_symbol)

            # Recurse unless it's a class (avoid complexity)
            if not isinstance(dep_symbol, PyClass):
                create_dependencies_visualization(dep_symbol, depth + 1)
```

### Visualizing the Graph
Finally, we can visualize our dependency graph starting from a specific symbol:
```python
# Get target symbol
target_func = codebase.get_function("get_query_runner")

# Add root node
G.add_node(target_func, color=COLOR_PALETTE["StartFunction"])

# Generate dependency graph
create_dependencies_visualization(target_func)

# Render visualization
codebase.visualize(G)
```

### Take a look
<iframe
  width="100%"
  height="600px"
  scrolling="no"
  loading="lazy"
  src={`https://codegen.sh/embedded/graph?id=39a36f0c-9d35-4666-9db7-12ae7c28fc17&zoom=0.8&targetNodeName=get_query_runner`}
  className="rounded-xl "
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>
<Info>
View on [codegen.sh](https://www.codegen.sh/codemod/39a36f0c-9d35-4666-9db7-12ae7c28fc17/public/diff)
</Info>

## Blast Radius visualization

Understanding the impact of code changes is crucial for safe refactoring. A blast radius visualization shows how changes to one function might affect other parts of the codebase by tracing usage relationships. In this tutorial we will create a blast radius visualization of the `export_asset` function. View the source code [here](https://github.com/PostHog/posthog/blob/c2986d9ac7502aa107a4afbe31b3633848be6582/posthog/tasks/exporter.py#L57).

### Basic Setup
<Info>
We'll use the same basic setup as the [Call Trace Visualization](/tutorials/codebase-visualization#call-trace-visualization) tutorial.
</Info>

### Helper Functions
We'll create some utility functions to help build our visualization:
```python
# List of HTTP methods to highlight
HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]

def generate_edge_meta(usage: Usage) -> dict:
    """Generate metadata for graph edges

    Args:
        usage (Usage): Usage relationship information

    Returns:
        dict: Edge metadata including name and location
    """
    return {
        "name": usage.match.source,
        "file_path": usage.match.filepath,
        "start_point": usage.match.start_point,
        "end_point": usage.match.end_point,
        "symbol_name": usage.match.__class__.__name__
    }

def is_http_method(symbol: PySymbol) -> bool:
    """Check if a symbol is an HTTP endpoint method

    Args:
        symbol (PySymbol): Symbol to check

    Returns:
        bool: True if symbol is an HTTP method
    """
    if isinstance(symbol, PyFunction) and symbol.is_method:
        return symbol.name in HTTP_METHODS
    return False
```

### Building the Blast Radius Visualization
The main function for creating our blast radius visualization:
```python
def create_blast_radius_visualization(symbol: PySymbol, depth: int = 0):
    """Create visualization of symbol usage relationships

    Args:
        symbol (PySymbol): Starting symbol to analyze
        depth (int): Current recursion depth
    """
    # Prevent excessive recursion
    if depth >= MAX_DEPTH:
        return

    # Process each usage of the symbol
    for usage in symbol.usages:
        usage_symbol = usage.usage_symbol

        # Determine node color based on type
        if is_http_method(usage_symbol):
            color = COLOR_PALETTE.get("HTTP_METHOD")
        else:
            color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#f694ff")

        # Add node and edge to graph
        G.add_node(usage_symbol, color=color)
        G.add_edge(symbol, usage_symbol, **generate_edge_meta(usage))

        # Recursively process usage symbol
        create_blast_radius_visualization(usage_symbol, depth + 1)
```

### Visualizing the Graph
Finally, we can create our blast radius visualization:
```python
# Get target function to analyze
target_func = codebase.get_function('export_asset')

# Add root node
G.add_node(target_func, color=COLOR_PALETTE.get("StartFunction"))

# Build the visualization
create_blast_radius_visualization(target_func)

# Render graph to show impact flow
# Note: a -> b means changes to a will impact b
codebase.visualize(G)
```

### Take a look
<iframe
  width="100%"
  height="600px"
  scrolling="no"
  loading="lazy"
  src={`https://codegen.sh/embedded/graph?id=d255db6c-9a86-4197-9b78-16c506858a3b&zoom=1&targetNodeName=export_asset`}
  className="rounded-xl "
  style={{
    backgroundColor: "#15141b",
  }}
></iframe>
<Info>
View on [codegen.sh](https://www.codegen.sh/codemod/d255db6c-9a86-4197-9b78-16c506858a3b/public/diff)
</Info>

## What's Next?

<CardGroup cols={2}>
  <Card
    title="Codebase Modularity"
    icon="diagram-project"
    href="/tutorials/modularity"
  >
    Learn how to use Codegen to create modular codebases.
  </Card>
  <Card
    title="Deleting Dead Code"
    icon="trash"
    href="/tutorials/deleting-dead-code"
  >
    Learn how to use Codegen to delete dead code.
  </Card>
  <Card
    title="Increase Type Coverage"
    icon="shield-check"
    href="/tutorials/increase-type-coverage"
  >
    Learn how to use Codegen to increase type coverage.
  </Card>
  <Card title="API Reference" icon="code" href="/api-reference">
    Explore the complete API documentation for all Codegen classes and methods.
  </Card>
</CardGroup>

---
title: "Mining Training Data for LLMs"
sidebarTitle: "Mining Data"
description: "Learn how to generate training data for large language models using Codegen"
icon: "network-wired"
iconType: "solid"
---

This guide demonstrates how to use Codegen to generate high-quality training data for large language models (LLMs) by extracting function implementations along with their dependencies and usages. This approach is similar to [word2vec](https://www.tensorflow.org/text/tutorials/word2vec) or [node2vec](https://snap.stanford.edu/node2vec/) - given the context of a function, learn to predict the function's implementation.

<Info>View the full code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/7b978091c3153b687c32928fe10f05425e22f6a5/examples/generate_training_data)</Info>

<Tip>This example works with both Python and Typescript repositories without modification</Tip>

## Overview

The process involves three main steps:

1. Finding all functions in the codebase
2. Extracting their implementations, dependencies, and usages
3. Generating structured training data

Let's walk through each step using Codegen.

## Step 1: Finding Functions and Their Context

First, we will do a "graph expansion" for each function - grab the function's source, as well as the full source of all usages of the function and all dependencies.

<Info>See [dependencies and usages](/building-with-codegen/dependencies-and-usages) to learn more about navigating the code graph</Info>

First, let's import the types we need from Codegen:

```python
import codegen
from codegen import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
```

Here's how we get the full context for each function:

```python
def get_function_context(function) -> dict:
    """Get the implementation, dependencies, and usages of a function."""
    context = {
        "implementation": {"source": function.source, "filepath": function.filepath},
        "dependencies": [],
        "usages": [],
    }

    # Add dependencies
    for dep in function.dependencies:
        # Hop through imports to find the root symbol source
        if isinstance(dep, Import):
            dep = hop_through_imports(dep)

        context["dependencies"].append({"source": dep.source, "filepath": dep.filepath})

    # Add usages
    for usage in function.usages:
        context["usages"].append({
            "source": usage.usage_symbol.source,
            "filepath": usage.usage_symbol.filepath,
        })

    return context
```

Notice how we use `hop_through_imports` to resolve dependencies. When working with imports, symbols can be re-exported multiple times. For example, a helper function might be imported and re-exported through several files before being used. We need to follow this chain to find the actual implementation:

```python
def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import."""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol
```

This creates a structured representation of each function's context:

```json
{
  "implementation": {
    "source": "def process_data(input: str) -> dict: ...",
    "filepath": "src/data_processor.py"
  },
  "dependencies": [
    {
      "source": "def validate_input(data: str) -> bool: ...",
      "filepath": "src/validators.py"
    }
  ],
  "usages": [
    {
      "source": "result = process_data(user_input)",
      "filepath": "src/api.py"
    }
  ]
}
```

## Step 2: Processing the Codebase

Next, we process all functions in the codebase to generate our training data:

```python
def run(codebase: Codebase):
    """Generate training data using a node2vec-like approach for code embeddings."""
    # Track all function contexts
    training_data = {
        "functions": [],
        "metadata": {
            "total_functions": len(codebase.functions),
            "total_processed": 0,
            "avg_dependencies": 0,
            "avg_usages": 0,
        },
    }

    # Process each function in the codebase
    for function in codebase.functions:
        # Skip if function is too small
        if len(function.source.split("\n")) < 2:
            continue

        # Get function context
        context = get_function_context(function)

        # Only keep functions with enough context
        if len(context["dependencies"]) + len(context["usages"]) > 0:
            training_data["functions"].append(context)

    # Update metadata
    training_data["metadata"]["total_processed"] = len(training_data["functions"])
    if training_data["functions"]:
        training_data["metadata"]["avg_dependencies"] = sum(
            len(f["dependencies"]) for f in training_data["functions"]
        ) / len(training_data["functions"])
        training_data["metadata"]["avg_usages"] = sum(
            len(f["usages"]) for f in training_data["functions"]
        ) / len(training_data["functions"])

    return training_data
```

## Step 3: Running the Generator

Finally, we can run our training data generator on any codebase.

<Note>See [parsing codebases](/building-with-codegen/parsing-codebases) to learn more</Note>

```python
if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi")

    print("Generating training data...")
    training_data = run(codebase)

    print("Saving training data...")
    with open("training_data.json", "w") as f:
        json.dump(training_data, f, indent=2)
    print("Training data saved to training_data.json")
```

This will:
1. Load the target codebase
2. Process all functions
3. Save the structured training data to a JSON file

<Tip>
  You can use any Git repository as your source codebase by passing the repo URL
  to [Codebase.from_repo(...)](/api-reference/core/Codebase#from-repo).
</Tip>

## Using the Training Data

The generated data can be used to train LLMs in several ways:

1. **Masked Function Prediction**: Hide a function's implementation and predict it from dependencies and usages
2. **Code Embeddings**: Generate embeddings that capture semantic relationships between functions
3. **Dependency Prediction**: Learn to predict which functions are likely to be dependencies
4. **Usage Pattern Learning**: Train models to understand common usage patterns

For example, to create a masked prediction task:

```python
def create_training_example(function_data):
    """Create a masked prediction example from function data."""
    return {
        "context": {
            "dependencies": function_data["dependencies"],
            "usages": function_data["usages"]
        },
        "target": function_data["implementation"]
    }

# Create training examples
examples = [create_training_example(f) for f in training_data["functions"]]
```



---
title: "Organizing Your Codebase"
sidebarTitle: "Organization"
icon: "folder-tree"
iconType: "solid"
---

Codegen SDK provides a powerful set of tools for deterministically moving code safely and efficiently. This guide will walk you through the basics of moving code with Codegen SDK.

Common use cases include:

<AccordionGroup>
  <Accordion title="Splitting up large files">

```python
print(f"🔍 Processing file: {filepath}")
file = codebase.get_file(filepath)

# Get the directory path for creating new files
dir_path = file.directory.path if file.directory else ""

# Iterate through all functions in the file
for function in file.functions:
    # Create new filename based on function name
    new_filepath = f"{dir_path}/{function.name}.py"
    print(f"📝 Creating new file: {new_filepath}")

    # Create the new file
    new_file = codebase.create_file(new_filepath)

    # Move the function to the new file, including dependencies
    print(f"➡️ Moving function: {function.name}")
    function.move_to_file(new_file, include_dependencies=True)
```

  </Accordion>

  <Accordion title="Organize code into modules">

```python
# Dictionary to track modules and their functions
module_map = {
    "utils": lambda f: f.name.startswith("util_") or f.name.startswith("helper_"),
    "api": lambda f: f.name.startswith("api_") or f.name.startswith("endpoint_"),
    "data": lambda f: f.name.startswith("data_") or f.name.startswith("db_"),
    "core": lambda f: True  # Default module for other functions
}

print("🔍 Starting code organization...")

# Create module directories if they don't exist
for module in module_map.keys():
    if not codebase.has_directory(module):
        print(f"📁 Creating module directory: {module}")
        codebase.create_directory(module, exist_ok=True)

# Process each file in the codebase
for file in codebase.files:
    print(f"\n📄 Processing file: {file.filepath}")

    # Skip if file is already in a module directory
    if any(file.filepath.startswith(module) for module in module_map.keys()):
        continue

    # Process each function in the file
    for function in file.functions:
        # Determine which module this function belongs to
        target_module = next(
            (module for module, condition in module_map.items()
             if condition(function)),
            "core"
        )

        # Create the new file path
        new_filepath = f"{target_module}/{function.name}.py"

        print(f"  ➡️ Moving {function.name} to {target_module} module")

        # Create new file and move function
        if not codebase.has_file(new_filepath):
            new_file = codebase.create_file(new_filepath)
            function.move_to_file(new_file, include_dependencies=True)

print("\n✅ Code organization complete!")
```

  </Accordion>

  <Accordion title="Break up import cycles">

```python
# Create a graph to detect cycles
import networkx as nx

# Build dependency graph
G = nx.DiGraph()

# Add edges for imports between files
for file in codebase.files:
    for imp in file.imports:
        if imp.from_file:
            G.add_edge(file.filepath, imp.from_file.filepath)

# Find cycles in the graph
cycles = list(nx.simple_cycles(G))

if not cycles:
    print("✅ No import cycles found!")
    exit()

print(f"🔍 Found {len(cycles)} import cycles")

# Process each cycle
for cycle in cycles:
    print(f"\n⭕ Processing cycle: {' -> '.join(cycle)}")

    # Get the first two files in the cycle
    file1 = codebase.get_file(cycle[0])
    file2 = codebase.get_file(cycle[1])

    # Find functions in file1 that are used by file2
    for function in file1.functions:
        if any(usage.file == file2 for usage in function.usages):
            # Create new file for the shared function
            new_filepath = f"shared/{function.name}.py"
            print(f"  ➡️ Moving {function.name} to {new_filepath}")

            if not codebase.has_directory("shared"):
                codebase.create_directory("shared")

            new_file = codebase.create_file(new_filepath)
            function.move_to_file(new_file, include_dependencies=True)

print("\n✅ Import cycles resolved!")
```

  </Accordion>
</AccordionGroup>

<Tip>
  Most operations in Codegen will automatically handle updaging
  [dependencies](/building-with-codegen/dependencies-and-usages) and
  [imports](/building-with-codegen/imports). See [Moving
  Symbols](/building-with-codegen/moving-symbols) to learn more.
</Tip>

## Basic Symbol Movement

To move a symbol from one file to another, you can use the [move_to_file](/api-reference/core/Function#move-to-file) method.

<CodeGroup>
```python python
# Get the symbol
symbol_to_move = source_file.get_symbol("my_function")
# Pick a destination file
dst_file = codebase.get_file("path/to/dst/location.py")
# Move the symbol, move all of its dependencies with it (remove from old file), and add an import of symbol into old file
symbol_to_move.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
```

```python typescript
# Get the symbol
symbol_to_move = source_file.get_symbol("myFunction")
# Pick a destination file
dst_file = codebase.get_file("path/to/dst/location.ts")
# Move the symbol, move all of its dependencies with it (remove from old file), and add an import of symbol into old file
symbol_to_move.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
```

</CodeGroup>

This will move `my_function` to `path/to/dst/location.py`, safely updating all references to it in the process.

## Updating Imports

After moving a symbol, you may need to update imports throughout your codebase. GraphSitter offers two strategies for this:

1. **Update All Imports**: This strategy updates all imports across the codebase to reflect the new location of the symbol.

<CodeGroup>
```python python
symbol_to_move = codebase.get_symbol("symbol_to_move")
dst_file = codebase.create_file("new_file.py")
symbol_to_move.move_to_file(dst_file, strategy="update_all_imports")
```

```python typescript
symbol_to_move = codebase.get_symbol("symbolToMove")
dst_file = codebase.create_file("new_file.ts")
symbol_to_move.move_to_file(dst_file, strategy="update_all_imports")
```

</CodeGroup>

<Warning>Updating all imports can result in very large PRs</Warning>

2. **Add Back Edge**: This strategy adds an import in the original file that re-imports (and exports) the moved symbol, maintaining backwards compatibility. This will result in fewer total modifications, as existing imports will not need to be updated.

<CodeGroup>
```python python
symbol_to_move = codebase.get_symbol("symbol_to_move")
dst_file = codebase.create_file("new_file.py")
symbol_to_move.move_to_file(dst_file, strategy="add_back_edge")
```

```python typescript
symbol_to_move = codebase.get_symbol("symbolToMove")
dst_file = codebase.create_file("new_file.ts")
symbol_to_move.move_to_file(dst_file, strategy="add_back_edge")
```

</CodeGroup>

## Handling Dependencies

By default, Codegen will move all of a symbols dependencies along with it. This ensures that your codebase remains consistent and functional.

<CodeGroup>
```python python
my_symbol = codebase.get_symbol("my_symbol")
dst_file = codebase.create_file("new_file.py")
my_symbol.move_to_file(dst_file, include_dependencies=True)
```

```python typescript
my_symbol = codebase.get_symbol("mySymbol")
dst_file = codebase.create_file("new_file.ts")
my_symbol.move_to_file(dst_file, include_dependencies=True)
```

</CodeGroup>

If you set `include_dependencies=False`, only the symbol itself will be moved, and any dependencies will remain in the original file.

## Moving Multiple Symbols

If you need to move multiple symbols, you can do so in a loop:

```python
source_file = codebase.get_file("path/to/source_file.py")
dest_file = codebase.get_file("path/to/destination_file.py")
# Create a list of symbols to move
symbols_to_move = [source_file.get_function("my_function"), source_file.get_class("MyClass")]
# Move each symbol to the destination file
for symbol in symbols_to_move:
    symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")
```

## Best Practices

1. **Commit After Major Changes**: If you're making multiple significant changes, use `codebase.commit()` between them to ensure the codebase graph is up-to-date.

2. **Re-fetch References**: After a commit, re-fetch any file or symbol references you're working with, as they may have become stale.

3. **Handle Errors**: Be prepared to handle cases where symbols or files might not exist, or where moves might fail due to naming conflicts.

By following these guidelines, you can effectively move symbols around your codebase while maintaining its integrity and functionality.


---
title: "Improving Code Modularity"
sidebarTitle: "Modularity"
icon: "diagram-project"
iconType: "solid"
---

Codegen SDK provides powerful tools for analyzing and improving code modularity. This guide will help you identify and fix common modularity issues like circular dependencies, tight coupling, and poorly organized imports.

Common use cases include:
- Breaking up circular dependencies
- Organizing imports and exports
- Identifying highly coupled modules
- Extracting shared code into common modules
- Analyzing module boundaries

## Analyzing Import Relationships

First, let's see how to analyze import relationships in your codebase:

```python
import networkx as nx
from collections import defaultdict

# Create a graph of file dependencies
def create_dependency_graph():
    G = nx.DiGraph()

    for file in codebase.files:
        # Add node for this file
        G.add_node(file.filepath)

        # Add edges for each import
        for imp in file.imports:
            if imp.from_file:  # Skip external imports
                G.add_edge(file.filepath, imp.from_file.filepath)

    return G

# Create and analyze the graph
graph = create_dependency_graph()

# Find circular dependencies
cycles = list(nx.simple_cycles(graph))
if cycles:
    print("🔄 Found circular dependencies:")
    for cycle in cycles:
        print(f"  • {' -> '.join(cycle)}")

# Calculate modularity metrics
print("\n📊 Modularity Metrics:")
print(f"  • Number of files: {len(graph.nodes)}")
print(f"  • Number of imports: {len(graph.edges)}")
print(f"  • Average imports per file: {len(graph.edges)/len(graph.nodes):.1f}")
```

## Breaking Circular Dependencies

When you find circular dependencies, here's how to break them:

```python
def break_circular_dependency(cycle):
    # Get the first two files in the cycle
    file1 = codebase.get_file(cycle[0])
    file2 = codebase.get_file(cycle[1])

    # Create a shared module for common code
    shared_dir = "shared"
    if not codebase.has_directory(shared_dir):
        codebase.create_directory(shared_dir)

    # Find symbols used by both files
    shared_symbols = []
    for symbol in file1.symbols:
        if any(usage.file == file2 for usage in symbol.usages):
            shared_symbols.append(symbol)

    # Move shared symbols to a new file
    if shared_symbols:
        shared_file = codebase.create_file(f"{shared_dir}/shared_types.py")
        for symbol in shared_symbols:
            symbol.move_to_file(shared_file, strategy="update_all_imports")

# Break each cycle found
for cycle in cycles:
    break_circular_dependency(cycle)
```

## Organizing Imports

Clean up and organize imports across your codebase:

```python
def organize_file_imports(file):
    # Group imports by type
    std_lib_imports = []
    third_party_imports = []
    local_imports = []

    for imp in file.imports:
        if imp.is_standard_library:
            std_lib_imports.append(imp)
        elif imp.is_third_party:
            third_party_imports.append(imp)
        else:
            local_imports.append(imp)

    # Sort each group
    for group in [std_lib_imports, third_party_imports, local_imports]:
        group.sort(key=lambda x: x.module_name)

    # Remove all existing imports
    for imp in file.imports:
        imp.remove()

    # Add imports back in organized groups
    if std_lib_imports:
        for imp in std_lib_imports:
            file.add_import(imp.source)
        file.insert_after_imports("")  # Add newline

    if third_party_imports:
        for imp in third_party_imports:
            file.add_import(imp.source)
        file.insert_after_imports("")  # Add newline

    if local_imports:
        for imp in local_imports:
            file.add_import(imp.source)

# Organize imports in all files
for file in codebase.files:
    organize_file_imports(file)
```

## Identifying Highly Coupled Modules

Find modules that might need to be split up:

```python
from collections import defaultdict

def analyze_module_coupling():
    coupling_scores = defaultdict(int)

    for file in codebase.files:
        # Count unique files imported from
        imported_files = {imp.from_file for imp in file.imports if imp.from_file}
        coupling_scores[file.filepath] = len(imported_files)

        # Count files that import this file
        importing_files = {usage.file for symbol in file.symbols
                         for usage in symbol.usages if usage.file != file}
        coupling_scores[file.filepath] += len(importing_files)

    # Sort by coupling score
    sorted_files = sorted(coupling_scores.items(),
                         key=lambda x: x[1],
                         reverse=True)

    print("\n🔍 Module Coupling Analysis:")
    print("\nMost coupled files:")
    for filepath, score in sorted_files[:5]:
        print(f"  • {filepath}: {score} connections")

analyze_module_coupling()
```

## Extracting Shared Code

When you find highly coupled modules, extract shared code:

```python
def extract_shared_code(file, min_usages=3):
    # Find symbols used by multiple files
    for symbol in file.symbols:
        # Get unique files using this symbol
        using_files = {usage.file for usage in symbol.usages
                      if usage.file != file}

        if len(using_files) >= min_usages:
            # Create appropriate shared module
            module_name = determine_shared_module(symbol)
            if not codebase.has_file(f"shared/{module_name}.py"):
                shared_file = codebase.create_file(f"shared/{module_name}.py")
            else:
                shared_file = codebase.get_file(f"shared/{module_name}.py")

            # Move symbol to shared module
            symbol.move_to_file(shared_file, strategy="update_all_imports")

def determine_shared_module(symbol):
    # Logic to determine appropriate shared module name
    if symbol.is_type:
        return "types"
    elif symbol.is_constant:
        return "constants"
    elif symbol.is_utility:
        return "utils"
    else:
        return "common"
```

---
title: "Managing Feature Flags"
sidebarTitle: "Feature Flags"
icon: "flag"
iconType: "solid"
---

Codegen has been used in production for multi-million line codebases to automatically delete "dead" (rolled-out) feature flags. This guide will walk you through analyzing feature flag usage and safely removing rolled out flags.

<Warning>
    Every codebase does feature flags differently. This guide shows common techniques and syntax but likely requires adaptation to codebase-specific circumstances.
</Warning>

## Analyzing Feature Flag Usage

Before removing a feature flag, it's important to analyze its usage across the codebase. Codegen provides tools to help identify where and how feature flags are used.

### For Python Codebases

For Python codebases using a `FeatureFlags` class pattern like so:
```python
class FeatureFlags:
    FEATURE_1 = False
    FEATURE_2 = True
```

You can use [Class.get_attribute(...)](/api-reference/core/Class#get-attribute) and [Attribute.usages](/api-reference/core/Attribute#usages) to analyze the coverage of your flags, like so:



```python
feature_flag_usage = {}
feature_flag_class = codebase.get_class('FeatureFlag')

if feature_flag_class:
    # Initialize usage count for all attributes
    for attr in feature_flag_class.attributes:
        feature_flag_usage[attr.name] = 0

    # Get all usages of the FeatureFlag class
    for usage in feature_flag_class.usages:
        usage_source = usage.usage_symbol.source if hasattr(usage, 'usage_symbol') else str(usage)
        for flag_name in feature_flag_usage.keys():
            if f"FeatureFlag.{flag_name}" in usage_source:
                feature_flag_usage[flag_name] += 1

    sorted_flags = sorted(feature_flag_usage.items(), key=lambda x: x[1], reverse=True)

    print("Feature Flag Usage Table:")
    print("-------------------------")
    print(f"{'Feature Flag':<30} | {'Usage Count':<12}")
    print("-" * 45)
    for flag, count in sorted_flags:
        print(f"{flag:<30} | {count:<12}")

    print(f"\nTotal feature flags: {len(sorted_flags)}")
else:
    print("❗ FeatureFlag enum not found in the codebase")
```

This will output a table showing all feature flags and their usage counts, helping identify which flags are candidates for removal.

<Tip>
    Learn more about [Attributes](/building-with-codegen/class-api#class-attributes) and [tracking usages](/building-with-codegen/dependencies-and-usages) here
</Tip>


## Removing Rolled Out Flags

Once you've identified a flag that's ready to be removed, Codegen can help safely delete it and its associated code paths.

<Tip>
    This primarily leverages Codegen's API for [reduction conditions](/building-with-codegen/reducing-conditions)
</Tip>

### Python Example

For Python codebases, here's how to remove a feature flag and its usages:

```python
flag_name = "FEATURE_TO_REMOVE"

# Get the feature flag variable
feature_flag_file = codebase.get_file("app/utils/feature_flags.py")
flag_class = feature_flag_file.get_class("FeatureFlag")

# Check if the flag exists
flag_var = flag_class.get_attribute(flag_name)
if not flag_var:
    print(f'No such flag: {flag_name}')
    return

# Remove all usages of the feature flag
for usage in flag_var.usages:
    if isinstance(usage.parent, IfBlockStatement):
        # For if statements, reduce the condition to True
        usage.parent.reduce_condition(True)
    elif isinstance(usage.parent, WithStatement):
        # For with statements, keep the code block
        usage.parent.code_block.unwrap()
    else:
        # For other cases, remove the usage
        usage.remove()

# Remove the flag definition
flag_var.remove()

# Commit changes
codebase.commit()
```

### React/TypeScript Example

For React applications using a hooks-based feature flag system:

```python
feature_flag_name = "NEW_UI_ENABLED"
target_value = True  # The value to reduce the flag to

print(f'Removing feature flag: {feature_flag_name}')

# 1. Remove from configuration
config_file = codebase.get_file("src/featureFlags/config.ts")
feature_flag_config = config_file.get_symbol("FEATURE_FLAG_CONFIG").value
if feature_flag_name in feature_flag_config.keys():
    feature_flag_config.pop(feature_flag_name)
    print('✅ Removed from feature flag config')

# 2. Find and reduce all hook usages
hook = codebase.get_function("useFeatureFlag")
for usage in hook.usages:
    fcall = usage.match
    if isinstance(fcall, FunctionCall):
        # Check if this usage is for our target flag
        first_arg = fcall.args[0].value
        if isinstance(first_arg, String) and first_arg.content == feature_flag_name:
            print(f'Reducing in: {fcall.parent_symbol.name}')
            # This automatically handles:
            # - Ternary expressions: flag ? <New /> : <Old />
            # - If statements: if (flag) { ... }
            # - Conditional rendering: {flag && <Component />}
            fcall.reduce_condition(target_value)

# 3. Commit changes
codebase.commit()
```

This will:
1. Remove the feature flag from the configuration
2. Find all usages of the `useFeatureFlag` hook for this flag
3. Automatically reduce any conditional logic using the flag
4. Handle common React patterns like ternaries and conditional rendering


## Related Resources
- [Reducing Conditions](/building-with-codegen/reducing-conditions) - Details on condition reduction APIs
- [Dead Code Removal](/tutorials/deleting-dead-code) - Remove unused code after flag deletion

---
title: "Deleting Dead Code"
sidebarTitle: "Dead Code"
icon: "trash"
iconType: "solid"
---

Dead code refers to code that is not being used or referenced anywhere in your codebase.

However, it's important to note that some code might appear unused but should not be deleted, including:
- Test files and test functions
- Functions with decorators (which may be called indirectly)
- Public API endpoints
- Event handlers or callback functions
- Code used through reflection or dynamic imports

This guide will show you how to safely identify and remove genuinely unused code while preserving important functionality.

## Overview

To simply identify code without any external usages, you can check for the absence of [Symbol.usages](/api-reference/core/Symbol#usages).

<Tip>See [Dependencies and Usages](/building-with-codegen/dependencies-and-usages) for more information on how to use these properties.</Tip>

```python
# Iterate through all functions in the codebase
for function in codebase.functions:
    # Remove functions with no usages
    if not function.usages:
        function.remove()

# Commit
codebase.commit()
```

<Warning>
This will remove all code that is not explicitly referenced elsewhere, including tests, endpoints, etc. This is almost certainly not what you want. We recommend further filtering.
</Warning>

## Filtering for Special Cases

To filter out special cases that are not explicitly referenced yet are, nonetheless, worth keeping around, you can use the following pattern:


```python
for function in codebase.functions:

    # Skip test files
    if "test" in function.file.filepath:
        continue

    # Skip decorated functions
    if function.decorators:
        continue

    # Skip public routes, e.g. next.js endpoints
    # (Typescript only)
    if 'routes' in function.file.filepath and function.is_jsx:
        continue

    # ... etc.

    # Check if the function has no usages and no call sites
    if not function.usages and not function.call_sites:
        # Print a message indicating the removal of the function
        print(f"Removing unused function: {function.name}")
        # Remove the function from the file
        function.remove()

# Commit
codebase.commit()
```


## Cleaning Up Unused Variables

To remove unused variables, you can check for their usages within their scope:

```python typescript
for func in codebase.functions:
    # Iterate through local variable assignments in the function
    for var_assignments in func.code_block.local_var_assignments:
        # Check if the local variable assignment has no usages
        if not var_assignments.local_usages:
            # Remove the local variable assignment
            var_assignments.remove()

# Commit
codebase.commit()
```


## Cleaning Up After Removal

After removing dead code, you may need to clean up any remaining artifacts:

```python
for file in codebase.files:
    # Check if the file is empty
    if not file.content.strip():
        # Print a message indicating the removal of the empty file
        print(f"Removing empty file: {file.filepath}")
        # Remove the empty file
        file.remove()

# commit is NECESSARY to remove the files from the codebase
codebase.commit()

# Remove redundant newlines
for file in codebase.files:
    # Replace three or more consecutive newlines with two newlines
    file.edit(re.sub(r"\n{3,}", "\n\n", file.content))
```


---
title: "Increasing Type Coverage"
sidebarTitle: "Type Coverage"
icon: "shield-check"
iconType: "solid"
---

This guide demonstrates how to analyze and manipulate type annotations with Codegen SDK.

Common use cases include:

- Adding a type to a union or generic type
- Checking if a generic type has a given subtype
- Resolving a type annotation

<Tip>
    Adding type hints can improve developer experience and [significantly speed up](https://github.com/microsoft/Typescript/wiki/Performance#using-type-annotations) programs like the Typescript compiler and `mypy`.
</Tip>

<Note>See [Type Annotations](/building-with-codegen/type-annotations) for a general overview of the type maninpulation</Note>

## APIs for monitoring types

Codegen programs typically access type annotations through the following APIs:
- [Parameter.type](/api-reference/core/Parameter#type)
- [Function.return_type](/api-reference/python/PyFunction#return-type)
- [Assignment.type](/api-reference/core/Assignment#type)

Each of these has an associated setter.


## Finding the extent of your type coverage

To get an indication of your progress on type coverage, analyze the percentage of typed elements across your codebase

```python
# Initialize counters for parameters
total_parameters = 0
typed_parameters = 0

# Initialize counters for return types
total_functions = 0
typed_returns = 0

# Initialize counters for class attributes
total_attributes = 0
typed_attributes = 0

# Count parameter and return type coverage
for function in codebase.functions:
    # Count parameters
    total_parameters += len(function.parameters)
    typed_parameters += sum(1 for param in function.parameters if param.is_typed)

    # Count return types
    total_functions += 1
    if function.return_type and function.return_type.is_typed:
        typed_returns += 1

# Count class attribute coverage
for cls in codebase.classes:
    for attr in cls.attributes:
        total_attributes += 1
        if attr.is_typed:
            typed_attributes += 1

# Calculate percentages
param_percentage = (typed_parameters / total_parameters * 100) if total_parameters > 0 else 0
return_percentage = (typed_returns / total_functions * 100) if total_functions > 0 else 0
attr_percentage = (typed_attributes / total_attributes * 100) if total_attributes > 0 else 0

# Print results
print("\nType Coverage Analysis")
print("---------------------")
print(f"Parameters: {param_percentage:.1f}% ({typed_parameters}/{total_parameters} typed)")
print(f"Return types: {return_percentage:.1f}% ({typed_returns}/{total_functions} typed)")
print(f"Class attributes: {attr_percentage:.1f}% ({typed_attributes}/{total_attributes} typed)")
```

This analysis gives you a breakdown of type coverage across three key areas:
1. Function parameters - Arguments passed to functions
2. Return types - Function return type annotations
3. Class attributes - Type hints on class variables

<Tip>
    Focus first on adding types to the most frequently used functions and classes, as these will have the biggest impact on type checking and IDE support.
</Tip>

## Adding simple return type annotations

To add a return type, use `function.set_return_type`. The script below will add a `-> None` return type to all functions that contain no return statements:

<CodeGroup>
```python For Python
for file in codebase.files:
    # Check if 'app' is in the file's filepath
    if "app" in file.filepath:
        # Iterate through all functions in the file
        for function in file.functions:
            # Check if the function has no return statements
            if len(function.return_statements) == 0:
                # Set the return type to None
                function.set_return_type("None")
```

```python For Typescript
for file in codebase.files:
    # Check if 'app' is in the file's filepath
    if "app" in file.filepath:
        # Iterate through all functions in the file
        for function in file.functions:
            # Check if the function has no return statements
            if len(function.return_statements) == 0:
                # Set the return type to None
                function.set_return_type("null")
```
</CodeGroup>


## Coming Soon: Advanced Type Inference

<Warning>Codegen is building out an API for direct interface with `tsc` and `mypy` for precise type inference. Interested piloting this API? Let us know!</Warning>

---
title: "Managing TypeScript Exports"
sidebarTitle: "Export Management"
description: "Safely and systematically manage exports in your TypeScript codebase"
icon: "ship"
iconType: "solid"
---

Codegen provides powerful tools for managing and reorganizing exports in TypeScript codebases. This tutorial builds on the concepts covered in [exports](/building-with-codegen/exports) to show you how to automate common export management tasks and ensure your module boundaries stay clean and maintainable.

## Common Export Management Tasks

### Collecting and Processing Exports

When reorganizing exports, the first step is identifying which exports need to be processed:

```python
processed_imports = set()

for file in codebase.files:
    # Only process files under /src/shared
    if '/src/shared' not in file.filepath:
        continue

    # Gather all reexports that are not external exports
    all_reexports = []
    for export_stmt in file.export_statements:
        for export in export_stmt.exports:
            if export.is_reexport() and not export.is_external_export:
                all_reexports.append(export)

    # Skip if there are none
    if not all_reexports:
        continue
```

### Moving Exports to Public Files

When centralizing exports in public-facing files:

```python
# Replace "src/" with "src/shared/"
resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")

# Get relative path from the "public" file back to the original file
relative_path = codebase.get_relative_path(
    from_file=resolved_public_file,
    to_file=export.resolved_symbol.filepath
)

# Ensure the "public" file exists
if not codebase.has_file(resolved_public_file):
    target_file = codebase.create_file(resolved_public_file, sync=True)
else:
    target_file = codebase.get_file(resolved_public_file)

# If target file already has a wildcard export for this relative path, skip
if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
    has_wildcard = True
    continue
```

### Managing Different Export Types

Codegen can handle all types of exports automatically:

<AccordionGroup>
  <Accordion title="Wildcard Exports">
    ```python
    # A) Wildcard export, e.g. `export * from "..."`
    if export.is_wildcard_export():
        target_file.insert_before(f'export * from "{relative_path}"')
    ```
  </Accordion>

  <Accordion title="Type Exports">
    ```python
    # B) Type export, e.g. `export type { Foo, Bar } from "..."`
    elif export.is_type_export():
        # Does this file already have a type export statement for the path?
        statement = file.get_export_statement_for_path(relative_path, "TYPE")
        if statement:
            # Insert into existing statement
            if export.is_aliased():
                statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
            else:
                statement.insert(0, f"{export.name}")
        else:
            # Insert a new type export statement
            if export.is_aliased():
                target_file.insert_before(
                    f'export type {{ {export.resolved_symbol.name} as {export.name} }} '
                    f'from "{relative_path}"'
                )
            else:
                target_file.insert_before(
                    f'export type {{ {export.name} }} from "{relative_path}"'
                )
    ```
  </Accordion>

  <Accordion title="Named Exports">
    ```python
    # C) Normal export, e.g. `export { Foo, Bar } from "..."`
    else:
        statement = file.get_export_statement_for_path(relative_path, "EXPORT")
        if statement:
            # Insert into existing statement
            if export.is_aliased():
                statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
            else:
                statement.insert(0, f"{export.name}")
        else:
            # Insert a brand-new normal export statement
            if export.is_aliased():
                target_file.insert_before(
                    f'export {{ {export.resolved_symbol.name} as {export.name} }} '
                    f'from "{relative_path}"'
                )
            else:
                target_file.insert_before(
                    f'export {{ {export.name} }} from "{relative_path}"'
                )
    ```
  </Accordion>
</AccordionGroup>

## Updating Import References

After moving exports, you need to update all import references:

```python
# Now update all import usages that refer to this export
for usage in export.symbol_usages():
    if isinstance(usage, TSImport) and usage not in processed_imports:
        processed_imports.add(usage)

        # Translate the resolved_public_file to the usage file's TS config import path
        new_path = usage.file.ts_config.translate_import_path(resolved_public_file)

        if has_wildcard and export.name != export.resolved_symbol.name:
            name = f"{export.resolved_symbol.name} as {export.name}"
        else:
            name = usage.name

        if usage.is_type_import():
            new_import = f'import type {{ {name} }} from "{new_path}"'
        else:
            new_import = f'import {{ {name} }} from "{new_path}"'

        usage.file.insert_before(new_import)
        usage.remove()

# Remove the old export from the original file
export.remove()

# If the file ends up with no exports, remove it entirely
if not file.export_statements and len(file.symbols) == 0:
    file.remove()
```

## Best Practices

1. **Check for Wildcards First**: Always check for existing wildcard exports before adding new ones:
```python
if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
    has_wildcard = True
    continue
```

2. **Handle Path Translations**: Use TypeScript config for path translations:
```python
new_path = usage.file.ts_config.translate_import_path(resolved_public_file)
```

3. **Clean Up Empty Files**: Remove files that no longer contain exports or symbols:
```python
if not file.export_statements and len(file.symbols) == 0:
    file.remove()
```

## Next Steps

After reorganizing your exports:

1. Run your test suite to verify everything still works
2. Review the generated import statements
3. Check for any empty files that should be removed
4. Verify that all export types (wildcard, type, named) are working as expected

<Note>
Remember that managing exports is an iterative process. You may need to run the codemod multiple times as your codebase evolves.
</Note>

### Related tutorials
- [Moving symbols](/building-with-codegen/moving-symbols)
- [Exports](/building-with-codegen/exports)
- [Dependencies and usages](/building-with-codegen/dependencies-and-usages)

## Complete Codemod

Here's the complete codemod that you can copy and use directly:

```python
processed_imports = set()

for file in codebase.files:
    # Only process files under /src/shared
    if '/src/shared' not in file.filepath:
        continue

    # Gather all reexports that are not external exports
    all_reexports = []
    for export_stmt in file.export_statements:
        for export in export_stmt.exports:
            if export.is_reexport() and not export.is_external_export:
                all_reexports.append(export)

    # Skip if there are none
    if not all_reexports:
        continue

    for export in all_reexports:
        has_wildcard = False

        # Replace "src/" with "src/shared/"
        resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")

        # Get relative path from the "public" file back to the original file
        relative_path = codebase.get_relative_path(
            from_file=resolved_public_file,
            to_file=export.resolved_symbol.filepath
        )

        # Ensure the "public" file exists
        if not codebase.has_file(resolved_public_file):
            target_file = codebase.create_file(resolved_public_file, sync=True)
        else:
            target_file = codebase.get_file(resolved_public_file)

        # If target file already has a wildcard export for this relative path, skip
        if target_file.has_export_statement_for_path(relative_path, "WILDCARD"):
            has_wildcard = True
            continue

        # Compare "public" path to the local file's export.filepath
        if codebase._remove_extension(resolved_public_file) != codebase._remove_extension(export.filepath):

            # A) Wildcard export, e.g. `export * from "..."`
            if export.is_wildcard_export():
                target_file.insert_before(f'export * from "{relative_path}"')

            # B) Type export, e.g. `export type { Foo, Bar } from "..."`
            elif export.is_type_export():
                # Does this file already have a type export statement for the path?
                statement = file.get_export_statement_for_path(relative_path, "TYPE")
                if statement:
                    # Insert into existing statement
                    if export.is_aliased():
                        statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                    else:
                        statement.insert(0, f"{export.name}")
                else:
                    # Insert a new type export statement
                    if export.is_aliased():
                        target_file.insert_before(
                            f'export type {{ {export.resolved_symbol.name} as {export.name} }} '
                            f'from "{relative_path}"'
                        )
                    else:
                        target_file.insert_before(
                            f'export type {{ {export.name} }} from "{relative_path}"'
                        )

            # C) Normal export, e.g. `export { Foo, Bar } from "..."`
            else:
                statement = file.get_export_statement_for_path(relative_path, "EXPORT")
                if statement:
                    # Insert into existing statement
                    if export.is_aliased():
                        statement.insert(0, f"{export.resolved_symbol.name} as {export.name}")
                    else:
                        statement.insert(0, f"{export.name}")
                else:
                    # Insert a brand-new normal export statement
                    if export.is_aliased():
                        target_file.insert_before(
                            f'export {{ {export.resolved_symbol.name} as {export.name} }} '
                            f'from "{relative_path}"'
                        )
                    else:
                        target_file.insert_before(
                            f'export {{ {export.name} }} from "{relative_path}"'
                        )

        # Now update all import usages that refer to this export
        for usage in export.symbol_usages():
            if isinstance(usage, TSImport) and usage not in processed_imports:
                processed_imports.add(usage)

                # Translate the resolved_public_file to the usage file's TS config import path
                new_path = usage.file.ts_config.translate_import_path(resolved_public_file)

                if has_wildcard and export.name != export.resolved_symbol.name:
                    name = f"{export.resolved_symbol.name} as {export.name}"
                else:
                    name = usage.name

                if usage.is_type_import():
                    new_import = f'import type {{ {name} }} from "{new_path}"'
                else:
                    new_import = f'import {{ {name} }} from "{new_path}"'

                usage.file.insert_before(new_import)
                usage.remove()

        # Remove the old export from the original file
        export.remove()

    # If the file ends up with no exports, remove it entirely
    if not file.export_statements and len(file.symbols) == 0:
        file.remove()
```

---
title: "Converting Default Exports"
sidebarTitle: "Default Export Conversion"
description: "Convert default exports to named exports in your TypeScript codebase"
icon: "arrow-right-arrow-left"
iconType: "solid"
---

Codegen provides tools to help you migrate away from default exports to named exports in your TypeScript codebase. This tutorial builds on the concepts covered in [exports](/building-with-codegen/exports) to show you how to automate this conversion process.

## Overview

Default exports can make code harder to maintain and refactor. Converting them to named exports provides several benefits:

- Better IDE support for imports and refactoring
- More explicit and consistent import statements
- Easier to track symbol usage across the codebase

## Converting Default Exports

Here's how to convert default exports to named exports:

```python
for file in codebase.files:
    target_file = file.filepath
    if not target_file:
        print(f"⚠️ Target file not found: {filepath}")
        continue

    # Get corresponding non-shared file
    non_shared_path = target_file.filepath.replace('/shared/', '/')
    if not codebase.has_file(non_shared_path):
        print(f"⚠️ No matching non-shared file for: {filepath}")
        continue

    non_shared_file = codebase.get_file(non_shared_path)
    print(f"📄 Processing {target_file.filepath}")

    # Process individual exports
    for export in target_file.exports:
        # Handle default exports
        if export.is_reexport() and export.is_default_export():
            print(f"  🔄 Converting default export '{export.name}'")
            default_export = next((e for e in non_shared_file.default_exports), None)
            if default_export:
                default_export.make_non_default()

    print(f"✨ Fixed exports in {target_file.filepath}")
```

## Understanding the Process

Let's break down how this works:

<AccordionGroup>
  <Accordion title="Finding Default Exports">
    ```python
    # Process individual exports
    for export in target_file.exports:
        # Handle default exports
        if export.is_reexport() and export.is_default_export():
            print(f"  🔄 Converting default export '{export.name}'")
    ```

    The code identifies default exports by checking:
    1. If it's a re-export (`is_reexport()`)
    2. If it's a default export (`is_default_export()`)
  </Accordion>

  <Accordion title="Converting to Named Exports">
    ```python
    default_export = next((e for e in non_shared_file.default_exports), None)
    if default_export:
        default_export.make_non_default()
    ```

    For each default export:
    1. Find the corresponding export in the non-shared file
    2. Convert it to a named export using `make_non_default()`
  </Accordion>

  <Accordion title="File Path Handling">
    ```python
    # Get corresponding non-shared file
    non_shared_path = target_file.filepath.replace('/shared/', '/')
    if not codebase.has_file(non_shared_path):
        print(f"⚠️ No matching non-shared file for: {filepath}")
        continue

    non_shared_file = codebase.get_file(non_shared_path)
    ```

    The code:
    1. Maps shared files to their non-shared counterparts
    2. Verifies the non-shared file exists
    3. Loads the non-shared file for processing
  </Accordion>
</AccordionGroup>

## Best Practices

1. **Check for Missing Files**: Always verify files exist before processing:
```python
if not target_file:
    print(f"⚠️ Target file not found: {filepath}")
    continue
```

2. **Log Progress**: Add logging to track the conversion process:
```python
print(f"📄 Processing {target_file.filepath}")
print(f"  🔄 Converting default export '{export.name}'")
```

3. **Handle Missing Exports**: Check that default exports exist before converting:
```python
default_export = next((e for e in non_shared_file.default_exports), None)
if default_export:
    default_export.make_non_default()
```

## Next Steps

After converting default exports:

1. Run your test suite to verify everything still works
2. Update any import statements that were using default imports
3. Review the changes to ensure all exports were converted correctly
4. Consider adding ESLint rules to prevent new default exports

<Note>
Remember to test thoroughly after converting default exports, as this change affects how other files import the converted modules.
</Note>

### Related tutorials
- [Managing typescript exports](/tutorials/managing-typescript-exports)
- [Exports](/building-with-codegen/exports)
- [Dependencies and usages](/building-with-codegen/dependencies-and-usages)

## Complete Codemod

Here's the complete codemod that you can copy and use directly:

```python

for file in codebase.files:
    target_file = file.filepath
    if not target_file:
        print(f"⚠️ Target file not found: {filepath}")
        continue

    # Get corresponding non-shared file
    non_shared_path = target_file.filepath.replace('/shared/', '/')
    if not codebase.has_file(non_shared_path):
        print(f"⚠️ No matching non-shared file for: {filepath}")
        continue

    non_shared_file = codebase.get_file(non_shared_path)
    print(f"📄 Processing {target_file.filepath}")

    # Process individual exports
    for export in target_file.exports:
        # Handle default exports
        if export.is_reexport() and export.is_default_export():
            print(f"  🔄 Converting default export '{export.name}'")
            default_export = next((e for e in non_shared_file.default_exports), None)
            if default_export:
                default_export.make_non_default()

    print(f"✨ Fixed exports in {target_file.filepath}")

```

---
title: "Creating Documentation"
sidebarTitle: "Documentation"
icon: "book"
iconType: "solid"
---

This guide demonstrates how to determine docs coverage and create documentation for your codebase.

This primarily leverages two APIs:
- [`codebase.ai(...)`](/api-reference/core/Codebase#ai) for generating docstrings
- [`function.set_docstring(...)`](/api-reference/core/HasBlock#set-docstring) for modifying them

## Determining Documentation Coverage

In order to determine the extent of your documentation coverage, you can iterate through all symbols of interest and count the number of docstrings:

To see your current documentation coverage, you can iterate through all symbols of interest and count the number of docstrings:

```python python
# Initialize counters
total_functions = 0
functions_with_docs = 0
total_classes = 0
classes_with_docs = 0

# Check functions
for function in codebase.functions:
    total_functions += 1
    if function.docstring:
        functions_with_docs += 1

# Check classes
for cls in codebase.classes:
    total_classes += 1
    if cls.docstring:
        classes_with_docs += 1

# Calculate percentages
func_coverage = (functions_with_docs / total_functions * 100) if total_functions > 0 else 0
class_coverage = (classes_with_docs / total_classes * 100) if total_classes > 0 else 0

# Print results with emojis
print("\n📊 Documentation Coverage Report:")
print(f"\n📝 Functions:")
print(f"  • Total: {total_functions}")
print(f"  • Documented: {functions_with_docs}")
print(f"  • Coverage: {func_coverage:.1f}%")

print(f"\n📚 Classes:")
print(f"  • Total: {total_classes}")
print(f"  • Documented: {classes_with_docs}")
print(f"  • Coverage: {class_coverage:.1f}%")

print(f"\n🎯 Overall Coverage: {((functions_with_docs + classes_with_docs) / (total_functions + total_classes) * 100):.1f}%")
```

Which provides the following output:
```
📊 Documentation Coverage Report:
📝 Functions:
  • Total: 1384
  • Documented: 331
  • Coverage: 23.9%
📚 Classes:
  • Total: 453
  • Documented: 91
  • Coverage: 20.1%
🎯 Overall Coverage: 23.0%
```

## Identifying Areas of Low Documentation Coverage


To identify areas of low documentation coverage, you can iterate through all directories and count the number of functions with docstrings.

<Note>Learn more about [`Directories` here](/building-with-codegen/files-and-directories).</Note>

```python python
# Track directory stats
dir_stats = {}

# Analyze each directory
for directory in codebase.directories:
    # Skip test, sql and alembic directories
    if any(x in directory.path.lower() for x in ['test', 'sql', 'alembic']):
        continue

    # Get undecorated functions
    funcs = [f for f in directory.functions if not f.is_decorated]
    total = len(funcs)

    # Only analyze dirs with >10 functions
    if total > 10:
        documented = sum(1 for f in funcs if f.docstring)
        coverage = (documented / total * 100)
        dir_stats[directory.path] = {
            'total': total,
            'documented': documented,
            'coverage': coverage
        }

# Find lowest coverage directory
if dir_stats:
    lowest_dir = min(dir_stats.items(), key=lambda x: x[1]['coverage'])
    path, stats = lowest_dir

    print(f"📉 Lowest coverage directory: '{path}'")
    print(f"  • Total functions: {stats['total']}")
    print(f"  • Documented: {stats['documented']}")
    print(f"  • Coverage: {stats['coverage']:.1f}%")

    # Print all directory stats for comparison
    print("\n📊 All directory coverage rates:")
    for path, stats in sorted(dir_stats.items(), key=lambda x: x[1]['coverage']):
        print(f"  '{path}': {stats['coverage']:.1f}% ({stats['documented']}/{stats['total']} functions)")
```

Which provides the following output:
```python
📉 Lowest coverage directory: 'codegen-backend/app/utils/github_utils/branch'
  • Total functions: 12
  • Documented: 0
  • Coverage: 0.0%
📊 All directory coverage rates:
  'codegen-backend/app/utils/github_utils/branch': 0.0% (0/12 functions)
  'codegen-backend/app/utils/slack': 14.3% (2/14 functions)
  'codegen-backend/app/modal_app/github': 18.2% (2/11 functions)
  'codegen-backend/app/modal_app/slack': 18.2% (2/11 functions)
  'codegen-backend/app/utils/github_utils/webhook': 21.4% (6/28 functions)
  'codegen-backend/app/modal_app/cron': 23.1% (3/13 functions)
  'codegen-backend/app/utils/github_utils': 23.5% (39/166 functions)
  'codegen-backend/app/codemod': 25.0% (7/28 functions)
```

## Leveraging AI for Generating Documentation

For non-trivial codebases, it can be challenging to achieve full documentation coverage.

The most efficient way to edit informative docstrings is to use [codebase.ai](/api-reference/core/Codebase#ai) to generate docstrings, then use the [set_docstring](/api-reference/core/HasBlock#set-docstring) method to update the docstring.

<Tip>Learn more about using AI in our [guides](/building-with-codegen/calling-out-to-llms).</Tip>

```python python
# Import datetime for timestamp
from datetime import datetime

# Get current timestamp
timestamp = datetime.now().strftime("%B %d, %Y")

print("📚 Generating and Updating Function Documentation")

# Process all functions in the codebase
for function in codebase.functions:
    current_docstring = function.docstring()

    if current_docstring:
        # Update existing docstring to be more descriptive
        new_docstring = codebase.ai(
            f"Update the docstring for {function.name} to be more descriptive and comprehensive.",
            target=function
        )
        new_docstring += f"\n\nUpdated on: {timestamp}"
    else:
        # Generate new docstring for function
        new_docstring = codebase.ai(
            f"Generate a comprehensive docstring for {function.name} including parameters, return type, and description.",
            target=function
        )
        new_docstring += f"\n\nCreated on: {timestamp}"

    # Set the new or updated docstring
    function.set_docstring(new_docstring)
```



## Adding Explicit Parameter Names and Types

Alternatively, you can also rely on deterministic string formatting to edit docstrings.

To add "Google-style" parameter names and types to a function docstring, you can use the following code snippet:

```python python
# Iterate through all functions in the codebase
for function in codebase.functions:
    # Skip if function already has a docstring
    if function.docstring:
        continue

    # Build parameter documentation
    param_docs = []
    for param in function.parameters:
        param_type = param.type.source if param.is_typed else "Any"
        param_docs.append(f"    {param.name} ({param_type}): Description of {param.name}")

    # Get return type if present
    return_type = function.return_type.source if function.return_type else "None"

    # Create Google-style docstring
    docstring = f\'\'\"""
    Description of {function.name}.

    Args:
{chr(10).join(param_docs)}

    Returns:
        {return_type}: Description of return value
    """\'\'\

    # Set the new docstring
    function.set_docstring(docstring)
```


---
title: "React Modernization"
sidebarTitle: "React Modernization"
icon: "react"
iconType: "brands"
description: "Modernize your React codebase with Codegen"
---

Codegen SDK provides powerful APIs for modernizing React codebases. This guide will walk you through common React modernization patterns.

Common use cases include:

- Upgrading to modern APIs, including React 18+
- Automatically memoizing components
- Converting to modern hooks
- Standardizing prop types
- Organizing components into individual files

and much more.

## Converting Class Components to Functions

Here's how to convert React class components to functional components:

```python
# Find all React class components
for class_def in codebase.classes:
    # Skip if not a React component
    if not class_def.is_jsx or "Component" not in [base.name for base in class_def.bases]:
        continue

    print(f"Converting {class_def.name} to functional component")

    # Extract state from constructor
    constructor = class_def.get_method("constructor")
    state_properties = []
    if constructor:
        for statement in constructor.code_block.statements:
            if "this.state" in statement.source:
                # Extract state properties
                state_properties = [prop.strip() for prop in
                    statement.source.split("{")[1].split("}")[0].split(",")]

    # Create useState hooks for each state property
    state_hooks = []
    for prop in state_properties:
        hook_name = f"[{prop}, set{prop[0].upper()}{prop[1:]}]"
        state_hooks.append(f"const {hook_name} = useState(null);")

    # Convert lifecycle methods to effects
    effects = []
    if class_def.get_method("componentDidMount"):
        effects.append("""
    useEffect(() => {
        // TODO: Move componentDidMount logic here
    }, []);
    """)

    if class_def.get_method("componentDidUpdate"):
        effects.append("""
    useEffect(() => {
        // TODO: Move componentDidUpdate logic here
    });
    """)

    # Get the render method
    render_method = class_def.get_method("render")

    # Create the functional component
    func_component = f"""
const {class_def.name} = ({class_def.get_method("render").parameters[0].name}) => {{
    {chr(10).join(state_hooks)}
    {chr(10).join(effects)}

    {render_method.code_block.source}
}}
"""

    # Replace the class with the functional component
    class_def.edit(func_component)

    # Add required imports
    file = class_def.file
    if not any("useState" in imp.source for imp in file.imports):
        file.add_import("import { useState, useEffect } from 'react';")
```

## Migrating to Modern Hooks

Convert legacy patterns to modern React hooks:

```python
# Find components using legacy patterns
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Look for common legacy patterns
    for call in function.function_calls:
        # Convert withRouter to useNavigate
        if call.name == "withRouter":
            # Add useNavigate import
            function.file.add_import(
                "import { useNavigate } from 'react-router-dom';"
            )
            # Add navigate hook
            function.insert_before_first_return("const navigate = useNavigate();")
            # Replace history.push calls
            for history_call in function.function_calls:
                if "history.push" in history_call.source:
                    history_call.edit(
                        history_call.source.replace("history.push", "navigate")
                    )

        # Convert lifecycle methods in hooks
        elif call.name == "componentDidMount":
            call.parent.edit("""
useEffect(() => {
    // Your componentDidMount logic here
}, []);
""")
```

## Standardizing Props

### Inferring Props from Usage

Add proper prop types and TypeScript interfaces based on how props are used:

```python
# Add TypeScript interfaces for props
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Get props parameter
    props_param = function.parameters[0] if function.parameters else None
    if not props_param:
        continue

    # Collect used props
    used_props = set()
    for prop_access in function.function_calls:
        if f"{props_param.name}." in prop_access.source:
            prop_name = prop_access.source.split(".")[1]
            used_props.add(prop_name)

    # Create interface
    if used_props:
        interface_def = f"""
interface {function.name}Props {{
    {chr(10).join(f'    {prop}: any;' for prop in used_props)}
}}
"""
        function.insert_before(interface_def)
        # Update function signature
        function.edit(function.source.replace(
            f"({props_param.name})",
            f"({props_param.name}: {function.name}Props)"
        ))
```

### Extracting Inline Props

Convert inline prop type definitions to separate type declarations:

```python
# Iterate over all files in the codebase
for file in codebase.files:
    # Iterate over all functions in the file
    for function in file.functions:
        # Check if the function is a React functional component
        if function.is_jsx:  # Assuming is_jsx indicates a function component
            # Check if the function has inline props definition
            if len(function.parameters) == 1 and isinstance(function.parameters[0].type, Dict):
                # Extract the inline prop type
                inline_props: TSObjectType = function.parameters[0].type.source
                # Create a new type definition for the props
                props_type_name = f"{function.name}Props"
                props_type_definition = f"type {props_type_name} = {inline_props};"

                # Set the new type for the parameter
                function.parameters[0].set_type_annotation(props_type_name)
                # Add the new type definition to the file
                function.insert_before('\n' + props_type_definition + '\n')
```

This will convert components from:

```typescript
function UserCard({ name, age }: { name: string; age: number }) {
  return (
    <div>
      {name} ({age})
    </div>
  );
}
```

To:

```typescript
type UserCardProps = { name: string; age: number };

function UserCard({ name, age }: UserCardProps) {
  return (
    <div>
      {name} ({age})
    </div>
  );
}
```

<Note>
  Extracting prop types makes them reusable and easier to maintain. It also
  improves code readability by separating type definitions from component logic.
</Note>

## Updating Fragment Syntax

Modernize React Fragment syntax:

```python
for function in codebase.functions:
    if not function.is_jsx:
        continue

    # Replace React.Fragment with <>
    for element in function.jsx_elements:
        if element.name == "React.Fragment":
            element.edit(element.source.replace(
                "<React.Fragment>",
                "<>"
            ).replace(
                "</React.Fragment>",
                "</>"
            ))
```

## Organizing Components into Individual Files

A common modernization task is splitting files with multiple components into a more maintainable structure where each component has its own file. This is especially useful when modernizing legacy React codebases that might have grown organically.

```python
# Initialize a dictionary to store files and their corresponding JSX components
files_with_jsx_components = {}

# Iterate through all files in the codebase
for file in codebase.files:
    # Check if the file is in the components directory
    if 'components' not in file.filepath:
        continue

    # Count the number of JSX components in the file
    jsx_count = sum(1 for function in file.functions if function.is_jsx)

    # Only proceed if there are multiple JSX components
    if jsx_count > 1:
        # Identify non-default exported components
        non_default_components = [
            func for func in file.functions
            if func.is_jsx and not func.is_exported
        ]
        default_components = [
            func for func in file.functions
            if func.is_jsx and func.is_exported and func.export.is_default_export()
        ]

        # Log the file path and its components
        print(f"📁 {file.filepath}:")
        for component in default_components:
            print(f"  🟢 {component.name} (default)")
        for component in non_default_components:
            print(f"  🔵 {component.name}")

            # Create a new directory path based on the original file's directory
            new_dir_path = "/".join(file.filepath.split("/")[:-1]) + "/" + file.name.split(".")[0]
            codebase.create_directory(new_dir_path, exist_ok=True)

            # Create a new file path for the component
            new_file_path = f"{new_dir_path}/{component.name}.tsx"
            new_file = codebase.create_file(new_file_path)

            # Log the movement of the component
            print(f"    🫸 Moved to: {new_file_path}")

            # Move the component to the new file
            component.move_to_file(new_file, strategy="add_back_edge")
```

This script will:

1. Find files containing multiple React components
2. Create a new directory structure based on the original file
3. Move each non-default exported component to its own file
4. Preserve imports and dependencies automatically
5. Keep default exports in their original location

For example, given this structure:

```
components/
  Forms.tsx  # Contains Button, Input, Form (default)
```

It will create:

```
components/
  Forms.tsx  # Contains Form (default)
  forms/
    Button.tsx
    Input.tsx
```

<Note>
  The `strategy="add_back_edge"` parameter ensures that any components that were
  previously co-located can still import each other without circular
  dependencies. Learn more about [moving
  code](/building-with-codegen/moving-symbols) here.
</Note>



---
title: "Migrating from unittest to pytest"
sidebarTitle: "Unittest to Pytest"
description: "Learn how to migrate unittest test suites to pytest using Codegen"
icon: "vial"
iconType: "solid"
---

Migrating from [unittest](https://docs.python.org/3/library/unittest.html) to [pytest](https://docs.pytest.org/) involves converting test classes and assertions to pytest's more modern and concise style. This guide will walk you through using Codegen to automate this migration.

<Info>
You can find the complete example code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/7b978091c3153b687c32928fe10f05425e22f6a5/examples/unittest_to_pytest).
</Info>

## Overview

The migration process involves four main steps:

1. Converting test class inheritance and setup/teardown methods
2. Updating assertions to pytest style
3. Converting test discovery patterns
4. Modernizing fixture usage

Let's walk through each step using Codegen.

## Step 1: Convert Test Classes and Setup Methods

The first step is to convert unittest's class-based tests to pytest's function-based style. This includes:

- Removing `unittest.TestCase` inheritance
- Converting `setUp` and `tearDown` methods to fixtures
- Updating class-level setup methods

```python
# From:
class TestUsers(unittest.TestCase):
    def setUp(self):
        self.db = setup_test_db()

    def tearDown(self):
        self.db.cleanup()

    def test_create_user(self):
        user = self.db.create_user("test")
        self.assertEqual(user.name, "test")

# To:
import pytest

@pytest.fixture
def db():
    db = setup_test_db()
    yield db
    db.cleanup()

def test_create_user(db):
    user = db.create_user("test")
    assert user.name == "test"
```

## Step 2: Update Assertions

Next, we'll convert unittest's assertion methods to pytest's plain assert statements:

```python
# From:
def test_user_validation(self):
    self.assertTrue(is_valid_email("user@example.com"))
    self.assertFalse(is_valid_email("invalid"))
    self.assertEqual(get_user_count(), 0)
    self.assertIn("admin", get_roles())
    self.assertRaises(ValueError, parse_user_id, "invalid")

# To:
def test_user_validation():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid")
    assert get_user_count() == 0
    assert "admin" in get_roles()
    with pytest.raises(ValueError):
        parse_user_id("invalid")
```

## Step 3: Update Test Discovery

pytest uses a different test discovery pattern than unittest. We'll update the test file names and patterns:

```python
# From:
if __name__ == '__main__':
    unittest.main()

# To:
# Remove the unittest.main() block entirely
# Rename test files to test_*.py or *_test.py
```

## Step 4: Modernize Fixture Usage

Finally, we'll update how test dependencies are managed using pytest's powerful fixture system:

```python
# From:
class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_conn = create_test_db()

    def setUp(self):
        self.transaction = self.db_conn.begin()

    def tearDown(self):
        self.transaction.rollback()

# To:
@pytest.fixture(scope="session")
def db_conn():
    return create_test_db()

@pytest.fixture
def transaction(db_conn):
    transaction = db_conn.begin()
    yield transaction
    transaction.rollback()
```

## Common Patterns

Here are some common patterns you'll encounter when migrating to pytest:

1. **Parameterized Tests**

```python
# From:
def test_validation(self):
    test_cases = [("valid@email.com", True), ("invalid", False)]
    for email, expected in test_cases:
        with self.subTest(email=email):
            self.assertEqual(is_valid_email(email), expected)

# To:
@pytest.mark.parametrize("email,expected", [
    ("valid@email.com", True),
    ("invalid", False)
])
def test_validation(email, expected):
    assert is_valid_email(email) == expected
```

2. **Exception Testing**

```python
# From:
def test_exceptions(self):
    self.assertRaises(ValueError, process_data, None)
    with self.assertRaises(TypeError):
        process_data(123)

# To:
def test_exceptions():
    with pytest.raises(ValueError):
        process_data(None)
    with pytest.raises(TypeError):
        process_data(123)
```

3. **Temporary Resources**

```python
# From:
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.temp_dir)

# To:
@pytest.fixture
def temp_dir():
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)
```

## Tips and Notes

1. pytest fixtures are more flexible than unittest's setup/teardown methods:

   - They can be shared across test files
   - They support different scopes (function, class, module, session)
   - They can be parameterized

2. pytest's assertion introspection provides better error messages by default:

   ```python
   # pytest shows a detailed comparison
   assert result == expected
   ```

3. You can gradually migrate to pytest:

   - pytest can run unittest-style tests
   - Convert one test file at a time
   - Start with assertion style updates before moving to fixtures

4. Consider using pytest's built-in fixtures:
   - `tmp_path` for temporary directories
   - `capsys` for capturing stdout/stderr
   - `monkeypatch` for modifying objects
   - `caplog` for capturing log messages


---
title: "Migrating from SQLAlchemy 1.4 to 2.0"
sidebarTitle: "SQLAlchemy 1.4 to 2.0"
description: "Learn how to migrate SQLAlchemy 1.4 codebases to 2.0 using Codegen"
icon: "layer-group"
iconType: "solid"
---

Migrating from [SQLAlchemy](https://www.sqlalchemy.org/) 1.4 to 2.0 involves several API changes to support the new 2.0-style query interface. This guide will walk you through using Codegen to automate this migration, handling query syntax, session usage, and ORM patterns.

<Info>
You can find the complete example code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/7b978091c3153b687c32928fe10f05425e22f6a5/examples/sqlalchemy_1.4_to_2.0).
</Info>

## Overview

The migration process involves three main steps:

1. Converting legacy Query objects to select() statements
2. Updating session execution patterns
3. Modernizing ORM relationship declarations

Let's walk through each step using Codegen.

## Step 1: Convert Query to Select

First, we need to convert legacy Query-style operations to the new select() syntax:

```python
def convert_query_to_select(file):
    """Convert Query-style operations to select() statements"""
    for call in file.function_calls:
        if call.name == "query":
            # Convert query(Model) to select(Model)
            call.set_name("select")

            # Update method chains
            if call.parent and call.parent.is_method_chain:
                chain = call.parent
                if "filter" in chain.source:
                    # Convert .filter() to .where()
                    chain.source = chain.source.replace(".filter(", ".where(")
                if "filter_by" in chain.source:
                    # Convert .filter_by(name='x') to .where(Model.name == 'x')
                    model = call.args[0].value
                    conditions = chain.source.split("filter_by(")[1].split(")")[0]
                    new_conditions = []
                    for cond in conditions.split(","):
                        if "=" in cond:
                            key, value = cond.split("=")
                            new_conditions.append(f"{model}.{key.strip()} == {value.strip()}")
                    chain.edit(f".where({' & '.join(new_conditions)})")
```

This transforms code from:

```python
# Legacy Query style
session.query(User).filter_by(name='john').filter(User.age >= 18).all()
```

to:

```python
# New select() style
session.execute(
    select(User).where(User.name == 'john').where(User.age >= 18)
).scalars().all()
```

<Note>
  SQLAlchemy 2.0 standardizes on select() statements for all queries, providing
  better type checking and a more consistent API.
</Note>

## Step 2: Update Session Execution

Next, we update how queries are executed with the Session:

```python
def update_session_execution(file):
    """Update session execution patterns for 2.0 style"""
    for call in file.function_calls:
        if call.name == "query":
            # Find the full query chain
            chain = call
            while chain.parent and chain.parent.is_method_chain:
                chain = chain.parent

            # Wrap in session.execute() if needed
            if not chain.parent or "execute" not in chain.parent.source:
                chain.edit(f"execute(select{chain.source[5:]})")

            # Add .scalars() for single-entity queries
            if len(call.args) == 1:
                chain.edit(f"{chain.source}.scalars()")
```

This converts patterns like:

```python
# Old style
users = session.query(User).all()
first_user = session.query(User).first()
```

to:

```python
# New style
users = session.execute(select(User)).scalars().all()
first_user = session.execute(select(User)).scalars().first()
```

<Tip>
  The new execution pattern is more explicit about what's being returned, making
  it easier to understand and maintain type safety.
</Tip>

## Step 3: Update ORM Relationships

Finally, we update relationship declarations to use the new style:

```

```


---
title: "Fixing Import Loops"
description: "Learn how to identify and fix problematic import loops using Codegen."
icon: "arrows-rotate"
iconType: "solid"
---
<Frame caption="Import loops in pytorch/torchgen/model.py">
    <iframe
    width="100%"
    height="500px"
    scrolling="no"
    src={`https://www.codegen.sh/embedded/graph/?id=8b575318-ff94-41f1-94df-6e21d9de45d1&zoom=1&targetNodeName=model`}
    className="rounded-xl"
    style={{
        backgroundColor: "#15141b",
    }}
    ></iframe>
</Frame>


Import loops occur when two or more Python modules depend on each other, creating a circular dependency. While some import cycles can be harmless, others can lead to runtime errors and make code harder to maintain.

In this tutorial, we'll explore how to identify and fix problematic import cycles using Codegen.

<Info>
You can find the complete example code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/main/examples/removing_import_loops_in_pytorch).
</Info>

## Overview

The steps to identify and fix import loops are as follows:
1. Detect import loops
2. Visualize them
3. Identify problematic cycles with mixed static/dynamic imports
4. Fix these cycles using Codegen

# Step 1: Detect Import Loops
- Create a graph
- Loop through imports in the codebase and add edges between the import files
- Find strongly connected components using Networkx (the import loops)
```python
G = nx.MultiDiGraph()

# Add all edges to the graph
for imp in codebase.imports:
    if imp.from_file and imp.to_file:
        edge_color = "red" if imp.is_dynamic else "black"
        edge_label = "dynamic" if imp.is_dynamic else "static"

        # Store the import statement and its metadata
        G.add_edge(
            imp.to_file.filepath,
            imp.from_file.filepath,
            color=edge_color,
            label=edge_label,
            is_dynamic=imp.is_dynamic,
            import_statement=imp,  # Store the whole import object
            key=id(imp.import_statement),
        )
# Find strongly connected components
cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]

print(f"🔄 Found {len(cycles)} import cycles:")
for i, cycle in enumerate(cycles, 1):
    print(f"\nCycle #{i}:")
    print(f"Size: {len(cycle)} files")

    # Create subgraph for this cycle to count edges
    cycle_subgraph = G.subgraph(cycle)

    # Count total edges
    total_edges = cycle_subgraph.number_of_edges()
    print(f"Total number of imports in cycle: {total_edges}")

    # Count dynamic and static imports separately
    dynamic_imports = sum(1 for u, v, data in cycle_subgraph.edges(data=True) if data.get("color") == "red")
    static_imports = sum(1 for u, v, data in cycle_subgraph.edges(data=True) if data.get("color") == "black")

    print(f"Number of dynamic imports: {dynamic_imports}")
    print(f"Number of static imports: {static_imports}")
```


## Understanding Import Cycles

Not all import cycles are problematic! Here's an example of a cycle that one may think would cause an error but it does not because due to using dynamic imports.

```python
# top level import in in APoT_tensor.py
from quantizer.py import objectA
```

```python
# dynamic import in quantizer.py
def some_func():
    # dynamic import (evaluated when some_func() is called)
    from APoT_tensor.py import objectB
```

<img src="/images/valid-import-loop.png" />

A dynamic import is an import defined inside of a function, method or any executable body of code which delays the import execution until that function, method or body of code is called.

You can use `imp.is_dynamic` to check if the import is dynamic allowing you to investigate imports that are handled more intentionally.

# Step 2: Visualize Import Loops
- Create a new subgraph to visualize one cycle
- color and label the edges based on their type (dynamic/static)
- visualize the cycle graph using `codebase.visualize(graph)`

```python
cycle = cycles[0]

def create_single_loop_graph(cycle):
    cycle_graph = nx.MultiDiGraph()  # Changed to MultiDiGraph to support multiple edges
    cycle = list(cycle)
    for i in range(len(cycle)):
        for j in range(len(cycle)):
            # Get all edges between these nodes from original graph
            edge_data_dict = G.get_edge_data(cycle[i], cycle[j])
            if edge_data_dict:
                # For each edge between these nodes
                for edge_key, edge_data in edge_data_dict.items():
                    # Add edge with all its attributes to cycle graph
                    cycle_graph.add_edge(cycle[i], cycle[j], **edge_data)
    return cycle_graph


cycle_graph = create_single_loop_graph(cycle)
codebase.visualize(cycle_graph)
```

<Frame caption="Import loops in pytorch/torchgen/model.py">
    <iframe
    width="100%"
    height="500px"
    scrolling="no"
    src={`https://www.codegen.sh/embedded/graph/?id=8b575318-ff94-41f1-94df-6e21d9de45d1&zoom=1&targetNodeName=model`}
    className="rounded-xl"
    style={{
        backgroundColor: "#15141b",
    }}
    ></iframe>
</Frame>


# Step 3: Identify problematic cycles with mixed static & dynamic imports

The import loops that we are really concerned about are those that have mixed static/dynamic imports.

Here's an example of a problematic cycle that we want to fix:

```python
# In flex_decoding.py
from .flex_attention import (
    compute_forward_block_mn,
    compute_forward_inner,
    # ... more static imports
)

# Also in flex_decoding.py
def create_flex_decoding_kernel(*args, **kwargs):
    from .flex_attention import set_head_dim_values  # dynamic import
```

It's clear that there is both a top level and a dynamic import that imports from the *same* module. Thus, this can cause issues if not handled carefully.

<img src="/images/problematic-import-loop.png" />

Let's find these problematic cycles:

```python
def find_problematic_import_loops(G, sccs):
    """Find cycles where files have both static and dynamic imports between them."""
    problematic_cycles = []

    for i, scc in enumerate(sccs):
        if i == 2:  # skipping the second import loop as it's incredibly long (it's also invalid)
            continue
        mixed_import_files = {}  # (from_file, to_file) -> {dynamic: count, static: count}

        # Check all file pairs in the cycle
        for from_file in scc:
            for to_file in scc:
                if G.has_edge(from_file, to_file):
                    # Get all edges between these files
                    edges = G.get_edge_data(from_file, to_file)

                    # Count imports by type
                    dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
                    static_count = sum(1 for e in edges.values() if e["color"] == "black")

                    # If we have both types between same files, this is problematic
                    if dynamic_count > 0 and static_count > 0:
                        mixed_import_files[(from_file, to_file)] = {"dynamic": dynamic_count, "static": static_count, "edges": edges}

        if mixed_import_files:
            problematic_cycles.append({"files": scc, "mixed_imports": mixed_import_files, "index": i})

    # Print findings
    print(f"Found {len(problematic_cycles)} cycles with mixed imports:")
    for i, cycle in enumerate(problematic_cycles):
        print(f"\n⚠️  Problematic Cycle #{i + 1}:")
        print(f"\n⚠️  Index #{cycle['index']}:")
        print(f"Size: {len(cycle['files'])} files")

        for (from_file, to_file), data in cycle["mixed_imports"].items():
            print("\n📁 Mixed imports detected:")
            print(f"  From: {from_file}")
            print(f"  To:   {to_file}")
            print(f"  Dynamic imports: {data['dynamic']}")
            print(f"  Static imports: {data['static']}")

    return problematic_cycles

problematic_cycles = find_problematic_import_loops(G, cycles)
```

# Step 4: Fix the loop by moving the shared symbols to a separate `utils.py` file
One common fix to this problem to break this cycle is to move all the shared symbols to a separate `utils.py` file. We can do this using the method `symbol.move_to_file`:

```python
# Create new utils file
utils_file = codebase.create_file("torch/_inductor/kernel/flex_utils.py")

# Get the two files involved in the import cycle
decoding_file = codebase.get_file("torch/_inductor/kernel/flex_decoding.py")
attention_file = codebase.get_file("torch/_inductor/kernel/flex_attention.py")
attention_file_path = "torch/_inductor/kernel/flex_attention.py"
decoding_file_path = "torch/_inductor/kernel/flex_decoding.py"

# Track symbols to move
symbols_to_move = set()

# Find imports from flex_attention in flex_decoding
for imp in decoding_file.imports:
    if imp.from_file and imp.from_file.filepath == attention_file_path:
        # Get the actual symbol from flex_attention
        if imp.imported_symbol:
            symbols_to_move.add(imp.imported_symbol)

# Move identified symbols to utils file
for symbol in symbols_to_move:
    symbol.move_to_file(utils_file)

print(f"🔄 Moved {len(symbols_to_move)} symbols to flex_utils.py")
for symbol in symbols_to_move:
    print(symbol.name)
```

```python
# run this command to have the changes take effect in the codebase
codebase.commit()
```

Next Steps
Verify all tests pass after the migration and fix other problematic import loops using the suggested strategies:
    1. Move the shared symbols to a separate file
    2. If a module needs imports only for type hints, consider using `if TYPE_CHECKING` from the `typing` module
    3. Use lazy imports using `importlib` to load imports dynamically

---
title: "Migrating from Python 2 to Python 3"
sidebarTitle: "Python 2 to 3"
description: "Learn how to migrate Python 2 codebases to Python 3 using Codegen"
icon: "snake"
iconType: "solid"
---

Migrating from Python 2 to Python 3 involves several syntax and API changes. This guide will walk you through using Codegen to automate this migration, handling print statements, string handling, iterators, and more.

<Info>
You can find the complete example code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/7b978091c3153b687c32928fe10f05425e22f6a5/examples/python2_to_python3).
</Info>

## Overview

The migration process involves five main steps:

1. Converting print statements to function calls
2. Updating Unicode to str
3. Converting raw_input to input
4. Updating exception handling syntax
5. Modernizing iterator methods

Let's walk through each step using Codegen.

## Step 1: Convert Print Statements

First, we need to convert Python 2's print statements to Python 3's print function calls:

```python
def convert_print_statements(file):
    """Convert Python 2 print statements to Python 3 function calls"""
    lines = file.content.split('\n')
    new_content = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('print '):
            indent = line[:len(line) - len(line.lstrip())]
            args = stripped[6:].strip()
            new_content.append(f"{indent}print({args})")
        else:
            new_content.append(line)

    if new_content != lines:
        file.edit('\n'.join(new_content))
```

This transforms code from:

```python
print "Hello, world!"
print x, y, z
```

to:

```python
print("Hello, world!")
print(x, y, z)
```

<Note>
  In Python 3, `print` is a function rather than a statement, requiring
  parentheses around its arguments.
</Note>

## Step 2: Update Unicode to str

Next, we update Unicode-related code to use Python 3's unified string type:

```python
def update_unicode_to_str(file):
    """Convert Unicode-related code to str for Python 3"""
    # Update imports from 'unicode' to 'str'
    for imp in file.imports:
        if imp.name == 'unicode':
            imp.set_name("str")

    # Update function calls from Unicode to str
    for func_call in file.function_calls:
        if func_call.name == "unicode":
            func_call.set_name("str")

        # Check function arguments for Unicode references
        for arg in func_call.args:
            if arg.value == "unicode":
                arg.set_value("str")

    # Find and update Unicode string literals (u"...")
    for string_literal in file.find('u"'):
        if string_literal.source.startswith('u"') or string_literal.source.startswith("u'"):
            new_string = string_literal.source[1:]  # Remove the 'u' prefix
            string_literal.edit(new_string)
```

This converts code from:

```python
from __future__ import unicode_literals
text = unicode("Hello")
prefix = u"prefix"
```

to:

```python
text = str("Hello")
prefix = "prefix"
```

<Note>
  Python 3 unifies string types, making the `unicode` type and `u` prefix
  unnecessary.
</Note>

## Step 3: Convert raw_input to input

Python 3 renames `raw_input()` to `input()`:

```python
def convert_raw_input(file):
    """Convert raw_input() calls to input()"""
    for call in file.function_calls:
        if call.name == "raw_input":
            call.edit(f"input{call.source[len('raw_input'):]}")
```

This updates code from:

```python
name = raw_input("Enter your name: ")
```

to:

```python
name = input("Enter your name: ")
```

<Tip>
  Python 3's `input()` function always returns a string, like Python 2's
  `raw_input()`.
</Tip>

## Step 4: Update Exception Handling

Python 3 changes the syntax for exception handling:

```python
def update_exception_syntax(file):
    """Update Python 2 exception handling to Python 3 syntax"""
    for editable in file.find("except "):
        if editable.source.lstrip().startswith("except") and ", " in editable.source and " as " not in editable.source:
            parts = editable.source.split(",", 1)
            new_source = f"{parts[0]} as{parts[1]}"
            editable.edit(new_source)
```

This converts code from:

```python
try:
    process_data()
except ValueError, e:
    print(e)
```

to:

```python
try:
    process_data()
except ValueError as e:
    print(e)
```

<Note>
  Python 3 uses `as` instead of a comma to name the exception variable.
</Note>

## Step 5: Update Iterator Methods

Finally, we update iterator methods to use Python 3's naming:

```python
def update_iterators(file):
    """Update iterator methods from Python 2 to Python 3"""
    for cls in file.classes:
        next_method = cls.get_method("next")
        if next_method:
            # Create new __next__ method with same content
            new_method_source = next_method.source.replace("def next", "def __next__")
            cls.add_source(new_method_source)
            next_method.remove()
```

This transforms iterator classes from:

```python
class MyIterator:
    def next(self):
        return self.value
```

to:

```python
class MyIterator:
    def __next__(self):
        return self.value
```

<Note>
  Python 3 renames the `next()` method to `__next__()` for consistency with
  other special methods.
</Note>

## Running the Migration

You can run the complete migration using our example script:

```bash
git clone https://github.com/codegen-sh/codegen-examples.git
cd codegen-examples/python2_to_python3
python run.py
```

The script will:

1. Process all Python [files](/api-reference/python/PyFile) in your codebase
2. Apply the transformations in the correct order
3. Maintain your code's functionality while updating to Python 3 syntax

## Next Steps

After migration, you might want to:

- Add type hints to your code
- Use f-strings for string formatting
- Update dependencies to Python 3 versions
- Run the test suite to verify functionality

Check out these related tutorials:

- [Increase Type Coverage](/tutorials/increase-type-coverage)
- [Organizing Your Codebase](/tutorials/organize-your-codebase)
- [Creating Documentation](/tutorials/creating-documentation)

## Learn More

- [Python 3 Documentation](https://docs.python.org/3/)
- [What's New in Python 3](https://docs.python.org/3/whatsnew/3.0.html)
- [Codegen API Reference](/api-reference)
- [Dependencies and Usages](/building-with-codegen/dependencies-and-usages)


---
title: "Migrating from Flask to FastAPI"
sidebarTitle: "Flask to FastAPI"
icon: "bolt"
iconType: "solid"
---

Migrating from [Flask](https://flask.palletsprojects.com/) to [FastAPI](https://fastapi.tiangolo.com/) involves several key changes to your codebase. This guide will walk you through using Codegen to automate this migration, handling imports, route decorators, static files, and template rendering.

You can find the complete example code in our [examples repository](https://github.com/codegen-sh/codegen-examples/tree/7b978091c3153b687c32928fe10f05425e22f6a5/examples/flask_to_fastapi_migration)

## Overview

The migration process involves four main steps:

1. Updating imports and initialization
2. Converting route decorators
3. Setting up static file handling
4. Updating template handling

Let's walk through each step using Codegen.

## I: Update Imports and Initialization

First, we need to update Flask imports to their FastAPI equivalents and modify the app initialization:

<Tip>
  Learn more about [imports here](/building-with-codegen/imports).
</Tip>

```python
from codegen import Codebase

# Parse the codebase
codebase = Codebase("./")

# Update imports and initialization
for file in codebase.files:
    # Update Flask to FastAPI imports
    for imp in file.imports:
        if imp.name == "Flask":
            imp.set_name("FastAPI")
        elif imp.module == "flask":
            imp.set_module("fastapi")

    # Update app initialization
    for call in file.function_calls:
        if call.name == "Flask":
            call.set_name("FastAPI")
            # Remove __name__ argument (not needed in FastAPI)
            if len(call.args) > 0 and call.args[0].value == "__name__":
                call.args[0].remove()
```

This transforms code from:

```python
from flask import Flask
app = Flask(__name__)
```

to:

```python
from fastapi import FastAPI
app = FastAPI()
```

<Note>
  FastAPI doesn't require the `__name__` argument that Flask uses for template
  resolution. Codegen automatically removes it during migration.
</Note>

## II: Convert Route Decorators

Next, we update Flask's route decorators to FastAPI's operation decorators:

```python
for function in file.functions:
    for decorator in function.decorators:
        if "@app.route" in decorator.source:
            route = decorator.source.split('"')[1]
            method = "get"  # Default to GET
            if "methods=" in decorator.source:
                methods = decorator.source.split("methods=")[1].split("]")[0]
                if "post" in methods.lower():
                    method = "post"
                elif "put" in methods.lower():
                    method = "put"
                elif "delete" in methods.lower():
                    method = "delete"
            decorator.edit(f'@app.{method}("{route}")')
```

This converts decorators from Flask style:

```python
@app.route("/users", methods=["POST"])
def create_user():
    pass
```

to FastAPI style:

```python
@app.post("/users")
def create_user():
    pass
```

<Tip>
  FastAPI provides specific decorators for each HTTP method, making the API more
  explicit and enabling better type checking and OpenAPI documentation.
</Tip>

## III: Setup Static Files

FastAPI handles static files differently than Flask. We need to add the StaticFiles mounting:

```python
# Add StaticFiles import
file.add_import("from fastapi.staticfiles import StaticFiles")

# Mount static directory
file.add_symbol_from_source(
    'app.mount("/static", StaticFiles(directory="static"), name="static")'
)
```

This sets up static file serving equivalent to Flask's automatic static file handling.

<Note>
  FastAPI requires explicit mounting of static directories, which provides more
  flexibility in how you serve static files.
</Note>

## IV: Update Template Handling

Finally, we update the template rendering to use FastAPI's Jinja2Templates:

```python
for func_call in file.function_calls:
    if func_call.name == "render_template":
        # Convert to FastAPI's template response
        func_call.set_name("Jinja2Templates(directory='templates').TemplateResponse")
        if len(func_call.args) > 1:
            # Convert template variables to context dict
            context_arg = ", ".join(
                f"{arg.name}={arg.value}" for arg in func_call.args[1:]
            )
            func_call.set_kwarg("context", f"{'{'}{context_arg}{'}'}")
        # Add required request parameter
        func_call.set_kwarg("request", "request")
```

This transforms template rendering from Flask style:

```python
@app.get("/users")
def list_users():
    return render_template("users.html", users=users)
```

to FastAPI style:

```python
@app.get("/users")
def list_users(request: Request):
    return Jinja2Templates(directory="templates").TemplateResponse(
        "users.html",
        context={"users": users},
        request=request
    )
```

<Note>
  FastAPI requires the `request` object to be passed to templates. Codegen
  automatically adds this parameter during migration.
</Note>

## Running the Migration

You can run the complete migration using our example script:

```bash
git clone https://github.com/codegen-sh/codegen-examples.git
cd codegen-examples/flask_to_fastapi_migration
python run.py
```

The script will:

1. Process all Python [files](/api-reference/python/PyFile) in your codebase
2. Apply the transformations in the correct order
3. Maintain your code's functionality while updating to FastAPI patterns

## Next Steps

After migration, you might want to:

- Add type hints to your route parameters
- Set up dependency injection
- Add request/response models
- Configure CORS and middleware

Check out these related tutorials:

- [Increase Type Coverage](/tutorials/increase-type-coverage)
- [Managing TypeScript Exports](/tutorials/managing-typescript-exports)
- [Organizing Your Codebase](/tutorials/organize-your-codebase)

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Codegen API Reference](/api-reference)
- [Moving Symbols Guide](/building-with-codegen/moving-symbols)
- [Dependencies and Usages](/building-with-codegen/dependencies-and-usages)
'''
