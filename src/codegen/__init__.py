from codegen.agents import Agent

# Import version information from the auto-generated _version.py
try:
    from ._version import __version__, __version_tuple__, version, version_tuple
except ImportError:
    # Fallback for development/editable installs where _version.py might not exist
    __version__ = version = "0.0.0+unknown"
    __version_tuple__ = version_tuple = (0, 0, 0, "unknown")

__all__ = ["__version__", "__version_tuple__", "version", "version_tuple", "Agent"]
