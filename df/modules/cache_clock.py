import io
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig
from df.osinfo import system

ID: str = "cache_clock"
NAME: str = "Claude Code Cache Clock Mod"
DESCRIPTION: str = "A Claude Code mod that adds a prompt cache line under the status line"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

REPO: str = "hamzafer/claude-code-mods"
MOD_DIR: str = "mods/cache-clock"

mod_path = Path.home() / ".claude" / "third-party-mods" / "cache-clock"


def latest_version() -> str:
    """
    Returns the sha of the latest commit that changed the mod
    """
    params = {"path": MOD_DIR, "per_page": "1"}
    response = requests.get(f"https://api.github.com/repos/{REPO}/commits", params=params).json()
    return str(response[0]["sha"])


def mod_files(version: str) -> List[str]:
    """
    Returns the paths of the mod's files at the given commit, without its tests
    """
    response = requests.get(f"https://api.github.com/repos/{REPO}/git/trees/{version}?recursive=1").json()
    return [
        entry["path"]
        for entry in response["tree"]
        if entry["type"] == "blob"
        and entry["path"].startswith(f"{MOD_DIR}/")
        and not entry["path"].startswith(f"{MOD_DIR}/tests/")
    ]


def is_compatible() -> Union[bool, str]:
    if system() not in ["Linux", "Darwin", "Windows"]:
        return False
    if shutil.which("node") is None:
        return "Node is required to draw the cache line"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    version = latest_version()
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"Downloading cache-clock {version[:7]}...")
        for path in mod_files(version):
            url = f"https://raw.githubusercontent.com/{REPO}/{version}/{path}"
            df.download_file(url, temp_dir / Path(path).relative_to(MOD_DIR))

        df.delete_or_unlink(mod_path, delete_recursively=True)
        df.ensure_parent_exists(mod_path)
        shutil.copytree(temp_dir, mod_path)

    config.set("version", version)
    print(f"Installed cache-clock {version[:7]} to {mod_path}")
    print(f"Add {mod_path} to CLAUDE_CODE_PLUGIN_DIRS in ~/.claude/settings.json, then run /cache-clock setup")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    df.delete_or_unlink(mod_path, delete_recursively=True)
    print("If you ran /cache-clock setup, also remove statusLine from ~/.claude/settings.json")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    current_version = config.get("version", "")
    return str(current_version) != latest_version()


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
