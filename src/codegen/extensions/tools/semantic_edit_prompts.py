FILE_EDIT_PROMPT = (
    """Edit a file in plain-text format.
* The assistant can edit files by specifying the file path and providing a draft of the new file content.
* The draft content doesn't need to be exactly the same as the existing file; the assistant may skip unchanged lines using comments like `# unchanged` to indicate unchanged sections.
* IMPORTANT: For large files (e.g., > 300 lines), specify the range of lines to edit using `start` and `end` (1-indexed, inclusive). The range should be smaller than 300 lines.
* To append to a file, set both `start` and `end` to `-1`.
* If the file doesn't exist, a new file will be created with the provided content.
* If specifying start and end, leave some room for context (e.g., 30 lines before and 30 lines after the edit range). However, for the end parameter, do not exceed the last line of the file.
* For example if the file is 500 lines long and an edit is requested from line 450 to 500, make the start parameter 430 and the end parameter 500.
* Another example if the file is 500 lines long and an edit is requested from line 450 to 490, make the start parameter 430 and the end parameter 500.
* Always choose edit ranges that include full code blocks.
* Ensure that if the file is less than 300 lines, do not specify a start or end parameter. Only specify for large files over 300 lines.

* IMPORTANT: If it's not specified or implied where the code should be added, just append it to the end of the file by setting  the start=-1 and end=-1

**Example 1: general edit for short files**
For example, given an existing file `/path/to/file.py` that looks like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|        self.z = 3
6|
7|print(MyClass().z)
8|print(MyClass().x)
(this is the end of the file)

The assistant wants to edit the file to look like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|
6|print(MyClass().y)
(this is the end of the file)

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=1 end=-1
content=```
class MyClass:
    def __init__(self):
        # no changes before
        self.y = 2
        # self.z is removed

# MyClass().z is removed
print(MyClass().y)
```

**Example 2: append to file for short files**
For example, given an existing file `/path/to/file.py` that looks like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|        self.z = 3
6|
7|print(MyClass().z)
8|print(MyClass().x)
(this is the end of the file)

To append the following lines to the file:
```python
print(MyClass().y)
```

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=-1 end=-1
content=```
print(MyClass().y)
```

**Example 3: edit for long files**

Given an existing file `/path/to/file.py` that looks like this:
(1000 more lines above)
971|def helper_function():
972|    """
    "Helper function for MyClass"
    """
973|    pass
974|
975|class BaseClass:
976|    """
    "Base class for MyClass"
    """
977|    def base_method(self):
978|        pass
979|
980|# Configuration for MyClass
981|MY_CONFIG = {
982|    "x": 1,
983|    "y": 2,
984|    "z": 3
985|}
986|
987|@decorator
988|class MyClass(BaseClass):
989|    """
    "Main class implementation"
    """
990|    def __init__(self):
991|        self.x = MY_CONFIG["x"]
992|        self.y = MY_CONFIG["y"]
993|        self.z = MY_CONFIG["z"]
994|
995|    def get_values(self):
996|        return self.x, self.y, self.z
997|
998|print(MyClass().z)
999|print(MyClass().x)
1000|
1001|# Additional helper functions
1002|def process_values(obj):
1003|    """
    "Process MyClass values"
    """
1004|    return sum([obj.x, obj.y, obj.z])
(2000 more lines below)

The assistant wants to edit lines 990-993 to remove the z value. The assistant should capture enough context by getting 30 lines before and after:

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=960 end=1020
content=```
# Previous helper functions and configuration preserved
def helper_function():
    """
    "Helper function for MyClass"
    """
    pass

class BaseClass:
    """
    "Base class for MyClass"
    """
    def base_method(self):
        pass

# Configuration for MyClass
MY_CONFIG = {
    "x": 1,
    "y": 2,
    "z": 3
}

@decorator
class MyClass(BaseClass):
    """
    "Main class implementation"
    """
    def __init__(self):
        self.x = MY_CONFIG["x"]
        self.y = MY_CONFIG["y"]
        # Removed z configuration

    def get_values(self):
        return self.x, self.y

print(MyClass().y)  # Updated print statement
print(MyClass().x)

# Additional helper functions
def process_values(obj):
    """
    "Process MyClass values"
    """
    return sum([obj.x, obj.y])  # Updated to remove z
```

**Example 4: edit with maximum context**

Given a file with complex class hierarchy and dependencies:
(many lines above)
450|class ParentClass:
451|    """
    "Parent class with important context"
    """
452|    def parent_method(self):
453|        return "parent"
454|
455|class Mixin:
456|    """
    "Mixin with critical functionality"
    """
457|    def mixin_method(self):
458|        return "mixin"
459|
460|# Important configuration
461|SETTINGS = {
462|    "timeout": 30,
463|    "retries": 3
464|}
465|
466|@important_decorator
467|class TargetClass(ParentClass, Mixin):
468|    """
    "Class that needs modification"
    """
469|    def __init__(self):
470|        self.timeout = SETTINGS["timeout"]
471|        self.retries = SETTINGS["retries"]
472|
473|    def process(self):
474|        return self.parent_method() + self.mixin_method()
475|
476|# Usage examples
477|instance = TargetClass()
478|result = instance.process()
479|
480|def helper():
481|    """
    "Helper function that uses TargetClass"
    """
482|    return TargetClass().process()
(many lines below)

The assistant wants to modify the process method. To ensure all context is captured (inheritance, mixins, configuration), it should get at least 30 lines before and after:

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=420 end=510
content=```
# Previous context preserved
class ParentClass:
    """
    "Parent class with important context"
    """
    def parent_method(self):
        return "parent"

class Mixin:
    """
    "Mixin with critical functionality"
    """
    def mixin_method(self):
        return "mixin"

# Important configuration
SETTINGS = {
    "timeout": 30,
    "retries": 3
}

@important_decorator
class TargetClass(ParentClass, Mixin):
    """
    "Class that needs modification"
    """
    def __init__(self):
        self.timeout = SETTINGS["timeout"]
        self.retries = SETTINGS["retries"]

    def process(self):
        # Modified to add error handling
        try:
            return self.parent_method() + " - " + self.mixin_method()
        except Exception as e:
            return f"Error: e"

# Usage examples preserved
instance = TargetClass()
result = instance.process()

def helper():
    """
    "Helper function that uses TargetClass"
    """
    return TargetClass().process()
```
"""
)


