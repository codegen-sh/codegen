# SQLAlchemy Soft Delete Codemod

This codemod automatically adds soft delete conditions to SQLAlchemy join queries in your codebase. It ensures that joins only include non-deleted records by adding appropriate `deleted_at` checks.

## Overview

The codemod analyzes your codebase and automatically adds soft delete conditions to SQLAlchemy join methods (`join`, `outerjoin`, `innerjoin`) for specified models. This helps prevent accidentally including soft-deleted records in query results.

## How It Works

The codemod processes your codebase in several steps:

1. **Join Detection**

   ```python
   def should_process_join_call(call, soft_delete_models, join_methods):
       if str(call.name) not in join_methods:
           return False

       call_args = list(call.args)
       if not call_args:
           return False

       model_name = str(call_args[0].value)
       return model_name in soft_delete_models
   ```

   - Scans for SQLAlchemy join method calls (`join`, `outerjoin`, `innerjoin`)
   - Identifies joins involving soft-deletable models
   - Analyzes existing join conditions

1. **Condition Addition**

   ```python
   def add_deleted_at_check(file, call, model_name):
       call_args = list(call.args)
       deleted_at_check = f"{model_name}.deleted_at.is_(None)"

       if len(call_args) == 1:
           call_args.append(deleted_at_check)
           return

       second_arg = call_args[1].value
       if isinstance(second_arg, FunctionCall) and second_arg.name == "and_":
           second_arg.args.append(deleted_at_check)
       else:
           call_args[1].edit(f"and_({second_arg.source}, {deleted_at_check})")
   ```

   - Adds `deleted_at.is_(None)` checks to qualifying joins
   - Handles different join condition patterns:
     - Simple joins with no conditions
     - Joins with existing conditions (combines using `and_`)
   - Preserves existing conditions while adding soft delete checks

1. **Import Management**

   ```python
   def ensure_and_import(file):
       if not any("and_" in imp.name for imp in file.imports):
           file.add_import_from_import_string("from sqlalchemy import and_")
   ```

   - Automatically adds required SQLAlchemy imports (`and_`)
   - Prevents duplicate imports

## Configuration

### Soft Delete Models

The codemod processes joins for the following models:

```python
soft_delete_models = {"User", "Update", "Proposal", "Comment", "Project", "Team", "SavedSession"}
```

### Join Methods

The codemod handles these SQLAlchemy join methods:

```python
join_methods = {"join", "outerjoin", "innerjoin"}
```

## Code Transformations

### Simple Join with Model Reference

```python
# Before
query.join(Project, Session.project)

# After
from sqlalchemy import and_

query.join(Project, and_(Session.project, Project.deleted_at.is_(None)))
```

### Join with Column Equality

```python
# Before
query.join(Project, Session.project_id == Project.id)

# After
from sqlalchemy import and_

query.join(Project, and_(Session.project_id == Project.id, Project.deleted_at.is_(None)))
```

### Multiple Joins in Query Chain

```python
# Before
Session.query.join(Project, Session.project).join(Account, Project.account).outerjoin(Proposal, Session.proposal)

# After
from sqlalchemy import and_

Session.query.join(Project, and_(Session.project, Project.deleted_at.is_(None))).join(Account, Project.account).outerjoin(Proposal, and_(Session.proposal, Proposal.deleted_at.is_(None)))
```

## Graph Disable Mode

This codemod includes support for running without the graph feature enabled. This is useful for the faster processing of large codebases and reduced memory usage.

To run in no-graph mode:

```python
codebase = Codebase(str(repo_path), language="python", config=CodebaseConfig(feature_flags=GSFeatureFlags(disable_graph=True)))
```

## Running the Conversion

```bash
# Install Codegen
pip install codegen

# Run the conversion
python run.py
```

## Learn More

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
