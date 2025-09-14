import io
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig

ID: str = "lazygit"
NAME: str = "LazyGit"
DESCRIPTION: str = "A simple terminal UI for git commands"
DEPENDENCIES: List[str] = []
if platform.system() == "Windows":
    DEPENDENCIES = ["windows_local_bin"]
CONFLICTING: List[str] = []


def latest_version() -> str:
    """
    Returns the latest version of lazygit
    """
    version = requests.get("https://api.github.com/repos/jesseduffield/lazygit/releases/latest").json()["tag_name"]
    return version.lstrip("v")


def dl_link(version: str, os: str, arch: str) -> str:
    """
    Returns the download link for the specified version
    """
    url = f"https://github.com/jesseduffield/lazygit/releases/download/v{version}/"
    # Convert platform names to lowercase for filenames
    os_lower = os.lower()
    if os == "Windows":
        return url + f"lazygit_{version}_{os_lower}_{arch}.zip"
    else:
        return url + f"lazygit_{version}_{os_lower}_{arch}.tar.gz"


def is_compatible() -> Union[bool, str]:
    return (
        (platform.system() == "Linux" and platform.machine() in ["x86_64", "aarch64"])
        or (platform.system() == "Darwin" and platform.machine() in ["x86_64", "aarch64"])
        or (platform.system() == "Windows" and platform.machine() in ["AMD64", "x86_64"])
    )


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading lazygit...")
        temp_dir = Path(temp_dir)
        pf = platform.system()
        arch = platform.machine()
        if pf == "Windows" and arch == "AMD64":
            arch = "x86_64"
        if arch == "aarch64":
            arch = "arm64"
        version = latest_version()
        link = dl_link(version, pf, arch)
        download_path = temp_dir / ("lazygit.zip" if pf == "Windows" else "lazygit.tar.gz")
        df.download_file(link, download_path)
        print("Unpacking lazygit...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing lazygit...")
        lazygit_path = temp_dir / "lazygit.exe" if pf == "Windows" else temp_dir / "lazygit"
        if pf != "Windows":
            lazygit_path.chmod(0o755)
        # Copy lazygit to the bin folder (create folder if it doesn't exist)
        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        lazygit_exec = (bin_dir / "lazygit.exe") if pf == "Windows" else (bin_dir / "lazygit")
        shutil.copy(lazygit_path, lazygit_exec)
        # Save the installed version
        config.set("version", version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the lazygit executable
    (Path.home() / ".local" / "bin" / "lazygit").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return config.get("version") != latest_version()


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
