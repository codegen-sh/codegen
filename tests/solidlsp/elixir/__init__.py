import platform


def _test_nextls_available() -> str:
    """Test if Next LS is available and return error reason if not."""
    # Check if we're on Windows (Next LS doesn't support Windows)
    if platform.system() == "Windows":
        return "Next LS does not support Windows"

    # Try to import and check Elixir availability
    try:
        from solidlsp.language_servers.elixir_tools.elixir_tools import ElixirTools

        # Check if Elixir is installed
        elixir_version = ElixirTools._get_elixir_version()
        if not elixir_version:
            return "Elixir is not installed or not in PATH"

        return ""  # No error, Next LS should be available

    except ImportError as e:
        return f"Failed to import ElixirTools: {e}"
    except Exception as e:
        return f"Error checking Next LS availability: {e}"


NEXTLS_UNAVAILABLE_REASON = _test_nextls_available()
NEXTLS_UNAVAILABLE = bool(NEXTLS_UNAVAILABLE_REASON)
