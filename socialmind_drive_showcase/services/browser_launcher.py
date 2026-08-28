"""Best-effort Chrome app-mode launcher with default-browser fallback."""

import os
from pathlib import Path
import subprocess
import webbrowser


def chrome_candidates():
    roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
             os.environ.get("LOCALAPPDATA")]
    suffixes = [Path("Google/Chrome/Application/chrome.exe"),
                Path("Google/Chrome Beta/Application/chrome.exe")]
    return tuple(Path(root) / suffix for root in roots if root for suffix in suffixes)


def open_showcase(url, presentation=True, candidates=None):
    for path in tuple(candidates) if candidates is not None else chrome_candidates():
        if Path(path).is_file():
            args = [str(path), f"--app={url}"] if presentation else [str(path), url]
            subprocess.Popen(args, shell=False)
            return "CHROME_APP" if presentation else "CHROME_TAB"
    webbrowser.open(url, new=1)
    return "DEFAULT_BROWSER"

