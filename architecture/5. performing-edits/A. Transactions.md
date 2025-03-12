# Transactions

Transactions represent atomic changes to files in the codebase. Each transaction defines a specific modification that can be queued, validated, and executed.

## Transaction Types

The transaction system is built around a base `Transaction` class with specialized subclasses:

### Content Transactions

- **RemoveTransaction**: Removes content between specified byte positions
- **InsertTransaction**: Inserts new content at a specified byte position
- **EditTransaction**: Replaces content between specified byte positions

### File Transactions

- **FileAddTransaction**: Creates a new file
- **FileRenameTransaction**: Renames an existing file
- **FileRemoveTransaction**: Deletes a file

## Transaction Priority

Transactions are executed in a specific order defined by the `TransactionPriority` enum:

1. **Remove** (highest priority)
1. **Edit**
1. **Insert**
1. **FileAdd**
1. **FileRename**
1. **FileRemove**

This ordering ensures that content is removed before editing or inserting, and that all content operations happen before file operations.

## Key Concepts

### Byte-Level Operations

All content transactions operate at the byte level rather than on lines or characters. This provides precise control over modifications and allows transactions to work with any file type, regardless of encoding or line ending conventions.

### Content Generation

Transactions support both static content (direct strings) and dynamic content (generated at execution time). This flexibility allows for complex transformations where the new content depends on the state of the codebase at execution time.

Most content transactions use static content, but dynamic content is supported for rare cases where the new content depends on the state of other transactions. One common example is handling whitespace during add and remove transactions.

### File Operations

File transactions are used to create, rename, and delete files.

> NOTE: It is important to note that most file transactions such as `FileAddTransaction` are no-ops (AKA skiping Transaction Manager) and instead applied immediately once the `create_file` API is called. This allows for created files to be immediately available for edit and use. The reason file operations are still added to Transaction Manager is to help with optimizing graph re-parse and diff generation. (Keeping track of which files exist and don't exist anymore).

## Next Step

After understanding the transaction system, they are managed by the [Transaction Manager](./B.%20Transaction%20Manager.md) to ensure consistency and atomicity.
