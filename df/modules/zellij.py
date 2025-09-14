import io
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig

ID: str = "zellij"
NAME: str = "Zellij"
DESCRIPTION: str = "A terminal workspace with batteries included"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

release_url = "https://github.com/zellij-org/zellij/releases/latest"


def dl_link(platform: str, arch: str) -> str:
    """
    Returns the download link for the latest version
    """
    # Typical file names:
    # zellij-aarch64-apple-darwin.tar.gz
    # zellij-aarch64-unknown-linux-musl.tar.gz
    # zellij-x86_64-apple-darwin.tar.gz
    # zellij-x86_64-unknown-linux-musl.tar.gz
    url = f"{release_url}/download/"
    if platform == "linux":
        return url + f"zellij-{arch}-unknown-linux-musl.tar.gz"
    elif platform == "darwin":
        return url + f"zellij-{arch}-apple-darwin.tar.gz"
    else:
        raise ValueError(f"Unsupported platform {platform}")


def is_compatible() -> Union[bool, str]:
    # We only support Linux/Mac with x86_64 and aarch64
    # Zellij does not have official Windows support yet
    return platform.system() in ["Linux", "Darwin"] and platform.machine() in [
        "x86_64",
        "aarch64",
    ]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir_str:
        print("Downloading zellij...")
        temp_dir = Path(temp_dir_str)
        download_path = temp_dir / "zellij.tar.gz"
        pf = platform.system().lower()
        arch = platform.machine().lower()
        link = dl_link(pf, arch)
        df.download_file(link, download_path)
        print("Unpacking zellij...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing zellij...")
        zellij_path = temp_dir / "zellij"
        zellij_path.chmod(0o755)
        # Copy zellij to the bin folder (create folder if it doesn't exist)
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(zellij_path, Path.home() / ".local" / "bin" / "zellij")
        # Save the installed version
        latest_version = requests.get(release_url).url.split("/")[-1]
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the zellij executable
    (Path.home() / ".local" / "bin" / "zellij").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1]
    current_version = config.get("version", "")
    return str(current_version) != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
