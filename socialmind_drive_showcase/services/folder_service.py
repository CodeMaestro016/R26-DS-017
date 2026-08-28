"""Open only predefined project folders; no browser-supplied paths."""

import os
from pathlib import Path


def open_predefined_folder(path):
    target = Path(path).resolve()
    if not target.is_dir():
        raise FileNotFoundError(str(target))
    if os.name == "nt":
        os.startfile(target)  # type: ignore[attr-defined]
    else:
        raise OSError("Folder opening is currently supported on Windows only.")

