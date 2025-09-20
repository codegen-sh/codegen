"""Import hook implementation for autogenlib."""

import sys
import importlib.abc
import importlib.machinery
import logging
import os
from ._state import description
from ._generator import generate_code
from ._cache import get_cached_code, cache_module
from ._context import get_module_context, set_module_context
from ._caller import get_caller_info

logger = logging.getLogger(__name__)


class AutoLibFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        pass

    def find_spec(self, fullname, path, target=None):
        # Only handle imports under the 'autogenlib' namespace, excluding autogenlib itself
        if not fullname.startswith("autogenlib.") or fullname == "autogenlib":
            return None

        if not description:
            return None

        # Get caller code context
        try:
            caller_info = get_caller_info()
            if caller_info.get("code"):
                logger.debug(f"Got caller context from {caller_info.get('filename')}")
            else:
                logger.debug("No caller context available")
        except Exception as e:
            logger.warning(f"Error getting caller info: {e}")
            caller_info = {"code": "", "filename": ""}

        # Parse the fullname into components and determine the module structure
        parts = fullname.split(".")

        # Handle package structure (e.g., autogenlib.tokens.secure)
        is_package = False
        package_path = None
        module_to_check = fullname

        if len(parts) > 2:
            # This might be a nested package or a module within a package
            parent_module_name = ".".join(parts[:-1])  # e.g., 'autogenlib.tokens'

            # Check if the parent module exists as a package
            if parent_module_name in sys.modules:
                parent_module = sys.modules[parent_module_name]
                parent_path = getattr(parent_module, "__path__", None)

                if parent_path:
                    # Parent is a package
                    is_package = False
                    package_path = parent_path

                    # We need to check if this is requesting a module that doesn't exist yet
                    # If the parent exists as a package, we'll create a module within it
                    module_to_check = fullname

                    # Check if an attribute in the parent
                    attr_name = parts[-1]
                    if hasattr(parent_module, attr_name):
                        # The attribute exists, no need to generate code
                        return None
            else:
                # Parent module doesn't exist yet
                # Start by generating the immediate parent package
                parent_package_name = ".".join(parts[:2])  # e.g., 'autogenlib.tokens'

                # First ensure the parent package exists
                if parent_package_name not in sys.modules:
                    # Generate the parent package
                    parent_code = generate_code(
                        description, parent_package_name, None, caller_info
                    )
                    if parent_code:
                        # Cache the generated code with the prompt
                        cache_module(parent_package_name, parent_code, description)
                        # Update the module context
                        set_module_context(parent_package_name, parent_code)

                        # Create a spec for the parent package
                        parent_loader = AutoLibLoader(parent_package_name, parent_code)
                        parent_spec = importlib.machinery.ModuleSpec(
                            parent_package_name, parent_loader, is_package=True
                        )

                        # Create and initialize the parent package
                        parent_module = importlib.util.module_from_spec(parent_spec)
                        sys.modules[parent_package_name] = parent_module
                        parent_spec.loader.exec_module(parent_module)

                        # Set the __path__ attribute to make it a proper package
                        # This is crucial for nested imports to work
                        if not hasattr(parent_module, "__path__"):
                            parent_module.__path__ = []

                # Now handle the subpackage or module
                if len(parts) == 3:
                    # This is a direct submodule of the parent (e.g., autogenlib.tokens.secure)
                    is_package = False
                    module_to_check = fullname
                else:
                    # This is a nested subpackage (e.g., autogenlib.tokens.secure.module)
                    # We need to create intermediate packages
                    current_pkg = (
                        parts[0] + "." + parts[1]
                    )  # Start with autogenlib.tokens

                    for i in range(2, len(parts) - 1):
                        sub_pkg = (
                            current_pkg + "." + parts[i]
                        )  # e.g., autogenlib.tokens.secure

                        if sub_pkg not in sys.modules:
                            # Generate and load this subpackage
                            sub_code = generate_code(
                                description, sub_pkg, None, caller_info
                            )
                            if sub_code:
                                cache_module(sub_pkg, sub_code, description)
                                set_module_context(sub_pkg, sub_code)

                                sub_loader = AutoLibLoader(sub_pkg, sub_code)
                                sub_spec = importlib.machinery.ModuleSpec(
                                    sub_pkg, sub_loader, is_package=True
                                )

                                sub_module = importlib.util.module_from_spec(sub_spec)
                                sys.modules[sub_pkg] = sub_module
                                sub_spec.loader.exec_module(sub_module)

                                if not hasattr(sub_module, "__path__"):
                                    sub_module.__path__ = []

                        current_pkg = sub_pkg

                    # Finally, set up for the actual module we want to import
                    is_package = False
                    module_to_check = fullname
        else:
            # Standard case: autogenlib.module
            is_package = len(parts) == 2
            module_to_check = fullname

            # Handle attribute import (e.g., autogenlib.tokens.generate_token)
            if len(parts) > 2:
                module_name = ".".join(parts[:2])  # e.g., 'autogenlib.tokens'
                attr_name = parts[-1]  # e.g., 'generate_token'

                # Check if the module exists but is missing this attribute
                if module_name in sys.modules:
                    module = sys.modules[module_name]

                    # If the attribute doesn't exist, regenerate the module
                    if not hasattr(module, attr_name):
                        # Get the current module code
                        module_context = get_module_context(module_name)
                        current_code = module_context.get("code", "")

                        # Generate updated code including the new function
                        new_code = generate_code(
                            description, fullname, current_code, caller_info
                        )
                        if new_code:
                            # Update the cache and module
                            cache_module(module_name, new_code, description)
                            set_module_context(module_name, new_code)

                            # Execute the new code in the module's namespace
                            exec(new_code, module.__dict__)

                            # If the attribute exists now, return None to continue normal import
                            if hasattr(module, attr_name):
                                return None

        # Check if the module is already cached
        code = get_cached_code(module_to_check)

        if code is None:
            # Generate code using OpenAI's API with caller context
            code = generate_code(description, module_to_check, None, caller_info)
            if code is not None:
                # Cache the generated code with the prompt
                cache_module(module_to_check, code, description)
                # Update the module context
                set_module_context(module_to_check, code)

        if code is not None:
            # Create a spec for the module
            loader = AutoLibLoader(module_to_check, code)
            spec = importlib.machinery.ModuleSpec(
                module_to_check, loader, is_package=is_package
            )

            # Set origin for proper package handling
            if is_package:
                spec.submodule_search_locations = []

            return spec

        return None


class AutoLibLoader(importlib.abc.Loader):
    def __init__(self, fullname, code):
        self.fullname = fullname
        self.code = code

    def create_module(self, spec):
        return None  # Use the default module creation

    def exec_module(self, module):
        # Set up package attributes if this is a package
        if getattr(module.__spec__, "submodule_search_locations", None) is not None:
            # This is a package
            if not hasattr(module, "__path__"):
                module.__path__ = []

            # Create a virtual __init__.py for packages
            if "__init__" not in self.code:
                init_code = self.code
            else:
                init_code = self.code

            # Execute the code
            exec(init_code, module.__dict__)
        else:
            # Regular module
            exec(self.code, module.__dict__)

        # Update the module context
        set_module_context(self.fullname, self.code)
