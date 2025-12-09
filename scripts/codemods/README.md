# Codegen Codemods

This directory contains codemod scripts that can be used to automate code transformations using the Codegen SDK.

## Available Codemods

### Remove Empty usePresenter Parameters

**Script**: `remove_empty_presenter_params.py`

This codemod finds all usages of `usePresenter` where the second argument is an empty object (`{}`) and removes that parameter.

#### Usage

```bash
# Navigate to your project root
cd your-project-root

# Run the script
python scripts/codemods/remove_empty_presenter_params.py
```

#### What it does

The script:

1. Searches for all function calls to `usePresenter` in your codebase
1. Identifies calls where the second argument is an empty object (`{}`)
1. Removes the empty object parameter
1. Commits the changes to your files

#### Example Transformation

Before:

```javascript
const presenter = usePresenter(someValue, {});
```

After:

```javascript
const presenter = usePresenter(someValue);
```

#### Configuration

By default, the script is configured for TypeScript/JavaScript codebases. If your project uses a different language, you can modify the language parameter in the script:

```python
# Change "typescript" to your project's language
codebase = Codebase("./", language="typescript")
```
