# Type Engine

Type Engine is an experimental feature of Codegen that leverages the [TypeScript Compiler API](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API) to provide deeper insight into a user's codebase (such as resolving return types).

> NOTE: Currently, this is only implemented for TypeScript projects.

There are currently two experimental implementations of TypeScript's Type Engine: an external process-based implementation and a V8-based implementation.

## Implementation (External Process)

During codebase parsing, the Type Engine spawns a type inference subprocess (defined in `src/codegen/sdk/typescript/external/typescript_analyzer/run_full.ts`) that concurrently parses the codebase with the TypeScript API to resolve return types. The final analyzer output is placed in `/tmp/typescript-analysis.json` and is read in by Codegen to resolve return types.

## Implementation (V8)

The V8-based implementation is much more flexible and powerful in comparison but is currently not as stable. It uses the [PyMiniRacer](https://github.com/sqreen/py_mini_racer) package to spawn a V8-based JavaScript engine that can parse the codebase with the TypeScript API to resolve return types.

The entirety of `src/codegen/sdk/typescript/external/typescript_analyzer` is compiled down using [Rollup.js](https://rollupjs.org/) into a single `index.js` file. A couple of patches are applied to the engine source to remove `require` and `export` statements, which are not supported by MiniRacer.

Then, the entire `index.js` file is loaded into the MiniRacer context. To work around file read limitations with V8, an in-memory shadow filesystem is created that mimics the user's repository's filesystem. These are defined in `fsi.ts` (`FileSystemInterface`) and `fs_proxy.ts` (`ProxyFileSystem`). The TypeScript Compiler then uses the custom `ProxyFileSystem.readFile` function instead of the traditional `fs.readFile`.

Once the analyzer is initialized and the codebase is parsed, the entire TypeScript Compiler API is available in the MiniRacer context. The analyzer can then be used to resolve return types for any function in the codebase or to parse the codebase and generate a full type analysis.

## Next Step

The type engine works in conjunction with the [Dependency Manager](./dependency-manager.md) to ensure type safety across project dependencies.
