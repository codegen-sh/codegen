# Codemods

This directory contains scripts for automated code modifications (codemods).

## Available Codemods

### Remove Empty Presenter Parameters

The `remove_empty_presenter_params.py` script finds all usages of the `usePresenter` function and removes the second parameter when it's an empty object (`{}`).

#### Usage

```bash
# Run in dry-run mode (doesn't modify files, just shows what would change)
python scripts/codemods/remove_empty_presenter_params.py --dry-run

# Run and apply changes
python scripts/codemods/remove_empty_presenter_params.py
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
