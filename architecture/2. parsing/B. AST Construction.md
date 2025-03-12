# AST Construction

The tree-sitter CST/AST is powerful but it focuses on syntax highlighting and not semantic meaning.
For example, take decorators:

```python
@decorator
def my_function():
    pass
```

```
module [0, 0] - [3, 0]
  decorated_definition [0, 0] - [2, 8]
    decorator [0, 0] - [0, 10]
      identifier [0, 1] - [0, 10]
    definition: function_definition [1, 0] - [2, 8]
      name: identifier [1, 4] - [1, 15]
      parameters: parameters [1, 15] - [1, 17]
      body: block [2, 4] - [2, 8]
        pass_statement [2, 4] - [2, 8]

```

You can see the decorated_definition node has a decorator and a definition. This makes sense for syntax highlighting - the decorator is highlighted seperately from the function definition.

However, this is not useful for semantic analysis. We need to know that the decorator is decorating the function definition - there is a single function definition which may contain multiple decorators.
This becomes visibile when we consider function call chains:

```python
a().b().c().d()
```

```
module [0, 0] - [2, 0]
  expression_statement [0, 0] - [0, 15]
    call [0, 0] - [0, 15]
      function: attribute [0, 0] - [0, 13]
        object: call [0, 0] - [0, 11]
          function: attribute [0, 0] - [0, 9]
            object: call [0, 0] - [0, 7]
              function: attribute [0, 0] - [0, 5]
                object: call [0, 0] - [0, 3]
                  function: identifier [0, 0] - [0, 1]
                  arguments: argument_list [0, 1] - [0, 3]
                attribute: identifier [0, 4] - [0, 5]
              arguments: argument_list [0, 5] - [0, 7]
            attribute: identifier [0, 8] - [0, 9]
          arguments: argument_list [0, 9] - [0, 11]
        attribute: identifier [0, 12] - [0, 13]
      arguments: argument_list [0, 13] - [0, 15]
```

You can see that the chain of calls is represented as a deeply nested structure. This is not useful for semantic analysis or performing edits on these nodes. Therefore, when parsing we need to build an AST that is more useful for semantic analysis.

## Implementation

- For each file, we parse a file-specific AST
- We offer two modes of parsing:
  - Pattern based parsing: It maps a particular node type to a semantic node type. For example, we broadly map all identifiers to the `Name` node type.
  - Custom parsing: It takes a CST and builds a custom node type. For example, we can turn a decorated_definition node into a function_definition node with decorators. This involves careful arranging of the CST nodes into a new structure.

## Pattern based parsing

To do this, we need to build a mapping between the tree-sitter node types and our semantic node types. These mappings are language specific and stored in node_classes. They are processed by parser.py at runtime. We can access these via many functions - child_by_field_name, \_parse_expression, etc. These methods both wrap the tree-sitter methods and parse the tree-sitter node into our semantic node.

## Custom parsing

These are more complex and require more work. Most symbols (classes, functions, etc), imports, exports, and other complex constructs are parsed using custom parsing.

## Statement parsing

Statements have another layer of complexity. They are essentially pattern based but the mapping and logic is defined directly in the parser.py file.

## Next Step

After the AST is constructed, the system moves on to [Directory Parsing](./C.%20Directory%20Parsing.md) to build a hierarchical representation of the codebase's directory structure.
