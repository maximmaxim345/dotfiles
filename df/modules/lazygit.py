from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import requests
import io
from pathlib import Path
from typing import Union, List

ID: str = "lazygit"
NAME: str = "LazyGit"
DESCRIPTION: str = "A simple terminal UI for git commands"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []


def latest_version() -> str:
    """
    Returns the latest version of lazygit
    """
    version = requests.get(
        "https://api.github.com/repos/jesseduffield/lazygit/releases/latest"
    ).json()["tag_name"]
    return version.lstrip("v")


def dl_link(version: str, os: str, arch: str) -> str:
    """
    Returns the download link for the specified version
    """
    url = "https://github.com/jesseduffield/lazygit/releases/latest/download/"
    return url + f"lazygit_{version}_{os}_{arch}.tar.gz"


def is_compatible() -> Union[bool, str]:
    # We only support Linux with x86_64
    return platform.system() in ["Linux"] and platform.machine() in ["x86_64"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading lazygit...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "lazygit.tar.gz"
        arch = platform.machine().lower()
        version = latest_version()
        link = dl_link(version, "Linux", arch)
        df.download_file(link, download_path)
        print("Unpacking lazygit...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing lazygit...")
        lazygit_path = temp_dir / "lazygit"
        lazygit_path.chmod(0o755)
        # Copy lazygit to the bin folder (create folder if it doesn't exist)
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(lazygit_path, Path.home() / ".local" / "bin" / "lazygit")
        # Save the installed version
        config.set("version", version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the lazygit executable
    (Path.home() / ".local" / "bin" / "lazygit").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return config.get("version") != latest_version()


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
