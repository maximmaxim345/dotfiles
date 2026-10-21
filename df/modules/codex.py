import io
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

import requests

import df
from df.config import ModuleConfig
from df.osinfo import running_in_termux, system

ID: str = "codex"
NAME: str = "Codex CLI"
DESCRIPTION: str = "OpenAI's coding agent for the terminal"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

bin_path = Path.home() / ".local" / "bin" / "codex"


def target() -> str:
    arch = "aarch64" if platform.machine() in ["arm64", "aarch64"] else "x86_64"
    return f"{arch}-apple-darwin" if system() == "Darwin" else f"{arch}-unknown-linux-musl"


def latest_tag() -> str:
    return str(requests.get("https://api.github.com/repos/openai/codex/releases/latest").json()["tag_name"])


def installed_elsewhere() -> Optional[str]:
    found = shutil.which("codex")
    return found if found and Path(found).resolve() != bin_path.resolve() else None


def is_compatible() -> Union[bool, str]:
    if running_in_termux():
        return "Not supported in Termux"
    if system() not in ["Linux", "Darwin"] or platform.machine() not in ["x86_64", "aarch64", "arm64"]:
        return "Only supported on Linux and macOS, x86_64 or arm64"
    return True


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    elsewhere = installed_elsewhere()
    if elsewhere:
        config.set("external", True)
        print(f"Codex is already installed at {elsewhere}, leaving it alone")
        return
    tag = latest_tag()
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"Downloading Codex {tag}...")
        archive = temp_dir / "codex.tar.gz"
        df.download_file(f"https://github.com/openai/codex/releases/download/{tag}/codex-{target()}.tar.gz", archive)
        shutil.unpack_archive(archive, temp_dir)
        binary = temp_dir / f"codex-{target()}"
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(binary, bin_path)
        bin_path.chmod(0o755)
    config.set("version", tag)
    print(f"Installed {bin_path}")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if not config.get("external", False):
        bin_path.unlink(missing_ok=True)
    config.unset("external")


def has_update(config: ModuleConfig) -> Union[bool, str]:
    if config.get("external", False):
        return False
    return str(config.get("version", "")) != latest_tag()


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
