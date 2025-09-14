import io
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig

ID: str = "zoxide"
NAME: str = "Zoxide"
DESCRIPTION: str = "A smarter cd command. Supports all major shells."
DEPENDENCIES: List[str] = []
if platform.system() == "Windows":
    DEPENDENCIES = ["windows_local_bin"]
CONFLICTING: List[str] = []

release_url = "https://github.com/ajeetdsouza/zoxide/releases/latest"


def dl_link(version: str, platform: str, arch: str) -> str:
    """
    Returns the download link for the specified version
    """
    url = f"https://github.com/ajeetdsouza/zoxide/releases/download/v{version}/"
    if platform == "linux":
        return url + f"zoxide-{version}-{arch}-unknown-linux-musl.tar.gz"
    elif platform == "darwin":
        return url + f"zoxide-{version}-{arch}-apple-darwin.tar.gz"
    elif platform == "windows":
        return url + f"zoxide-{version}-{arch}-pc-windows-msvc.zip"
    else:
        raise ValueError(f"Unsupported platform {platform}")


def is_compatible() -> Union[bool, str]:
    return (platform.system() in ["Linux", "Darwin"] and platform.machine() in ["x86_64", "aarch64"]) or (
        platform.system() == "Windows" and platform.machine() == "AMD64"
    )


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    latest_version = requests.get(release_url).url.split("/")[-1].lstrip("v")
    with tempfile.TemporaryDirectory() as temp_dir_str:
        print("Downloading zoxide...")
        temp_dir = Path(temp_dir_str)
        pf = platform.system().lower()
        arch = platform.machine().lower()
        if arch == "amd64":
            arch = "x86_64"
        link = dl_link(latest_version, pf, arch)
        if pf == "windows":
            download_path = temp_dir / "zoxide.zip"
            df.download_file(link, download_path)
            print("Unpacking zoxide...")
            shutil.unpack_archive(download_path, temp_dir)
            zoxide_path = temp_dir / "zoxide.exe"
        else:
            download_path = temp_dir / "zoxide.tar.gz"
            df.download_file(link, download_path)
            print("Unpacking zoxide...")
            shutil.unpack_archive(download_path, temp_dir)
            zoxide_path = temp_dir / "zoxide"
            zoxide_path.chmod(0o755)

        print("Installing zoxide...")
        # Copy zoxide to the bin folder (create folder if it doesn't exist)
        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        if pf == "windows":
            shutil.copy(zoxide_path, bin_dir / "zoxide.exe")
        else:
            shutil.copy(zoxide_path, bin_dir / "zoxide")
        # Save the installed version
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the zoxide executable
    bin_dir = Path.home() / ".local" / "bin"
    if platform.system() == "Windows":
        (bin_dir / "zoxide.exe").unlink(missing_ok=True)
    else:
        (bin_dir / "zoxide").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1].lstrip("v")
    current_version = config.get("version", "")
    return str(current_version) != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
