import os
import sys

# Add the project's root directory to the PYTHONPATH
# This allows Python to locate modules in the parent directory, enabling relative imports.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
