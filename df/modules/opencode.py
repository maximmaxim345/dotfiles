import io
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Union

import df
from df.config import ModuleConfig
from df.osinfo import running_in_termux, system

ID: str = "opencode"
NAME: str = "OpenCode"
DESCRIPTION: str = "OpenCode 2, an open source coding agent for the terminal"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

# The official installer puts the binary here
installed_path = Path.home() / ".opencode" / "bin" / "opencode"
bin_path = Path.home() / ".local" / "bin" / "opencode"


def installed_elsewhere() -> Optional[str]:
    found = shutil.which("opencode")
    return found if found and Path(found).resolve() != installed_path.resolve() else None


def is_compatible() -> Union[bool, str]:
    if running_in_termux():
        return "Not supported in Termux"
    if system() not in ["Linux", "Darwin"]:
        return "Only supported on Linux and macOS"
    if not shutil.which("bash") or not shutil.which("curl"):
        return "Needs bash and curl"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    elsewhere = installed_elsewhere()
    if elsewhere:
        config.set("external", True)
        print(f"OpenCode is already installed at {elsewhere}, leaving it alone")
        return
    with tempfile.TemporaryDirectory() as temp_dir_str:
        script = Path(temp_dir_str) / "install.sh"
        df.download_file("https://opencode.ai/v2/install", script)
        result = subprocess.run(["bash", str(script), "--no-modify-path"], capture_output=True, text=True)
        print(result.stdout if result.returncode == 0 else result.stdout + result.stderr)
        result.check_returncode()
    df.symlink_path(installed_path, bin_path)
    print(f"Linked {bin_path}, OpenCode updates itself with: opencode upgrade")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if not config.get("external", False):
        df.delete_or_unlink(bin_path)
        df.delete_or_unlink(installed_path.parent, delete_recursively=True)
    config.unset("external")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    pass
