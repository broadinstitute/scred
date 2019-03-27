"""
tests/context.py

Adds ../scred/ to $PATH and imports modules for testing
"""

import os
import sys
sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

# Bring in subpackages. Not sure why, but `import scred` here and
# `from context import scred.dtypes` in test_*.py throws ModuleNotFound error
import scred.dtypes as dtypes

# ---------------------------------------------------

# No idea why this doesn't work. What's up with pathlib.Path here?

# from pathlib import Path
# import sys

# tests_folder = Path(__file__).parent
# pkg_folder = tests_folder.parent.resolve()
# sys.path.insert(0, pkg_folder)

# import scred
