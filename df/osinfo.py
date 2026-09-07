import os
import platform
from pathlib import Path

# These helpers are in their own module rather than in df/__init__.py because
# modules need them while building DEPENDENCIES and other module level values,
# at which point the df package itself is only partially imported


def system() -> str:
    """Return the OS name, reporting Android as Linux"""
    # Python 3.13 and newer report Termux as Android, but modules treat it
    # like any other Linux
    name = platform.system()
    return "Linux" if name == "Android" else name


def running_in_termux() -> bool:
    """Check if we are running inside Termux on Android"""
    # TERMUX_VERSION is only exported by the login shell, so fall back to the
    # prefix and the installation directory for other ways of starting a shell
    if os.environ.get("TERMUX_VERSION"):
        return True
    if "com.termux" in os.environ.get("PREFIX", ""):
        return True
    return Path("/data/data/com.termux/files/usr").is_dir()
