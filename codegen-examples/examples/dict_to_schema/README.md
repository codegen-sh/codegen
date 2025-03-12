# Dict to Schema

This example demonstrates how to automatically convert Python dictionary literals into Pydantic models. The codemod makes this process simple by handling all the tedious manual updates automatically.

> [!NOTE]
> View example transformations created by this codemod on the `modal-labs/modal-client` repository [here](https://www.codegen.sh/codemod/6b5f2dfa-948a-4953-b283-9bd4b8545632/public/diff).

## How the Conversion Script Works

The script (`run.py`) automates the entire conversion process in a few key steps:

1. **Codebase Loading**

   ```python
   codebase = Codebase.from_repo("modal-labs/modal-client")
   ```

   - Loads your codebase into Codegen's intelligent code analysis engine
   - Provides a simple SDK for making codebase-wide changes
   - Supports any Git repository as input

1. **Dictionary Detection**

   ```python
   if "{" in global_var.source and "}" in global_var.source:
       dict_content = global_var.value.source.strip("{}")
   ```

   - Automatically identifies dictionary literals in your code
   - Processes both global variables and class attributes
   - Skips empty dictionaries to avoid unnecessary conversions

1. **Schema Creation**

   ```python
   class_name = global_var.name.title() + "Schema"
   model_def = f"""class {class_name}(BaseModel):
       {dict_content.replace(",", "\n    ")}"""
   ```

   - Generates meaningful model names based on variable names
   - Converts dictionary key-value pairs to class attributes
   - Maintains proper Python indentation

1. **Code Updates**

   ```python
   global_var.insert_before(model_def + "\n\n")
   global_var.set_value(f"{class_name}(**{global_var.value.source})")
   ```

   - Inserts new Pydantic models in appropriate locations
   - Updates dictionary assignments to use the new models
   - Automatically adds required Pydantic imports

## Common Conversion Patterns

### Global Variables

```python
# Before
config = {"host": "localhost", "port": 8080}


# After
class ConfigSchema(BaseModel):
    host: str = "localhost"
    port: int = 8080


config = ConfigSchema(**{"host": "localhost", "port": 8080})
```

### Class Attributes

```python
# Before
class Service:
    defaults = {"timeout": 30, "retries": 3}


# After
class DefaultsSchema(BaseModel):
    timeout: int = 30
    retries: int = 3


class Service:
    defaults = DefaultsSchema(**{"timeout": 30, "retries": 3})
```

## Running the Conversion

```bash
# Install Codegen
pip install codegen

# Run the conversion
python run.py
```

## Learn More

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
