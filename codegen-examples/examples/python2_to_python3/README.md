# Python 2 to Python 3 Migration Example

[![Documentation](https://img.shields.io/badge/docs-docs.codegen.com-blue)](https://docs.codegen.com/tutorials/python2-to-python3)

This example demonstrates how to use Codegen to automatically migrate Python 2 code to Python 3. For a complete walkthrough, check out our [tutorial](https://docs.codegen.com/tutorials/python2-to-python3).

## What This Example Does

The migration script handles five key transformations:

1. **Convert Print Statements**

   ```python
   # From:
   print "Hello, world!"
   print x, y, z

   # To:
   print("Hello, world!")
   print(x, y, z)
   ```

1. **Update Unicode to str**

   ```python
   # From:
   from __future__ import unicode_literals

   text = unicode("Hello")
   prefix = "prefix"

   # To:
   text = str("Hello")
   prefix = "prefix"
   ```

1. **Convert raw_input to input**

   ```python
   # From:
   name = raw_input("Enter your name: ")

   # To:
   name = input("Enter your name: ")
   ```

1. **Update Exception Handling**

   ```python
   # From:
   try:
       process_data()
   except ValueError, e:
       print(e)

   # To:
   try:
       process_data()
   except ValueError as e:
       print(e)
   ```

1. **Modernize Iterator Methods**

   ```python
   # From:
   class MyIterator:
       def next(self):
           return self.value


   # To:
   class MyIterator:
       def __next__(self):
           return self.value
   ```

## Running the Example

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

The script will process all Python files in the `repo-before` directory and apply the transformations in the correct order.

## Understanding the Code

- `run.py` - The migration script
- `input_repo/` - Sample Python 2 code to migrate

## Learn More

- [Full Tutorial](https://docs.codegen.com/tutorials/python2-to-python3)
- [Python 3 Documentation](https://docs.python.org/3/)
- [What's New in Python 3](https://docs.python.org/3/whatsnew/3.0.html)
- [Codegen Documentation](https://docs.codegen.com)