COMMANDER_SYSTEM_PROMPT = """You are an expert code editor.

Another agent has determined an edit needs to be made to this file.

Your job is to produce a new version of the specified section based on the old version the provided instructions.

The provided draft may be incomplete (it may skip lines) and/or incorrectly indented.

The instructions will be provided via demonstrations and helpful comments, like so:
```
# ... existing code ...

# edit: change function name and body
def function_redefinition():
    return 'new_function_body'

# ... existing code ...
```

In addition, for large files, only a subset of lines will be provided that correspond to the edit you need to make.

You must understand the intent behind the edits and apply them properly based on the instructions and common sense about how to apply them.

CRITICAL REQUIREMENTS:
1. ONLY modify the content between the specified boundaries. DO NOT add content outside the edit range.
2. Preserve ALL original spacing, including:
   - Indentation at the start of lines
   - Empty lines between functions/classes
   - Trailing whitespace
   - Newlines at the end of the file
3. Do not modify any lines that are not part of the explicit changes
4. Keep all original comments that are part of the functionality
5. Remove any placeholder comments like "# no changes before" or "# new code here"

Example of correct formatting:
```python
class MyClass:
    def method1(self):
        # Original comment preserved
        x = 5  # Inline comment kept

        if x > 0:
            return True
```

Note how the example maintains:
1. Original comments and docstrings
2. Exact indentation
3. Empty lines
4. No content outside the edit range
"""


_HUMAN_PROMPT_DRAFT_EDITOR = """
HERE IS THE OLD VERSION OF THE SECTION:
```
{original_file_section}
```

HERE ARE INSTRUCTIONS FOR THE EDIT:
```
{edit_content}
```


OUTPUT REQUIREMENTS:
1. Wrap your response in a code block using triple backticks (```).
2. Include ONLY the final code, no explanations.
3. Preserve ALL spacing and indentation exactly.
4. Remove any placeholder comments like "# no changes" or "# new code here".
5. Keep actual code comments that are part of the functionality.
6. Understand the intent behind the edits and apply them correctly.
"""
