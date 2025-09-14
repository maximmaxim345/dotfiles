import io
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Union

import requests

import df
from df.config import ModuleConfig

ID: str = "starship"
NAME: str = "Starship"
DESCRIPTION: str = "The minimal, blazing-fast, and infinitely customizable prompt for any shell!"
DEPENDENCIES: List[str] = []
if platform.system() == "Windows":
    DEPENDENCIES = ["windows_local_bin"]
CONFLICTING: List[str] = []

release_url = "https://github.com/starship/starship/releases/latest"
script_link = "https://starship.rs/install.sh"
bin_dir = Path.home() / ".local" / "bin"


def is_compatible() -> Union[bool, str]:
    return (platform.system() in ["Linux", "Darwin"] and platform.machine() in ["x86_64", "aarch64"]) or (
        platform.system() == "Windows" and platform.machine() in ["AMD64", "x86_64"]
    )


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if platform.system() == "Windows":
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            print("Downloading Starship...")
            latest_version = requests.get(release_url).url.split("/")[-1]
            arch = platform.machine().lower()
            if arch in ["amd64", "x86_64"]:
                arch = "x86_64"
            elif arch == "aarch64":
                arch = "aarch64"
            download_url = (
                f"https://github.com/starship/starship/releases/download/{latest_version}/starship-{arch}-pc-windows-msvc.zip"
            )
            download_path = temp_dir / "starship.zip"
            df.download_file(download_url, download_path)
            print("Unzipping Starship...")
            shutil.unpack_archive(download_path, temp_dir)
            print("Installing Starship...")
            bin_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(temp_dir / "starship.exe", bin_dir / "starship.exe")
            config.set("version", latest_version)
    else:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            script_path = temp_dir / "install.sh"

            print("Downloading Starship installer...")
            df.download_file(script_link, script_path)
            bin_dir.mkdir(parents=True, exist_ok=True)

            print("Installing Starship...")
            result = subprocess.run(
                ["sh", str(script_path), "-b", str(bin_dir), "-y"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
            )
            if result.stdout:
                stdout.write(result.stdout)
            if result.stderr:
                stdout.write(result.stderr)
            # Save the (probably) installed version
            latest_version = requests.get(release_url).url.split("/")[-1]
            config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # just remove the binary
    starship_path = bin_dir / "starship"
    if platform.system() == "Windows":
        starship_path = bin_dir / "starship.exe"
    starship_path.unlink(missing_ok=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1]
    current_version = config.get("version", "")
    return str(current_version) != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
