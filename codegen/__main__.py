# C:\Programs\codegen\src\codegen\__main__.py
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import compatibility module first
from codegen.compat import *

# Import only what we need for version
try:
    from codegen.cli.cli import main
except ImportError:

    def main():
        # Fallback version function
        import importlib.metadata

        version = importlib.metadata.version("codegen")
        print(version)


if __name__ == "__main__":
    main()
