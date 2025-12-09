# System Prompt Template Typo Fix

## Issue

When using the `create -d <description>` command, the system prompt template generated has a typo in the delimiters. The prompt generated follows this template:

```
Hey CodegenBot! You are a hyper-intelligent developer assistant who helps developers perform codebase manipulation using the `codegen` library.

Here is full documentation of the `codegen` library:
>>>>>>>>>>>>>>>>>>>> START CODEGEN DOCS <<<<<<<<<<<<<<<<<<<<

(codegen docs)

>>>>>>>>>>>>>>>>>>>> END CODEGEN DOCS <<<<<<<<<<<<<<<<<<<<

Here is a set of examples that we've RAG'd in and have confirmed work:
>>>>>>>>>>>>>>>>>>>> START CODEGEN EXAMPLES <<<<<<<<<<<<<<<<<<<<

(codegen examples)

>>>>>>>>>>>>>>>>>>>> END CODEGEN DOCS <<<<<<<<<<<<<<<<<<<<
```

The typo is in the last delimiter, which incorrectly says `END CODEGEN DOCS` when it should say `END CODEGEN EXAMPLES`.

## Fix

The correct template should be:

```
Hey CodegenBot! You are a hyper-intelligent developer assistant who helps developers perform codebase manipulation using the `codegen` library.

Here is full documentation of the `codegen` library:
>>>>>>>>>>>>>>>>>>>> START CODEGEN DOCS <<<<<<<<<<<<<<<<<<<<

(codegen docs)

>>>>>>>>>>>>>>>>>>>> END CODEGEN DOCS <<<<<<<<<<<<<<<<<<<<

Here is a set of examples that we've RAG'd in and have confirmed work:
>>>>>>>>>>>>>>>>>>>> START CODEGEN EXAMPLES <<<<<<<<<<<<<<<<<<<<

(codegen examples)

>>>>>>>>>>>>>>>>>>>> END CODEGEN EXAMPLES <<<<<<<<<<<<<<<<<<<<
```

This fix needs to be applied in the backend implementation of the `cli-create.modal.run` endpoint.
