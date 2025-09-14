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
CONFLICTING: List[str] = []

release_url = "https://github.com/starship/starship/releases/latest"
script_link = "https://starship.rs/install.sh"
bin_dir = Path.home() / ".local" / "bin"


def is_compatible() -> Union[bool, str]:
    return platform.system() in ["Linux", "Darwin", "Windows"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    if platform.system() == "Windows":
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            print("Downloading Starship...")
            latest_version = requests.get(release_url).url.split("/")[-1]
            download_url = (
                f"https://github.com/starship/starship/releases/download/{latest_version}/starship-x86_64-pc-windows-msvc.zip"
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
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
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
    return config.get("version") != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)
