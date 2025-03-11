# Dependency Manager

> WARNING: Dependency manager is an experimental feature designed for Codegen Cloud! The current implementation WILL delete any existing `node_modules` folder!

## Motivation

A future goal of Codegen is to support resolving symbols directly from dependencies, instead of falling back to `ExternalModule`s. (In fact, some experimental Codegen features such as [Type Engine](./type-engine.md) already parse and use 3rd party dependencies from `node_modules`)

This requires us to pull and install dependencies from a repository's `package.json`. However, simply installing dependencies from `package.json` is not enough, as many projects require internal dependencies that use custom NPM registries. Others require custom post-install scripts that may not run on our codemod environments.

Dependency Manager is an experimental solution to this problem. It creates a shadow tree of `package.json` files that includes all core dependencies and settings from the repository's original `package.json` without any custom registries or potentially problematic settings.

> NOTE: Currently, this is only implemented for TypeScript projects.

## Implementation

Given this example codebase structure:

```
repo/
├── package.json
├── node_modules/
├── src/
│   ├── frontend/
│   │   └── package.json
│   └── backend/
│       └── package.json
└── tests/
    └── package.json
```

Dependency Manager first deletes any existing `node_modules` folder in the user's repository. After this step, Dependency Manager initializes itself to use the correct version of NPM, Yarn, or PNPM for the user's repository.

Dependency Manager then creates a "shadow copy" of the repository's original `package.json` file. This shadow copy is used to later revert any changes made by Codegen before running codemods. With these steps, the codebase structure now looks like this:

```
repo/
├── package.json
├── package.json.gs_internal.bak
├── src/
│   ├── frontend/
│   │   └── package.json
│   │   └── package.json.gs_internal.bak
│   └── backend/
│       └── package.json
│       └── package.json.gs_internal.bak
└── tests/
    └── package.json
    └── package.json.gs_internal.bak
```

Next, Dependency Manager iterates through all the `package.json` files and creates a "clean" version of each file. This "clean" version only includes a subset of information from the original, including:

- Name
- Version
- Package Manager Details
- Workspaces

Most importantly, this step iterates through `dependencies` and `devDependencies` of each `package.json` file and validates them against the npm registry. If a package is not found, it is added to a list of invalid dependencies and removed from the `package.json` file.

After this step, the codebase structure now looks like this:

```
repo/
├── package.json (modified)
├── package.json.gs_internal.bak
├── src/
│   ├── frontend/
│   │   └── package.json (modified)
│   │   └── package.json.gs_internal.bak
│   └── backend/
│       └── package.json (modified)
│       └── package.json.gs_internal.bak
└── tests/
    └── package.json (modified)
    └── package.json.gs_internal.bak
```

After the shadow and cleaning steps, Dependency Manager proceeds to install the user's dependencies through NPM, Yarn, or PNPM, depending on the detected installer type. Finally, Dependency Manager restores the original `package.json` files and removes the shadow copies.

The final codebase structure looks like this:

```
repo/
├── package.json
├── node_modules/
├── src/
│   ├── frontend/
│   │   └── package.json
│   └── backend/
│       └── package.json
└── tests/
    └── package.json
```

If all goes well, Dependency Manager will have successfully installed the user's dependencies and prepared the codebase for codemods.

## Next Step

The dependency manager works closely with the [Type Engine](./type-engine.md) to ensure type compatibility across dependencies.
