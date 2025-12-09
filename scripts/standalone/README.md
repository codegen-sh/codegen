# Standalone Scripts

This directory contains standalone scripts that don't rely on the Codegen SDK. These scripts can be used in any codebase without additional dependencies.

## Available Scripts

### Remove Empty Presenter Parameters

The `remove_empty_presenter_params.py` script finds all usages of the `usePresenter` function and removes the second parameter when it's an empty object (`{}`).

#### Usage

```bash
# Run in dry-run mode (doesn't modify files, just shows what would change)
python scripts/standalone/remove_empty_presenter_params.py --dry-run

# Run and apply changes
python scripts/standalone/remove_empty_presenter_params.py
```

#### What it does

This script:

1. Searches for all JavaScript and TypeScript files in your codebase
1. Finds all calls to `usePresenter` where the second parameter is an empty object (`{}`)
1. Removes the empty object parameter while preserving the rest of the function call
1. Reports all changes made

#### Examples

Before:

```javascript
const presenter = usePresenter(data, {});
```

After:

```javascript
const presenter = usePresenter(data);
```

Before:

```javascript
const presenter = usePresenter(data, {}, options);
```

After:

```javascript
const presenter = usePresenter(data, options);
```

#### How it works

The script uses regular expressions to find and modify `usePresenter` calls. It handles various forms of empty objects, including those with whitespace and comments. The script is designed to be lightweight and doesn't require any external dependencies beyond the Python standard library.
