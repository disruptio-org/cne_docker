"""Application package bootstrap helpers."""

from pathlib import Path
import sys

_APP_DIR = Path(__file__).resolve().parent
_API_DIR = _APP_DIR.parent
_REPO_ROOT = _API_DIR.parent

for path in (_REPO_ROOT, _API_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

__all__ = []
