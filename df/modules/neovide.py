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

ID: str = "neovide"
NAME: str = "Neovide"
DESCRIPTION: str = (
    "No Nonsense Neovim Client in Rust, with additional distrobox integration. "
    "For macOS and Windows, please install Neovide using your preferred package manager "
    "(e.g., Homebrew, Scoop, or Chocolatey)."
)
DEPENDENCIES: List[str] = []
CONFLICTING: List[str] = []

VERSION: str = "1.0.3"

release_url = "https://github.com/neovide/neovide/releases/latest"


def is_compatible() -> Union[bool, str]:
    return platform.system() == "Linux" and platform.machine() in ["x86_64"]


def install(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Download the font
    with tempfile.TemporaryDirectory() as temp_dir_str:
        print("Downloading Neovide...")
        temp_dir = Path(temp_dir_str)
        download_path = temp_dir / "neovide.AppImage"
        link = f"{release_url}/download/neovide.AppImage"
        df.download_file(link, download_path)
        # print("Unzipping Neovide...")
        # shutil.unpack_archive(download_path, temp_dir)

        print("Installing Neovide with distrobox wrapper...")

        (Path.home() / ".local" / "bin").mkdir(parents=True, exist_ok=True)
        (Path.home() / ".local" / "share" / "applications").mkdir(parents=True, exist_ok=True)
        # For maximum compatibility, we need to run the appimage with the --appimage-extract flag
        # This is especially useful for running inside distrobox containers
        neovide_path = download_path
        neovide_path.chmod(0o755)
        subprocess.run(
            [neovide_path, "--appimage-extract"],
            cwd=temp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        # Copy the folder to the local lib folder
        (Path.home() / ".local" / "lib").mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            temp_dir / "squashfs-root",
            Path.home() / ".local" / "lib" / "neovide",
            dirs_exist_ok=True,
        )
        # Copy the launcher script (wrapper around neovide
        shutil.copyfile(
            df.DOTFILES_PATH / "neovide" / "neovide",
            Path.home() / ".local" / "bin" / "neovide",
        )
        (Path.home() / ".local" / "bin" / "neovide").chmod(0o755)

        # Copy the desktop file (with changed path flag)
        desktop_file = f"""
[Desktop Entry]
Type=Application
Exec={Path.home() / ".local" / "bin" / "neovide"} %F
Icon=neovide
Name=Neovide (nvim)
Keywords=Text;Editor;
Categories=Utility;TextEditor;
Comment=No Nonsense Neovim Client in Rust
MimeType=text/english;text/plain;text/x-makefile;text/x-c++hdr;text/x-c++src;text/x-chdr;text/x-csrc;text/x-java;text/x-moc;text/x-pascal;text/x-tcl;text/x-tex;application/x-shellscript;text/x-c;text/x-c++;"""
        with open(Path.home() / ".local" / "share" / "applications" / "neovide.desktop", "w") as f:
            f.write(desktop_file)

        # Simlink the icon (delete first if it exists)
        icon_path = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        icon_path.mkdir(parents=True, exist_ok=True)
        icon_path = icon_path / "neovide.svg"
        icon_src_path = Path.home() / ".local" / "lib" / "neovide" / "neovide.svg"
        icon_path.unlink(missing_ok=True)
        shutil.copyfile(icon_src_path, icon_path)
        # Save the installed version
        latest_version = requests.get(release_url).url.split("/")[-1]
        config.set("version", latest_version)


def uninstall(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    # Delete the executable
    (Path.home() / ".local" / "bin" / "neovide").unlink(missing_ok=True)
    # Delete the desktop file and icon
    (Path.home() / ".local" / "share" / "applications" / "neovide.desktop").unlink(missing_ok=True)
    (Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "neovide.svg").unlink(missing_ok=True)
    # Delete the folder
    shutil.rmtree(Path.home() / ".local" / "lib" / "neovide", ignore_errors=True)


def has_update(config: ModuleConfig) -> Union[bool, str]:
    latest_version = requests.get(release_url).url.split("/")[-1]
    current_version = config.get("version", "")
    return str(current_version) != latest_version


def update(config: ModuleConfig, stdout: io.TextIOWrapper) -> None:
    install(config, stdout)  # this will overwrite the old version
