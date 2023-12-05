from df.config import ModuleConfig
import df
import platform
import tempfile
import shutil
import subprocess
import io
import requests
from pathlib import Path
from typing import Union, List

ID: str = "topgrade"
NAME: str = "Topgrade"
DESCRIPTION: str = "Upgrade all the things"
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []


def dl_link(pltform: str, arch: str) -> str:
    """
    Returns the download link for the latest version
    """
    # Typical file names:
    # topgrade-v13.0.0-aarch64-unknown-linux-gnu.tar.gz
    # topgrade-v13.0.0-aarch64-unknown-linux-musl.tar.gz
    # topgrade-v13.0.0-armv7-unknown-linux-gnueabihf.tar.gz
    # topgrade-v13.0.0-x86_64-apple-darwin.tar.gz
    # topgrade-v13.0.0-x86_64-pc-windows-msvc.zip
    # topgrade-v13.0.0-x86_64-unknown-linux-gnu.tar.gz
    # topgrade-v13.0.0-x86_64-unknown-linux-musl.tar.gz

    url = "https://github.com/topgrade-rs/topgrade/releases/latest"
    response = requests.get(url)
    latest_version = response.url.split("/")[-1]
    if pltform == "linux":
        libc, version = platform.libc_ver()
        libc = "gnu" if libc == "glibc" else "musl"
        return url + f"/download/topgrade-{latest_version}-x86_64-unknown-linux-{libc}.tar.gz"
    elif pltform == "darwin":
        return url + f"/download/topgrade-{latest_version}-x86_64-apple-darwin.tar.gz"
    elif pltform == "windows":
        return url + f"/download/topgrade-{latest_version}-x86_64-pc-windows-msvc.zip"
    else:
        raise ValueError(f"Unsupported platform {pltform}")


def is_compatible() -> Union[bool, str]:
    # We only support Linux/Mac with x86_64 and aarch64 for now
    return platform.system() in ["Linux", "Darwin"] and platform.machine() in [
        "x86_64",
        "aarch64",
    ]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading topgrade...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "topgrade.tar.gz"
        pf = platform.system().lower()
        arch = platform.machine().lower()
        link = dl_link(pf, arch)
        df.download_file(link, download_path)
        print("Unpacking topgrade...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing topgrade...")
        zellij_path = temp_dir / "topgrade"
        zellij_path.chmod(0o755)
        # Copy topgrade to the bin folder (create folder if it doesn't exist)
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(zellij_path, Path.home() / ".local" / "bin" / "topgrade")


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Run bob erase
    subprocess.run(["bob", "erase"], stdout=stdout, stderr=stdout)
    # Delete the bob executable
    (Path.home() / ".local" / "bin" / "topgrade").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    return False


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # has built-in update mechanism
    pass
