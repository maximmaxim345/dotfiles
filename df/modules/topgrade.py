import io
import platform
import shutil
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig

ID: str = "topgrade"
NAME: str = "Topgrade"
DESCRIPTION: str = "Upgrade all the things"
DEPENDENCIES: List[str] = []
if platform.system() == "Windows":
    DEPENDENCIES = ["windows_local_bin"]
CONFLICTING: List[str] = []


def dl_link(pltform: str, arch: str) -> str:
    """
    Returns the download link for the latest version
    """
    api_url = "https://github.com/topgrade-rs/topgrade/releases/latest"
    response = requests.get(api_url)
    latest_version = response.url.split("/")[-1]
    download_base = "https://github.com/topgrade-rs/topgrade/releases/download"
    if pltform == "linux":
        libc, version = platform.libc_ver()
        libc = "gnu" if libc == "glibc" else "musl"
        return f"{download_base}/{latest_version}/topgrade-{latest_version}-{arch}-unknown-linux-{libc}.tar.gz"
    elif pltform == "windows":
        return f"{download_base}/{latest_version}/topgrade-{latest_version}-x86_64-pc-windows-msvc.zip"
    elif pltform == "darwin":
        return f"{download_base}/{latest_version}/topgrade-{latest_version}-{arch}-apple-darwin.tar.gz"
    else:
        raise ValueError(f"Unsupported platform {pltform}")


def is_compatible() -> Union[bool, str]:
    return (
        (platform.system() == "Linux" and platform.machine() in ["x86_64", "aarch64"])
        or (platform.system() == "Darwin" and platform.machine() in ["x86_64", "aarch64"])
        or (platform.system() == "Windows" and platform.machine() == "AMD64")
    )


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading topgrade...")
        temp_dir = Path(temp_dir)
        pf = platform.system().lower()
        arch = platform.machine().lower()
        if arch in ["amd64", "AMD64"]:
            arch = "x86_64"
        link = dl_link(pf, arch)
        if pf == "windows":
            download_path = temp_dir / "topgrade.zip"
            df.download_file(link, download_path)
            print("Unzipping topgrade...")
            shutil.unpack_archive(download_path, temp_dir)
            topgrade_path = temp_dir / "topgrade.exe"
        else:
            download_path = temp_dir / "topgrade.tar.gz"
            df.download_file(link, download_path)
            print("Unpacking topgrade...")
            shutil.unpack_archive(download_path, temp_dir)
            topgrade_path = temp_dir / "topgrade"
            topgrade_path.chmod(0o755)

        print("Installing topgrade...")
        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        topgrade_exec = (bin_dir / "topgrade.exe") if pf == "windows" else (bin_dir / "topgrade")
        shutil.copy(topgrade_path, topgrade_exec)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    bin_dir = Path.home() / ".local" / "bin"
    topgrade_exec = (bin_dir / "topgrade.exe") if platform.system() == "Windows" else (bin_dir / "topgrade")
    (bin_dir / topgrade_exec).unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # has built-in update mechanism
    pass
