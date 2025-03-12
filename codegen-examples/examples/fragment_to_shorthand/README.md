# Transform React Fragment to Shorthand Syntax

This example demonstrates how to use Codegen to automatically convert React Fragment components to the shorthand syntax (\<>). The script makes this process simple by handling all the tedious manual updates automatically.

> [!NOTE]
> This codemod helps modernize React codebases by using the more concise fragment syntax while maintaining functionality.

## How the Migration Script Works

The script automates the entire conversion process in a few key steps:

1. **Fragment Detection**

   ```jsx
   // From:
   <Fragment>
     <div>Hello</div>
     <div>World</div>
   </Fragment>

   // To:
   <>
     <div>Hello</div>
     <div>World</div>
   </>
   ```

1. **Import Cleanup**

   ```typescript
   // From:
   import React, { Fragment } from 'react';

   // To:
   import React from 'react';
   ```

## Why This Makes Migration Easy

1. **Zero Manual Updates**

   - Codegen SDK handles all Fragment replacements
   - Automatically cleans up imports

1. **Consistent Changes**

   - Ensures all Fragments are converted
   - Maintains code functionality

1. **Safe Transformations**

   - Preserves JSX structure
   - Handles nested Fragments correctly

## Running the Migration

The script will:

1. Find all Fragment components
1. Convert them to shorthand syntax
1. Clean up Fragment imports
1. Preserve other React imports

## Learn More

- [React Fragments](https://react.dev/reference/react/Fragment)
- [JSX Fragments](https://react.dev/reference/jsx#jsx-fragments)
- [Codegen Documentation](https://docs.codegen.com)
- [More on Codegen SDK jsx elements API](https://docs.codegen.com/api-reference/typescript/JSXElement#jsxelement)

## Contributing

Feel free to submit issues and enhancement requests!
