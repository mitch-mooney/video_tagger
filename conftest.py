import sys
import os

# Ensure project root is on sys.path so `pytest tests/` works without `python -m pytest`
sys.path.insert(0, os.path.dirname(__file__))
