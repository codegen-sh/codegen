# Optional Agent import to avoid dependency issues during development
try:
    from codegen.agents import Agent
except ImportError:
    # Fallback Agent class if dependencies are missing
    class Agent:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Agent(placeholder - dependencies missing)"

# Import version information from the auto-generated _version.py
try:
    from ._version import __version__, __version_tuple__, version, version_tuple
except ImportError:
    # Fallback for development/editable installs where _version.py might not exist
    __version__ = version = "0.0.0+unknown"
    __version_tuple__ = version_tuple = (0, 0, 0, "unknown")

__all__ = ["__version__", "__version_tuple__", "version", "version_tuple", "Agent"]
