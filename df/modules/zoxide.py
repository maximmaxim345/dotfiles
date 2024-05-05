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

ID: str = "zoxide"
NAME: str = "Zoxide"
DESCRIPTION: str = "A smarter cd command. Supports all major shells."
DEPENDENCIES: List[str] = []
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
    else:
        raise ValueError(f"Unsupported platform {platform}")


def is_compatible() -> Union[bool, str]:
    # We only support Linux/Mac with x86_64 and aarch64
    return platform.system() in ["Linux", "Darwin"] and platform.machine() in [
        "x86_64",
        "aarch64",
    ]

# TODO: We could also support Windows here
def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    latest_version = requests.get(release_url).url.split("/")[-1].lstrip("v")
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading zoxide...")
        temp_dir = Path(temp_dir)
        download_path = temp_dir / "zoxide.tar.gz"
        pf = platform.system().lower()
        arch = platform.machine().lower()
        link = dl_link(latest_version, pf, arch)
        df.download_file(link, download_path)
        print("Unpacking zoxide...")
        shutil.unpack_archive(download_path, temp_dir)

        print("Installing zoxide...")
        zoxide_path = temp_dir / "zoxide"
        zoxide_path.chmod(0o755)
        # Copy zoxide to the bin folder (create folder if it doesn't exist)
        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        shutil.copy(zoxide_path, Path.home() / ".local" / "bin" / "zoxide")
        # Save the installed version
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the zoxide executable
    (Path.home() / ".local" / "bin" / "zoxide").unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1].lstrip("v")
    return config.get("version") != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
