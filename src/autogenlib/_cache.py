"""Cache management for autogenlib generated code."""

import os
import hashlib
import json
from ._state import caching_enabled


def get_cache_dir():
    """Get the directory where cached files are stored."""
    cache_dir = os.path.join(os.path.expanduser("~"), ".autogenlib_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_cache_path(fullname):
    """Get the path where the cached data for a module should be stored."""
    cache_dir = get_cache_dir()

    # Create a filename based on the module name
    # Use only the first two parts of the fullname (e.g., autogenlib.totp)
    # to ensure we're caching at the module level
    module_name = ".".join(fullname.split(".")[:2])
    filename = hashlib.md5(module_name.encode()).hexdigest() + ".json"
    return os.path.join(cache_dir, filename)


def get_cached_data(fullname):
    """Get the cached data for a module if it exists."""
    if not caching_enabled:
        return None

    cache_path = get_cache_path(fullname)
    try:
        with open(cache_path, "r") as f:
            data = json.load(f)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_cached_code(fullname):
    """Get the cached code for a module if it exists."""
    if not caching_enabled:
        return None

    data = get_cached_data(fullname)
    if data:
        return data.get("code")
    return None


def get_cached_prompt(fullname):
    """Get the cached initial prompt for a module if it exists."""
    if not caching_enabled:
        return None

    data = get_cached_data(fullname)
    if data:
        return data.get("prompt")
    return None


def cache_module(fullname, code, prompt):
    """Cache the code and prompt for a module."""
    if not caching_enabled:
        return

    cache_path = get_cache_path(fullname)
    data = {"code": code, "prompt": prompt, "module_name": fullname}
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)


def get_all_modules():
    """Get all cached modules."""
    if not caching_enabled:
        return {}

    cache_dir = get_cache_dir()
    modules = {}

    try:
        for filename in os.listdir(cache_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(cache_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        # Extract module name from the data or use the filename
                        module_name = data.get(
                            "module_name", os.path.splitext(filename)[0]
                        )
                        modules[module_name] = data
                except (json.JSONDecodeError, IOError):
                    continue
    except FileNotFoundError:
        pass

    return modules
