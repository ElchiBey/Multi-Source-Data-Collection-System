"""
Test package initialization.

This file ensures that the tests can properly import the src modules
by setting up the correct Python path.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Verify yaml can be imported
try:
    import yaml
except ImportError as e:
    print(f"Warning: yaml import failed in tests/__init__.py: {e}")
    # Try alternative import
    try:
        import ruamel.yaml as yaml
    except ImportError:
        print("Note: Install PyYAML with: pip install PyYAML") 